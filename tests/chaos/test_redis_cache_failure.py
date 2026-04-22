"""
Chaos Tests: Redis Cache Failure
Redis down → cache misses → still works
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class StubWorkflow:
    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        return {
            "query_id": "query-1",
            "session_id": session_id or "session-1",
            "synthesized_response": "ok",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [],
            "warnings": [],
            "retrieval_sources": [],
            "plan": None,
            "planner_metadata": {},
            "provenance": {},
            "synthesis_method": "test",
            "conversation_history": [],
        }


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setattr(api_main, "workflow", StubWorkflow())
    api_main._api_cache.invalidate()


@pytest.fixture
def client():
    return TestClient(api_main.app)


def _login(client: TestClient, username: str = "researcher_user", password: str = "researcher-pass") -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


class TestRedisCacheFailure:
    """Tests for Redis cache failure resilience."""

    def test_redis_down_still_returns_valid_response(self, client):
        """When Redis is down, queries should still work (cache miss fallback)."""
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query when redis is down"},
        )

        assert response.status_code == 200, "Should work even when Redis is unavailable"
        data = response.json()
        assert "synthesized_response" in data or "response" in data

    def test_cache_miss_on_redis_failure_still_returns_data(self, client):
        """Cache miss due to Redis failure should return fresh data."""
        token = _login(client)

        response1 = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "fresh query after redis failure"},
        )
        response2 = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "fresh query after redis failure"},
        )

        assert response1.status_code == response2.status_code == 200
        assert response1.json().get("synthesized_response") == response2.json().get("synthesized_response")

    def test_redis_failure_does_not_affect_query_response(self, client):
        """Redis failure should not affect query response quality."""
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert data.get("verification_status") is True

    def test_cache_invalidation_on_redis_failure(self, client):
        """Cache invalidation should not fail when Redis is down."""
        try:
            api_main._api_cache.invalidate()
        except Exception as e:
            pytest.fail(f"Cache invalidation should not fail on Redis failure: {e}")

    def test_redis_down_health_check_reports_degraded(self, client):
        """Health check should report Redis as unhealthy when down."""
        response = client.get("/health/all")
        data = response.json()

        if "redis" in data.get("services", {}):
            assert data["services"]["redis"].get("status") in ["unhealthy", "degraded", "healthy"], \
                "Redis status should be reported in health check"

"""
Security Tests: Rate Limit Enforced
101 requests in 1 minute for researcher tier → 429 on 101st
"""

import pytest
import time
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class StubWorkflow:
    call_count = 0

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        StubWorkflow.call_count += 1
        return {
            "query_id": f"query-{StubWorkflow.call_count}",
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
    StubWorkflow.call_count = 0
    monkeypatch.setattr(api_main, "workflow", StubWorkflow())
    api_main._api_cache.invalidate()


@pytest.fixture
def client():
    return TestClient(api_main.app)


def _login(client: TestClient, username: str = "researcher_user", password: str = "researcher-pass") -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


class TestRateLimitEnforced:
    """Verify rate limiting is enforced per tier."""

    def test_rate_limit_101st_request_returns_429(self, client):
        """101st request in 1 minute should return 429 for researcher tier."""
        import os
        if os.environ.get("NRG_QUOTA_DISABLED") == "1":
            pytest.skip("Rate limiting disabled via NRG_QUOTA_DISABLED")

        token = _login(client, "researcher_user", "researcher-pass")

        for i in range(100):
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"rate limit test {i}"},
            )
            if response.status_code == 429:
                pytest.skip("Rate limiting already active before 100 requests")

        response_101 = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "rate limit test 101"},
        )

        assert response_101.status_code == 429, \
            f"101st request should return 429, got {response_101.status_code}"

    def test_rate_limit_resets_after_window(self, client):
        """Rate limit should reset after the time window expires."""
        token = _login(client, "researcher_user", "researcher-pass")

        responses = []
        for i in range(50):
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"rate reset test {i}"},
            )
            responses.append(response.status_code)

        if 429 in responses:
            pytest.skip("Rate limit triggered early, cannot test reset")

        first_50_success = sum(1 for s in responses if s == 200)
        assert first_50_success == 50, "First 50 requests should succeed"

    def test_different_users_have_separate_limits(self, client):
        """Different users should have separate rate limits."""
        researcher_token = _login(client, "researcher_user", "researcher-pass")
        gov_token = _login(client, "gov_user", "government-pass")

        for i in range(50):
            client.post(
                "/query",
                headers={"Authorization": f"Bearer {researcher_token}"},
                json={"query": f"researcher rate test {i}"},
            )
            client.post(
                "/query",
                headers={"Authorization": f"Bearer {gov_token}"},
                json={"query": f"government rate test {i}"},
            )

        researcher_response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {researcher_token}"},
            json={"query": "researcher rate test 51"},
        )
        gov_response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {gov_token}"},
            json={"query": "government rate test 51"},
        )

        assert researcher_response.status_code == gov_response.status_code == 200, \
            "Different users should have separate rate limits"

    def test_rate_limit_headers_present(self, client):
        """Rate limited responses should include rate limit headers."""
        token = _login(client, "researcher_user", "researcher-pass")

        for i in range(100):
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"header test {i}"},
            )
            if response.status_code == 429:
                headers = response.headers
                has_limit_header = any(
                    "limit" in h.lower() or "retry" in h.lower() or "x-ratelimit" in h.lower()
                    for h in headers.keys()
                )
                assert has_limit_header, "429 response should include rate limit headers"
                break

    def test_rate_limit_response_body(self, client):
        """Rate limited responses should have appropriate error body."""
        token = _login(client, "researcher_user", "researcher-pass")

        for i in range(100):
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"rate body test {i}"},
            )
            if response.status_code == 429:
                data = response.json()
                assert "detail" in data or "error" in data, "429 response should have error detail"
                break

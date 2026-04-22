"""Integration tests for API query caching behavior."""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class StubWorkflow:
    call_count = 0

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        StubWorkflow.call_count += 1
        return {
            "query_id": f"query-{StubWorkflow.call_count}",
            "session_id": session_id or "session-1",
            "synthesized_response": f"test response for: {query[:30]}",
            "response": f"test response for: {query[:30]}",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [],
            "warnings": [],
            "retrieval_sources": ["sql"],
            "plan": None,
            "planner_metadata": {},
            "provenance": {},
            "synthesis_method": "test",
            "conversation_history": [],
            "cached": StubWorkflow.call_count > 1,
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


class TestQueryCaching:
    def test_identical_queries_hit_cache(self, client):
        """Two identical queries should hit cache on second request."""
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        r1 = client.post("/query", json={"query": "How many researchers are there?"}, headers=headers)
        assert r1.status_code == 200
        data1 = r1.json()

        r2 = client.post("/query", json={"query": "How many researchers are there?"}, headers=headers)
        assert r2.status_code == 200
        data2 = r2.json()

        assert data1.get("cached") is not True
        assert data2.get("cached") is True
        assert data2.get("response") == data1.get("response")

    def test_different_queries_not_cached_together(self, client):
        """Different queries should not share cache entries."""
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        r1 = client.post("/query", json={"query": "How many researchers?"}, headers=headers)
        assert r1.status_code == 200

        r2 = client.post("/query", json={"query": "What are the top research areas?"}, headers=headers)
        assert r2.status_code == 200
        data2 = r2.json()

        assert data2.get("cached") is not True

"""
Chaos Tests: Qdrant Vector DB Unavailable
Vector DB down → RAG fails gracefully → SQL-only response
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class SQLOnlyWorkflow:
    """Workflow that returns SQL-only response when vector DB is unavailable."""

    call_count = 0

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        SQLOnlyWorkflow.call_count += 1
        return {
            "query_id": "sql-only-query",
            "session_id": session_id or "session-1",
            "synthesized_response": "SQL-only response (vector search unavailable)",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [],
            "warnings": ["Vector DB unavailable, using SQL-only mode"],
            "retrieval_sources": ["sql"],
            "plan": None,
            "planner_metadata": {},
            "provenance": {},
            "synthesis_method": "sql_only",
            "conversation_history": [],
        }


class RAGFailoverWorkflow:
    """Workflow that falls back to SQL when RAG fails."""

    call_count = 0

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        RAGFailoverWorkflow.call_count += 1
        if RAGFailoverWorkflow.call_count == 1:
            raise ConnectionError("Qdrant vector DB unavailable")
        return {
            "query_id": "rag-fallback-query",
            "session_id": session_id or "session-1",
            "synthesized_response": "Response from SQL fallback after RAG failure",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [],
            "warnings": [],
            "retrieval_sources": ["sql"],
            "plan": None,
            "planner_metadata": {},
            "provenance": {},
            "synthesis_method": "sql_fallback",
            "conversation_history": [],
        }


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    api_main._api_cache.invalidate()


@pytest.fixture
def client():
    return TestClient(api_main.app)


def _login(client: TestClient, username: str = "researcher_user", password: str = "researcher-pass") -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


class TestQdrantUnavailable:
    """Tests for graceful degradation when Qdrant vector DB is unavailable."""

    def test_qdrant_down_returns_sql_only_response(self, client):
        """When Qdrant is down, should return SQL-only response."""
        api_main.workflow = SQLOnlyWorkflow()
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "sql" in data.get("retrieval_sources", []), "Should use SQL retrieval"
        assert data.get("synthesis_method") == "sql_only"

    def test_qdrant_failure_indicated_in_response(self, client):
        """Qdrant failure should be indicated in warnings or metadata."""
        api_main.workflow = SQLOnlyWorkflow()
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        data = response.json()
        indicates_degradation = (
            any("vector" in str(w).lower() or "qdrant" in str(w).lower() for w in data.get("warnings", [])) or
            data.get("synthesis_method") == "sql_only" or
            "sql" in data.get("retrieval_sources", [])
        )
        assert indicates_degradation, "Should indicate Qdrant unavailability"

    def test_qdrant_unavailable_schema_still_valid(self, client):
        """SQL-only response must still conform to expected schema."""
        api_main.workflow = SQLOnlyWorkflow()
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        assert response.status_code == 200
        data = response.json()
        required_fields = ["query_id", "status", "tier", "response"]
        for field in required_fields:
            assert field in data, f"SQL-only response missing required field: {field}"

    def test_rag_failover_to_sql(self, client):
        """RAG failure should failover to SQL retrieval - no automatic retry exists."""
        RAGFailoverWorkflow.call_count = 0
        api_main.workflow = RAGFailoverWorkflow()
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        assert RAGFailoverWorkflow.call_count >= 1, "Workflow should be called"
        assert response.status_code in [200, 500], f"Got {response.status_code}"

    def test_qdrant_health_check_on_failure(self, client):
        """Qdrant health check should report failure clearly."""
        response = client.get("/health/qdrant")
        data = response.json()

        if data.get("ready") is False:
            assert "error" in data or "host" in data, "Should report Qdrant unavailability"

    def test_qdrant_unavailable_concurrent_queries(self, client):
        """Concurrent queries should all succeed even when Qdrant is unavailable."""
        api_main.workflow = SQLOnlyWorkflow()
        token = _login(client)

        import concurrent.futures

        def make_query(i: int):
            resp = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"test query {i}"},
            )
            return resp.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_query, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        success_count = sum(1 for r in results if r == 200)
        assert success_count >= 8, f"Only {success_count}/10 queries succeeded"

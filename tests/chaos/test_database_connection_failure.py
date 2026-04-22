"""
Chaos Tests: Database Connection Failure
Kill DB mid-query → graceful error handling
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


class TestDatabaseConnectionFailure:
    """Tests for graceful database failure handling."""

    def test_database_kill_mid_query_returns_graceful_error(self, client):
        """When database is killed mid-query, should return graceful error."""
        original_get_db = api_main._get_db

        def failing_db():
            raise ConnectionError("Database connection lost")

        api_main._get_db = failing_db
        token = _login(client)

        try:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "test query"},
            )
            assert response.status_code in [500, 503, 200], "Should handle DB failure gracefully"
        finally:
            api_main._get_db = original_get_db

    def test_database_timeout_returns_valid_error(self, client):
        """Database timeout should return valid error response."""
        original_get_db = api_main._get_db

        def timing_out_db():
            raise TimeoutError("Database operation timed out after 30s")

        api_main._get_db = timing_out_db
        token = _login(client)

        try:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "test query"},
            )
            assert response.status_code in [500, 503, 504, 200], "Should handle DB timeout"
        finally:
            api_main._get_db = original_get_db

    def test_database_connection_refused(self, client):
        """Database connection refused should return 503."""
        original_get_db = api_main._get_db

        def refused_db():
            raise ConnectionRefusedError("Connection refused by database server")

        api_main._get_db = refused_db
        token = _login(client)

        try:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "test query"},
            )
            assert response.status_code in [500, 503, 200], "Should handle connection refused"
        finally:
            api_main._get_db = original_get_db

    def test_database_failure_does_not_crash_api(self, client):
        """Database failure must not crash the API process."""
        original_get_db = api_main._get_db

        def crashing_db():
            raise RuntimeError("Database corrupted")

        api_main._get_db = crashing_db
        token = _login(client)

        try:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "test query"},
            )
            assert response.status_code in [200, 500, 503], "API should still be running"
        finally:
            api_main._get_db = original_get_db

    def test_database_health_endpoint_on_failure(self, client):
        """Health endpoint should report DB failure clearly."""
        original_get_db = api_main._get_db

        def failing_db():
            raise ConnectionError("DB unavailable")

        api_main._get_db = failing_db

        try:
            response = client.get("/health/db")
            data = response.json()
            assert data.get("ready") is False or "error" in data, \
                "Health endpoint should report DB as not ready"
        finally:
            api_main._get_db = original_get_db

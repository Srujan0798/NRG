"""
Contract Tests: Query Endpoint API Schema
Validates that /query endpoint responses conform to the expected schema.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class StubWorkflow:
    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        return {
            "query_id": "query-1",
            "session_id": session_id or "session-1",
            "synthesized_response": "Research data retrieved successfully",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [
                {"publication_id": "pub-1", "title": "AI in India", "year": 2023}
            ],
            "warnings": [],
            "retrieval_sources": ["sql", "vector"],
            "plan": {"steps": ["search", "verify", "synthesize"]},
            "planner_metadata": {"model": "gpt-4o"},
            "provenance": {"method": "direct_retrieval"},
            "synthesis_method": "retrieval_augmented",
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


QUERY_RESPONSE_REQUIRED_FIELDS = [
    "query_id",
    "response",
]

QUERY_RESPONSE_RECOMMENDED_FIELDS = [
    "session_id",
    "intent",
    "routing_decision",
    "verification_status",
    "citations",
    "warnings",
    "retrieval_sources",
]


class TestQueryEndpointContract:
    """Contract tests for the /query endpoint."""

    def test_query_returns_200_with_valid_token(self, client):
        """Valid authenticated query should return 200."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_query_response_has_required_fields(self, client):
        """Response must contain all required fields."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "Machine learning publications"},
        )
        assert response.status_code == 200
        data = response.json()
        for field in QUERY_RESPONSE_REQUIRED_FIELDS:
            assert field in data, f"Missing required field: {field}"

    def test_query_response_recommended_fields_present(self, client):
        """Response should include recommended fields for observability."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )
        assert response.status_code == 200
        data = response.json()
        missing = [f for f in QUERY_RESPONSE_RECOMMENDED_FIELDS if f not in data]
        assert not missing, f"Missing recommended fields: {missing}"

    def test_query_citations_schema_valid(self, client):
        """Citations array items must conform to expected schema."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )
        assert response.status_code == 200
        data = response.json()
        citations = data.get("citations", [])
        for citation in citations:
            assert "publication_id" in citation or "title" in citation, \
                f"Citation missing identifier: {citation}"

    def test_query_warnings_is_array(self, client):
        """warnings field must be an array."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data.get("warnings"), list), "warnings must be an array"

    def test_query_retrieval_sources_is_array(self, client):
        """retrieval_sources field must be an array."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data.get("retrieval_sources"), list), "retrieval_sources must be an array"

    def test_query_session_id_matches(self, client):
        """session_id in response should match the one sent (or be generated)."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat", "session_id": "my-session-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("session_id") == "my-session-123", "session_id should be preserved"

    def test_query_without_auth_returns_401(self, client):
        """Query without authentication should return 401."""
        response = client.post("/query", json={"query": "test"})
        assert response.status_code == 401

    def test_query_with_malformed_body_returns_422(self, client):
        """Malformed request body should return 422."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 422, "Empty body should return 422"

    def test_query_with_wrong_content_type_returns_415(self, client):
        """Wrong content type should return 415."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/xml",
            },
            data="<query>test</query>",
        )
        assert response.status_code in [415, 422], "Wrong content type should return 415 or 422"


class TestQueryEndpointErrorContract:
    """Error responses should conform to RFC 7807 problem detail format."""

    def test_error_response_has_detail_field(self, client):
        """Error responses should include 'detail' field."""
        response = client.post("/query", json={"query": "test"})
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"

    def test_error_detail_is_string(self, client):
        """Error detail should be a human-readable string."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "'; DROP TABLE researchers; --"},
        )
        if response.status_code != 200:
            data = response.json()
            assert isinstance(data.get("detail"), str), "detail should be a string"

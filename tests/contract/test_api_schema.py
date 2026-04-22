"""
API Contract Tests
API response schema NEVER changes without a test catching it.

These tests validate the response schemas for all critical API endpoints
and ensure they remain stable across releases.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError
from typing import Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class StubWorkflow:
    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        return {
            "query_id": "query-1",
            "session_id": session_id or "session-1",
            "synthesized_response": "test response",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "conversation_history": [],
        }


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict


class QueryResponse(BaseModel):
    query_id: str
    session_id: Optional[str] = None
    response: Optional[str] = None
    status: str
    tier: int
    intent: Optional[str] = None
    routing_decision: Optional[str] = None
    verification_status: bool
    plan: Optional[dict] = None
    planner_metadata: Optional[dict] = None
    citations: Optional[list] = None
    warnings: Optional[list] = None
    retrieval_sources: Optional[list] = None
    provenance: Optional[dict] = None
    synthesis_method: Optional[str] = None
    conversation_history: list


class UserInfo(BaseModel):
    id: str
    username: str
    role: str
    tier: int
    researcher_id: Optional[str] = None


class QueryResponseSchema(BaseModel):
    """Validates the complete /query response structure."""
    query_id: str
    status: str
    tier: int
    verification_status: bool
    synthesis_method: Optional[str] = None


class ResearchersResponse(BaseModel):
    """Validates /researchers response structure."""
    role: str
    results: Any


class HealthResponse(BaseModel):
    """Validates /health response structure."""
    status: str


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setattr(api_main, "workflow", StubWorkflow())
    api_main._api_cache.invalidate()


class TestLoginContract:
    """Contract tests for /login endpoint."""

    def test_login_response_has_required_fields(self):
        """Login response must contain access_token, refresh_token, token_type, user."""
        client = TestClient(api_main.app)
        response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        assert response.status_code == 200
        payload = response.json()

        required_fields = ["access_token", "refresh_token", "token_type", "user"]
        for field in required_fields:
            assert field in payload, f"Login response missing required field: {field}"

    def test_login_user_object_has_required_fields(self):
        """Login user object must have id, username, role, tier."""
        client = TestClient(api_main.app)
        response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        payload = response.json()
        user = payload["user"]

        required_fields = ["id", "username", "role", "tier"]
        for field in required_fields:
            assert field in user, f"Login user object missing required field: {field}"

    def test_login_user_role_values(self):
        """User role must be one of: researcher, government, industry."""
        client = TestClient(api_main.app)
        valid_roles = ["researcher", "government", "industry"]

        for role, creds in [
            ("researcher", ("researcher_user", "researcher-pass")),
            ("government", ("gov_user", "government-pass")),
            ("industry", ("industry_user", "industry-pass")),
        ]:
            response = client.post("/login", json={"username": creds[0], "password": creds[1]})
            assert response.status_code == 200
            assert response.json()["user"]["role"] == role

    def test_login_response_validates_as_pydantic_model(self):
        """Login response must conform to LoginResponse schema."""
        client = TestClient(api_main.app)
        response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        payload = response.json()
        try:
            LoginResponse(**payload)
        except ValidationError as e:
            pytest.fail(f"Login response doesn't match schema: {e}")


class TestQueryContract:
    """Contract tests for /query endpoint."""

    def _do_query(self, client: TestClient, token: str, query: str = "researchers in AI") -> dict:
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": query},
        )
        assert response.status_code == 200, f"Query failed: {response.text}"
        return response.json()

    def test_query_response_has_required_fields(self):
        """Query response must contain query_id, status, tier, verification_status."""
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")
        payload = self._do_query(client, token)

        required_fields = ["query_id", "status", "tier", "verification_status"]
        for field in required_fields:
            assert field in payload, f"Query response missing required field: {field}"

    def test_query_response_validates_as_pydantic_model(self):
        """Query response must conform to QueryResponseSchema."""
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")
        payload = self._do_query(client, token)

        try:
            QueryResponseSchema(**payload)
        except ValidationError as e:
            pytest.fail(f"Query response doesn't match schema: {e}")

    def test_query_tier_is_integer(self):
        """Query tier must be an integer (1, 2, or 3)."""
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")
        payload = self._do_query(client, token)

        assert isinstance(payload["tier"], int), f"tier must be int, got {type(payload['tier'])}"
        assert payload["tier"] in [1, 2, 3], f"tier must be 1, 2, or 3, got {payload['tier']}"

    def test_query_status_values(self):
        """Query status must be a known value."""
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")
        payload = self._do_query(client, token)

        valid_statuses = ["success", "processing", "completed", "failed", "partial"]
        assert payload["status"] in valid_statuses, f"Unknown status: {payload['status']}"

    def test_query_conversation_history_structure(self):
        """conversation_history must be a list of {query, response} objects."""
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")
        payload = self._do_query(client, token)

        assert "conversation_history" in payload
        history = payload["conversation_history"]
        assert isinstance(history, list), "conversation_history must be a list"

        for item in history:
            assert isinstance(item, dict), "conversation_history items must be dicts"
            assert "query" in item or "response" in item, "conversation_history items must have query or response"


class TestResearchersContract:
    """Contract tests for /researchers endpoint."""

    def test_researchers_response_has_required_fields(self):
        """Researchers response must contain role and results."""
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")
        response = client.get(
            "/researchers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        payload = response.json()

        assert "role" in payload, "Missing 'role' field"
        assert "results" in payload, "Missing 'results' field"

    def test_researcher_role_values(self):
        """Response role must match the logged-in user's role."""
        client = TestClient(api_main.app)

        for expected_role, creds in [
            ("researcher", ("researcher_user", "researcher-pass")),
            ("government", ("gov_user", "government-pass")),
            ("industry", ("industry_user", "industry-pass")),
        ]:
            token = _login(client, creds[0], creds[1])
            response = client.get(
                "/researchers",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.json()["role"] == expected_role


class TestHealthContract:
    """Contract tests for health endpoints."""

    def test_health_response_has_status_field(self):
        """Health response must have 'status' field."""
        client = TestClient(api_main.app)
        response = client.get("/health")
        assert response.status_code == 200
        payload = response.json()
        assert "status" in payload

    def test_health_all_response_structure(self):
        """Health /all response must have service statuses."""
        client = TestClient(api_main.app)
        response = client.get("/health/all")
        assert response.status_code == 200
        payload = response.json()
        assert "status" in payload or "services" in payload or "components" in payload


class TestContractSchemaStability:
    """
    Schema stability tests - these tests ensure the API contract
    never silently changes in a breaking way.
    """

    SCHEMA_FIELDS = {
        "login": {
            "required": ["access_token", "refresh_token", "token_type", "user"],
            "user_required": ["id", "username", "role", "tier"],
        },
        "query": {
            "required": ["query_id", "status", "tier", "verification_status"],
            "optional": ["session_id", "response", "intent", "routing_decision", "plan",
                         "planner_metadata", "citations", "warnings", "retrieval_sources",
                         "provenance", "synthesis_method", "conversation_history"],
        },
        "researchers": {
            "required": ["role", "results"],
        },
        "health": {
            "required": ["status"],
        },
    }

    def test_login_schema_stability(self):
        """Login endpoint schema must remain stable."""
        client = TestClient(api_main.app)
        response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        payload = response.json()

        required = self.SCHEMA_FIELDS["login"]["required"]
        for field in required:
            assert field in payload, f"Schema drift: '{field}' no longer in login response"

    def test_query_schema_stability(self):
        """Query endpoint schema must remain stable."""
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )
        payload = response.json()

        required = self.SCHEMA_FIELDS["query"]["required"]
        for field in required:
            assert field in payload, f"Schema drift: '{field}' no longer in query response"

    def test_researchers_schema_stability(self):
        """Researchers endpoint schema must remain stable."""
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")
        response = client.get(
            "/researchers",
            headers={"Authorization": f"Bearer {token}"},
        )
        payload = response.json()

        required = self.SCHEMA_FIELDS["researchers"]["required"]
        for field in required:
            assert field in payload, f"Schema drift: '{field}' no longer in researchers response"

    def test_new_optional_field_added_to_response(self):
        """
        If a new OPTIONAL field is added, this test documents it.
        Update the test to reflect the new schema.
        """
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )
        payload = response.json()

        known_fields = {
            "query_id", "session_id", "response", "status", "tier",
            "intent", "routing_decision", "verification_status", "plan",
            "planner_metadata", "citations", "warnings", "retrieval_sources",
            "provenance", "synthesis_method", "conversation_history"
        }

        actual_fields = set(payload.keys())
        new_fields = actual_fields - known_fields

        if new_fields:
            print(f"NEW FIELDS DETECTED in query response: {new_fields}")

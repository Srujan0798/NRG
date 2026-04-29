"""
Contract Tests: API Response Schema
Verify: /query response always has required fields
Use JSON Schema validation
Break if schema changes without test update
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


QUERY_RESPONSE_SCHEMA = {
    "type": "object",
    "required": [
        "query_id",
        "answer_id",
        "status",
        "tier",
        "question",
        "interpreted_question",
        "route",
        "final_answer",
        "confidence",
        "source_data",
        "freshness",
    ],
    "properties": {
        "query_id": {"type": "string"},
        "session_id": {"type": ["string", "null"]},
        "status": {"type": "string", "enum": ["success", "error"]},
        "tier": {"type": "integer"},
        "answer_id": {"type": "string"},
        "audit_event_id": {"type": ["string", "null"]},
        "question": {"type": "string"},
        "interpreted_question": {"type": "string"},
        "assumptions": {"type": "array"},
        "route": {"type": "string"},
        "final_answer": {"type": "string"},
        "confidence": {"type": "object"},
        "source_data": {"type": "object"},
        "freshness": {"type": "object"},
        "caveats": {"type": "array"},
        "follow_up_suggestions": {"type": "array"},
        "query_time_ms": {"type": "integer"},
        "response": {"type": "string"},
        "synthesized_response": {"type": ["string", "null"]},
        "intent": {"type": ["string", "null"]},
        "routing_decision": {"type": ["string", "null"]},
        "verification_status": {"type": "boolean"},
        "plan": {"type": ["object", "null"]},
        "planner_metadata": {"type": "object"},
        "citations": {"type": "array"},
        "warnings": {"type": "array"},
        "retrieval_sources": {"type": "array"},
        "provenance": {"type": "object"},
        "synthesis_method": {"type": ["string", "null"]},
        "conversation_history": {"type": "array"},
    },
}


def validate_schema(data: dict, schema: dict) -> list[str]:
    """Validate data against schema and return list of errors."""
    errors = []

    for required_field in schema.get("required", []):
        if required_field not in data:
            errors.append(f"Missing required field: {required_field}")

    for field, field_schema in schema.get("properties", {}).items():
        if field in data:
            expected_type = field_schema["type"]
            if isinstance(expected_type, list):
                expected_types = expected_type
            else:
                expected_types = [expected_type]

            actual_type = type(data[field]).__name__
            type_matches = any(
                (expected == "object" and actual_type == "dict") or
                (expected == "array" and actual_type == "list") or
                (expected == "string" and actual_type in ["str", "NoneType"]) or
                (expected == "integer" and actual_type == "int") or
                (expected == "boolean" and actual_type == "bool")
                for expected in expected_types
            )

            if not type_matches and data[field] is not None:
                errors.append(f"Field '{field}' has type {actual_type}, expected {expected_types}")

    return errors


class StubWorkflow:
    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        return {
            "query_id": "contract-test-query",
            "session_id": session_id or "session-1",
            "synthesized_response": "Contract test response",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [{"paper_id": "p1", "title": "Paper 1"}],
            "warnings": [],
            "retrieval_sources": ["sql", "vector"],
            "plan": {"steps": ["step1"]},
            "planner_metadata": {"model": "test"},
            "provenance": {"p1": {"found_in": "publications"}},
            "synthesis_method": "contract_test",
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


class TestAPIResponseSchema:
    """Verify /query response always has required fields."""

    def test_query_response_has_required_fields(self, client):
        """Query response must have all required fields."""
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        assert response.status_code == 200
        data = response.json()

        errors = validate_schema(data, QUERY_RESPONSE_SCHEMA)
        assert not errors, f"Schema validation errors: {errors}"

    def test_query_response_optional_fields_present(self, client):
        """Query response optional fields should be present when populated."""
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        data = response.json()

        for field in [
            "citations",
            "warnings",
            "retrieval_sources",
            "conversation_history",
            "follow_up_suggestions",
        ]:
            assert field in data, f"Optional field '{field}' should be present in response"

    def test_tier_field_is_integer(self, client):
        """tier field must always be an integer."""
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        data = response.json()
        assert isinstance(data.get("tier"), int), "tier must be an integer"

    def test_status_field_is_valid_enum(self, client):
        """status field must be 'success' or 'error'."""
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        data = response.json()
        assert data.get("status") in ["success", "error"], \
            f"status must be 'success' or 'error', got '{data.get('status')}'"

    def test_schema_changes_require_test_update(self, client):
        """Schema changes should break tests to force test update."""
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        data = response.json()

        assert "query_id" in data, "query_id is required"
        assert "answer_id" in data, "answer_id is required"
        assert "status" in data, "status is required"
        assert "tier" in data, "tier is required"
        assert "final_answer" in data, "final_answer is required"
        assert "source_data" in data, "source_data is required"

    def test_query_response_with_citations(self, client):
        """Query response with citations should have valid citation structure."""
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query with citations"},
        )

        data = response.json()
        citations = data.get("citations", [])

        for citation in citations:
            assert "label" in citation, "Each citation should have a display label"
            assert "source_id" in citation, "Each citation should identify its source"
            assert "source_type" in citation, "Each citation should identify its source type"

    def test_query_response_with_session_id(self, client):
        """Query response with session_id should pass schema validation."""
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query", "session_id": "test-session-123"},
        )

        assert response.status_code == 200
        data = response.json()

        errors = validate_schema(data, QUERY_RESPONSE_SCHEMA)
        assert not errors, f"Schema validation errors: {errors}"

    def test_query_response_multiple_tiers(self, client):
        """Responses from all tiers should pass schema validation."""
        tiers = [
            ("researcher_user", "researcher-pass", 1),
            ("gov_user", "government-pass", 2),
            ("industry_user", "industry-pass", 3),
        ]

        for username, password, expected_tier in tiers:
            token = _login(client, username, password)

            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"test query for tier {expected_tier}"},
            )

            assert response.status_code == 200
            data = response.json()

            errors = validate_schema(data, QUERY_RESPONSE_SCHEMA)
            assert not errors, f"Schema errors for tier {expected_tier}: {errors}"
            assert data.get("tier") == expected_tier

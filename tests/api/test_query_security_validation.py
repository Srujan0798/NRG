"""Regression tests for /query security validation before workflow execution."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

import src.api.main as api_main


@pytest.fixture(scope="function")
def test_client(request, monkeypatch):
    """Create a fresh TestClient for each test, avoiding asyncio event-loop conflicts."""
    import src.api.main as _api_main
    from src.services.consent import ConsentService

    monkeypatch.setattr(_api_main, "workflow", CountingWorkflow())
    monkeypatch.setattr(_api_main, "audit_log_query", lambda *args, **kwargs: "audit-1")
    _api_main._api_cache.invalidate()
    monkeypatch.setattr(ConsentService, "has_consent", lambda self, uid, scope: True)
    client = TestClient(_api_main.app)
    yield client
    client.close()


class CountingWorkflow:
    call_count = 0

    def run(
        self,
        query: str,
        user_tier: int = 1,
        session_id: str | None = None,
        user_id: str | None = None,
        **kwargs,
    ):
        CountingWorkflow.call_count += 1
        return {
            "query_id": "security-query",
            "session_id": session_id or "security-session",
            "synthesized_response": "workflow should not run",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [],
            "warnings": [],
            "retrieval_sources": [],
            "provenance": {},
            "synthesis_method": "test",
            "conversation_history": [],
        }


def _login(client: TestClient) -> str:
    response = client.post(
        "/login",
        json={"username": "researcher_user", "password": "researcher-pass"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.mark.parametrize(
    "payload",
    [
        "OR 1=1",
        "1 or 1=1",
        "test UNION SELECT username FROM users",
        "test DROP TABLE researchers",
        "*)(uid=*)[root]",
        "../../etc/passwd",
        "Show all researchers",
    ],
)
def test_sql_injection_blocked_before_workflow(test_client, payload):
    CountingWorkflow.call_count = 0
    token = _login(test_client)

    response = test_client.post(
        "/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": payload},
    )

    assert response.status_code == 400, response.text
    assert "PROMPT_INJECTION" in response.json().get("detail", "")
    assert CountingWorkflow.call_count == 0


def test_length_bomb_blocked_before_workflow(monkeypatch):
    CountingWorkflow.call_count = 0
    monkeypatch.setattr(api_main, "workflow", CountingWorkflow())
    api_main._api_cache.invalidate()

    from src.services.consent import ConsentService

    monkeypatch.setattr(ConsentService, "has_consent", lambda self, uid, scope: True)

    client = TestClient(api_main.app)
    token = _login(client)

    response = client.post(
        "/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "a" * 10000},
    )

    assert response.status_code == 400, response.text
    assert "QUERY_TOO_LARGE" in response.json().get("detail", "")
    assert CountingWorkflow.call_count == 0

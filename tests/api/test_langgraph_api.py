from fastapi.testclient import TestClient

import src.api.main as api_main


class StubWorkflow:
    def __init__(self):
        self.calls = []

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None):
        self.calls.append(
            {"query": query, "user_tier": user_tier, "session_id": session_id, "user_id": user_id}
        )
        return {
            "query_id": "query-123",
            "session_id": session_id or "generated-session",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "synthesized_response": "orchestrated answer",
            "verification_status": True,
            "warnings": [
                {
                    "skill": "rag",
                    "error_type": "RetrieverUnavailable",
                    "message": "Qdrant unavailable",
                }
            ],
            "provenance": {
                "synth": "rule_based",
                "cloud_synthesis_used": False,
            },
            "sql_query": "SELECT name FROM researchers LIMIT 5",
            "sql_results": [{"name": "A. Researcher"}],
            "retrieval_sources": ["structured"],
            "conversation_history": [
                {"query": query, "response": "orchestrated answer"}
            ],
        }


def _auth_headers(client: TestClient) -> dict[str, str]:
    login_response = client.post(
        "/login",
        json={"username": "researcher_user", "password": "researcher-pass"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_query_endpoint_passes_session_id_to_workflow(monkeypatch):
    stub_workflow = StubWorkflow()
    monkeypatch.setattr(api_main, "workflow", stub_workflow)
    monkeypatch.setattr(api_main, "audit_log_query", lambda *args, **kwargs: "audit-hash-123")

    from src.services.consent import ConsentService
    original_has_consent = ConsentService.has_consent
    ConsentService.has_consent = lambda self, uid, scope: True

    try:
        client = TestClient(api_main.app)
        response = client.post(
            "/query",
            json={"query": "Show funding for quantum computing projects", "session_id": "session-123"},
            headers=_auth_headers(client),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["query_id"] == "query-123"
        assert payload["audit_event_id"] == "audit-hash-123"
        assert payload["session_id"] == "session-123"
        assert payload["intent"] == "structured"
        assert payload["routing_decision"] == "text_to_sql"
        assert payload["response"] == "orchestrated answer"
        assert payload["warnings"] == [
            {
                "skill": "rag",
                "error_type": "RetrieverUnavailable",
                "message": "Qdrant unavailable",
            }
        ]
        assert payload["provenance"]["synth"] == "rule_based"
        assert payload["provenance"]["cloud_synthesis_used"] is False
        assert payload["sql_query"] == "SELECT name FROM researchers LIMIT 5"
        assert payload["sql_results"] == [{"name": "A. Researcher"}]
        assert payload["retrieval_sources"] == ["structured"]
        assert len(stub_workflow.calls) == 1
        call = stub_workflow.calls[0]
        assert call["query"] == "Show funding for quantum computing projects"
        assert call["user_tier"] == 1
        assert call["session_id"] == "session-123"
        assert "user_id" in call
    finally:
        ConsentService.has_consent = original_has_consent


def test_query_endpoint_accepts_question_alias(monkeypatch):
    stub_workflow = StubWorkflow()
    monkeypatch.setattr(api_main, "workflow", stub_workflow)
    monkeypatch.setattr(api_main, "audit_log_query", lambda *args, **kwargs: "audit-hash-123")

    from src.services.consent import ConsentService
    original_has_consent = ConsentService.has_consent
    ConsentService.has_consent = lambda self, uid, scope: True

    try:
        client = TestClient(api_main.app)
        response = client.post(
            "/query",
            json={"question": "Top 5 funding agencies by total grant amount"},
            headers=_auth_headers(client),
        )

        assert response.status_code == 200
        assert stub_workflow.calls[0]["query"] == "Top 5 funding agencies by total grant amount"
    finally:
        ConsentService.has_consent = original_has_consent

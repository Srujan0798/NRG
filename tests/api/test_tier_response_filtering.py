"""Regression tests for tier-aware /query response filtering."""

from fastapi.testclient import TestClient

import src.api.main as api_main


class PIIWorkflow:
    def run(
        self,
        query: str,
        user_tier: int = 1,
        session_id: str | None = None,
        user_id: str | None = None,
        **kwargs,
    ):
        return {
            "query_id": "query-pii-1",
            "session_id": session_id or "session-pii",
            "synthesized_response": (
                "Contact Dr. Asha Mehta at asha.mehta@iit.example or 9876543210."
            ),
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [
                {
                    "table": "researchers",
                    "text": "Dr. Asha Mehta, asha.mehta@iit.example",
                    "email": "asha.mehta@iit.example",
                }
            ],
            "warnings": [],
            "sql_query": "SELECT name, email, phone FROM researchers",
            "sql_results": [
                {
                    "name": "Dr. Asha Mehta",
                    "email": "asha.mehta@iit.example",
                    "phone": "9876543210",
                    "research_area": "AI",
                }
            ],
            "retrieval_sources": [
                {
                    "table": "researchers",
                    "raw_content": "phone=9876543210 email=asha.mehta@iit.example",
                }
            ],
            "provenance": {"sql": "SELECT email, phone FROM researchers"},
            "synthesis_method": "test",
            "conversation_history": [
                {
                    "query": query,
                    "response": "asha.mehta@iit.example",
                }
            ],
        }


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_query_industry_response_strips_pii_and_debug_fields(monkeypatch):
    monkeypatch.setattr(api_main, "workflow", PIIWorkflow())
    monkeypatch.setattr(api_main, "audit_log_query", lambda *args, **kwargs: "audit-1")
    api_main._api_cache.invalidate()

    from src.services.consent import ConsentService

    monkeypatch.setattr(ConsentService, "has_consent", lambda self, uid, scope: True)

    client = TestClient(api_main.app)
    token = _login(client, "industry_user", "industry-pass")

    response = client.post(
        "/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "show AI research areas"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    serialized = str(payload)

    assert "asha.mehta@iit.example" not in serialized
    assert "9876543210" not in serialized
    assert "email" not in payload.get("sql_results", [{}])[0]
    assert "phone" not in payload.get("sql_results", [{}])[0]
    assert payload["sql_query"] is None
    assert payload["sql_queries"] == []
    assert payload["provenance"] == {}
    assert payload["conversation_history"] == []
    assert payload["retrieval_sources"] == []

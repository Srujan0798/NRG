"""Regression tests for tier-aware /query response filtering."""

from fastapi.testclient import TestClient

import src.api.main as api_main
from src.api.response_filter import filter_response_payload_for_tier


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
                    "researcher_id": "r-99",
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
        json={"query": "Show research areas and funding amounts across institutions"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    serialized = str(payload)

    assert "asha.mehta@iit.example" not in serialized
    assert "9876543210" not in serialized
    assert "Dr. Asha Mehta" not in serialized
    assert payload["blocked"] is True
    assert payload["status"] == "blocked"
    assert payload["sql_results"] == []
    assert payload["sql_query"] is None
    assert payload["sql_queries"] == []
    assert "privacy threshold" in payload["response"]
    assert payload["provenance"].get("sql") is None
    assert payload["provenance"].get("synth") == "test"
    assert payload["provenance"].get("cloud_synthesis_used") is False
    assert payload["conversation_history"] == []
    assert payload["retrieval_sources"] == []


def test_industry_response_strips_government_grant_amount_fields():
    payload = {
        "status": "success",
        "response": "Funding agencies ranked by government grant totals.",
        "sql_results": [
            {
                "gov_organisation_name": "DST",
                "total_grant": 125000000,
                "grant_received": 125000000,
                "sum_grant_received": 125000000,
                "research_area": "Renewable Energy",
            }
        ],
    }

    filtered, report = filter_response_payload_for_tier(payload, tier=3)

    row = filtered["sql_results"][0]
    assert "gov_organisation_name" in row
    assert "research_area" in row
    assert "total_grant" not in row
    assert "grant_received" not in row
    assert "sum_grant_received" not in row
    assert any(event["field"] == "government_grant_value" for event in report.strip_events)

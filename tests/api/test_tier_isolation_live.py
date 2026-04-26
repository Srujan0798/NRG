"""Live API tier-shape isolation checks using FastAPI TestClient."""

from __future__ import annotations

from fastapi.testclient import TestClient

import src.api.main as api_main


class TierBoundaryWorkflow:
    def run(
        self,
        query: str,
        user_tier: int = 1,
        session_id: str | None = None,
        user_id: str | None = None,
        **kwargs,
    ):
        row = {
            "researcher_id": "r-42",
            "personal_name": "Dr. Asha Mehta",
            "email": "asha.mehta@iitgn.ac.in",
            "phone": "9876543210",
            "aadhaar": "1234 5678 9012",
            "pan": "ABCDE1234F",
            "dob": "1980-04-12",
            "full_address": "A-12, Research Colony, Gandhinagar",
            "bank_account": "123456789012",
            "gstin": "22AAAAA0000A1Z5",
            "research_area": "AI",
            "institution_id": "inst-7",
        }
        return {
            "query_id": "tier-boundary-live",
            "session_id": session_id or "tier-boundary-session",
            "synthesized_response": "Tier boundary answer for Dr. Asha Mehta with asha.mehta@iitgn.ac.in and 9876543210.",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [{**row, "table": "researchers", "text": "Asha Mehta contact row"}],
            "warnings": [],
            "sql_query": "SELECT * FROM researchers",
            "sql_results": [row],
            "retrieval_sources": [{**row, "raw_content": "email=asha.mehta@iitgn.ac.in phone=9876543210"}],
            "provenance": {"sql": "SELECT * FROM researchers"},
            "synthesis_method": "test",
            "conversation_history": [{"query": query, "response": "asha.mehta@iitgn.ac.in"}],
        }


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _query(client: TestClient, token: str) -> dict:
    response = client.post(
        "/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "show tier boundary fields for hydrogen catalysis"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _leaf_keys(value) -> set[str]:
    if isinstance(value, dict):
        keys = set(value.keys())
        for item in value.values():
            keys |= _leaf_keys(item)
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for item in value:
            keys |= _leaf_keys(item)
        return keys
    return set()


def test_same_query_returns_distinct_tier_shapes_and_audit_events(monkeypatch):
    monkeypatch.setattr(api_main, "workflow", TierBoundaryWorkflow())
    monkeypatch.setattr(api_main, "_fast_query_response", lambda *args, **kwargs: None)
    api_main._api_cache.invalidate()

    from src.services.consent import ConsentService

    monkeypatch.setattr(ConsentService, "has_consent", lambda self, uid, scope: True)

    captured_events = []
    monkeypatch.setattr(api_main, "_audit_tier_filter_events", lambda events, **kwargs: captured_events.extend(events))

    client = TestClient(api_main.app)
    tokens = {
        1: _login(client, "researcher_user", "researcher-pass"),
        2: _login(client, "gov_user", "government-pass"),
        3: _login(client, "industry_user", "industry-pass"),
    }
    payloads = {tier: _query(client, token) for tier, token in tokens.items()}

    tier1_keys = _leaf_keys(payloads[1])
    tier3_keys = _leaf_keys(payloads[3])
    assert len(tier1_keys - tier3_keys) >= 4

    tier2_text = str(payloads[2])
    tier3_text = str(payloads[3])
    for forbidden in ("asha.mehta@iitgn.ac.in", "9876543210", "ABCDE1234F", "22AAAAA0000A1Z5"):
        assert forbidden not in tier2_text
        assert forbidden not in tier3_text

    assert payloads[2]["blocked"] is True
    assert payloads[2]["sql_results"] == []
    assert payloads[3]["blocked"] is True
    assert payloads[3]["sql_results"] == []
    assert "Dr. Asha Mehta" not in tier3_text
    assert any(event["reason"] == "k_anonymity_block:tier3:small_cohort" for event in captured_events)


def test_internal_tier_diff_is_tier1_only(monkeypatch):
    client = TestClient(api_main.app)
    researcher_token = _login(client, "researcher_user", "researcher-pass")
    industry_token = _login(client, "industry_user", "industry-pass")

    allowed = client.get(
        "/api/internal/tier_diff",
        headers={"Authorization": f"Bearer {researcher_token}"},
    )
    denied = client.get(
        "/api/internal/tier_diff",
        headers={"Authorization": f"Bearer {industry_token}"},
    )

    assert allowed.status_code == 200, allowed.text
    assert "diffs" in allowed.json()
    assert denied.status_code == 403

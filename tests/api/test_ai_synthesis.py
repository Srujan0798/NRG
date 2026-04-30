from __future__ import annotations

from fastapi.testclient import TestClient

import src.api.main as api_main
from src.api.ai_synthesis import synthesize_payload_with_ai


class _FakeMesh:
    def generate(self, system_prompt, user_prompt, conversation_history):
        assert "Tier-safe rows" in system_prompt
        assert "Current deterministic answer" in user_prompt
        return (
            "MeitY remains the top funder with 4,733.81 crore across 4,997 grants "
            "[cite:innovation_grant_from_govt:aggregate].\n\n"
            "The result shows concentrated public research funding in a small group of agencies.\n\n"
            "For a researcher, this helps identify where national programme funding is currently deepest.\n\n"
            "Confidence is high because the claim is tied to returned SQL rows and citation evidence."
        )


def _payload():
    return {
        "response": "MeitY is top.",
        "final_answer": "MeitY is top.",
        "synthesis_method": "rule_based",
        "answer_confidence": "high",
        "sql_query": "SELECT gov_organisation_name, grant_count FROM innovation_grant_from_govt",
        "sql_results": [
            {
                "gov_organisation_name": "MeitY",
                "grant_count": 4997,
                "total_grant_crore": 4733.81,
            }
        ],
        "citations": [
            {
                "id": "innovation_grant_from_govt:aggregate",
                "source": "innovation_grant_from_govt",
            }
        ],
        "retrieval_sources": ["innovation_grant_from_govt"],
        "query_time_ms": 10,
        "provenance": {
            "synth": "rule_based",
            "cloud_synthesis_used": False,
        },
        "warnings": [{"message": "Deterministic fast path used."}],
    }


def test_ai_synthesis_rewrites_rule_based_payload(monkeypatch):
    monkeypatch.setenv("CLOUD_SYNTHESIS_ALLOWED", "true")
    monkeypatch.setenv("NRG_AI_SYNTHESIZE_FAST_PATHS", "true")
    monkeypatch.setenv("NRG_AI_SYNTHESIS_TIMEOUT_SECONDS", "2")
    monkeypatch.setenv("LLM_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_MODEL", "minimax-m2.7")
    monkeypatch.setattr("src.config.llm_config.get_llm_mesh", lambda: _FakeMesh())

    result = synthesize_payload_with_ai(
        _payload(),
        query="Top funding agencies",
        user_tier=1,
    )

    assert result["synthesis_method"] == "cloud_llm_fast_path"
    assert result["provenance"]["cloud_synthesis_used"] is True
    assert result["provenance"]["ai_provider"] == "minimax"
    assert "4,733.81" in result["response"]
    assert result["final_answer"] == result["response"]
    assert result["query_time_ms"] >= 10
    assert result["provenance"]["ai_synthesis_latency_ms"] >= 0
    assert not result["warnings"]


def test_ai_synthesis_leaves_payload_when_disabled(monkeypatch):
    monkeypatch.setenv("CLOUD_SYNTHESIS_ALLOWED", "false")
    monkeypatch.delenv("NRG_AI_SYNTHESIZE_FAST_PATHS", raising=False)
    payload = _payload()

    result = synthesize_payload_with_ai(
        payload,
        query="Top funding agencies",
        user_tier=1,
    )

    assert result is payload
    assert result["synthesis_method"] == "rule_based"


def test_ai_synthesis_requires_explicit_fast_path_opt_in(monkeypatch):
    monkeypatch.setenv("CLOUD_SYNTHESIS_ALLOWED", "true")
    monkeypatch.delenv("NRG_AI_SYNTHESIZE_FAST_PATHS", raising=False)
    payload = _payload()

    result = synthesize_payload_with_ai(
        payload,
        query="Top funding agencies",
        user_tier=1,
    )

    assert result is payload
    assert result["synthesis_method"] == "rule_based"


def test_ai_synthesis_default_timeout_is_short_for_fast_paths(monkeypatch):
    from src.api import ai_synthesis

    monkeypatch.delenv("NRG_AI_SYNTHESIS_TIMEOUT_SECONDS", raising=False)

    assert ai_synthesis._timeout_seconds() == 2.0


class _WorkflowWithEvidence:
    def run(self, query: str, user_tier: int = 1, session_id=None, user_id=None):
        return {
            **_payload(),
            "query_id": "query-ai-synthesis",
            "session_id": session_id,
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "synthesized_response": "MeitY is top.",
            "verification_status": True,
            "conversation_history": [],
        }


def _auth_headers(client: TestClient) -> dict[str, str]:
    login_response = client.post(
        "/login",
        json={"username": "researcher_user", "password": "researcher-pass"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_query_endpoint_applies_ai_synthesis_after_tier_filter(monkeypatch):
    monkeypatch.setenv("CLOUD_SYNTHESIS_ALLOWED", "true")
    monkeypatch.setenv("NRG_AI_SYNTHESIZE_FAST_PATHS", "true")
    monkeypatch.setenv("NRG_AI_SYNTHESIS_TIMEOUT_SECONDS", "2")
    monkeypatch.setenv("LLM_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_MODEL", "minimax-m2.7")
    monkeypatch.setattr("src.config.llm_config.get_llm_mesh", lambda: _FakeMesh())
    monkeypatch.setattr(api_main, "workflow", _WorkflowWithEvidence())
    monkeypatch.setattr(api_main, "audit_log_query", lambda *args, **kwargs: "audit-ai-123")
    api_main._api_cache.invalidate()

    from src.services.consent import ConsentService

    original_has_consent = ConsentService.has_consent
    ConsentService.has_consent = lambda self, uid, scope: True

    try:
        client = TestClient(api_main.app)
        response = client.post(
            "/query",
            json={"query": "Top funding agencies"},
            headers=_auth_headers(client),
        )
    finally:
        ConsentService.has_consent = original_has_consent

    assert response.status_code == 200
    payload = response.json()
    assert payload["synthesis_method"] == "cloud_llm_fast_path"
    assert payload["provenance"]["cloud_synthesis_used"] is True
    assert payload["provenance"]["ai_provider"] == "minimax"
    assert "4,733.81" in payload["response"]
    assert payload["final_answer"] == payload["response"]

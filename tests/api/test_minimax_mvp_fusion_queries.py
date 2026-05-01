"""Regression coverage extracted from the Desktop Minimax v1.0 sample corpus.

The external v1.0 bundle is not a source tree replacement. Its useful value here is a
set of reviewer-facing query shapes that should route through NRG's real
answer-engine contract without hardcoded release-only tables or privacy leaks.
"""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

import src.api.main as api_main
from src.services.consent import ConsentService


MINIMAX_SAMPLE_QUERIES = [
    "Find top researchers in AI and machine learning",
    "Show me publications on hydrogen technology from Gujarat",
    "What are the collaboration patterns in renewable energy research?",
    "State-wise distribution of research output over last 5 years",
    "Compare funding allocation across major institutions",
    "Show TRL stage distribution for technology programs",
    "Which institutions have expertise in battery technology?",
    "Find labs working on semiconductor research",
    "Show partnership opportunities in quantum computing",
]


def _fast_answer(query: str, tier: int = 1) -> dict:
    response = api_main._fast_query_response(
        query,
        user_tier=tier,
        user_id=f"minimax-fusion-tier-{tier}",
        session_id=f"minimax-fusion-{tier}-{abs(hash(query))}",
    )
    assert response is not None, f"Query did not route to a bounded NRG answer: {query}"
    return response


def test_minimax_sample_queries_have_distinct_verified_nrg_answers():
    seen_responses: set[str] = set()

    for query in MINIMAX_SAMPLE_QUERIES:
        response = _fast_answer(query)
        answer = response.get("response") or ""

        assert response.get("status") == "success"
        assert response.get("verification_status") in (True, "verified", "needs_clarification")
        assert response.get("citations"), query
        assert response.get("intent") not in {"generic", "unknown"}, query
        assert "Dr. Researcher" not in answer
        assert "Math.random" not in answer
        assert answer not in seen_responses, f"Repeated answer body for query: {query}"
        seen_responses.add(answer)


def test_minimax_trl_distribution_routes_to_normalized_dhairya_safe_fast_path():
    response = _fast_answer("Show TRL stage distribution for technology programs")
    sql = response.get("sql_query") or ""

    assert response["intent"] == "trl_stage_distribution"
    assert response["sql_results"]
    assert len(response["sql_results"]) >= 9
    assert "trl_stages" in sql
    assert "CASE stage_of_technology" in sql
    assert "Level 9" in response["response"]
    assert "Dhairya" in response["response"]
    assert "'TRL 9'" not in sql
    assert '"TRL 9"' not in sql


def test_minimax_researcher_sample_is_tier3_safe_through_real_query_contract(monkeypatch):
    monkeypatch.setattr(ConsentService, "has_consent", lambda self, uid, scope: True)
    api_main._api_cache.invalidate()

    client = TestClient(api_main.app)
    login = client.post("/login", json={"username": "industry_user", "password": "industry-pass"})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    response = client.post(
        "/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "Find top researchers in AI and machine learning"},
    )

    client.close()

    assert response.status_code == 200, response.text
    payload = response.json()
    serialized = str(payload)

    assert payload["tier"] == 3
    assert payload["audit_event_id"]
    assert payload["citations"]
    for row in payload["source_data"]["rows"]:
        assert "researcher_id" not in row
        assert "author_id" not in row
        assert "person_id" not in row
        assert "email" not in row
        assert "phone" not in row
        if "name" in row:
            assert str(row["name"]).startswith("Researcher_")
    assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", serialized)
    assert not re.search(r"\b(?:\+91[-\s]?)?[6-9][0-9]{9}\b", serialized)

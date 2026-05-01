"""Regression coverage extracted from the Desktop GLM v1.0 bundle.

The GLM bundle is useful as query and workflow source material, not as a
replacement source tree. These tests keep its high-value query cases inside
NRG's real FastAPI answer contract and Dhairya-safe retrieval boundaries.
"""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

import src.api.main as api_main
from src.services.consent import ConsentService


GLM_QUERY_CASES = [
    "Who are the top researchers in hydrogen catalysis?",
    "Compare Gujarat and Maharashtra research output",
    "Top 10 publications in renewable energy",
    "Find researchers with more than 50 publications in Quantum Computing",
    "Which states have the most active researchers in Biotechnology?",
    "Compare average h-index across different research areas",
    "What are the most cited publications from IIT system?",
    "Which research area has the highest citation count?",
    "Which IIT has the strongest AI research program?",
    "Compare CSIR labs by research output",
    "List top 10 institutions by average researcher h-index",
]


def _fast_answer(query: str, tier: int = 1) -> dict:
    response = api_main._fast_query_response(
        query,
        user_tier=tier,
        user_id=f"glm-fusion-tier-{tier}",
        session_id=f"glm-fusion-{tier}-{abs(hash(query))}",
    )
    assert response is not None, f"Query did not route to a bounded NRG answer: {query}"
    return response


def test_glm_query_corpus_returns_distinct_verified_nrg_answers():
    seen_answers: set[str] = set()

    for query in GLM_QUERY_CASES:
        response = _fast_answer(query)
        answer = response.get("response") or ""

        assert response.get("status") == "success", query
        assert response.get("verification_status") in (True, "verified", "needs_clarification"), query
        assert response.get("citations"), query
        assert response.get("intent") not in {"generic", "unknown", "research_output_by_year"}, query
        assert "Math.random" not in answer
        assert "dummy" not in answer.lower()
        assert answer not in seen_answers, f"Repeated answer body for query: {query}"
        seen_answers.add(answer)


def test_glm_state_comparison_stays_state_bounded_not_year_output():
    response = _fast_answer("Compare Gujarat and Maharashtra research output")
    answer = response["response"]
    states = {str(row.get("state")) for row in response["sql_results"]}

    assert response["intent"] == "state_research_output_comparison"
    assert {"Gujarat", "Maharashtra"}.issubset(states)
    assert "Gujarat" in answer
    assert "Maharashtra" in answer
    assert "publication_year" not in (response.get("sql_query") or "")


def test_glm_publication_topic_query_does_not_route_to_funding_aggregate():
    response = _fast_answer("Top 10 publications in renewable energy")

    assert response["intent"] == "publication_topic_lookup"
    assert response["sql_results"]
    assert "publication" in response["response"].lower()
    assert "funding_aggregate" not in response["intent"]
    assert "c4_publication_area_read_model" in (response.get("sql_query") or "")


def test_glm_quantum_researcher_publication_threshold_is_not_year_output():
    response = _fast_answer("Find researchers with more than 50 publications in Quantum Computing")
    answer = response["response"].lower()

    assert response["intent"] in {"researcher_publication_threshold_proxy", "researcher_ranking"}
    assert "quantum" in answer
    assert "publication" in answer
    assert "research_output_by_year" != response["intent"]


def test_glm_h_index_and_citation_comparisons_route_to_aggregates():
    h_index = _fast_answer("Compare average h-index across different research areas")
    citations = _fast_answer("Which research area has the highest citation count?")
    institutions = _fast_answer("List top 10 institutions by average researcher h-index")

    assert h_index["intent"] == "research_area_h_index_comparison"
    assert h_index["sql_results"]
    assert "avg_h_index" in h_index["sql_results"][0]

    assert citations["intent"] == "research_area_citation_ranking"
    assert citations["sql_results"]
    assert "citation_count" in citations["sql_results"][0]

    assert institutions["intent"] == "institution_avg_h_index_ranking"
    assert institutions["sql_results"]
    assert "avg_h_index" in institutions["sql_results"][0]


def test_glm_iit_and_csir_queries_return_specific_bounded_answers():
    iit = _fast_answer("Which IIT has the strongest AI research program?")
    csir = _fast_answer("Compare CSIR labs by research output")

    assert iit["intent"] == "iit_ai_program_strength"
    assert iit["sql_results"]
    assert "IIT" in iit["response"]
    assert "Artificial Intelligence" in iit["response"] or "AI" in iit["response"]

    assert csir["intent"] == "csir_lab_output_lookup"
    assert csir["sql_results"]
    assert "CSIR" in csir["response"]
    assert "research_output_by_year" != csir["intent"]


def test_glm_researcher_query_is_tier3_safe_through_real_query_contract(monkeypatch):
    monkeypatch.setattr(ConsentService, "has_consent", lambda self, uid, scope: True)
    api_main._api_cache.invalidate()

    client = TestClient(api_main.app)
    login = client.post("/login", json={"username": "industry_user", "password": "industry-pass"})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    response = client.post(
        "/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "Who are the top researchers in hydrogen catalysis?"},
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
        if "researcher" in row:
            assert str(row["researcher"]).startswith("Researcher")
        if "name" in row:
            assert str(row["name"]).startswith("Researcher_")
    assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", serialized)
    assert not re.search(r"\b(?:\+91[-\s]?)?[6-9][0-9]{9}\b", serialized)

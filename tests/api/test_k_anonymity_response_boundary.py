"""Regression tests for k-anonymity response-boundary enforcement."""

from src.api.response_filter import apply_k_anonymity_threshold


def test_lower_tier_small_individual_cohort_is_blocked():
    payload = {
        "query_id": "k-small",
        "session_id": "session-k",
        "status": "success",
        "response": "Two matching researchers were found.",
        "sql_query": "SELECT researcher_id, name FROM researchers WHERE research_area = 'AI'",
        "sql_results": [
            {"researcher_id": "r-1", "name": "Researcher One", "research_area": "AI"},
            {"researcher_id": "r-2", "name": "Researcher Two", "research_area": "AI"},
        ],
        "citations": [{"text": "Researcher One"}],
        "retrieval_sources": [{"raw_content": "Researcher Two"}],
        "warnings": [],
    }

    filtered, events = apply_k_anonymity_threshold(payload, tier=3)

    assert filtered["blocked"] is True
    assert filtered["status"] == "blocked"
    assert filtered["sql_query"] is None
    assert filtered["sql_queries"] == []
    assert filtered["sql_results"] == []
    assert filtered["citations"] == []
    assert filtered["retrieval_sources"] == []
    assert "privacy threshold" in filtered["response"]
    assert any(event["reason"] == "k_anonymity_block:tier3:small_cohort" for event in events)


def test_lower_tier_aggregate_rows_without_person_identifier_are_not_blocked():
    payload = {
        "query_id": "k-aggregate",
        "status": "success",
        "response": "Institution aggregate result.",
        "sql_results": [
            {"institute": "IIT Madras", "publication_count": 22},
        ],
    }

    filtered, events = apply_k_anonymity_threshold(payload, tier=3)

    assert filtered is payload
    assert events == []


def test_tier1_small_individual_cohort_is_not_blocked():
    payload = {
        "query_id": "k-tier1",
        "status": "success",
        "response": "Researcher-level result.",
        "sql_results": [{"researcher_id": "r-1", "name": "Researcher One"}],
    }

    filtered, events = apply_k_anonymity_threshold(payload, tier=1)

    assert filtered is payload
    assert events == []

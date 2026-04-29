from src.api.answer_contract import (
    AnswerConfidence,
    AnswerEngineResponse,
    CitationRef,
    FreshnessInfo,
    SourceData,
    blocked_answer_payload,
    normalize_workflow_result,
)


def test_answer_engine_response_requires_v1_fields():
    response = AnswerEngineResponse(
        query_id="query-1",
        answer_id="answer-1",
        audit_event_id="audit-1",
        tier="researcher",
        question="Who leads hydrogen catalysis?",
        interpreted_question="Rank hydrogen catalysis researchers over the last five years.",
        assumptions=["Interpreted best as publications, citations, funded projects, and recency."],
        route="hybrid",
        final_answer="IIT-GN appears in the top cohort [1].",
        confidence=AnswerConfidence(level="high", reason="Evidence and citations passed verification."),
        citations=[CitationRef(id="1", source_type="sql_row", label="researchers row", source_id="researchers:1")],
        source_data=SourceData(sql_query="SELECT 1", rows=[{"rank": 1}], documents=[]),
        freshness=FreshnessInfo(database_snapshot=None, document_indexed_at=None, warning=None),
        caveats=[],
        follow_up_suggestions=["Change time range"],
        query_time_ms=124,
    )

    payload = response.model_dump()

    assert payload["final_answer"].startswith("IIT-GN")
    assert payload["blocked"] is False
    assert payload["confidence"]["level"] == "high"
    assert payload["source_data"]["rows"] == [{"rank": 1}]


def test_normalize_workflow_result_maps_legacy_fields():
    payload = normalize_workflow_result(
        question="Top funding agencies",
        tier=1,
        audit_event_id="audit-1",
        elapsed_ms=321,
        result={
            "query_id": "query-legacy",
            "session_id": "session-1",
            "synthesized_response": "DST leads by total grant amount [cite:structured:0].",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "answer_confidence": "high",
            "sql_query": "SELECT agency, SUM(amount) FROM funding GROUP BY agency",
            "sql_results": [{"agency": "DST", "total": 10}],
            "citations": [{"id": "structured:0", "title": "funding row"}],
            "warnings": [],
            "retrieval_sources": ["structured"],
        },
    )

    assert payload["query_id"] == "query-legacy"
    assert payload["route"] == "sql"
    assert payload["final_answer"].startswith("DST leads")
    assert payload["confidence"]["level"] == "high"
    assert payload["blocked"] is False
    assert payload["source_data"]["sql_query"].startswith("SELECT agency")
    assert payload["source_data"]["rows"] == [{"agency": "DST", "total": 10}]


def test_blocked_answer_payload_marks_blocked_flag():
    payload = blocked_answer_payload(
        question="Show phone numbers",
        user_tier=1,
        audit_event_id="audit-1",
        reason="Security policy blocked this query: PROMPT_INJECTION",
    )

    assert payload["route"] == "blocked"
    assert payload["blocked"] is True
    assert payload["confidence"]["level"] == "needs_clarification"
    assert payload["source_data"]["rows"] == []

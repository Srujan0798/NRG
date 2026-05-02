from __future__ import annotations

import uuid
from typing import Any, Literal, cast

from pydantic import BaseModel, Field

TierName = Literal["researcher", "government", "industry"]
RouteName = Literal["sql", "rag", "hybrid", "clarify", "blocked"]
ConfidenceLevel = Literal["high", "medium", "low", "needs_clarification"]
SourceType = Literal["sql_row", "document_chunk", "graph_edge"]
BLOCKED_QUERY_PLACEHOLDER = "[blocked by security policy]"
JSONDict = dict[str, Any]
JSONRows = list[JSONDict]


def _empty_str_list() -> list[str]:
    return []


def _empty_json_rows() -> JSONRows:
    return []


class AnswerConfidence(BaseModel):
    level: ConfidenceLevel
    reason: str


class CitationRef(BaseModel):
    id: str
    source_type: SourceType
    label: str
    source_id: str
    masked: bool = False


def _empty_citation_refs() -> list[CitationRef]:
    return []


class SourceData(BaseModel):
    sql_query: str | None = None
    rows: JSONRows = Field(default_factory=_empty_json_rows)
    documents: JSONRows = Field(default_factory=_empty_json_rows)


class FreshnessInfo(BaseModel):
    database_snapshot: str | None = None
    document_indexed_at: str | None = None
    warning: str | None = None


class HybridEvidence(BaseModel):
    sql_rows: int = 0
    document_chunks: int = 0


class ProvenanceInfo(BaseModel):
    planner: str | None = None
    synth: str | None = None
    verifier: str | None = None
    cloud_synthesis_used: bool = False
    hybrid_evidence: HybridEvidence | None = None


class AnswerEngineResponse(BaseModel):
    query_id: str
    answer_id: str
    audit_event_id: str | None
    tier: TierName
    question: str
    interpreted_question: str
    assumptions: list[str] = Field(default_factory=_empty_str_list)
    route: RouteName
    blocked: bool = False
    final_answer: str
    confidence: AnswerConfidence
    citations: list[CitationRef] = Field(default_factory=_empty_citation_refs)
    source_data: SourceData = Field(default_factory=SourceData)
    provenance: ProvenanceInfo = Field(default_factory=ProvenanceInfo)
    freshness: FreshnessInfo = Field(default_factory=FreshnessInfo)
    caveats: list[str] = Field(default_factory=_empty_str_list)
    follow_up_suggestions: list[str] = Field(default_factory=_empty_str_list)
    query_time_ms: int = 0


def tier_name(tier: int | str) -> TierName:
    value = str(tier).lower()
    if value in {"1", "researcher", "tier1", "t1"}:
        return "researcher"
    if value in {"2", "government", "gov", "tier2", "t2"}:
        return "government"
    return "industry"


def normalize_route(route: str | None, intent: str | None = None) -> RouteName:
    value = (route or intent or "").lower()
    if value in {"text_to_sql", "structured", "sql"}:
        return "sql"
    if value in {"rag", "unstructured", "vector"}:
        return "rag"
    if value in {"text_to_sql+rag", "hybrid", "sql+rag"}:
        return "hybrid"
    if value in {"clarify", "needs_clarification"}:
        return "clarify"
    if value == "blocked":
        return "blocked"
    return "hybrid" if "rag" in value and "sql" in value else "sql"


def normalize_confidence(value: Any, verification_status: Any = None) -> AnswerConfidence:
    raw = str(value or "").lower()
    if raw in {
        "high",
        "ok",
        "pass",
        "passed",
        "true",
        "verified",
        "success",
    } or normalize_verification_status(verification_status):
        return AnswerConfidence(level="high", reason="Evidence and citations passed verification.")
    if raw in {"medium", "partial", "warning"}:
        return AnswerConfidence(level="medium", reason="Evidence supports the answer with caveats.")
    if raw in {"needs_clarification", "low_clarify", "clarify"}:
        return AnswerConfidence(
            level="needs_clarification",
            reason="The query needs clarification before a safe full answer.",
        )
    return AnswerConfidence(level="low", reason="Only partial evidence is available.")


def normalize_verification_status(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)

    raw = str(value).strip().lower()
    if raw in {"ok", "pass", "passed", "true", "verified", "success", "safe"}:
        return True
    if raw in {
        "blocked",
        "fail",
        "failed",
        "false",
        "needs_clarification",
        "low_clarify",
        "retry",
        "unsafe",
        "unknown",
        "",
    }:
        return False
    return False


def normalize_citations(raw_citations: list[Any]) -> list[CitationRef]:
    citations: list[CitationRef] = []
    for index, item in enumerate(raw_citations or [], start=1):
        if not isinstance(item, dict):
            continue
        citation = cast(JSONDict, item)
        raw_id = str(citation.get("id") or citation.get("pub_id") or citation.get("source_id") or index)
        source_type: SourceType = (
            "document_chunk" if citation.get("chunk_id") or citation.get("chunk_text") else "sql_row"
        )
        citations.append(
            CitationRef(
                id=str(index),
                source_type=source_type,
                label=str(citation.get("title") or citation.get("source") or f"Source {index}"),
                source_id=raw_id,
                masked=bool(citation.get("masked", False)),
            )
        )
    return citations


def _string_list(values: Any) -> list[str]:
    if not values:
        return []
    if not isinstance(values, list):
        values = [values]
    return [item if isinstance(item, str) else str(item) for item in cast(list[Any], values)]


def _json_dict(value: Any) -> JSONDict:
    return cast(JSONDict, value) if isinstance(value, dict) else {}


def _json_rows(value: Any) -> JSONRows:
    if not isinstance(value, list):
        return []
    return [cast(JSONDict, item) for item in cast(list[Any], value) if isinstance(item, dict)]


def blocked_answer_payload(
    *,
    question: str,
    user_tier: int,
    audit_event_id: str | None,
    reason: str,
    query_id: str | None = None,
) -> dict[str, Any]:
    final_answer = (
        "I cannot process this request because it asks for sensitive or restricted information. "
        "Try an aggregate question about institutions, labs, capability areas, or public contact routes instead."
    )
    safe_question = BLOCKED_QUERY_PLACEHOLDER
    return {
        "query_id": query_id or str(uuid.uuid4()),
        "answer_id": str(uuid.uuid4()),
        "audit_event_id": audit_event_id,
        "tier": user_tier,
        "query": safe_question,
        "question": safe_question,
        "interpreted_question": safe_question,
        "assumptions": [],
        "route": "blocked",
        "blocked": True,
        "final_answer": final_answer,
        "response": final_answer,
        "status": "blocked",
        "verification_status": False,
        "confidence": {"level": "needs_clarification", "reason": reason},
        "verification": {
            "status": "blocked",
            "safe_to_trust": False,
            "reason": reason,
            "audit_event_id": audit_event_id,
        },
        "answer_confidence": "needs_clarification",
        "citations": [],
        "source_data": {"sql_query": None, "rows": [], "documents": []},
        "freshness": {"database_snapshot": None, "document_indexed_at": None, "warning": None},
        "caveats": [reason],
        "follow_up_suggestions": [
            "Show aggregate counts by institution",
            "Show labs working in this area",
            "Show public partnership routes",
        ],
        "query_time_ms": 0,
        "sql_query": None,
        "sql_results": [],
        "retrieval_sources": [],
        "warnings": [{"message": reason}],
        "conversation_history": [],
    }


def normalize_workflow_result(
    *,
    question: str,
    tier: int,
    audit_event_id: str | None,
    elapsed_ms: float,
    result: JSONDict,
) -> JSONDict:
    planner_metadata = _json_dict(result.get("planner_metadata"))
    response = AnswerEngineResponse(
        query_id=str(result.get("query_id") or uuid.uuid4()),
        answer_id=str(result.get("answer_id") or uuid.uuid4()),
        audit_event_id=audit_event_id,
        tier=tier_name(tier),
        question=question,
        interpreted_question=str(
            result.get("interpreted_question") or result.get("user_query") or question
        ),
        assumptions=_string_list(result.get("assumptions") or planner_metadata.get("assumptions") or []),
        route=normalize_route(result.get("routing_decision"), result.get("intent")),
        final_answer=str(
            result.get("final_answer")
            or result.get("synthesized_response")
            or result.get("response")
            or ""
        ),
        confidence=normalize_confidence(
            result.get("answer_confidence"), result.get("verification_status")
        ),
        citations=normalize_citations(cast(list[Any], result.get("citations", []))),
        source_data=SourceData(
            sql_query=str(result.get("sql_query")) if result.get("sql_query") is not None else None,
            rows=_json_rows(result.get("sql_results")),
            documents=_json_rows(result.get("retrieved_chunks")),
        ),
        provenance=ProvenanceInfo(**_json_dict(result.get("provenance"))),
        freshness=FreshnessInfo(**_json_dict(result.get("freshness"))),
        caveats=_string_list(result.get("caveats") or result.get("warnings") or []),
        follow_up_suggestions=_string_list(result.get("follow_up_suggestions") or []),
        query_time_ms=int(elapsed_ms),
    )
    payload = response.model_dump()
    for citation in _json_rows(payload["citations"]):
        citation.setdefault("title", citation.get("label"))
        citation.setdefault("publication_id", citation.get("source_id"))
        citation.setdefault("paper_id", citation.get("source_id"))
        citation.setdefault("pub_id", citation.get("source_id"))
    raw_verification_status = result.get("verification_status", False)
    verification_status = normalize_verification_status(raw_verification_status)
    payload.update(
        {
            "query": question,
            "response": payload["final_answer"],
            "status": "success",
            "tier": tier,
            "session_id": result.get("session_id"),
            "intent": result.get("intent"),
            "routing_decision": result.get("routing_decision"),
            "verification_status": verification_status,
            "verification": {
                "status": raw_verification_status,
                "safe_to_trust": verification_status,
                "confidence": payload["confidence"],
                "citation_validity": result.get("citation_validity", 1.0),
                "audit_event_id": audit_event_id,
            },
            "citation_validity": result.get("citation_validity", 1.0),
            "plan": result.get("plan"),
            "planner_metadata": planner_metadata,
            "answer_confidence": payload["confidence"]["level"],
            "answer_confidence_score": result.get(
                "answer_confidence_score",
                result.get("faithfulness_score", 0.95 if verification_status else 0.45),
            ),
            "sql_anomaly_report": result.get("sql_anomaly_report", {}),
            "sql_query": payload["source_data"]["sql_query"],
            "sql_queries": result.get("sql_queries", []),
            "sql_results": payload["source_data"]["rows"],
            "retrieval_sources": result.get("retrieval_sources", []),
            "provenance": result.get("provenance", {}),
            "synthesis_method": result.get("synthesis_method"),
            "conversation_history": result.get("conversation_history", []),
            "node_timings": result.get("node_timings", {}),
            "warnings": result.get("warnings", []),
        }
    )
    return payload

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

TierName = Literal["researcher", "government", "industry"]
RouteName = Literal["sql", "rag", "hybrid", "clarify", "blocked"]
ConfidenceLevel = Literal["high", "medium", "low", "needs_clarification"]
SourceType = Literal["sql_row", "document_chunk", "graph_edge"]


class AnswerConfidence(BaseModel):
    level: ConfidenceLevel
    reason: str


class CitationRef(BaseModel):
    id: str
    source_type: SourceType
    label: str
    source_id: str
    masked: bool = False


class SourceData(BaseModel):
    sql_query: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    documents: list[dict[str, Any]] = Field(default_factory=list)


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
    assumptions: list[str] = Field(default_factory=list)
    route: RouteName
    blocked: bool = False
    final_answer: str
    confidence: AnswerConfidence
    citations: list[CitationRef] = Field(default_factory=list)
    source_data: SourceData = Field(default_factory=SourceData)
    provenance: ProvenanceInfo = Field(default_factory=ProvenanceInfo)
    freshness: FreshnessInfo = Field(default_factory=FreshnessInfo)
    caveats: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)
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
    if raw in {"high", "pass", "passed", "true"} or verification_status is True:
        return AnswerConfidence(level="high", reason="Evidence and citations passed verification.")
    if raw in {"medium", "partial", "warning"}:
        return AnswerConfidence(level="medium", reason="Evidence supports the answer with caveats.")
    if raw in {"needs_clarification", "low_clarify", "clarify"}:
        return AnswerConfidence(
            level="needs_clarification",
            reason="The query needs clarification before a safe full answer.",
        )
    return AnswerConfidence(level="low", reason="Only partial evidence is available.")


def normalize_citations(raw_citations: list[Any]) -> list[CitationRef]:
    citations: list[CitationRef] = []
    for index, item in enumerate(raw_citations or [], start=1):
        if not isinstance(item, dict):
            continue
        raw_id = str(item.get("id") or item.get("pub_id") or item.get("source_id") or index)
        source_type: SourceType = "document_chunk" if item.get("chunk_id") or item.get("chunk_text") else "sql_row"
        citations.append(
            CitationRef(
                id=str(index),
                source_type=source_type,
                label=str(item.get("title") or item.get("source") or f"Source {index}"),
                source_id=raw_id,
                masked=bool(item.get("masked", False)),
            )
        )
    return citations


def _string_list(values: Any) -> list[str]:
    if not values:
        return []
    if not isinstance(values, list):
        values = [values]
    return [item if isinstance(item, str) else str(item) for item in values]


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
    return {
        "query_id": query_id or str(uuid.uuid4()),
        "answer_id": str(uuid.uuid4()),
        "audit_event_id": audit_event_id,
        "tier": user_tier,
        "query": question,
        "question": question,
        "interpreted_question": question,
        "assumptions": [],
        "route": "blocked",
        "blocked": True,
        "final_answer": final_answer,
        "response": final_answer,
        "status": "blocked",
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
    result: dict[str, Any],
) -> dict[str, Any]:
    planner_metadata = result.get("planner_metadata") or {}
    response = AnswerEngineResponse(
        query_id=str(result.get("query_id") or uuid.uuid4()),
        answer_id=str(result.get("answer_id") or uuid.uuid4()),
        audit_event_id=audit_event_id,
        tier=tier_name(tier),
        question=question,
        interpreted_question=str(result.get("interpreted_question") or result.get("user_query") or question),
        assumptions=list(result.get("assumptions") or planner_metadata.get("assumptions") or []),
        route=normalize_route(result.get("routing_decision"), result.get("intent")),
        final_answer=str(result.get("final_answer") or result.get("synthesized_response") or result.get("response") or ""),
        confidence=normalize_confidence(result.get("answer_confidence"), result.get("verification_status")),
        citations=normalize_citations(result.get("citations", [])),
        source_data=SourceData(
            sql_query=result.get("sql_query"),
            rows=list(result.get("sql_results") or []),
            documents=list(result.get("retrieved_chunks") or []),
        ),
        provenance=ProvenanceInfo(**dict(result.get("provenance") or {})),
        freshness=FreshnessInfo(**dict(result.get("freshness") or {})),
        caveats=_string_list(result.get("caveats") or result.get("warnings") or []),
        follow_up_suggestions=_string_list(result.get("follow_up_suggestions") or []),
        query_time_ms=int(elapsed_ms),
    )
    payload = response.model_dump()
    verification_status = result.get("verification_status", False)
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
                "status": verification_status,
                "safe_to_trust": verification_status is True,
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
                result.get("faithfulness_score", 0.95 if result.get("verification_status", False) else 0.45),
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

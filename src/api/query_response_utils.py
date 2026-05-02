"""Response utilities shared by the NRG query endpoints."""

from __future__ import annotations

import asyncio
import atexit
import json
import re
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, cast

from src.api.answer_contract import normalize_workflow_result
from src.api.logging_config import get_logger
from src.services.answer_records import get_answer_record_store

logger = get_logger(__name__)
JSONDict = dict[str, Any]
_answer_record_executor: ThreadPoolExecutor | None = None
_answer_record_executor_lock = threading.Lock()


def _get_answer_record_executor() -> ThreadPoolExecutor:
    global _answer_record_executor
    with _answer_record_executor_lock:
        if _answer_record_executor is None:
            _answer_record_executor = ThreadPoolExecutor(
                max_workers=1,
                thread_name_prefix="answer_record",
            )
        return _answer_record_executor


def shutdown_answer_record_executor() -> None:
    global _answer_record_executor
    with _answer_record_executor_lock:
        executor = _answer_record_executor
        _answer_record_executor = None
    if executor is not None:
        executor.shutdown(wait=False, cancel_futures=True)


atexit.register(shutdown_answer_record_executor)


def answer_confidence_from_verification(verification_status: Any) -> str:
    if verification_status in (True, "ok", "pass"):
        return "high"
    if verification_status == "retry":
        return "medium"
    if verification_status in ("needs_clarification", "low_clarify"):
        return "needs_clarification"
    return "low"


def redact_pii_from_response(response_data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Redact obvious Indian PII from response text and citation fields."""
    pii_patterns: dict[str, re.Pattern[str]] = {
        "AADHAAR": re.compile(r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b"),
        "PAN": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"),
        "PHONE": re.compile(r"\b[6-9][0-9]{9}\b"),
        "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    }

    redacted_types: list[str] = []
    redacted_response = response_data.copy()

    def _redact_text(text: str) -> tuple[str, list[str]]:
        found_types: list[str] = []
        result = text
        for pii_type, pattern in pii_patterns.items():
            if pattern.search(result):
                placeholder = f"[{pii_type}_REDACTED]"
                result = pattern.sub(placeholder, result)
                found_types.append(pii_type)
        return result, found_types

    text_fields_to_check = ["response", "final_answer", "warnings"]
    for fname in text_fields_to_check:
        if fname in redacted_response and isinstance(redacted_response[fname], str):
            redacted_response[fname], found = _redact_text(redacted_response[fname])
            redacted_types.extend(found)

    if "citations" in redacted_response and isinstance(redacted_response["citations"], list):
        redacted_citations: list[Any] = []
        for citation in cast(list[Any], redacted_response["citations"]):
            if isinstance(citation, dict):
                redacted_citation = cast(JSONDict, citation).copy()
                for key in ["text", "context", "paper_title"]:
                    if key in redacted_citation and isinstance(redacted_citation[key], str):
                        redacted_citation[key], found = _redact_text(redacted_citation[key])
                        redacted_types.extend(found)
                redacted_citations.append(redacted_citation)
            else:
                redacted_citations.append(citation)
        redacted_response["citations"] = redacted_citations

    if redacted_types:
        redacted_types = list(set(redacted_types))
        logger.debug(f"PII redaction applied to response: {redacted_types}")

    return redacted_response, redacted_types


def sse(event: str, payload: Any) -> str:
    data = payload if isinstance(payload, str) else json.dumps(payload, default=str)
    return f"event: {event}\ndata: {data}\n\n"


def normalise_stream_answer_payload(
    result: dict[str, Any],
    *,
    request: Any,
    user_tier: int,
    audit_event_id: str | None,
) -> dict[str, Any]:
    verification = result.get("verification_status", True)
    return normalize_workflow_result(
        question=request.query,
        tier=user_tier,
        audit_event_id=result.get("audit_event_id", audit_event_id),
        elapsed_ms=0,
        result={
            **result,
            "query_id": result.get("query_id", str(uuid.uuid4())),
            "session_id": result.get("session_id", request.session_id),
            "synthesized_response": result.get("synthesized_response") or result.get("response", ""),
            "routing_decision": result.get("routing_decision", "text_to_sql"),
            "verification_status": verification,
            "answer_confidence": result.get(
                "answer_confidence",
                answer_confidence_from_verification(verification),
            ),
            "provenance": result.get("provenance", {"synth": "critical_path_stream"}),
        },
    )


def normalise_query_answer_payload(
    request: Any,
    *,
    user_tier: int,
    audit_event_id: str | None,
    elapsed_ms: float,
    result: dict[str, Any],
    default_routing: str = "text_to_sql",
    default_verification: bool = True,
) -> dict[str, Any]:
    normalized_result = {
        **result,
        "query_id": result.get("query_id", str(uuid.uuid4())),
        "session_id": result.get("session_id", request.session_id),
        "synthesized_response": result.get("synthesized_response") or result.get("response", ""),
        "routing_decision": result.get("routing_decision", default_routing),
        "verification_status": result.get("verification_status", default_verification),
    }
    return normalize_workflow_result(
        question=request.query,
        tier=user_tier,
        audit_event_id=audit_event_id,
        elapsed_ms=elapsed_ms,
        result=normalized_result,
    )


def persist_answer_record(user_id: str, session_id: str | None, payload: dict[str, Any]) -> None:
    if payload.get("status") != "success" or not payload.get("answer_id"):
        return
    try:
        get_answer_record_store().save(
            user_id=user_id,
            session_id=session_id,
            payload=payload,
        )
    except Exception:
        logger.warning("Answer record persistence failed", exc_info=True)


def schedule_answer_record_persist(user_id: str, session_id: str | None, payload: dict[str, Any]) -> None:
    executor = _get_answer_record_executor()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        executor.submit(persist_answer_record, user_id, session_id, payload)
        return
    loop.run_in_executor(executor, persist_answer_record, user_id, session_id, payload)


def extract_citations_from_text(text: str) -> list[JSONDict]:
    citations: list[JSONDict] = []
    cite_pattern = re.compile(r"\[cite:([^:\]]+):([^\]]+)\]")
    for pub_id, chunk_id in cite_pattern.findall(text):
        citations.append({"id": f"{pub_id}:{chunk_id}", "pub_id": pub_id, "chunk_id": chunk_id})
    return citations

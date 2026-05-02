"""Frontend UAT telemetry ingestion endpoint."""

from __future__ import annotations

import re
import threading
from typing import Any, cast

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, model_validator

from src.api.logging_config import get_logger

router = APIRouter(tags=["telemetry"])
logger = get_logger(__name__)

TELEMETRY_EVENT_NAMES = {
    "app.first_paint",
    "query.submitted",
    "query.phase_observed",
    "query.completed",
    "query.aborted",
    "citation.opened",
    "audit.verified",
    "proof.verify_clicked",
    "proof.verified",
    "persona.switched",
    "error.shown",
    "empty.shown",
}


class TelemetryEventIn(BaseModel):
    schema_version: int = Field(default=1, ge=1, le=1)
    event_id: str = Field(min_length=4, max_length=128)
    event: str = Field(min_length=3, max_length=80)
    ts: str = Field(min_length=10, max_length=64)
    session_id: str = Field(min_length=1, max_length=128)
    route: str = Field(default="/", max_length=256)
    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event_name(self):
        if self.event not in TELEMETRY_EVENT_NAMES:
            raise ValueError("Unsupported telemetry event")
        return self


class TelemetryBatchIn(BaseModel):
    events: list[TelemetryEventIn] = Field(min_length=1, max_length=200)


_telemetry_recent_events: list[dict[str, Any]] = []
_telemetry_lock = threading.Lock()


def _redact_telemetry_pii(value: Any) -> Any:
    if isinstance(value, str):
        patterns = [
            (re.compile(r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b"), "[AADHAAR_REDACTED]"),
            (re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"), "[PAN_REDACTED]"),
            (re.compile(r"\b[6-9][0-9]{9}\b"), "[PHONE_REDACTED]"),
            (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
        ]
        redacted = value
        for pattern, replacement in patterns:
            redacted = pattern.sub(replacement, redacted)
        return redacted
    if isinstance(value, list):
        return [_redact_telemetry_pii(item) for item in cast(list[Any], value)]
    if isinstance(value, dict):
        value_dict = cast(dict[str, Any], value)
        return {key: _redact_telemetry_pii(item) for key, item in value_dict.items()}
    return value


@router.post("/api/telemetry", status_code=202)
async def ingest_telemetry(batch: TelemetryBatchIn, raw_request: Request):
    """Accept UAT telemetry, keep it PII-stripped, and bind the batch to the audit chain."""
    redacted_events = [
        _redact_telemetry_pii(event.model_dump())
        for event in batch.events
    ]

    with _telemetry_lock:
        _telemetry_recent_events.extend(redacted_events)
        if len(_telemetry_recent_events) > 1000:
            del _telemetry_recent_events[:-1000]

    audit_event_id = None
    try:
        from src.audit import AuditEvent, get_audit_log

        event_names = [event["event"] for event in redacted_events]
        session_id = redacted_events[0].get("session_id", "anonymous")
        audit_event_id = get_audit_log().append(AuditEvent(
            event_type="telemetry_batch",
            user_id=str(session_id),
            result={
                "count": len(redacted_events),
                "events": event_names,
                "client": raw_request.client.host if raw_request.client else None,
            },
        ))
    except Exception as exc:
        logger.warning("Telemetry audit binding failed", error=str(exc))

    logger.info(
        "Telemetry batch accepted",
        count=len(redacted_events),
        events=[event["event"] for event in redacted_events],
        audit_event_id=audit_event_id,
    )
    return {"accepted": len(redacted_events), "audit_event_id": audit_event_id}

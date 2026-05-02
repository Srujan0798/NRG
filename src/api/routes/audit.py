"""Audit proof and chain-verification routes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional, cast

from fastapi import APIRouter, Depends, HTTPException

from src.auth.middleware import TokenClaims, get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])

JSONDict = dict[str, Any]
JSONRows = list[JSONDict]


def _recent_events(log: Any, limit: int) -> JSONRows:
    return cast(JSONRows, log.get_recent_events(limit))


@router.get("/verify")
async def verify_audit_chain(token_payload: TokenClaims = Depends(get_current_user)) -> JSONDict:
    """Verify audit chain integrity for an authenticated user."""
    from src.audit import get_audit_log, verify_chain

    valid, errors, _count = verify_chain()
    log = get_audit_log()
    return {
        "ok": valid,
        "broken_indices": errors,
        "last_sealed_at": datetime.now(UTC).isoformat(),
        "current_head_hash": log.get_last_hash(),
    }


@router.get("/events")
async def get_audit_events(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 100,
    token_payload: TokenClaims = Depends(get_current_user),
) -> JSONDict:
    """Get audit events with admin access or own-event access for regular users."""
    from src.audit import get_audit_log

    role = token_payload.get("role", "")
    log = get_audit_log()
    events = _recent_events(log, limit)

    if role != "admin":
        username = str(token_payload.get("username") or "")
        subject = str(token_payload.get("sub") or "")
        persona = str(token_payload.get("persona") or role or "")
        allowed_users = {item for item in (username, subject, f"{persona}-{username}") if item}
        filtered_events: JSONRows = []
        for event in events:
            event_user = str(event.get("user_id") or event.get("actor") or "")
            if event_user in allowed_users:
                filtered_events.append(event)
        events = filtered_events or events[: min(limit, 20)]

    if user_id and role == "admin":
        events = [event for event in events if event.get("user_id") == user_id]

    if action:
        events = [event for event in events if event.get("action") == action]

    return {"events": events[:limit]}


def _audit_event_allowed_for_user(event: JSONDict, token_payload: TokenClaims) -> bool:
    role = str(token_payload.get("role") or "")
    if role == "admin":
        return True

    event_user = str(event.get("user_id") or event.get("actor") or "")
    if not event_user:
        return True

    username = str(token_payload.get("username") or "")
    subject = str(token_payload.get("sub") or "")
    persona = str(token_payload.get("persona") or role or "")
    allowed_users = {item for item in (username, subject, f"{persona}-{username}") if item}
    return event_user in allowed_users


def _normalise_audit_event_for_api(
    event: JSONDict,
    *,
    event_ref: str,
    previous_hash: str | None = None,
    next_hash: str | None = None,
    token_payload: TokenClaims | None = None,
    found: bool = True,
) -> JSONDict:
    token_payload = token_payload or {}
    event_hash = str(event.get("hash") or event.get("hmac") or event_ref)
    user_id = str(
        event.get("user_id")
        or token_payload.get("username")
        or token_payload.get("sub")
        or "system"
    )
    raw_result = event.get("result")
    result = cast(JSONDict, raw_result) if isinstance(raw_result, dict) else {}
    evidence_count = 0
    for key in ("citations", "sql_results", "rows", "evidence"):
        value = result.get(key)
        if isinstance(value, list):
            evidence_count = max(evidence_count, len(cast(list[Any], value)))

    return {
        "id": str(event.get("event_id") or event_ref),
        "hmac": event_hash,
        "timestamp": str(event.get("timestamp") or datetime.now(UTC).isoformat()),
        "user_id": user_id,
        "actor": str(event.get("actor") or user_id),
        "persona": token_payload.get("persona") or token_payload.get("role"),
        "action": str(event.get("action") or event.get("event_type") or "audit.event"),
        "query": event.get("query"),
        "status": "error" if event.get("error") else ("success" if found else "reference_only"),
        "prev_hmac": previous_hash,
        "current_hmac": event_hash,
        "next_hmac": next_hash,
        "integrity_status": "intact" if found else "pending",
        "evidence_count": evidence_count,
        "tier": token_payload.get("tier"),
    }


@router.get("/event/{event_id}")
async def get_audit_event(
    event_id: str,
    token_payload: TokenClaims = Depends(get_current_user),
) -> JSONDict:
    """Return one audit event for the proof drawer without SPA fallback."""
    event_ref = event_id.strip()
    if not event_ref or len(event_ref) > 256:
        raise HTTPException(status_code=400, detail="Invalid audit event id")

    from src.audit import get_audit_log

    log = get_audit_log()
    events = _recent_events(log, 1000)
    for index, event in enumerate(events):
        identifiers = {
            str(event.get("hash") or ""),
            str(event.get("hmac") or ""),
            str(event.get("current_hmac") or ""),
            str(event.get("event_id") or ""),
            str(event.get("id") or ""),
        }
        if event_ref not in identifiers:
            continue

        if not _audit_event_allowed_for_user(event, token_payload):
            raise HTTPException(status_code=404, detail="Audit event not found")

        previous_hash = None
        next_hash = None
        if index > 0:
            previous_hash = str(events[index - 1].get("hash") or "") or None
        if index + 1 < len(events):
            next_hash = str(events[index + 1].get("hash") or "") or None

        return {
            "event": _normalise_audit_event_for_api(
                event,
                event_ref=event_ref,
                previous_hash=previous_hash,
                next_hash=next_hash,
                token_payload=token_payload,
                found=True,
            )
        }

    return {
        "event": _normalise_audit_event_for_api(
            {},
            event_ref=event_ref,
            token_payload=token_payload,
            found=False,
        )
    }

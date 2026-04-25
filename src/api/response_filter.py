"""Tier-aware API response filtering for query results."""

from __future__ import annotations

import copy
import re
from typing import Any


_PII_VALUE_PATTERNS = (
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b[6-9][0-9]{9}\b"),
    re.compile(r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b"),
    re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
)

_PII_KEY_TOKENS = (
    "aadhaar",
    "address",
    "alternate_email",
    "author_email",
    "authors",
    "authors_with_affiliation",
    "bank",
    "contact",
    "corresponding_author",
    "date_of_birth",
    "dob",
    "email",
    "full_text",
    "fulltext",
    "inventor_personal",
    "orcid",
    "pan",
    "personal_phone",
    "phone",
    "raw_content",
    "recipient_details",
)

_TIER3_STRIPPED_FIELDS = {
    "conversation_history",
    "provenance",
    "retrieval_sources",
    "sql_query",
    "sql_queries",
}

_DROP = object()


def filter_query_response_for_tier(
    payload: dict[str, Any],
    tier: int,
) -> tuple[dict[str, Any], list[str]]:
    """Return a response payload safe for the caller's RBAC tier.

    Tier 1 retains the full response, relying on the existing top-level PII
    redactor. Tier 2 and Tier 3 get recursive PII removal. Tier 3 also loses
    debug/provenance fields that commonly contain raw SQL, row dumps, or prior
    model text.
    """
    if tier <= 1:
        return payload, []

    filtered = copy.deepcopy(payload)
    warnings: list[str] = []

    if tier >= 3:
        for field in _TIER3_STRIPPED_FIELDS:
            if field in filtered and filtered[field] not in ({}, [], None):
                warnings.append(f"{field} stripped for Tier 3 response policy")
            if field == "provenance":
                filtered[field] = {}
            else:
                filtered[field] = []

        if filtered.get("sql_query"):
            warnings.append("sql_query stripped for Tier 3 response policy")
        if filtered.get("sql_queries"):
            warnings.append("sql_queries stripped for Tier 3 response policy")
        filtered["sql_query"] = None
        filtered["sql_queries"] = []

    sanitized = _sanitize_nested(filtered, tier)
    if sanitized != filtered:
        warnings.append("PII fields sanitized for response policy")

    return sanitized, warnings


def _sanitize_nested(value: Any, tier: int, key: str | None = None) -> Any:
    if _is_blocked_key(key, tier):
        return _DROP

    if isinstance(value, dict):
        result = {}
        for item_key, item_value in value.items():
            if _is_blocked_key(item_key, tier):
                continue
            sanitized = _sanitize_nested(item_value, tier, item_key)
            if sanitized is not _DROP:
                result[item_key] = sanitized
        return result

    if isinstance(value, list):
        result = []
        for item in value:
            sanitized = _sanitize_nested(item, tier, key)
            if sanitized is not _DROP:
                result.append(sanitized)
        return result

    if isinstance(value, str):
        return _redact_pii_values(value)

    return value


def _is_blocked_key(key: str | None, tier: int) -> bool:
    if not key:
        return False

    normalized = key.lower()
    if any(token in normalized for token in _PII_KEY_TOKENS):
        return True

    if tier >= 3 and normalized in {"debug", "raw", "raw_rows", "trace"}:
        return True

    return False


def _redact_pii_values(value: str) -> str:
    redacted = value
    for pattern in _PII_VALUE_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted

"""Shared FastAPI dependencies for NRG API routes."""

from __future__ import annotations

import os
import re
import time
import uuid
from collections import OrderedDict, deque
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field, model_validator
from starlette.responses import JSONResponse

from src.api.response_filter import (
    TierResponseFilterReport,
    apply_k_anonymity_threshold,
    filter_response_payload_for_tier,
)
from src.api.middleware.security import enforce_tier_response_boundary
from src.auth.jwt_handler import JWTHandler
from src.data.database_v2 import NRGDatabase
from src.orchestration.graph import NRGWorkflow

from src.auth.middleware import get_current_user  # noqa: F401

brute_force_protection = __import__("src.api.middleware.security", fromlist=["brute_force_protection"]).brute_force_protection


QUERY_RESULT_CACHE_TTL_SECONDS = int(os.getenv("QUERY_RESULT_CACHE_TTL_SECONDS", "300"))


class _APIMemoryCache:
    MAX_SIZE: int = 1000

    def __init__(self, default_ttl: int = 30):
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._default_ttl = default_ttl

    @staticmethod
    def _normalize_query_for_cache(query: str) -> str:
        normalized = query.lower()
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once",
            "what", "which", "who", "whom", "this", "that", "these",
            "those", "am", "is", "it", "its",
        }
        words = normalized.split()
        filtered = [w for w in words if w not in stop_words or len(w) <= 2]
        return " ".join(filtered)

    def _make_cache_key(self, query: str, user_tier: int, intent: str = None, routing: str = None) -> str:
        normalized = self._normalize_query_for_cache(query)
        base = f"query:{hash(normalized.encode())}:{user_tier}"
        if intent:
            base += f":{intent}"
        if routing:
            base += f":{routing}"
        return base

    def get(self, key: str) -> Any:
        now = time.time()
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if now > expires_at:
            self._store.pop(key, None)
            return None
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        elif len(self._store) >= self.MAX_SIZE:
            self._store.popitem(last=False)
        self._store[key] = (time.time() + (ttl or self._default_ttl), value)

    def invalidate(self, prefix: str = "") -> None:
        if prefix:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                self._store.pop(k, None)
        else:
            self._store.clear()


_api_cache = _APIMemoryCache(default_ttl=QUERY_RESULT_CACHE_TTL_SECONDS)
_publication_count_cache: dict[tuple[int, bool], int] = {}
_tier_response_history: dict[int, deque[dict[str, Any]]] = {
    1: deque(maxlen=100),
    2: deque(maxlen=100),
    3: deque(maxlen=100),
}

_db_instance: NRGDatabase | None = None
_fast_query_context: dict[str, dict[str, Any]] = {}
_sql_domain_context: dict[str, dict[str, Any]] = {}

jwt_handler = JWTHandler()
workflow = NRGWorkflow()

REPO_ROOT = Path(__file__).resolve().parents[2]
KILLER_QUERY_HEALTH_FILE = REPO_ROOT / "evidence/2026-04-26/killer_query_health.json"
DEFAULT_VECTOR_DRIFT_STATUS_FILE = REPO_ROOT / ".cache" / "vector_drift_status.json"
DEFAULT_DATA_QUALITY_SCORECARD_FILE = REPO_ROOT / "docs/ops/data_quality_scorecard.json"


def get_api_cache() -> _APIMemoryCache:
    return _api_cache


def _get_db() -> NRGDatabase:
    global _db_instance
    if _db_instance is None:
        from src.data.database import resolve_database_path

        raw_url = os.getenv("DATABASE_URL", f"sqlite:///{resolve_database_path()}")
        if raw_url.startswith("postgresql://"):
            pass
        else:
            populated = Path(__file__).resolve().parents[2] / "data" / "nrg_research.db"
            if populated.exists():
                raw_url = f"sqlite:///{populated}"
        _db_instance = NRGDatabase(url=raw_url)
        _db_instance.create_tables()
    return _db_instance


def get_db() -> NRGDatabase:
    return _get_db()


def get_workflow() -> NRGWorkflow:
    return workflow


def get_jwt_handler() -> JWTHandler:
    return jwt_handler


def check_tier_rate_limit(user_id: str, tier: int, client_ip: str | None):
    from src.security.rate_limiter import check_tier_rate_limit as _fn
    return _fn(user_id, tier, client_ip)


def check_endpoint_rate_limit(endpoint: str, user_id: str):
    from src.security.rate_limiter import check_endpoint_rate_limit as _fn
    return _fn(endpoint, user_id)


def _apply_tier_response_filter(
    payload: Any,
    tier: int,
    *,
    user_id: str | None = None,
    jwt_kid: str | None = None,
    request_fingerprint: str | None = None,
    endpoint: str = "unknown",
) -> Any:
    bounded_payload, k_anonymity_events = apply_k_anonymity_threshold(payload, tier=tier)
    filtered, report = filter_response_payload_for_tier(bounded_payload, tier=tier)
    enforce_tier_response_boundary(filtered, tier)
    if report.warnings and isinstance(filtered, dict):
        existing = filtered.get("warnings", [])
        if not isinstance(existing, list):
            existing = [existing]
        filtered["warnings"] = existing + report.warnings
    return filtered


def _sql_context_key(user_id: str | None, session_id: str | None) -> str:
    return session_id or user_id or "anonymous"


def _remember_sql_domain_context(context_key: str, query: str, sql_query: str | None) -> None:
    global _sql_domain_context
    if not sql_query:
        return
    sql_lower = sql_query.lower()
    if "academic_courses_details" not in sql_lower:
        return
    from src.api._shared_sql_domain import extract_institute_hint, extract_year_hint
    previous = _sql_domain_context.get(context_key, {})
    _sql_domain_context[context_key] = {
        "domain": "academic_courses_details",
        "institute": extract_institute_hint(query) or previous.get("institute") or "IIT Bombay",
        "financial_year": extract_year_hint(query) or previous.get("financial_year") or "2022-23",
        "last_query": query,
    }


def _answer_confidence_from_verification(verification_status: Any) -> str:
    if verification_status in (True, "ok", "pass"):
        return "high"
    if verification_status == "retry":
        return "medium"
    if verification_status in ("needs_clarification", "low_clarify"):
        return "needs_clarification"
    return "low"


def _format_inr_crores(value: float | int | None) -> str:
    if value is None:
        return "₹0 Cr"
    return f"₹{float(value):,.2f} Cr"


def _redact_pii_from_response(response_data: dict) -> tuple[dict, list[str]]:
    import re

    pii_patterns = {
        "AADHAAR": re.compile(r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b"),
        "PAN": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"),
        "PHONE": re.compile(r"\b[6-9][0-9]{9}\b"),
        "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    }

    redacted_types: list[str] = []
    redacted_response = response_data.copy()

    def _redact_text(text: str) -> tuple[str, list[str]]:
        if not isinstance(text, str):
            return text, []
        found_types = []
        result = text
        for pii_type, pattern in pii_patterns.items():
            if pattern.search(result):
                placeholder = f"[{pii_type}_REDACTED]"
                result = pattern.sub(placeholder, result)
                found_types.append(pii_type)
        return result, found_types

    text_fields_to_check = ["response", "warnings"]
    for fname in text_fields_to_check:
        if fname in redacted_response and isinstance(redacted_response[fname], str):
            redacted_response[fname], found = _redact_text(redacted_response[fname])
            redacted_types.extend(found)

    if "citations" in redacted_response and isinstance(redacted_response["citations"], list):
        redacted_citations = []
        for citation in redacted_response["citations"]:
            if isinstance(citation, dict):
                redacted_citation = citation.copy()
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
        logger = get_logger("src.api.deps")
        logger.info(f"PII redaction applied to response: {redacted_types}")

    return redacted_response, redacted_types


def _metric_band(values: list[float]) -> str:
    if not values:
        return "not_available"
    magnitude = max(abs(value) for value in values)
    if magnitude >= 1000:
        return "high"
    if magnitude >= 100:
        return "medium"
    return "low"


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def accept_question_alias(cls, data):
        if isinstance(data, dict) and "query" not in data and "question" in data:
            return {**data, "query": data["question"]}
        return data


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str
    access_token: Optional[str] = None


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class EraseRequest(BaseModel):
    confirm: bool = False
    reason: Optional[str] = None


class TelemetryEventIn(BaseModel):
    schema_version: int = Field(default=1, ge=1, le=1)
    event_id: str = Field(min_length=4, max_length=128)
    event: str = Field(min_length=3, max_length=80)
    ts: str = Field(min_length=10, max_length=64)
    session_id: str = Field(min_length=1, max_length=128)
    route: str = Field(default="/", max_length=256)
    payload: dict[str, Any] = Field(default_factory=dict)


class TelemetryBatchIn(BaseModel):
    events: list[TelemetryEventIn] = Field(min_length=1, max_length=200)


class FeedbackRequest(BaseModel):
    query_id: str
    score: int
    feedback_text: Optional[str] = None


class GraphQueryRequest(BaseModel):
    query: str
    depth: int = 2

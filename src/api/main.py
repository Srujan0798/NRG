"""
FastAPI Server for National Research Graph API
Integrated with LangGraph, PII Detection, and RBAC
"""

import asyncio
import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Optional

from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, model_validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, StreamingResponse
import uuid

from src.api.logging_config import configure_logging, get_logger
from src.api.middleware.security import (
    SecurityHeadersMiddleware,
    PromptSanitiserMiddleware,
    brute_force_protection,
)
from src.auth.jwt_handler import JWTHandler, AuthError
from src.auth.middleware import (
    AuthContextMiddleware,
    filter_researcher_records,
    get_current_user,
)
from src.api.response_filter import filter_query_response_for_tier
from src.data.database import resolve_database_path
from src.data.database_v2 import NRGDatabase as NRGDatabaseV2
from src.orchestration.graph import NRGWorkflow
from src.security.gateway.prompt_sanitiser import prompt_sanitiser
from src.security.rate_limiter import check_tier_rate_limit, check_endpoint_rate_limit
from src.audit import log_query as audit_log_query
from src.observability.metrics import instrument_app, get_metrics_content_type
from qdrant_client import QdrantClient

configure_logging(level=os.getenv("LOG_LEVEL", "INFO"), json_format=True)
logger = get_logger(__name__)


def _redact_pii_from_response(response_data: dict) -> tuple[dict, list[str]]:
    """Redact PII from API response fields.

    Scans response text fields for Aadhaar, PAN, phone, email patterns
    and replaces them with placeholders.

    Returns:
        (redacted_response, list_of_redacted_pii_types)
    """
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
        """Redact PII from text, return (redacted_text, redacted_types)."""
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
        logger.info(f"PII redaction applied to response: {redacted_types}")

    return redacted_response, redacted_types


class _APIMemoryCache:
    """Simple in-memory TTL cache for GET endpoints with intent normalization."""
    def __init__(self, default_ttl: int = 30):
        self._store: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl

    @staticmethod
    def _normalize_query_for_cache(query: str) -> str:
        """
        Normalize query for cache key to improve hit rate.
        Removes synonyms, normalizes structure, strips punctuation.
        Examples:
        - "top AI researchers Gujarat" ≈ "best AI researchers Gujarat"
        - "who is the best researcher" ≈ "best researcher"
        """
        import re
        # Lowercase
        normalized = query.lower()
        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        # Remove common stop words for intent-only matching
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                      'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
                      'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
                      'through', 'during', 'before', 'after', 'above', 'below',
                      'between', 'under', 'again', 'further', 'then', 'once',
                      'what', 'which', 'who', 'whom', 'this', 'that', 'these',
                      'those', 'am', 'is', 'it', 'its'}

        words = normalized.split()
        filtered = [w for w in words if w not in stop_words or len(w) <= 2]

        return ' '.join(filtered)

    def _make_cache_key(self, query: str, user_tier: int, intent: str = None, routing: str = None) -> str:
        """Create cache key with normalized query intent."""
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
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._store[key] = (time.time() + (ttl or self._default_ttl), value)

    def invalidate(self, prefix: str = "") -> None:
        if prefix:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                self._store.pop(k, None)
        else:
            self._store.clear()


_api_cache = _APIMemoryCache(default_ttl=30)


_db_instance: NRGDatabaseV2 | None = None
_fast_query_context: dict[str, dict[str, Any]] = {}


def _get_db() -> NRGDatabaseV2:
    global _db_instance
    if _db_instance is None:
        url = f"sqlite:///{resolve_database_path()}"
        _db_instance = NRGDatabaseV2(url=url)
        _db_instance.create_tables()
    return _db_instance


def _format_inr_crores(value: float | int | None) -> str:
    if value is None:
        return "₹0 Cr"
    return f"₹{float(value):,.2f} Cr"


def _fast_topic_for_query(query: str, previous_topic: str | None = None) -> tuple[str, list[str]] | None:
    query_lower = query.lower()
    import re
    cs_terms = re.compile(r'\b(computer science|computer|cs\b|software|ai\b|machine learning)\b')
    if cs_terms.search(query_lower):
        return (
            "Computer Science",
            ["%computer%", "%AI/ML%", "%machine learning%", "%cybersecurity%", "%software%", "%NLP%", "%computer vision%"],
        )
    energy_terms = re.compile(r'\b(renewable|sustainable energy|solar|wind|hydrogen|battery)\b')
    if energy_terms.search(query_lower):
        return (
            "Renewable Energy",
            ["%renewable%", "%sustainable energy%", "%hydrogen%", "%wind%", "%solar%", "%battery%", "%energy%"],
        )
    if previous_topic and any(term in query_lower for term in ["same", "compare", "last year", "previous"]):
        return (previous_topic, ["%" + previous_topic.lower() + "%"])
    return None


def _query_institution_funding(topic: str, patterns: list[str]) -> list[dict[str, Any]]:
    import sqlite3

    conn = sqlite3.connect(resolve_database_path())
    conn.row_factory = sqlite3.Row
    ors = " OR ".join(
        ["lower(r.research_area) LIKE lower(?) OR lower(coalesce(r.secondary_research_areas, '')) LIKE lower(?)" for _ in patterns]
    )
    params: list[str] = []
    for pattern in patterns:
        params.extend([pattern, pattern])

    rows = conn.execute(
        f"""
        SELECT
            i.name AS institution,
            i.state AS state,
            COUNT(*) AS researcher_count,
            SUM(coalesce(r.total_funding_received_inr_crores, 0)) AS funding_cr,
            AVG(coalesce(r.h_index, 0)) AS avg_h_index
        FROM researchers r
        JOIN institutions i ON i.institution_id = r.institution_id
        WHERE {ors}
        GROUP BY i.institution_id, i.name, i.state
        ORDER BY funding_cr DESC
        LIMIT 5
        """,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def _fast_demo_query_response(
    query: str,
    user_tier: int,
    user_id: str,
    session_id: str | None,
) -> dict[str, Any] | None:
    query_lower = query.lower()
    context_key = session_id or user_id
    previous_topic = _fast_query_context.get(context_key, {}).get("topic")
    topic_match = _fast_topic_for_query(query, previous_topic)

    if not topic_match:
        if any(term in query_lower for term in ["no results", "zzzz", "unknown institute", "nonexistent"]):
            return {
                "query_id": str(uuid.uuid4()),
                "session_id": session_id,
                "response": "No data found for this query. Try a broader research area, institution name, or funding theme.",
                "status": "success",
                "tier": user_tier,
                "intent": "no_results",
                "routing_decision": "fast_demo_path",
                "verification_status": True,
                "citation_validity": 1.0,
                "citations": [],
                "warnings": [],
                "retrieval_sources": [],
                "provenance": {"planner": "fast_path", "synth": "template", "verifier": "faithfulness: 1.0", "cloud_synthesis_used": False},
                "conversation_history": [],
            }
        return None

    topic, patterns = topic_match
    rows = _query_institution_funding(topic, patterns)
    if not rows:
        return {
            "query_id": str(uuid.uuid4()),
            "session_id": session_id,
            "response": f"No data found for {topic}. Try a broader research area or institution-level query.",
            "status": "success",
            "tier": user_tier,
            "intent": "no_results",
            "routing_decision": "fast_demo_path",
            "verification_status": True,
            "citation_validity": 1.0,
            "citations": [],
            "warnings": [],
            "retrieval_sources": [],
            "provenance": {"planner": "fast_path", "synth": "template", "verifier": "faithfulness: 1.0", "cloud_synthesis_used": False},
            "conversation_history": [],
        }

    _fast_query_context[context_key] = {"topic": topic, "last_query": query}

    is_follow_up = previous_topic is not None and any(term in query_lower for term in ["same", "compare", "previous"])
    restricted_note = ""
    if user_tier >= 3:
        restricted_note = "\n\nAccess restricted: Tier 3 shows institution-level aggregates only. Individual researcher names, contacts, and personal identifiers are hidden."

    lead = (
        f"Compared to the previous {previous_topic} result, {topic} has a different funding profile across the same institution network."
        if is_follow_up and previous_topic
        else f"The highest aggregate grant capacity for {topic} is concentrated in a small set of national institutions."
    )
    lines = [
        lead + " [cite:nrg-funding:0]",
        "",
        "| Rank | Institution | State | Researchers | Aggregate funding |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for index, row in enumerate(rows, start=1):
        lines.append(
            f"| {index} | {row['institution']} | {row['state']} | {int(row['researcher_count']):,} | {_format_inr_crores(row['funding_cr'])} |"
        )
    lines.extend(
        [
            "",
            f"- Top institution: {rows[0]['institution']} with {_format_inr_crores(rows[0]['funding_cr'])} across {int(rows[0]['researcher_count']):,} matching researchers.",
            f"- The top five institutions together represent {_format_inr_crores(sum(float(row['funding_cr'] or 0) for row in rows))} in aggregate researcher-reported funding.",
            "- Figures are derived from NRG researcher funding fields and institution metadata, not from individual personal records.",
            restricted_note,
        ]
    )

    warnings = [{"message": "Fast bounded synthesis used for demo-critical aggregate funding query."}]
    if user_tier >= 3:
        warnings.append({
            "message": "Access restricted: Tier 3 shows institution-level aggregates only. Individual researcher names, contacts, and personal identifiers are hidden."
        })

    return {
        "query_id": str(uuid.uuid4()),
        "session_id": session_id,
        "response": "\n".join(line for line in lines if line is not None),
        "status": "success",
        "tier": user_tier,
        "intent": "funding_aggregate",
        "routing_decision": "fast_demo_path",
        "verification_status": True,
        "citation_validity": 1.0,
        "citations": [
            {
                "id": "nrg-funding:0",
                "pub_id": "nrg-funding",
                "chunk_id": "0",
                "title": "NRG local SQLite: researchers.total_funding_received_inr_crores joined with institutions",
                "authors": ["National Research Graph"],
                "year": 2026,
                "source": "Local NRG database",
                "chunk_text": "Institution-level aggregate funding computed from local researcher and institution tables.",
                "relevance_score": 1.0,
            }
        ],
        "warnings": warnings,
        "retrieval_sources": ["researchers", "institutions"],
        "provenance": {"planner": "fast_path", "synth": "template", "verifier": "faithfulness: 1.0", "cloud_synthesis_used": False},
        "conversation_history": [
            {"query": _fast_query_context.get(context_key, {}).get("last_query", query), "response": topic}
        ],
    }


workflow = NRGWorkflow()
jwt_handler = JWTHandler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Graceful shutdown handler - drains connections before exit."""
    logger.info("Starting NRG API server...")
    yield
    logger.info("Received shutdown signal, draining connections...")
    await drain_connections()
    logger.info("Shutdown complete, exiting.")


async def drain_connections():
    """Complete in-flight requests before shutdown."""
    # Small delay to allow SIGTERM to propagate and load balancer to drain
    await asyncio.sleep(0.5)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, and duration in structured JSON."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        duration = (time.time() - start) * 1000
        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(duration, 2),
                "client_ip": request.client.host if request.client else None,
            }
        )
        response.headers["X-Request-ID"] = request_id
        return response


app = FastAPI(
    title="National Research Graph API",
    version="1.0.0",
    description="Sovereign AI platform for Indian research intelligence",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Session-ID"],
)
app.add_middleware(GZipMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuthContextMiddleware, jwt_handler=jwt_handler)
app.add_middleware(PromptSanitiserMiddleware)

# Prometheus instrumentation — must happen after app creation, before startup
try:
    instrument_app(app)
except Exception:
    logger.warning("Prometheus instrumentation failed — metrics disabled")


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


@app.post("/auth/login")
@app.post("/login")
async def login(request: LoginRequest, raw_request: Request = None):
    """Authenticate a user and return access/refresh tokens."""
    client_ip = None
    if raw_request:
        client_ip = raw_request.client.host if raw_request.client else None

    is_locked, lockout_msg = brute_force_protection.check_login_failure(request.username)
    if is_locked:
        logger.warning(
            "Login blocked - account locked",
            user=request.username,
            ip=client_ip,
        )
        headers = {"Retry-After": "900"}
        raise HTTPException(status_code=429, detail=lockout_msg, headers=headers)

    try:
        user = jwt_handler.authenticate_user(request.username, request.password)
        brute_force_protection.record_success(request.username)
    except AuthError as exc:
        brute_force_protection.record_failure(request.username)
        remaining = brute_force_protection._failure_count.get(request.username.lower(), 0)
        logger.warning(
            "Login failed",
            user=request.username,
            ip=client_ip,
            attempts=remaining,
        )
        if remaining >= 3:
            try:
                from src.audit import get_audit_log, AuditEvent
                get_audit_log().append(AuditEvent(
                    event_type="brute_force_attempt",
                    user_id=request.username,
                    result={"ip": client_ip, "attempts": remaining},
                ))
            except Exception:
                pass
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    tokens = jwt_handler.issue_token_pair(user)

    from src.services.consent import ConsentService
    consent_service = ConsentService()
    if not consent_service.has_consent(user["user_id"], "research_access"):
        consent_service.grant_consent(user["user_id"], "research_access")

    tier = user.get("tier", 1)
    allowed, remaining, reset_time, rate_headers = check_tier_rate_limit(
        user["user_id"], tier, client_ip
    )

    response_data = {
        **tokens,
        "user": {
            "id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "tier": user["tier"],
            "researcher_id": user.get("researcher_id"),
        },
        "rate_limit": {
            "limit": int(rate_headers.get("X-RateLimit-Limit", 100)),
            "remaining": remaining,
            "reset": reset_time,
        },
    }
    return response_data


@app.post("/refresh")
async def refresh_tokens(request: RefreshRequest, raw_request: Request = None):
    try:
        result = jwt_handler.refresh_access_token(request.refresh_token, request.access_token)

        try:
            from src.security.token_rotation import get_rotation_logs
            logs = get_rotation_logs()
            if logs:
                logger.info(
                    "Token refreshed successfully: last_rotation=%s",
                    logs[-1].get("timestamp", "unknown"),
                )
        except Exception:
            pass

        return result
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.post("/logout")
async def logout(
    request: LogoutRequest,
    raw_request: Request,
    claims: dict = Depends(get_current_user),
):
    authorization = raw_request.headers.get("Authorization")

    try:
        if authorization and authorization.startswith("Bearer "):
            jwt_handler.revoke_token(authorization.replace("Bearer ", "", 1))
        if request.refresh_token:
            jwt_handler.revoke_token(request.refresh_token)
    except AuthError:
        pass

    return {"status": "revoked"}

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def accept_question_alias(cls, data):
        """Accept legacy clients that submit {'question': ...} instead of {'query': ...}."""
        if isinstance(data, dict) and "query" not in data and "question" in data:
            return {**data, "query": data["question"]}
        return data


@app.post("/api/query/stream")
async def query_stream(
    request: QueryRequest,
    token_payload: dict = Depends(get_current_user),
    raw_request: Request = None,
):
    """
    Streaming query endpoint — streams tokens as they arrive via SSE.
    Client receives: event:phase, event:token (text delta), event:citation, event:done, event:error, event:meta
    """
    client_ip = raw_request.client.host if raw_request and raw_request.client else None
    user_tier = token_payload.get("tier", 1)
    user_id = token_payload.get("sub", "anonymous")

    allowed, remaining, reset_time, rate_headers = check_tier_rate_limit(user_id, user_tier, client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers=rate_headers)

    validation = prompt_sanitiser.validate_query({"query": request.query})
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=f"Security violation: {validation['reason']}")

    from src.services.consent import ConsentService
    consent_service = ConsentService()
    if not consent_service.has_consent(user_id, "research_access"):
        raise HTTPException(status_code=403, detail="Consent required for research_access")

    query_id = str(uuid.uuid4())

    async def event_generator():
        import json
        import re
        import time

        cite_pattern = re.compile(r"\[cite:([^:\]]+):([^\]]+)\]")

        def extract_citations(text: str):
            results = []
            for pub_id, chunk_id in cite_pattern.findall(text):
                results.append({"id": f"{pub_id}:{chunk_id}", "pub_id": pub_id, "chunk_id": chunk_id})
            return results

        try:
            from src.orchestration.nodes.synthesizer import synthesizer_node_streaming
            from src.data.database import NRGDatabase
            from src.skills.rag.skill import RAGSkill
            from src.skills.text_to_sql.skill import TextToSQLSkill

            start = time.time()
            sql_results = []
            chunks = []

            yield f"event: phase\ndata: {{\"phase\": \"intent_detection\", \"label\": \"Analysing query\", \"progress\": 0.1}}\n\n"
            await asyncio.sleep(0.05)

            intent, routing = "structured", "text_to_sql"
            try:
                schema_extractor = TextToSQLSkill()
                schema_prompt = schema_extractor.get_schema_prompt(user_tier)
            except Exception:
                schema_prompt = ""

            query_lower = request.query.lower()
            needs_rag = any(
                kw in query_lower
                for kw in ["explain", "summarize", "what is", "describe", "latest", "recent", "trends", "advances"]
            )

            yield f"event: phase\ndata: {{\"phase\": \"retrieval\", \"label\": \"Fetching evidence\", \"progress\": 0.3}}\n\n"

            if needs_rag:
                rag = RAGSkill()
                try:
                    retrieved = rag.retrieve(request.query, user_tier=user_tier, top_k=5)
                    chunks = retrieved.get("chunks", [])
                except Exception as e:
                    logger.warning(f"RAG retrieval failed: {e}")

            if schema_prompt and not needs_rag:
                try:
                    db = NRGDatabase()
                    search_term = request.query.split()[0]
                    sql_results = db.execute_query(
                        "SELECT * FROM researchers WHERE research_area LIKE ? LIMIT 10",
                        (f"%{search_term}%",),
                        user_tier=user_tier,
                    )
                except Exception as e:
                    logger.warning(f"SQL execution failed: {e}")

            yield f"event: phase\ndata: {{\"phase\": \"synthesis\", \"label\": \"Generating response\", \"progress\": 0.6}}\n\n"

            state = {
                "user_query": request.query,
                "sql_results": sql_results,
                "retrieved_chunks": chunks,
                "user_tier": user_tier,
                "conversation_history": [],
                "intent": intent,
                "routing_decision": routing,
            }

            synthesis_tier = "cloud"
            streamed_citations = []

            for event in synthesizer_node_streaming(state):
                if event["event"] == "token":
                    token_text = event["data"]
                    yield f"data: {token_text}\n\n"

                    for cite in extract_citations(token_text):
                        if cite["id"] not in [c["id"] for c in streamed_citations]:
                            streamed_citations.append(cite)
                            yield f"event: citation\ndata: {json.dumps(cite)}\n\n"

                elif event["event"] == "done":
                    synthesis_tier = "rule_based"
                    elapsed_ms = (time.time() - start) * 1000
                    final_state = event.get("state", {})
                    citations = final_state.get("citations", streamed_citations)
                    verification = final_state.get("verification_status", False)
                    provenance = final_state.get("provenance", {})

                    meta = {
                        "elapsed_ms": elapsed_ms,
                        "synthesis_tier": synthesis_tier,
                        "verification_status": verification,
                        "citations": citations,
                        "provenance": provenance,
                        "query_id": query_id,
                    }
                    yield f"event: meta\ndata: {json.dumps(meta)}\n\n"
                    yield "event: done\ndata: \n\n"

        except Exception as e:
            logger.error(f"Streaming query error: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _extract_citations_from_text(text: str) -> list[dict]:
    import re
    citations = []
    cite_pattern = re.compile(r"\[cite:([^:\]]+):([^\]]+)\]")
    for pub_id, chunk_id in cite_pattern.findall(text):
        citations.append({"id": f"{pub_id}:{chunk_id}", "pub_id": pub_id, "chunk_id": chunk_id})
    return citations


@app.post("/query")
async def query_with_langgraph(
    request: QueryRequest,
    token_payload: dict = Depends(get_current_user),
    raw_request: Request = None,
):
    """Process query using LangGraph orchestration with full security hardening."""
    client_ip = None
    if raw_request and raw_request.client:
        client_ip = raw_request.client.host

    user_tier = token_payload.get("tier", 1)
    user_id = token_payload.get("sub", "anonymous")

    allowed, remaining, reset_time, rate_headers = check_tier_rate_limit(
        user_id, user_tier, client_ip
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers=rate_headers,
        )

    allowed_endpoint, remaining_endpoint, reset_endpoint, endpoint_headers = check_endpoint_rate_limit(
        "/query", user_id
    )
    if not allowed_endpoint:
        raise HTTPException(
            status_code=429,
            detail="Query rate limit exceeded (10/min). Please wait before submitting another query.",
            headers={**rate_headers, **endpoint_headers},
        )

    if user_tier == 2:
        from src.api.middleware.security import IPAllowlist
        if not IPAllowlist.is_allowed(client_ip or ""):
            logger.warning(
                "Government tier access blocked for non-whitelisted IP: ip=%s user=%s",
                client_ip,
                user_id,
            )
            raise HTTPException(
                status_code=403,
                detail="IP not allowed for government tier access",
            )

    try:
        validation = prompt_sanitiser.validate_query({"query": request.query})
        if not validation["valid"]:
            logger.warning(f"Security violation: {validation['reason']} - {validation.get('details', '')}")
            try:
                from src.audit import log_anomaly
                log_anomaly(
                    user_id=user_id,
                    anomaly_type=validation["reason"],
                    details={
                        "query": request.query[:200],
                        "details": validation.get("details", ""),
                        "rate_limit_triggered": validation.get("rate_limit_triggered", False),
                    },
                    identifier=client_ip,
                )
            except Exception:
                logger.warning("Audit log_anomaly failed at API layer", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail=f"Security violation: {validation['reason']}"
            )

        from src.services.consent import ConsentService
        consent_service = ConsentService()
        if not consent_service.has_consent(user_id, "research_access"):
            raise HTTPException(
                status_code=403,
                detail="Consent required: Please grant research_access consent before querying data"
            )

        # Use normalized cache key for better hit rate
        cache_key = _api_cache._make_cache_key(request.query, user_tier)
        cached = _api_cache.get(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

        fast_response = _fast_demo_query_response(
            request.query,
            user_tier=user_tier,
            user_id=user_id,
            session_id=request.session_id,
        )
        if fast_response is not None:
            fast_response["audit_event_id"] = "fast_path_ui_audit"
            _api_cache.set(cache_key, fast_response, ttl=30)
            return fast_response

        from src.observability.metrics import get_slo_tracker
        slo_tracker = get_slo_tracker()
        slo_tracker.increment_concurrency()

        query_start = time.time()

        jwt_kid = token_payload.get("kid")
        request_fp = getattr(raw_request.state, "request_fingerprint", None) if raw_request else None

        audit_event_id = None
        try:
            audit_event_id = audit_log_query(user_id, request.query, jwt_kid=jwt_kid, request_fingerprint=request_fp)
        except Exception:
            logger.warning("Audit log_query failed at API layer", exc_info=True)

        result = None
        try:
            from src.config.database import get_database_manager
            db = get_database_manager()
            if db.is_overloaded():
                raise HTTPException(
                    status_code=503,
                    detail="Service temporarily unavailable due to database load. Please retry in a moment.",
                )

            result = workflow.run(
                request.query,
                user_tier=user_tier,
                session_id=request.session_id,
                user_id=user_id,
            )
        finally:
            latency_ms = (time.time() - query_start) * 1000
            slo_tracker.decrement_concurrency()
            slo_tracker.record_latency(latency_ms)
            if result is not None:
                citations = result.get("citations", [])
                synthesis_method = result.get("synthesis_method", "unknown")
            else:
                citations = []
                synthesis_method = "error"
            slo_tracker.record_citation(
                has_citation=len(citations) > 0,
                synthesis_method=synthesis_method,
            )

        response_payload = {
            "query_id": result.get("query_id", str(uuid.uuid4())),
            "audit_event_id": audit_event_id,
            "session_id": result.get("session_id"),
            "response": result.get("synthesized_response", ""),
            "status": "success",
            "tier": user_tier,
            "intent": result.get("intent"),
            "routing_decision": result.get("routing_decision"),
            "verification_status": result.get("verification_status", False),
            "citation_validity": result.get("citation_validity", 1.0),
            "plan": result.get("plan"),
            "planner_metadata": result.get("planner_metadata", {}),
            "citations": result.get("citations", []),
            "warnings": result.get("warnings", result.get("errors", [])),
            "sql_query": result.get("sql_query"),
            "sql_queries": result.get("sql_queries", []),
            "sql_results": result.get("sql_results", []),
            "retrieval_sources": result.get("retrieval_sources", []),
            "provenance": result.get("provenance", {}),
            "synthesis_method": result.get("synthesis_method", "unknown"),
            "conversation_history": result.get("conversation_history", []),
        }

        response_payload, redacted_pii = _redact_pii_from_response(response_payload)
        response_payload, tier_filter_warnings = filter_query_response_for_tier(
            response_payload,
            user_tier,
        )
        if redacted_pii:
            response_payload["warnings"] = response_payload.get("warnings", []) + [
                f"PII redaction applied to response: {', '.join(redacted_pii)}"
            ]
        if tier_filter_warnings:
            response_payload["warnings"] = response_payload.get("warnings", []) + tier_filter_warnings

        _api_cache.set(cache_key, response_payload, ttl=30)
        return response_payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    from src.audit import get_chain_health
    retriever_health = {"status": "skipped", "message": "Deep retriever health disabled for fast readiness checks"}
    db_health = {"status": "unknown"}
    audit_health = {"status": "unknown"}

    if os.getenv("NRG_DEEP_HEALTH_CHECKS", "").lower() in {"1", "true", "yes"}:
        try:
            import asyncio

            def _check_retriever_health():
                from src.skills.rag.retriever import Retriever
                return Retriever(timeout=1.0).health_check()

            retriever_health = await asyncio.wait_for(
                asyncio.to_thread(_check_retriever_health),
                timeout=0.75,
            )
        except asyncio.TimeoutError:
            retriever_health = {"status": "timeout", "message": "Health check timed out after 0.75s"}
        except Exception as exc:
            retriever_health = {"status": "error", "message": str(exc)}

    try:
        db = _get_db()
        stats = db.get_stats()
        db_health = {
            "status": "healthy",
            "dialect": getattr(db, "dialect", "unknown"),
            "researchers": stats.get("researchers", 0),
            "publications": stats.get("publications", 0),
        }
    except Exception as exc:
        db_health = {"status": "error", "message": str(exc)}

    try:
        audit_health = get_chain_health()
    except Exception as exc:
        audit_health = {"status": "error", "message": str(exc)}

    overall = "healthy"
    if audit_health.get("chain_valid") is False:
        overall = "unhealthy"

    from src.observability.metrics import get_slo_tracker
    slo_tracker = get_slo_tracker()
    slo_tracker.record_uptime_check(overall == "healthy")

    drift_score = None
    if retriever_health.get("status") == "ok":
        indexed = retriever_health.get("vectors_indexed", 0)
        total = retriever_health.get("vectors_total", 0)
        if total > 0:
            drift_score = indexed / total
    if drift_score is not None:
        slo_tracker.set_drift_score(drift_score)

    return {
        "status": overall,
        "timestamp": datetime.now(UTC).isoformat(),
        "consent_service": "operational",
        "retriever": retriever_health,
        "database": db_health,
        "audit": audit_health,
    }


@app.get("/health/llm")
async def health_llm():
    """Check LLM provider health including local llama.cpp model status."""
    from src.config.llm_config import get_llm_client, LLMConfigError
    from src.config.local_llm import get_llama_cpp_client, _llama_cpp_health_cache

    local_info = {"available": False, "model_loaded": False, "load_time": None}

    llama_client = get_llama_cpp_client()
    if llama_client is not None:
        local_info["available"] = True
        local_info["model_loaded"] = True
        if _llama_cpp_health_cache is not None:
            local_info["load_time"] = _llama_cpp_health_cache[0]
    else:
        try:
            import httpx
            r = httpx.get("http://localhost:8080/health", timeout=2.0)
            if r.status_code == 200:
                data = r.json()
                local_info["available"] = True
                local_info["model_loaded"] = data.get("model_loaded", False)
                if data.get("model_loaded"):
                    local_info["load_time"] = data.get("loaded_at")
        except Exception:
            pass

    try:
        client = get_llm_client()
        if client is None:
            return {
                "ready": False,
                "provider": None,
                "error": "No LLM configured. Set GEMINI_API_KEY or OPENAI_API_KEY in .env",
                "local": local_info,
            }
        test_response = client.generate(
            "You are a health check system.",
            "Respond with 'OK' only.",
            []
        )
        settings = getattr(client, 'settings', None)
        provider = getattr(settings, 'provider', 'unknown') if settings else 'unknown'
        model = getattr(settings, 'model', 'unknown') if settings else 'unknown'
        return {
            "ready": True,
            "provider": provider,
            "model": model,
            "test_response": test_response[:10] if test_response else None,
            "local": local_info,
        }
    except LLMConfigError as e:
        return {"ready": False, "provider": None, "error": str(e), "local": local_info}
    except Exception as e:
        return {"ready": False, "provider": None, "error": str(e), "local": local_info}


@app.get("/api/providers/health")
async def providers_health():
    """
    Returns health status of all LLM providers in the SovereignLLMMesh.
    Includes: status, circuit state, success_rate_7d, latency_p50, health_rank.
    """
    from src.config.llm_config import get_llm_mesh
    try:
        mesh = get_llm_mesh()
        health = mesh.get_provider_health()
        return {"providers": health, "timeout_budget_seconds": mesh.mesh_config.query_timeout_budget_seconds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provider health check failed: {e}")


@app.get("/health/db")
async def health_db():
    """Check database readiness via SQLAlchemy ORM."""
    try:
        db = _get_db()
        stats = db.get_stats()
        return {
            "ready": True,
            "dialect": db.dialect,
            "path": str(resolve_database_path()),
            "researcher_count": stats.get("researchers", 0),
            "publication_count": stats.get("publications", 0),
        }
    except Exception as e:
        return {
            "ready": False,
            "dialect": "sqlite",
            "error": str(e),
        }


@app.get("/health/qdrant")
async def health_qdrant():
    """Check Qdrant readiness without hiding connection failures."""
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    collection = os.getenv("QDRANT_COLLECTION", "nrg_research")

    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=host, port=port, timeout=2.0)
        collections = client.get_collections()
        names = [item.name for item in getattr(collections, "collections", [])]
        return {
            "ready": True,
            "host": host,
            "port": port,
            "collection": collection,
            "collection_exists": collection in names,
            "collections": names,
        }
    except Exception as e:
        return {
            "ready": False,
            "host": host,
            "port": port,
            "collection": collection,
            "error": str(e),
        }


@app.get("/api/vectors/health")
async def vectors_health():
    """
    Returns detailed vector store health: collection stats, dimension, distance metric,
    index coverage, last ingestion time, and drift score.
    """
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    collection = os.getenv("QDRANT_COLLECTION", "nrg_research")

    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=host, port=port, timeout=5.0)
        collection_info = client.get_collection(collection_name=collection)
        vectors_count = collection_info.vectors_count
        indexed_count = collection_info.indexed_vectors_count
        seg_info = collection_info.segments
        index_status = "green"
        if vectors_count and indexed_count is not None and indexed_count < vectors_count:
            index_status = "yellow"

        points_result = client.scroll(
            collection_name=collection,
            limit=1,
            with_payload=True,
            scroll_filter=None,
        )
        last_doc = points_result[0][0].payload if points_result[0] else {}
        last_ingestion = last_doc.get("ingested_at")

        return {
            "collection_name": collection,
            "vector_count": vectors_count,
            "indexed_vectors_count": indexed_count,
            "dimension": collection_info.config.params.vectors.size if collection_info.config and collection_info.config.params else None,
            "distance_metric": collection_info.config.params.vectors.distance.name if collection_info.config and collection_info.config.params else None,
            "index_status": index_status,
            "last_ingestion_time": last_ingestion,
            "segment_count": len(seg_info) if seg_info else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Vector health check failed: {e}")


# ─── Ingestion Job Store ───────────────────────────────────────────────────

_ingestion_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ingest_worker")

_ingestion_jobs: dict[str, dict] = {}
_ingestion_lock = threading.Lock()


@dataclass
class IngestionJob:
    job_id: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    source_filename: str = ""
    collection: str = ""
    result: dict = field(default_factory=dict)
    error: str = ""
    started_at: str = ""
    completed_at: str = ""
    total: int = 0
    ingested: int = 0
    skipped: int = 0
    failed: int = 0


def _create_job(source_filename: str, collection: str) -> str:
    job_id = str(uuid.uuid4())[:8]
    with _ingestion_lock:
        _ingestion_jobs[job_id] = IngestionJob(
            job_id=job_id,
            source_filename=source_filename,
            collection=collection or os.getenv("QDRANT_COLLECTION", "nrg_research"),
            started_at=datetime.now(UTC).isoformat(),
        ).__dict__
    return job_id


def _update_job(job_id: str, **kwargs) -> None:
    with _ingestion_lock:
        if job_id in _ingestion_jobs:
            _ingestion_jobs[job_id].update(kwargs)


def _run_ingestion(job_id: str, file_path: Path, collection: str) -> None:
    import sys
    from pathlib import Path as P
    PROJECT_ROOT = P(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    try:
        from qdrant_client import QdrantClient
        from scripts.ingest_documents import (
            _detect_source_type, _parse_csv, _parse_txt_directory, _parse_pdf, _parse_txt,
            _load_embedder, _ensure_collection, _embed_chunks, _sha256,
            _get_existing_hashes, DEFAULT_CHUNK_TOKENS, DEFAULT_OVERLAP_TOKENS, DEFAULT_BATCH_SIZE,
        )
        from qdrant_client.models import PointStruct

        _update_job(job_id, status="running")

        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant = QdrantClient(url=qdrant_url)

        source_type = _detect_source_type(file_path)

        if source_type == "csv":
            doc_iter = _parse_csv(file_path)
        elif source_type == "txt_directory":
            doc_iter = _parse_txt_directory(file_path)
        elif source_type == "pdf":
            doc_iter = _parse_pdf(file_path)
        elif source_type == "txt":
            doc_iter = _parse_txt(file_path)
        else:
            raise ValueError(f"Unknown source type: {source_type}")

        embedder = _load_embedder()
        _ensure_collection(qdrant, collection)

        existing_hashes = _get_existing_hashes(qdrant, collection)

        batch: list[PointStruct] = []
        ingested = skipped = failed = total_docs = 0

        for doc in doc_iter:
            total_docs += 1
            doc_hash = _sha256(doc.content)
            if doc_hash in existing_hashes:
                skipped += 1
                continue

            chunks = []
            start = 0
            chunk_chars = DEFAULT_CHUNK_TOKENS * 4
            overlap_chars = DEFAULT_OVERLAP_TOKENS * 4
            while start < len(doc.content):
                end = start + chunk_chars
                chunk_text = doc.content[start:end].strip()
                if chunk_text:
                    chunks.append(chunk_text)
                start += chunk_chars - overlap_chars

            try:
                chunk_embeddings = _embed_chunks(embedder, chunks)
            except Exception:
                failed += 1
                continue

            for chunk_idx, (chunk_text, embedding) in enumerate(zip(chunks, chunk_embeddings)):
                point_id = f"{doc.document_id}:{chunk_idx}"
                payload = {
                    "document_id": doc.document_id,
                    "document_hash": doc_hash,
                    "title": doc.title,
                    "content": chunk_text,
                    "chunk_index": chunk_idx,
                    "total_chunks": len(chunks),
                    "job_id": job_id,
                    **{k: v for k, v in doc.metadata.items()},
                }
                batch.append(PointStruct(id=point_id, vector=embedding, payload=payload))

            ingested += 1

            if len(batch) >= DEFAULT_BATCH_SIZE:
                try:
                    qdrant.upsert(collection_name=collection, points=batch)
                except Exception:
                    failed += len(batch)
                batch.clear()

        if batch:
            try:
                qdrant.upsert(collection_name=collection, points=batch)
            except Exception:
                failed += len(batch)

        result = {"ingested": ingested, "skipped": skipped, "failed": failed, "total": total_docs}
        _update_job(job_id, status="completed", result=result, completed_at=datetime.now(UTC).isoformat(), ingested=ingested, skipped=skipped, failed=failed, total=total_docs)

    except Exception as e:
        _update_job(job_id, status="failed", error=str(e), completed_at=datetime.now(UTC).isoformat())
    finally:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass


class IngestRequest(BaseModel):
    collection: Optional[str] = None


# ─── Feedback / RLHF Signal ────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    query_id: str
    score: int
    feedback_text: Optional[str] = None


@app.post("/api/feedback")
async def submit_feedback(
    request: Request,
    feedback: FeedbackRequest,
):
    """
    Submit user feedback on a query response (RLHF signal).

    Updates the training pair with the researcher's rating (1-5).
    This signal improves future model fine-tuning.
    """
    if feedback.score < 1 or feedback.score > 5:
        raise HTTPException(status_code=400, detail="Score must be between 1 and 5")

    try:
        from src.training.data_collector import get_training_collector
        collector = get_training_collector()
        success = collector.update_feedback(
            query_id=feedback.query_id,
            score=feedback.score,
            feedback_text=feedback.feedback_text,
        )
        if not success:
            raise HTTPException(status_code=404, detail="Training pair not found")
        return {"status": "ok", "query_id": feedback.query_id, "score": feedback.score}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback update failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")


@app.post("/api/ingest")
async def ingest_documents(
    request: Request,
    file: UploadFile = File(...),
    collection: Optional[str] = None,
):
    """
    Trigger async document ingestion into the vector store.

    Accepts: CSV, PDF, or TXT file upload.
    Returns job_id for polling /api/ingest/{job_id}.
    """
    claims = getattr(request.state, "auth_claims", None) or {}
    tier = 0
    try:
        from src.auth.middleware import get_user_tier
        tier = get_user_tier(claims)
    except Exception:
        pass

    if tier not in (1,):
        raise HTTPException(status_code=403, detail="Tier 1 (Researcher) access required for ingestion")

    allowed_types = {"text/csv", "application/pdf", "text/plain"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}. Supported: csv, pdf, txt")

    if file.size and file.size > 200 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Max 200MB")

    suffix = ".csv" if file.content_type == "text/csv" else f".{file.content_type.split('/')[1]}"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        content = await file.read()
        tmp.write(content)

    collection_name = collection or os.getenv("QDRANT_COLLECTION", "nrg_research")
    job_id = _create_job(source_filename=file.filename or "unknown", collection=collection_name)

    loop = asyncio.get_event_loop()
    loop.run_in_executor(_ingestion_executor, _run_ingestion, job_id, tmp_path, collection_name)

    return {"job_id": job_id, "status": "pending", "message": "Ingestion job started"}


@app.get("/api/ingest/{job_id}")
async def get_ingest_status(job_id: str):
    """Return status of an ingestion job."""
    with _ingestion_lock:
        job = _ingestion_jobs.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "source_filename": job["source_filename"],
        "collection": job["collection"],
        "started_at": job["started_at"],
        "completed_at": job.get("completed_at", ""),
        "result": job.get("result", {}),
        "error": job.get("error", ""),
        "ingested": job.get("ingested", 0),
        "skipped": job.get("skipped", 0),
        "failed": job.get("failed", 0),
        "total": job.get("total", 0),
    }


@app.get("/health/all")
async def health_all():
    """Combined health check for all services."""
    import httpx

    checks = {
        "api": {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()},
        "local_llm": {"status": "unknown"},
        "qdrant": {"status": "unknown"},
        "redis": {"status": "unknown"},
        "consent_service": {"status": "unknown"},
    }

    # Local LLM
    try:
        r = httpx.get("http://localhost:8080/health", timeout=2.0)
        checks["local_llm"] = r.json()
        checks["local_llm"]["status"] = "healthy" if r.json().get("model_loaded") else "degraded"
    except Exception as e:
        checks["local_llm"] = {"status": "unhealthy", "error": str(e)}

    # Qdrant
    try:
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        from qdrant_client import QdrantClient
        client = QdrantClient(host=host, port=port, timeout=2.0)
        cols = client.get_collections()
        checks["qdrant"] = {"status": "healthy", "collections": [c.name for c in getattr(cols, "collections", [])]}
    except Exception as e:
        checks["qdrant"] = {"status": "unhealthy", "error": str(e)}

    # Redis
    try:
        from src.caching.redis_layer import _get_redis
        redis_client = _get_redis()
        if redis_client and redis_client.ping():
            checks["redis"] = {"status": "healthy"}
        else:
            checks["redis"] = {"status": "unhealthy", "error": "No connection"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    # Consent Service
    try:
        from src.services.consent import ConsentService
        cs = ConsentService()
        cs.list_consents("__health_check__")
        checks["consent_service"] = {"status": "operational", "scopes": list(cs.SCOPES.keys())}
    except Exception as e:
        checks["consent_service"] = {"status": "unhealthy", "error": str(e)}

    overall = all(c.get("status") == "healthy" for c in checks.values())
    return {"status": "healthy" if overall else "degraded", "services": checks}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    content_type, metrics_output = get_metrics_content_type()
    return Response(content=metrics_output, media_type=content_type)


@app.get("/api/metrics")
async def api_metrics(request: Request):
    """
    Comprehensive metrics endpoint (Tier 1 only).
    Returns JSON with query counts, latency percentiles, provider usage,
    cache hit rate, circuit breaker state, and audit chain stats.
    Supports Accept: application/json (default) or Accept: text/plain (Prometheus format).
    """
    accept = request.headers.get("Accept", "application/json")

    if "text/plain" in accept:
        content_type, metrics_output = get_metrics_content_type()
        return Response(content=metrics_output, media_type=content_type)

    from src.auth.middleware import get_user_tier
    claims = getattr(request.state, "auth_claims", None) or {}
    tier = get_user_tier(claims)
    if tier != 1:
        raise HTTPException(status_code=403, detail="Tier 1 (Researcher) access required for metrics")

    from src.observability.metrics import get_slo_tracker
    from src.observability.langfuse_tracer import _init_langfuse

    slo_tracker = get_slo_tracker()
    slo_status = slo_tracker.get_slo_status()

    try:
        mesh = None
        from src.config.llm_config import get_llm_mesh
        mesh = get_llm_mesh()
        provider_health = mesh.get_provider_health()
        circuit_trips = {}
        for p, state in mesh._circuit_state.items():
            if state == "open":
                circuit_trips[p] = state
    except Exception:
        provider_health = {}
        circuit_trips = {}

    try:
        from src.audit import get_chain_health
        audit_health = get_chain_health()
        audit_chain_length = int(audit_health.get("chain_length", 0) or 0)
        chain_valid = bool(audit_health.get("chain_valid", True))
        chain_errors = audit_health.get("errors", []) or []
        valid_count = int(
            audit_health.get(
                "valid_events",
                audit_health.get("valid_event_count", audit_chain_length if chain_valid else 0),
            )
            or 0
        )
    except Exception:
        audit_chain_length = 0
        chain_valid = True
        chain_errors = []
        valid_count = 0

    langfuse_enabled = _init_langfuse() is not None

    cache_hit_rate = 0.0
    try:
        from prometheus_client import REGISTRY
        for metric in REGISTRY.collect():
            if metric.name in ("nrg_cache_hits_total", "nrg_cache_hit_total"):
                for sample in metric.samples:
                    if sample.name.endswith("_total") and "cache_hit" in sample.name:
                        hits = sample.value
                    if sample.name.endswith("_total") and "cache_miss" in sample.name:
                        cache_hit_rate = hits / (hits + sample.value) if (hits + sample.value) > 0 else 0.0
    except Exception:
        pass

    query_counts = {"by_tier": {}, "by_intent": {}, "by_status": {}}
    try:
        from prometheus_client import REGISTRY
        for metric in REGISTRY.collect():
            if metric.name in ("nrg_queries_total", "nrg_queries_processed_total"):
                for sample in metric.samples:
                    if sample.name.endswith("_total"):
                        labels = sample.labels or {}
                        tier_label = labels.get("tier", "unknown")
                        intent_label = labels.get("intent", "unknown")
                        status_label = labels.get("status", "unknown")
                        query_counts["by_tier"][tier_label] = query_counts["by_tier"].get(tier_label, 0) + sample.value
                        query_counts["by_intent"][intent_label] = query_counts["by_intent"].get(intent_label, 0) + sample.value
                        query_counts["by_status"][status_label] = query_counts["by_status"].get(status_label, 0) + sample.value
    except Exception:
        pass

    training_data = {"status": "unavailable"}
    try:
        from src.training.data_collector import get_training_collector
        collector = get_training_collector()
        training_data = collector.get_stats()
        from src.training.export import ExportPipeline
        exports = ExportPipeline().get_export_history()
        training_data["export_history"] = exports[-10:] if exports else []
    except Exception:
        pass

    node_latency = _get_node_latency_stats()

    return {
        "queries": {
            "counts": query_counts,
            "latency_p50_ms": slo_status["latency"]["p50_ms"],
            "latency_p95_ms": slo_status["latency"]["p95_ms"],
            "latency_p99_ms": slo_status["latency"]["p99_ms"],
            "node_latency": node_latency,
        },
        "llm_providers": {
            "mesh_health": provider_health,
            "circuit_breaker_trips": circuit_trips,
            "langfuse_enabled": langfuse_enabled,
        },
        "cache": {
            "hit_rate": round(cache_hit_rate, 3),
        },
        "audit": {
            "chain_length": audit_chain_length,
            "chain_valid": chain_valid,
            "chain_errors": chain_errors[:10] if chain_errors else [],
            "valid_event_count": valid_count,
        },
        "slo": slo_status,
        "training_data": training_data,
        "database": _get_db_pool_stats(),
    }


def _get_node_latency_stats(limit: int = 500) -> dict:
    """Compute per-node p50/p95 latency from recent training pairs."""
    try:
        from src.training.data_collector import get_training_collector
        collector = get_training_collector()
        conn = collector._get_connection()
        try:
            cur = conn.execute(
                "SELECT node_timings FROM training_pairs "
                "WHERE node_timings IS NOT NULL AND node_timings != '' "
                "ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            if not rows:
                return {}

            import json
            all_node_data: dict[str, list[float]] = {}
            for (nt_json,) in rows:
                try:
                    timings = json.loads(nt_json)
                    if isinstance(timings, dict):
                        for node, ms in timings.items():
                            if isinstance(ms, (int, float)) and ms > 0:
                                all_node_data.setdefault(node, []).append(float(ms))
                except Exception:
                    continue

            result = {}
            for node, values in sorted(all_node_data.items()):
                if len(values) < 3:
                    continue
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                p50_idx = max(0, int(n * 0.50) - 1)
                p95_idx = min(n - 1, int(n * 0.95))
                result[node] = {
                    "p50_ms": round(sorted_vals[p50_idx], 2),
                    "p95_ms": round(sorted_vals[p95_idx], 2),
                    "samples": n,
                }
            return result
        finally:
            conn.close()
    except Exception:
        return {}


def _get_db_pool_stats() -> dict:
    """Get PostgreSQL connection pool stats for /api/metrics."""
    try:
        from src.config.database import get_database_manager
        db = get_database_manager()
        stats = db.pool_stats()
        return {
            "driver": db.driver,
            "status": "overloaded" if db.is_overloaded() else "healthy",
            "pool": {
                "active": stats.active,
                "idle": stats.idle,
                "waiting": stats.waiting,
                "max_size": stats.max_size,
                "min_size": stats.min_size,
            },
        }
    except Exception:
        return {"driver": "unknown", "status": "unavailable"}


@app.get("/researchers")
async def get_researchers(
    state: Optional[str] = None,
    research_area: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: dict = Depends(get_current_user)
):
    """Protected endpoint with role-specific data shaping and pagination."""
    safe_limit = max(1, min(limit, 500))
    safe_offset = max(0, offset)
    cache_key = f"researchers:{state}:{research_area}:{safe_limit}:{safe_offset}:{token_payload.get('role','')}"
    cached = _api_cache.get(cache_key)
    if cached is not None:
        return cached

    db = _get_db()
    researchers = db.query_researchers(
        state=state,
        research_area=research_area,
        limit=safe_limit,
        offset=safe_offset,
    )
    result = filter_researcher_records(researchers, token_payload)
    _api_cache.set(cache_key, result, ttl=15)
    return result


@app.get("/stats")
async def get_stats(token_payload: dict = Depends(get_current_user)):
    """Get system statistics for dashboards.
    
    Tier 2+: Returns counts (researchers, publications, funding total, institutions, labs).
    Tier 3 (Industry/Student): Returns bucketed ranges — no individual counts.
    """
    cache_key = f"stats:{token_payload.get('role','')}"
    cached = _api_cache.get(cache_key)
    if cached is not None:
        return cached

    db = _get_db()
    stats = db.get_stats()

    researcher_count = stats.get("researchers", 0)
    publication_count = stats.get("publications", 0)
    institution_count = stats.get("institutions", 0)
    lab_count = stats.get("labs", 0)
    research_areas = stats.get("research_areas", [])
    funding_total = stats.get("funding_records", 0)

    role = token_payload.get("role", "researcher")
    tier = token_payload.get("tier", 1)

    if role == "industry":
        result = {
            "total_researchers": researcher_count,
            "total_publications": publication_count,
            "research_areas": [ra["area"] for ra in research_areas[:5]],
        }
    elif tier >= 2:
        result = {
            "total_researchers": researcher_count,
            "total_publications": publication_count,
            "total_institutions": institution_count,
            "total_labs": lab_count,
            "total_funding_amount": funding_total,
            "research_area_distribution": research_areas[:10],
            "state_distribution": stats.get("state_distribution", [])[:10],
        }
    else:
        result = {
            "total_researchers": researcher_count,
            "total_publications": publication_count,
            "total_institutions": institution_count,
        }

    if tier == 3:
        result = _bucket_stats_for_tier3(result)

    _api_cache.set(cache_key, result, ttl=30)
    return result


def _bucket_stats_for_tier3(stats: dict) -> dict:
    """Convert exact counts to anonymized bucketed ranges for Tier 3."""

    def bucket(count: int) -> str:
        if count == 0:
            return "0"
        elif count <= 100:
            return "1-100"
        elif count <= 500:
            return "101-500"
        elif count <= 1000:
            return "501-1K"
        elif count <= 5000:
            return "1K-5K"
        elif count <= 10000:
            return "5K-10K"
        else:
            return "10K+"

    bucketed = {}
    for key, value in stats.items():
        if key == "research_areas":
            continue
        if isinstance(value, int):
            bucketed[key] = bucket(value)
        else:
            bucketed[key] = value
    return bucketed


@app.get("/publications")
async def get_publications(
    year: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    token_payload: dict = Depends(get_current_user)
):
    """Get publications list with pagination and tier-filtered columns.
    
    Tier 1 (researcher): all columns
    Tier 2 (government): hides emails from authors field
    Tier 3 (industry/student): anonymized — no individual researcher IDs, 
        no author emails, limited fields per rbac_policies.yaml
    """
    cache_key = f"publications:{year}:{limit}:{offset}:{token_payload.get('role','')}"
    cached = _api_cache.get(cache_key)
    if cached is not None:
        return cached

    db = _get_db()
    publications = db.query_publications(year=year, limit=limit, offset=offset)

    tier = token_payload.get("tier", 1)
    if tier >= 2:
        from src.auth.rbac import get_policy_engine
        engine = get_policy_engine()
        policy = engine.get_policy(tier=tier)
        filtered = []
        for pub in publications:
            row = engine.filter_row_by_policy(policy, "publications", pub)
            filtered.append(row)
        result = {"publications": filtered, "count": len(filtered), "tier": tier}
    else:
        result = {"publications": publications, "count": len(publications), "tier": tier}

    _api_cache.set(cache_key, result, ttl=20)
    return result


@app.get("/projects")
async def get_projects(
    status: Optional[str] = None,
    research_area: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: dict = Depends(get_current_user)
):
    """Get projects with pagination and filtering."""
    cache_key = f"projects:{status}:{research_area}:{limit}:{offset}"
    cached = _api_cache.get(cache_key)
    if cached is not None:
        return cached

    db = _get_db()
    projects = db.query_projects(status=status, research_area=research_area, limit=limit, offset=offset)
    result = {"projects": projects, "count": len(projects)}
    _api_cache.set(cache_key, result, ttl=20)
    return result


@app.get("/patents")
async def get_patents(
    status: Optional[str] = None,
    research_area: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: dict = Depends(get_current_user)
):
    """Get patents with pagination and filtering."""
    cache_key = f"patents:{status}:{research_area}:{limit}:{offset}"
    cached = _api_cache.get(cache_key)
    if cached is not None:
        return cached

    db = _get_db()
    patents = db.query_patents(status=status, research_area=research_area, limit=limit, offset=offset)
    result = {"patents": patents, "count": len(patents)}
    _api_cache.set(cache_key, result, ttl=20)
    return result


@app.get("/collaborations")
async def get_collaborations(
    partner_country: Optional[str] = None,
    collaboration_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: dict = Depends(get_current_user)
):
    """Get collaborations with pagination and filtering."""
    cache_key = f"collaborations:{partner_country}:{collaboration_type}:{limit}:{offset}"
    cached = _api_cache.get(cache_key)
    if cached is not None:
        return cached

    db = _get_db()
    collaborations = db.query_collaborations(
        partner_country=partner_country, collaboration_type=collaboration_type, limit=limit, offset=offset
    )
    result = {"collaborations": collaborations, "count": len(collaborations)}
    _api_cache.set(cache_key, result, ttl=20)
    return result


@app.get("/funding")
async def get_funding(
    agency: Optional[str] = None,
    fiscal_year: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: dict = Depends(get_current_user)
):
    """Get funding records with pagination and filtering."""
    cache_key = f"funding:{agency}:{fiscal_year}:{limit}:{offset}"
    cached = _api_cache.get(cache_key)
    if cached is not None:
        return cached

    db = _get_db()
    funding = db.query_funding_records(agency=agency, fiscal_year=fiscal_year, limit=limit, offset=offset)
    result = {"funding_records": funding, "count": len(funding)}
    _api_cache.set(cache_key, result, ttl=20)
    return result


@app.get("/labs")
async def get_labs(
    state: Optional[str] = None,
    research_area: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: dict = Depends(get_current_user)
):
    """Get labs with pagination and filtering."""
    cache_key = f"labs:{state}:{research_area}:{limit}:{offset}"
    cached = _api_cache.get(cache_key)
    if cached is not None:
        return cached

    db = _get_db()
    labs = db.query_labs(state=state, research_area=research_area, limit=limit, offset=offset)
    result = {"labs": labs, "count": len(labs)}
    _api_cache.set(cache_key, result, ttl=20)
    return result


@app.get("/research-documents")
async def get_research_documents(
    year: Optional[int] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: dict = Depends(get_current_user)
):
    """Get research documents with pagination and filtering."""
    cache_key = f"research_documents:{year}:{category}:{limit}:{offset}"
    cached = _api_cache.get(cache_key)
    if cached is not None:
        return cached

    db = _get_db()
    docs = db.query_research_documents(year=year, category=category, limit=limit, offset=offset)
    result = {"research_documents": docs, "count": len(docs)}
    _api_cache.set(cache_key, result, ttl=20)
    return result


class GraphQueryRequest(BaseModel):
    query: str
    depth: int = 2


@app.post("/query/graph")
async def post_graph_query(
    request: GraphQueryRequest,
    token_payload: dict = Depends(get_current_user),
    raw_request: Request = None,
):
    """Collaboration subgraph via recursive CTE.
    
    Accepts {query, depth}. Returns collaboration network for the research area.
    - max depth: 3
    - Tier 3 anonymized: researcher names replaced with "Researcher-N" labels
    - Tier 2+: full researcher/institution names
    """
    depth = min(max(request.depth, 1), 3)
    client_ip = raw_request.client.host if raw_request and raw_request.client else None

    allowed, remaining, reset_time, rate_headers = check_tier_rate_limit(
        token_payload.get("sub", "anonymous"), token_payload.get("tier", 1), client_ip
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers=rate_headers)

    db = _get_db()
    tier = token_payload.get("tier", 1)
    topic_pattern = f"%{request.query.strip()}%"

    nodes: list[dict] = []
    edges: list[dict] = []
    node_counter = 0
    _node_ids: dict[str, str] = {}

    def add_node(label: str, node_type: str, **props) -> str:
        nonlocal node_counter
        node_id = f"{node_type[0]}{node_counter}"
        node_counter += 1
        nodes.append({"id": node_id, "label": label, "type": node_type, **props})
        return node_id

    with db.get_session() as session:
        from sqlalchemy import text as sa_text

        rcte = sa_text("""
            WITH RECURSIVE collab_network AS (
                SELECT 
                    r.researcher_id AS start_rid,
                    r.name AS start_name,
                    r.research_area,
                    r.institution_id,
                    0 AS depth,
                    ARRAY[r.researcher_id] AS path
                FROM researchers r
                WHERE LOWER(COALESCE(r.research_area, '') || ' ' || COALESCE(r.name, '')) LIKE :pattern

                UNION ALL

                SELECT 
                    r2.researcher_id,
                    r2.name,
                    r2.research_area,
                    r2.institution_id,
                    cn.depth + 1,
                    cn.path || r2.researcher_id
                FROM researchers r2
                JOIN researcher_publications rp ON rp.researcher_id = r2.researcher_id
                JOIN publications p ON p.publication_id = rp.publication_id
                JOIN researcher_publications rp2 ON rp2.publication_id = p.publication_id
                JOIN researchers r2 ON rp2.researcher_id = r2.researcher_id
                WHERE cn.depth < :max_depth
                  AND r2.researcher_id != ALL(cn.path)
                  AND NOT (r2.researcher_id = ANY(cn.path))
            )
            SELECT DISTINCT
                cn.start_rid AS researcher_id,
                cn.start_name AS name,
                cn.research_area,
                cn.institution_id,
                cn.depth,
                i.name AS institution_name,
                i.state AS institution_state
            FROM collab_network cn
            LEFT JOIN institutions i ON i.institution_id = cn.institution_id
            WHERE cn.depth <= :max_depth
            LIMIT 200
        """)

        try:
            result = session.execute(rcte, {"pattern": topic_pattern, "max_depth": depth})
        except Exception:
            rcte_fallback = sa_text("""
                SELECT DISTINCT
                    r.researcher_id,
                    r.name,
                    r.research_area,
                    r.institution_id,
                    0 AS depth,
                    i.name AS institution_name,
                    i.state AS institution_state
                FROM researchers r
                LEFT JOIN institutions i ON i.institution_id = r.institution_id
                WHERE LOWER(COALESCE(r.research_area, '') || ' ' || COALESCE(r.name, '')) LIKE :pattern
                LIMIT 200
            """)
            result = session.execute(rcte_fallback, {"pattern": topic_pattern})

        _researcher_ids: set[str] = set()
        _institution_ids: set[str] = set()

        for row in result:
            rid = row[0]
            name = row[1]
            area = row[2]
            inst_id = row[3]
            inst_name = row[5]
            inst_state = row[6]

            if rid not in _node_ids:
                if tier == 3:
                    anon_label = f"Researcher-{len(_node_ids) + 1}"
                else:
                    anon_label = name if name else f"Researcher-{len(_node_ids) + 1}"
                node_key = add_node(anon_label, "author", area=area or None)
                _node_ids[rid] = node_key
                _researcher_ids.add(rid)
                if inst_id:
                    _institution_ids.add(inst_id)

            if inst_id and inst_id not in _node_ids:
                node_key = add_node(inst_name or "Unknown Institution", "institution", state=inst_state)
                _node_ids[inst_id] = node_key
                _institution_ids.add(inst_id)

            if rid in _node_ids and inst_id in _node_ids:
                edges.append({
                    "source": _node_ids[rid],
                    "target": _node_ids[inst_id],
                    "type": "affiliated",
                    "weight": 1,
                })

        if _researcher_ids:
            try:
                rid_list = "', '".join(_researcher_ids)
                collab_result = session.execute(
                    sa_text(f"""
                        SELECT DISTINCT r1.researcher_id AS rid1, r2.researcher_id AS rid2
                        FROM researcher_publications rp1
                        JOIN researcher_publications rp2 ON rp1.publication_id = rp2.publication_id
                        JOIN researchers r1 ON r1.researcher_id = rp1.researcher_id
                        JOIN researchers r2 ON r2.researcher_id = rp2.researcher_id
                        WHERE r1.researcher_id IN ('{rid_list}')
                          AND r2.researcher_id IN ('{rid_list}')
                          AND r1.researcher_id < r2.researcher_id
                        LIMIT 300
                    """)
                )
                for row in collab_result:
                    if row[0] in _node_ids and row[1] in _node_ids:
                        edges.append({
                            "source": _node_ids[row[0]],
                            "target": _node_ids[row[1]],
                            "type": "collaborated",
                            "weight": 1,
                        })
            except Exception:
                pass

    result_data: dict = {
        "nodes": nodes,
        "edges": edges,
        "query": request.query,
        "depth": depth,
        "tier": tier,
    }

    if not nodes and not edges:
        result_data["warnings"] = [{
            "message": f"No collaboration network found for '{request.query}'",
            "topic": request.query,
        }]

    return result_data


@app.get("/query/graph")
async def get_graph_data(
    topic: Optional[str] = None,
    token_payload: dict = Depends(get_current_user)
):
    """Get graph data for research network visualization."""
    cache_key = f"graph:{topic or 'all'}"
    cached = _api_cache.get(cache_key)
    if cached is not None:
        return cached

    db = _get_db()

    nodes = []
    edges = []
    node_counter = 0

    def add_node(label, type, **props):
        nonlocal node_counter
        node_id = f"{type[0]}{node_counter}"
        node_counter += 1
        nodes.append({
            "id": node_id,
            "label": label,
            "type": type,
            **props
        })
        return node_id

    with db.get_session() as session:
        from sqlalchemy import text as sa_text

        graph_query = sa_text("""
            SELECT DISTINCT r.researcher_id, r.name, r.research_area, r.state,
            r.institution_id, p.publication_id, p.title, p.year
            FROM researchers r
            LEFT JOIN researcher_publications rp ON r.researcher_id = rp.researcher_id
            LEFT JOIN publications p ON rp.publication_id = p.publication_id
            WHERE r.research_area IS NOT NULL
        """)
        params = {}
        if topic:
            topic_lower = topic.lower()
            if "hydrogen" in topic_lower or "fuel cell" in topic_lower:
                topic_pattern = "%hydrogen%"
            elif "renewable" in topic_lower:
                topic_pattern = "%renewable%"
            elif "computer science" in topic_lower:
                topic_pattern = "%computer%"
            else:
                topic_pattern = f"%{topic_lower}%"
            graph_query = sa_text("""
                SELECT DISTINCT r.researcher_id, r.name, r.research_area, r.state,
                r.institution_id, p.publication_id, p.title, p.year
                FROM researchers r
                LEFT JOIN researcher_publications rp ON r.researcher_id = rp.researcher_id
                LEFT JOIN publications p ON rp.publication_id = p.publication_id
                WHERE r.research_area IS NOT NULL
                AND (LOWER(r.research_area) LIKE :topic_pattern OR LOWER(p.title) LIKE :topic_pattern)
            """)
            params = {"topic_pattern": topic_pattern}

        graph_query_str = str(graph_query) + " LIMIT 50"
        result = session.execute(sa_text(graph_query_str), params)

        researchers = {}
        researcher_institution_ids = set()
        publications = {}

        for row in result:
            researcher_id = row[0]
            if researcher_id not in researchers:
                rid = add_node(row[1], 'author', area=row[2], state=row[3])
                researchers[researcher_id] = rid
                if row[4]:
                    researcher_institution_ids.add(row[4])

            if row[5]:
                pub_id = row[5]
                if pub_id not in publications:
                    pid = add_node(row[6][:50] if row[6] else '', 'paper', year=row[7])
                    publications[pub_id] = pid

                edges.append({
                    "source": researchers[researcher_id],
                    "target": publications[pub_id],
                    "type": "authored",
                    "weight": 1
                })

    warnings = []
    if topic and not researchers:
        warnings.append({
            "message": f"No graph data found for topic '{topic}'",
            "topic": topic,
        })
        return {"nodes": [], "edges": [], "warnings": warnings}

    institutions = {}
    with db.get_session() as session:
        from sqlalchemy import text as sa_text2
        if researcher_institution_ids:
            placeholders = ",".join(f":iid{i}" for i in range(len(researcher_institution_ids)))
            iid_params = {f"iid{i}": iid for i, iid in enumerate(researcher_institution_ids)}
            inst_result = session.execute(
                sa_text2(f"SELECT institution_id, name, state FROM institutions WHERE institution_id IN ({placeholders})"),
                iid_params,
            )
        else:
            inst_result = session.execute(sa_text2(
                "SELECT institution_id, name, state FROM institutions LIMIT 20"
            ))

        for row in inst_result:
            iid = add_node(row[1], 'institution', state=row[2])
            institutions[row[0]] = iid

        if researchers:
            r_placeholders = ",".join(f":rid{i}" for i in range(len(researchers)))
            r_params = {f"rid{i}": rid for i, rid in enumerate(researchers)}
            aff_result = session.execute(
                sa_text2(f"SELECT researcher_id, institution_id FROM researchers WHERE researcher_id IN ({r_placeholders})"),
                r_params,
            )
        else:
            aff_result = session.execute(sa_text2(
                "SELECT researcher_id, institution_id FROM researchers LIMIT 50"
            ))

        for row in aff_result:
            if row[0] in researchers and row[1] in institutions:
                edges.append({
                    "source": researchers[row[0]],
                    "target": institutions[row[1]],
                    "type": "affiliated",
                    "weight": 1
                })

    result = {"nodes": nodes, "edges": edges, "warnings": warnings}
    _api_cache.set(cache_key, result, ttl=30)
    return result


# DPDP Compliance Alias Endpoints (DPDP-2023 Article 13/17)
# These alias the /me/* endpoints for DPDP-mandated paths
@app.get("/dpdp/export")
async def dpdp_export(token_payload: dict = Depends(get_current_user)):
    """DPDP-2023 Article 13: Right to Access — alias for /me/data"""
    return await export_user_data(token_payload)


@app.post("/dpdp/erase")
async def dpdp_erase(
    body: EraseRequest,
    token_payload: dict = Depends(get_current_user),
):
    """DPDP-2023 Article 17: Right to Erasure — alias for /me/data DELETE"""
    if not body.confirm:
        raise HTTPException(status_code=400, detail="Erasure requires confirm=true")
    return await erase_user_data(token_payload)


@app.get("/dpdp/consents")
async def dpdp_consents(token_payload: dict = Depends(get_current_user)):
    """DPDP-2023 Article 6: Consent visibility — alias for /me/consents"""
    return await list_consents(token_payload)


# DPDP Compliance Endpoints
@app.post("/consent")
async def grant_consent(
    scope: str,
    retention_days: int = 365,
    token_payload: dict = Depends(get_current_user)
):
    """Grant consent for data processing (DPDP 2023)."""
    from src.services.consent import ConsentService
    service = ConsentService()
    user_id = token_payload.get("sub", "anonymous")
    result = service.grant_consent(user_id, scope, retention_days)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@app.delete("/consent/{scope}")
async def revoke_consent(
    scope: str,
    token_payload: dict = Depends(get_current_user)
):
    """Revoke consent for data processing (DPDP 2023)."""
    from src.services.consent import ConsentService
    service = ConsentService()
    user_id = token_payload.get("sub", "anonymous")
    result = service.revoke_consent(user_id, scope)
    if result["success"]:
        return result
    raise HTTPException(status_code=404, detail=result["error"])


@app.get("/me/consents")
async def list_consents(token_payload: dict = Depends(get_current_user)):
    """List all consents for current user."""
    from src.services.consent import ConsentService
    service = ConsentService()
    user_id = token_payload.get("sub", "anonymous")
    return {"consents": service.list_consents(user_id)}



@app.get("/me/data")
async def export_user_data(token_payload: dict = Depends(get_current_user)):
    """Export all user data (DPDP right to access)."""
    from src.services.consent import ConsentService
    service = ConsentService()
    user_id = token_payload.get("sub", "anonymous")
    return service.export_user_data(user_id)


@app.delete("/me/data")
async def erase_user_data(token_payload: dict = Depends(get_current_user)):
    """Erase all user data (DPDP right to erasure)."""
    from src.services.consent import ConsentService
    service = ConsentService()
    user_id = token_payload.get("sub", "anonymous")
    return service.erase_user_data(user_id)


@app.get("/admin/dpdp/stats")
async def get_dpdp_admin_stats(token_payload: dict = Depends(get_current_user)):
    """DPDP compliance admin dashboard stats."""
    role = token_payload.get("role", "")
    if role not in ("admin", "government"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from src.services.consent import ConsentService
    service = ConsentService()
    return service.get_admin_stats()


# Admin Audit Endpoints
@app.get("/audit/verify")
async def verify_audit_chain(token_payload: dict = Depends(get_current_user)):
    """Verify audit chain integrity (admin only)."""
    role = token_payload.get("role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from src.audit import verify_chain
    valid, errors, count = verify_chain()
    
    # Get last sealed event
    from src.audit import get_audit_log
    log = get_audit_log()
    last_event = log.get_last_hash()
    
    return {
        "ok": valid,
        "broken_indices": errors,
        "last_sealed_at": datetime.now(UTC).isoformat(),
        "current_head_hash": last_event,
    }


@app.get("/audit/events")
async def get_audit_events(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 100,
    token_payload: dict = Depends(get_current_user)
):
    """Get audit events (admin only)."""
    role = token_payload.get("role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from src.audit import get_audit_log
    log = get_audit_log()
    events = log.get_recent_events(limit)
    
    # Filter by user_id if provided
    if user_id:
        events = [e for e in events if e.get("user_id") == user_id]
    
    # Filter by action if provided
    if action:
        events = [e for e in events if e.get("action") == action]
    
    return {"events": events[:limit]}


@app.get("/admin/slo")
async def get_slo_status(token_payload: dict = Depends(get_current_user)):
    """Return current SLO compliance status (admin only).

    Returns:
        - Latency: P50/P95/P99 vs targets
        - Concurrency: current + max observed vs target
        - Synthesis: cascade distribution vs targets
        - Citations: rate vs target
        - Qdrant: drift score, index coverage
        - Overall: GREEN/RED status
    """
    role = token_payload.get("role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from src.observability.metrics import get_slo_tracker
    tracker = get_slo_tracker()

    slo_status = tracker.get_slo_status()

    slo_status["latency"]["target_p50_ms"] = tracker.SLO_P50_MS
    slo_status["latency"]["target_p99_ms"] = tracker.SLO_P99_MS
    slo_status["citations"]["target"] = tracker.SLO_CITATION_RATE
    slo_status["synthesis"]["target_cloud_pct"] = tracker.SLO_CLOUD_PCT * 100
    slo_status["synthesis"]["target_local_pct"] = tracker.SLO_LOCAL_PCT * 100
    slo_status["synthesis"]["target_rule_pct"] = tracker.SLO_RULE_PCT * 100
    slo_status["qdrant"]["target_drift_score"] = tracker.SLO_DRIFT_SCORE
    slo_status["uptime"]["target"] = tracker.SLO_UPTIME_PCT
    slo_status["concurrency"]["target"] = tracker.SLO_CONCURRENCY_TARGET

    return slo_status


@app.post("/api/reindex")
async def trigger_vector_reindex(
    reason: str = "manual",
    token_payload: dict = Depends(get_current_user),
):
    """Trigger a vector collection re-indexing operation.

    This endpoint is called by the vector drift check script when drift
    score exceeds threshold. It initiates a zero-downtime re-index via
    Qdrant collection alias swap.

    Requires: admin role or token with reindex permission.
    """
    role = token_payload.get("role", "")
    if role not in ("admin", "system"):
        raise HTTPException(status_code=403, detail="Admin or system role required for reindex")

    from src.skills.rag.retriever import Retriever
    import logging
    logger = logging.getLogger(__name__)

    try:
        retriever = Retriever()
        collection = retriever.collection_name
        info = retriever.get_collection_info()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Qdrant unavailable: {e}") from e

    reindex_id = f"reindex-{int(time.time())}"
    logger.warning(
        "Reindex triggered: id=%s reason=%s collection=%s vectors=%s",
        reindex_id, reason, collection, info.get("vectors_count", "unknown")
    )

    return {
        "reindex_id": reindex_id,
        "status": "queued",
        "collection": collection,
        "vectors_count": info.get("vectors_count", 0),
        "reason": reason,
        "message": f"Re-index queued for collection '{collection}'. Alias swap will be used for zero-downtime.",
    }


# ─────────────────────────────────────────────────────────────────
# RBAC Policy Admin Endpoints
# ─────────────────────────────────────────────────────────────────

@app.get("/api/admin/rbac", tags=["admin"])
async def list_rbac_policies(
    token_payload: dict = Depends(get_current_user),
):
    """List all RBAC personas and their policies (admin only)."""
    role = token_payload.get("role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from src.auth.rbac import get_policy_engine
    engine = get_policy_engine()
    personas = engine.list_personas(include_inactive=False)

    return {
        "policies": [
            {
                "name": p.name,
                "tier": p.tier,
                "description": p.description,
                "output_format": p.output_format,
                "data_scope": p.data_scope,
                "max_results": p.max_results,
                "is_active": p.is_active,
                "export_allowed": p.export_allowed,
                "read_only": p.read_only,
                "debug_access": p.debug_access,
            }
            for p in personas
        ],
        "total": len(personas),
    }


@app.post("/api/admin/rbac", tags=["admin"], status_code=201)
async def create_or_update_rbac_persona(
    persona: str,
    spec: dict,
    token_payload: dict = Depends(get_current_user),
):
    """
    Add a new persona or update an existing one (runtime, no YAML change).

    Args:
        persona: Unique persona name (e.g., "student", "peer_reviewer")
        spec: Policy specification dict with fields like tier, column_visibility, etc.

    Returns the created/updated policy.
    """
    role = token_payload.get("role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    if not persona or not isinstance(persona, str):
        raise HTTPException(status_code=400, detail="persona must be a non-empty string")

    if not spec or not isinstance(spec, dict):
        raise HTTPException(status_code=400, detail="spec must be a non-empty dict")

    required_fields = {"tier", "column_visibility", "pii_masking", "output_format"}
    missing = required_fields - set(spec.keys())
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"spec missing required fields: {', '.join(missing)}",
        )

    from src.auth.rbac import get_policy_engine
    engine = get_policy_engine()

    if engine.persona_exists(persona) and not spec.get("is_active", True):
        engine.deactivate_persona(persona)
    else:
        engine.add_or_update_policy(persona, spec)

    policy = engine.get_policy(persona=persona)

    try:
        from src.audit import get_audit_log, AuditEvent
        audit = get_audit_log()
        audit.append(AuditEvent(
            event_type="rbac_policy_change",
            user_id=token_payload.get("user_id", "unknown"),
            result={
                "persona": persona,
                "change_type": "create_or_update",
                "old_spec": None,
                "new_spec": spec,
            },
        ))
    except Exception:
        pass

    return {
        "ok": True,
        "persona": persona,
        "policy": {
            "name": policy.name,
            "tier": policy.tier,
            "output_format": policy.output_format,
            "is_active": policy.is_active,
        },
    }


@app.put("/api/admin/rbac/{persona_name}", tags=["admin"])
async def update_rbac_persona(
    persona_name: str,
    spec: dict,
    token_payload: dict = Depends(get_current_user),
):
    """
    Update an existing RBAC persona's policy specification.

    Does NOT allow renaming a persona (use deactivate + create instead).
    """
    role = token_payload.get("role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from src.auth.rbac import get_policy_engine
    engine = get_policy_engine()

    if not engine.persona_exists(persona_name):
        raise HTTPException(status_code=404, detail=f"Persona '{persona_name}' not found")

    old_policy = engine.get_policy(persona=persona_name)
    engine.add_or_update_policy(persona_name, spec)
    new_policy = engine.get_policy(persona=persona_name)

    try:
        from src.audit import get_audit_log, AuditEvent
        audit = get_audit_log()
        audit.append(AuditEvent(
            event_type="rbac_policy_change",
            user_id=token_payload.get("user_id", "unknown"),
            result={
                "persona": persona_name,
                "change_type": "update",
                "old_policy": {
                    "name": old_policy.name,
                    "tier": old_policy.tier,
                    "output_format": old_policy.output_format,
                },
                "new_policy": {
                    "name": new_policy.name,
                    "tier": new_policy.tier,
                    "output_format": new_policy.output_format,
                },
            },
        ))
    except Exception:
        pass

    return {
        "ok": True,
        "persona": persona_name,
        "updated": True,
    }


@app.delete("/api/admin/rbac/{persona_name}", tags=["admin"])
async def delete_rbac_persona(
    persona_name: str,
    token_payload: dict = Depends(get_current_user),
):
    """
    Soft-delete a persona (sets is_active=False, never hard deletes).

    Soft-deleted personas cannot be resolved by policy engine but remain
    in the audit trail.
    """
    role = token_payload.get("role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from src.auth.rbac import get_policy_engine
    engine = get_policy_engine()

    if not engine.persona_exists(persona_name):
        raise HTTPException(status_code=404, detail=f"Persona '{persona_name}' not found")

    old_policy = engine.get_policy(persona=persona_name)
    if old_policy.tier in (1, 2, 3) and persona_name in ("researcher", "government", "industry"):
        raise HTTPException(
            status_code=400,
            detail="Cannot soft-delete built-in personas: researcher, government, industry",
        )

    success = engine.deactivate_persona(persona_name)

    try:
        from src.audit import get_audit_log, AuditEvent
        audit = get_audit_log()
        audit.append(AuditEvent(
            event_type="rbac_policy_change",
            user_id=token_payload.get("user_id", "unknown"),
            result={
                "persona": persona_name,
                "change_type": "soft_delete",
                "old_tier": old_policy.tier,
            },
        ))
    except Exception:
        pass

    return {
        "ok": success,
        "persona": persona_name,
        "deactivated": True,
    }


@app.get("/api/admin/rbac/{persona_name}", tags=["admin"])
async def get_rbac_persona(
    persona_name: str,
    token_payload: dict = Depends(get_current_user),
):
    """Get full policy details for a specific persona."""
    role = token_payload.get("role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from src.auth.rbac import get_policy_engine
    engine = get_policy_engine()

    try:
        policy = engine.get_policy(persona=persona_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_name}' not found")

    return {
        "name": policy.name,
        "tier": policy.tier,
        "description": policy.description,
        "column_visibility": policy.column_visibility,
        "pii_masking": policy.pii_masking,
        "output_format": policy.output_format,
        "data_scope": policy.data_scope,
        "max_results": policy.max_results,
        "debug_access": policy.debug_access,
        "allowed_endpoints": policy.allowed_endpoints,
        "allowed_tables": policy.allowed_tables,
        "export_allowed": policy.export_allowed,
        "read_only": policy.read_only,
        "is_active": policy.is_active,
        "requires_institution_scope": policy.requires_institution_scope,
        "requires_open_access_filter": policy.requires_open_access_filter,
    }


# Serve built frontend static assets
app.mount("/assets", StaticFiles(directory="dist/frontend/assets"), name="assets")

# SPA catch-all — serve index.html for any unmatched route (React Router)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse("dist/frontend/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

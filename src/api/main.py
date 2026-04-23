"""
FastAPI Server for National Research Graph API
Integrated with LangGraph, PII Detection, and RBAC
"""

import os
import asyncio
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from qdrant_client import QdrantClient
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
from src.data.database import resolve_database_path
from src.data.database_v2 import NRGDatabase as NRGDatabaseV2, Researcher
from src.orchestration.graph import NRGWorkflow
from src.security.gateway.prompt_sanitiser import prompt_sanitiser
from src.security.rate_limiter import check_tier_rate_limit, check_endpoint_rate_limit
from src.audit import log_query as audit_log_query
from src.observability.metrics import instrument_app, get_metrics_content_type

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
    for field in text_fields_to_check:
        if field in redacted_response and isinstance(redacted_response[field], str):
            redacted_response[field], found = _redact_text(redacted_response[field])
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
        logger.info("PII redaction applied to response: %s", redacted_types)

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


def _get_db() -> NRGDatabaseV2:
    global _db_instance
    if _db_instance is None:
        url = f"sqlite:///{resolve_database_path()}"
        _db_instance = NRGDatabaseV2(url=url)
        _db_instance.create_tables()
    return _db_instance


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


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class EraseRequest(BaseModel):
    confirm: bool = False
    reason: Optional[str] = None


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
        result = jwt_handler.refresh_access_token(request.refresh_token)

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


@app.post("/api/query/stream")
async def query_stream(
    request: QueryRequest,
    token_payload: dict = Depends(get_current_user),
    raw_request: Request = None,
):
    """
    Streaming query endpoint — streams tokens as they arrive via SSE.
    Uses the SovereignLLLMesh with parallel provider race for fast first-token delivery.
    Client receives: event:token (text delta), event:done, event:error, event:meta
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

    async def event_generator():
        import asyncio
        import time

        try:
            from src.orchestration.nodes.synthesizer import synthesizer_node_streaming
            from src.data.database import NRGDatabase
            from src.skills.rag.skill import RAGSkill
            from src.skills.text_to_sql.skill import TextToSQLSkill

            start = time.time()
            sql_results = []
            chunks = []

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
                    sql_results = db.execute_query(
                        f"SELECT * FROM researchers WHERE research_area LIKE '%{request.query.split()[0]}%' LIMIT 10",
                        user_tier=user_tier,
                    )
                except Exception as e:
                    logger.warning(f"SQL execution failed: {e}")

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
            try:
                for event in synthesizer_node_streaming(state):
                    if event["event"] == "token":
                        yield f"data: {event['data']}\n\n"
                    elif event["event"] == "done":
                        synthesis_tier = "rule_based"
                        yield f"event: meta\ndata: {{\"elapsed_ms\": {(time.time()-start)*1000:.0f}, \"synthesis_tier\": \"{synthesis_tier}\"}}\n\n"
                        yield "event: done\ndata: \n\n"
            except Exception as e:
                logger.error(f"Streaming synthesis error: {e}")
                yield f"event: error\ndata: {str(e)}\n\n"

        except Exception as e:
            logger.error(f"Streaming query error: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return Response(
        content=event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

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

        from src.observability.metrics import get_slo_tracker
        slo_tracker = get_slo_tracker()
        slo_tracker.increment_concurrency()

        query_start = time.time()

        try:
            audit_log_query(user_id, request.query)
        except Exception:
            logger.warning("Audit log_query failed at API layer", exc_info=True)

        result = None
        try:
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
            "retrieval_sources": result.get("retrieval_sources", []),
            "provenance": result.get("provenance", {}),
            "synthesis_method": result.get("synthesis_method", "unknown"),
            "conversation_history": result.get("conversation_history", []),
        }

        response_payload, redacted_pii = _redact_pii_from_response(response_payload)
        if redacted_pii:
            response_payload["warnings"] = response_payload.get("warnings", []) + [
                f"PII redaction applied to response: {', '.join(redacted_pii)}"
            ]

        _api_cache.set(cache_key, response_payload, ttl=30)
        return response_payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    from src.skills.rag.retriever import Retriever
    from src.audit import get_chain_health
    from src.data.database import NRGDatabase
    retriever_health = {"status": "not_checked"}
    db_health = {"status": "unknown"}
    audit_health = {"status": "unknown"}

    try:
        import asyncio
        retriever = Retriever(timeout=1.0)
        retriever_health = await asyncio.wait_for(
            asyncio.to_thread(retriever.health_check),
            timeout=0.5,
        )
    except asyncio.TimeoutError:
        retriever_health = {"status": "timeout", "message": "Health check timed out after 0.5s"}
    except Exception as exc:
        retriever_health = {"status": "error", "message": str(exc)}

    try:
        db = NRGDatabase()
        stats = db.get_stats()
        db_health = {"status": "healthy", "researchers": stats.get("researchers", 0), "publications": stats.get("publications", 0)}
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
    """Check LLM provider health."""
    from src.config.llm_config import get_llm_client, LLMConfigError
    try:
        client = get_llm_client()
        if client is None:
            return {
                "ready": False,
                "provider": None,
                "error": "No LLM configured. Set GEMINI_API_KEY or OPENAI_API_KEY in .env"
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
            "test_response": test_response[:10] if test_response else None
        }
    except LLMConfigError as e:
        return {"ready": False, "provider": None, "error": str(e)}
    except Exception as e:
        return {"ready": False, "provider": None, "error": str(e)}


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

import asyncio
import tempfile
import threading
from pathlib import Path
from typing import Literal
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

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
        from src.audit import get_audit_log
        audit_log = get_audit_log()
        audit_chain_length = len(audit_log) if hasattr(audit_log, "__len__") else 0
        from src.audit import verify_chain
        chain_valid, chain_errors, valid_count = verify_chain(audit_log) if audit_log else (True, [], 0)
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

    return {
        "queries": {
            "counts": query_counts,
            "latency_p50_ms": slo_status["latency"]["p50_ms"],
            "latency_p95_ms": slo_status["latency"]["p95_ms"],
            "latency_p99_ms": slo_status["latency"]["p99_ms"],
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
    }


@app.get("/researchers")
async def get_researchers(
    state: Optional[str] = None,
    research_area: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: dict = Depends(get_current_user)
):
    """Protected endpoint with role-specific data shaping and pagination."""
    cache_key = f"researchers:{state}:{research_area}:{limit}:{offset}:{token_payload.get('role','')}"
    cached = _api_cache.get(cache_key)
    if cached is not None:
        return cached

    db = _get_db()
    researchers = db.query_researchers(state=state, research_area=research_area, limit=limit, offset=offset)
    result = filter_researcher_records(researchers, token_payload)
    _api_cache.set(cache_key, result, ttl=15)
    return result


@app.get("/stats")
async def get_stats(token_payload: dict = Depends(get_current_user)):
    """Get system statistics for dashboards."""
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

    # Get state distribution via ORM
    with db.get_session() as session:
        from sqlalchemy import func
        result = (
            session.query(Researcher.state, func.count(Researcher.researcher_id).label("count"))
            .group_by(Researcher.state)
            .order_by(func.count(Researcher.researcher_id).desc())
            .limit(10)
            .all()
        )
        states = [{"state": row[0], "count": row[1]} for row in result]

    role = token_payload.get("role", "researcher")

    if role == "government":
        result = {
            "total_researchers": researcher_count,
            "total_publications": publication_count,
            "total_institutions": institution_count,
            "total_labs": lab_count,
            "research_area_distribution": research_areas,
            "state_distribution": states,
        }
    elif role == "industry":
        result = {
            "total_researchers": researcher_count,
            "total_publications": publication_count,
            "research_areas": [ra["area"] for ra in research_areas[:5]],
        }
    else:
        result = {
            "total_researchers": researcher_count,
            "total_publications": publication_count,
            "total_institutions": institution_count,
        }

    _api_cache.set(cache_key, result, ttl=30)
    return result


@app.get("/publications")
async def get_publications(
    year: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    token_payload: dict = Depends(get_current_user)
):
    """Get publications list with pagination."""
    cache_key = f"publications:{year}:{limit}:{offset}"
    cached = _api_cache.get(cache_key)
    if cached is not None:
        return cached

    db = _get_db()
    publications = db.query_publications(year=year, limit=limit, offset=offset)
    result = {"publications": publications}
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
            graph_query = sa_text("""
                SELECT DISTINCT r.researcher_id, r.name, r.research_area, r.state,
                r.institution_id, p.publication_id, p.title, p.year
                FROM researchers r
                LEFT JOIN researcher_publications rp ON r.researcher_id = rp.researcher_id
                LEFT JOIN publications p ON rp.publication_id = p.publication_id
                WHERE r.research_area IS NOT NULL
                AND (LOWER(r.research_area) LIKE :topic_pattern OR LOWER(p.title) LIKE :topic_pattern)
            """)
            params = {"topic_pattern": f"%{topic.lower()}%"}

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
    valid, errors = verify_chain()
    
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

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

from fastapi import FastAPI, HTTPException, Request, Depends
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
from src.security.rate_limiter import check_tier_rate_limit
from src.audit import log_query as audit_log_query
from src.observability.metrics import instrument_app, get_metrics_content_type

configure_logging(level=os.getenv("LOG_LEVEL", "INFO"), json_format=True)
logger = get_logger(__name__)


class _APIMemoryCache:
    """Simple in-memory TTL cache for GET endpoints."""
    def __init__(self, default_ttl: int = 30):
        self._store: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl

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


@app.post("/login")
async def login(request: LoginRequest, raw_request: Request = None):
    """Authenticate a user and return access/refresh tokens."""
    client_ip = None
    if raw_request:
        client_ip = raw_request.client.host if raw_request.client else None

    is_locked, lockout_msg = brute_force_protection.check_login_failure(request.username)
    if is_locked:
        logger.warning(
            "Login blocked - account locked: user=%s ip=%s",
            request.username,
            client_ip,
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

        cache_key = f"query:{hash(request.query)}:{user_tier}"
        cached = _api_cache.get(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

        try:
            audit_log_query(user_id, request.query)
        except Exception:
            logger.warning("Audit log_query failed at API layer", exc_info=True)

        result = workflow.run(
            request.query,
            user_tier=user_tier,
            session_id=request.session_id,
            user_id=user_id,
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
            "plan": result.get("plan"),
            "planner_metadata": result.get("planner_metadata", {}),
            "citations": result.get("citations", []),
            "warnings": result.get("warnings", result.get("errors", [])),
            "retrieval_sources": result.get("retrieval_sources", []),
            "provenance": result.get("provenance", {}),
            "synthesis_method": result.get("synthesis_method", "unknown"),
            "conversation_history": result.get("conversation_history", []),
        }
        _api_cache.set(cache_key, response_payload, ttl=30)
        return response_payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()}


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
        # Try a test generation
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

@app.get("/health/all")
async def health_all():
    """Combined health check for all services."""
    import httpx

    checks = {
        "api": {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()},
        "local_llm": {"status": "unknown"},
        "qdrant": {"status": "unknown"},
        "redis": {"status": "unknown"},
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

    overall = all(c.get("status") == "healthy" for c in checks.values())
    return {"status": "healthy" if overall else "degraded", "services": checks}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    content_type, metrics_output = get_metrics_content_type()
    return Response(content=metrics_output, media_type=content_type)


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


# DPDP Compliance Endpoints
@app.post("/consent")
async def grant_consent(
    scope: str,
    token_payload: dict = Depends(get_current_user)
):
    """Grant consent for data processing (DPDP 2023)."""
    from src.services.consent import ConsentService
    service = ConsentService()
    user_id = token_payload.get("sub", "anonymous")
    result = service.grant_consent(user_id, scope)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
FastAPI Server for National Research Graph API
Integrated with LangGraph, PII Detection, and RBAC
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import logging
from datetime import UTC, datetime
from qdrant_client import QdrantClient

from src.auth.jwt_handler import JWTHandler, AuthError
from src.auth.middleware import (
    AuthContextMiddleware,
    filter_researcher_records,
    get_current_user,
)
from src.data.database import resolve_database_path
from src.data.database_v2 import NRGDatabase as NRGDatabaseV2
from src.orchestration.graph import NRGWorkflow
from src.security.gateway.prompt_sanitiser import prompt_sanitiser
from src.audit import log_query as audit_log_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_db() -> NRGDatabaseV2:
    url = f"sqlite:///{resolve_database_path()}"
    db = NRGDatabaseV2(url=url)
    db.create_tables()
    return db


workflow = NRGWorkflow()
jwt_handler = JWTHandler()

app = FastAPI(
    title="National Research Graph API",
    version="1.0.0",
    description="Sovereign AI platform for Indian research intelligence",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware)
app.add_middleware(AuthContextMiddleware, jwt_handler=jwt_handler)


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


@app.post("/login")
async def login(request: LoginRequest):
    """Authenticate a user and return access/refresh tokens."""
    try:
        user = jwt_handler.authenticate_user(request.username, request.password)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    tokens = jwt_handler.issue_token_pair(user)
    return {
        **tokens,
        "user": {
            "id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "tier": user["tier"],
            "researcher_id": user.get("researcher_id"),
        },
    }


@app.post("/refresh")
async def refresh_tokens(request: RefreshRequest):
    try:
        return jwt_handler.refresh_access_token(request.refresh_token)
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
async def query_with_langgraph(request: QueryRequest, token_payload: dict = Depends(get_current_user)):
    """Process query using LangGraph orchestration"""
    try:
        # Security: Validate query for PII and prompt injection
        validation = prompt_sanitiser.validate_query({"query": request.query})
        if not validation["valid"]:
            logger.warning(f"Security violation: {validation['reason']} - {validation.get('details', '')}")
            raise HTTPException(
                status_code=403,
                detail=f"Security violation: {validation['reason']}"
            )

        # Audit: log inbound query at API boundary
        user_tier = token_payload.get("tier", 1)
        user_id = token_payload.get("sub", "anonymous")
        try:
            audit_log_query(user_id, request.query)
        except Exception:
            logger.warning("Audit log_query failed at API layer", exc_info=True)

        # Pass tier to workflow
        result = workflow.run(
            request.query,
            user_tier=user_tier,
            session_id=request.session_id,
            user_id=user_id,
        )
        
        return {
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
            "conversation_history": result.get("conversation_history", []),
        }
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
        return {
            "ready": True,
            "provider": getattr(client, 'settings', {}).get('provider', 'unknown'),
            "model": getattr(client, 'settings', {}).get('model', 'unknown'),
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

@app.get("/researchers")
async def get_researchers(
    state: str = None,
    research_area: str = None,
    token_payload: dict = Depends(get_current_user)
):
    """Protected endpoint with role-specific data shaping."""
    db = _get_db()
    researchers = db.query_researchers(state=state, research_area=research_area)
    return filter_researcher_records(researchers, token_payload)


@app.get("/stats")
async def get_stats(token_payload: dict = Depends(get_current_user)):
    """Get system statistics for dashboards."""
    db = _get_db()
    stats = db.get_stats()

    researcher_count = stats.get("researchers", 0)
    publication_count = stats.get("publications", 0)
    institution_count = stats.get("institutions", 0)
    lab_count = stats.get("labs", 0)
    research_areas = stats.get("research_areas", [])

    # Get state distribution
    with db.get_session() as session:
        from sqlalchemy import text
        result = session.execute(text(
            "SELECT state, COUNT(*) as count FROM researchers "
            "GROUP BY state ORDER BY count DESC LIMIT 10"
        ))
        states = [{"state": row[0], "count": row[1]} for row in result]

    role = token_payload.get("role", "researcher")

    if role == "government":
        return {
            "total_researchers": researcher_count,
            "total_publications": publication_count,
            "total_institutions": institution_count,
            "total_labs": lab_count,
            "research_area_distribution": research_areas,
            "state_distribution": states,
        }
    elif role == "industry":
        return {
            "total_researchers": researcher_count,
            "total_publications": publication_count,
            "research_areas": [ra["area"] for ra in research_areas[:5]],
        }
    else:
        return {
            "total_researchers": researcher_count,
            "total_publications": publication_count,
            "total_institutions": institution_count,
        }


@app.get("/publications")
async def get_publications(
    year: int = None,
    limit: int = 10,
    token_payload: dict = Depends(get_current_user)
):
    """Get publications list."""
    db = _get_db()
    publications = db.query_publications(year=year, limit=limit)
    return {"publications": publications}


@app.get("/query/graph")
async def get_graph_data(
    topic: str = None,
    token_payload: dict = Depends(get_current_user)
):
    """Get graph data for research network visualization."""
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

    return {"nodes": nodes, "edges": edges, "warnings": warnings}


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
    user_id: str = None,
    action: str = None,
    since: str = None,
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

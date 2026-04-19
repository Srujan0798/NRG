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
import sys
import logging
from datetime import UTC, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.auth.jwt_handler import JWTHandler, AuthError
from src.auth.middleware import (
    AuthContextMiddleware,
    filter_researcher_records,
    get_current_user,
)
from src.data.database import NRGDatabase
from src.orchestration.graph import NRGWorkflow
from src.security.gateway.prompt_sanitiser import prompt_sanitiser
from src.audit import log_query as audit_log_query
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

@app.get("/researchers")
async def get_researchers(
    state: str = None,
    research_area: str = None,
    token_payload: dict = Depends(get_current_user)
):
    """Protected endpoint with role-specific data shaping."""
    db = NRGDatabase("nrg_research.db")
    researchers = db.query_researchers(state=state, research_area=research_area)
    return filter_researcher_records(researchers, token_payload)


@app.get("/stats")
async def get_stats(token_payload: dict = Depends(get_current_user)):
    """Get system statistics for dashboards."""
    from src.data.database import sqlite3

    db_path = "nrg_research.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get counts
    cursor = conn.execute("SELECT COUNT(*) FROM researchers")
    researcher_count = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM publications")
    publication_count = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM institutions")
    institution_count = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM labs")
    lab_count = cursor.fetchone()[0]

    # Get research area distribution
    cursor = conn.execute(
        "SELECT research_area, COUNT(*) as count FROM researchers WHERE research_area IS NOT NULL GROUP BY research_area ORDER BY count DESC LIMIT 10"
    )
    research_areas = [{"area": row[0], "count": row[1]} for row in cursor.fetchall()]

    # Get state distribution
    cursor = conn.execute(
        "SELECT state, COUNT(*) as count FROM researchers GROUP BY state ORDER BY count DESC LIMIT 10"
    )
    states = [{"state": row[0], "count": row[1]} for row in cursor.fetchall()]

    conn.close()

    tier = token_payload.get("tier", 1)
    role = token_payload.get("role", "researcher")

    # Return tier-appropriate data
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
    else:  # researcher
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
    from src.data.database import sqlite3

    db_path = "nrg_research.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM publications WHERE 1=1"
    params = []

    if year:
        query += " AND year = ?"
        params.append(year)

    query += " ORDER BY year DESC LIMIT ?"
    params.append(limit)

    cursor = conn.execute(query, params)
    publications = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {"publications": publications}


@app.get("/query/graph")
async def get_graph_data(
    topic: str = None,
    token_payload: dict = Depends(get_current_user)
):
    """Get graph data for research network visualization."""
    from src.data.database import sqlite3

    db_path = "nrg_research.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    nodes = []
    edges = []
    node_id_map = {}
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

    # Get researchers with their publications
    cursor = conn.execute("""
        SELECT DISTINCT r.researcher_id, r.name, r.research_area, r.state,
                        p.publication_id, p.title, p.year
        FROM researchers r
        LEFT JOIN researcher_publications rp ON r.researcher_id = rp.researcher_id
        LEFT JOIN publications p ON rp.publication_id = p.publication_id
        WHERE r.research_area IS NOT NULL
        LIMIT 50
    """)

    researchers = {}
    publications = {}

    for row in cursor.fetchall():
        researcher_id = row['researcher_id']
        if researcher_id not in researchers:
            rid = add_node(row['name'], 'author',
                          area=row['research_area'], state=row['state'])
            researchers[researcher_id] = rid

        if row['publication_id']:
            pub_id = row['publication_id']
            if pub_id not in publications:
                pid = add_node(row['title'][:50], 'paper', year=row['year'])
                publications[pub_id] = pid

            # Add edge: author -> paper
            edges.append({
                "source": researchers[researcher_id],
                "target": publications[pub_id],
                "type": "authored",
                "weight": 1
            })

    # Get institutions
    cursor = conn.execute("""
        SELECT institution_id, name, state FROM institutions LIMIT 20
    """)
    institutions = {}
    for row in cursor.fetchall():
        iid = add_node(row['name'], 'institution', state=row['state'])
        institutions[row['institution_id']] = iid

    # Link researchers to institutions (random for demo)
    cursor = conn.execute("SELECT researcher_id, institution_id FROM researchers LIMIT 50")
    for row in cursor.fetchall():
        if row['researcher_id'] in researchers and row['institution_id'] in institutions:
            edges.append({
                "source": researchers[row['researcher_id']],
                "target": institutions[row['institution_id']],
                "type": "affiliated",
                "weight": 1
            })

    conn.close()

    return {"nodes": nodes, "edges": edges}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

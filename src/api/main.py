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
workflow = NRGWorkflow()
jwt_handler = JWTHandler()

app = FastAPI(
    title="National Research Graph API",
    version="1.0.0",
    description="Sovereign AI platform for Indian research intelligence",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

        # Pass tier to workflow
        user_tier = token_payload.get("tier", 1)
        user_id = token_payload.get("sub", "anonymous")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

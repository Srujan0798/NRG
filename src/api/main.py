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
        # Pass tier to workflow
        user_tier = token_payload.get("tier", 1)
        result = workflow.run(
            request.query,
            user_tier=user_tier,
            session_id=request.session_id,
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
async def get_researchers(token_payload: dict = Depends(get_current_user)):
    """Protected endpoint with role-specific data shaping."""
    db = NRGDatabase("nrg_research.db")
    researchers = db.query_researchers()
    return filter_researcher_records(researchers, token_payload)

if __name__ == "__main__":
    import uvicorn
    # Change port to 8001 as Kong is on 8000
    uvicorn.run(app, host="0.0.0.0", port=8001)

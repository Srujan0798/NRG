"""FastAPI authentication middleware and RBAC helpers."""

from __future__ import annotations

from collections import Counter
from typing import Callable

from fastapi import Depends, Header, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.auth.jwt_handler import AuthError, JWTHandler


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Attach decoded auth claims to request state when a bearer token is present."""

    def __init__(self, app, jwt_handler: JWTHandler):
        super().__init__(app)
        self.jwt_handler = jwt_handler

    async def dispatch(self, request: Request, call_next):
        request.state.auth_claims = None
        authorization = request.headers.get("Authorization")

        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "", 1)
            try:
                request.state.auth_claims = self.jwt_handler.verify_access_token(token)
            except AuthError:
                request.state.auth_claims = None

        return await call_next(request)


def get_current_user(request: Request, authorization: str = Header(default=None)) -> dict:
    claims = getattr(request.state, "auth_claims", None)
    if claims:
        return claims

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_roles(*roles: str) -> Callable[[dict], dict]:
    def dependency(claims: dict = Depends(get_current_user)) -> dict:
        if claims.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions",
            )
        return claims

    return dependency


def filter_researcher_records(records: list[dict], claims: dict) -> dict:
    role = claims["role"]

    if role == "researcher":
        own_researcher_id = claims.get("researcher_id")
        return {
            "role": role,
            "results": [
                _full_researcher_record(record)
                if record.get("researcher_id") == own_researcher_id
                else _public_researcher_record(record)
                for record in records
            ],
        }

    if role == "government":
        state_counts = Counter(record.get("state", "unknown") for record in records)
        area_counts = Counter(
            record.get("research_area", "unknown") for record in records if record.get("research_area")
        )
        return {
            "role": role,
            "results": {
                "total_researchers": len(records),
                "state_distribution": dict(state_counts),
                "research_area_distribution": dict(area_counts),
                "sample_records": [_government_record(record) for record in records[:5]],
            },
        }

    if role == "industry":
        return {
            "role": role,
            "results": [_licensed_researcher_record(record) for record in records],
        }

    raise HTTPException(status_code=403, detail="Unsupported role")


def _full_researcher_record(record: dict) -> dict:
    return dict(record)


def _public_researcher_record(record: dict) -> dict:
    return {
        "researcher_id": record.get("researcher_id"),
        "name": record.get("name"),
        "institution_id": record.get("institution_id"),
        "state": record.get("state"),
        "research_area": record.get("research_area"),
        "year_joined": record.get("year_joined"),
        "email": None,
        "phone": None,
        "orcid": None,
    }


def _government_record(record: dict) -> dict:
    return {
        "institution_id": record.get("institution_id"),
        "state": record.get("state"),
        "research_area": record.get("research_area"),
        "year_joined": record.get("year_joined"),
    }


def _licensed_researcher_record(record: dict) -> dict:
    return {
        "researcher_id": record.get("researcher_id"),
        "name": record.get("name"),
        "institution_id": record.get("institution_id"),
        "state": record.get("state"),
        "research_area": record.get("research_area"),
        "year_joined": record.get("year_joined"),
        "licensed": True,
    }

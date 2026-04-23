"""FastAPI authentication middleware and RBAC helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from fastapi import Depends, Header, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.auth.jwt_handler import AuthError, JWTHandler


TIER_COLUMN_VISIBILITY = {
    2: ["researcher_id", "name", "institution_id", "department", "state",
        "research_area", "secondary_research_areas", "years_experience",
        "year_joined", "h_index", "orcid", "email", "phone"],
    3: ["researcher_id", "name", "institution_id", "state",
        "research_area", "years_experience", "h_index"],
}

SENSITIVE_COLUMNS = {"email", "phone", "aadhaar_number", "pan_number", "date_of_birth"}


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Attach decoded auth claims to request state when a bearer token is present."""

    def __init__(self, app, jwt_handler: JWTHandler):
        super().__init__(app)
        self.jwt_handler = jwt_handler

    async def dispatch(self, request: Request, call_next):
        request.state.auth_claims = None
        authorization = request.headers.get("Authorization")
        client_ip = request.client.host if request.client else None

        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "", 1)
            try:
                request.state.auth_claims = self.jwt_handler.verify_access_token(token, client_ip=client_ip)
            except AuthError:
                request.state.auth_claims = None

        return await call_next(request)


def get_current_user(request: Request, authorization: str = Header(default=None)) -> dict:
    claims: dict[str, Any] = getattr(request.state, "auth_claims", None) or {}
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


def get_user_tier(claims: dict) -> int:
    """Extract tier from JWT claims, defaulting to most restrictive (tier 1)."""
    tier = claims.get("tier")
    if isinstance(tier, int) and tier in (1, 2, 3):
        return tier
    return 1


def _filter_columns_by_tier(record: dict, allowed_columns: list[str]) -> dict:
    """Filter record to only include allowed columns, redacting sensitive ones."""
    filtered = {}
    for col in allowed_columns:
        if col in record:
            filtered[col] = record[col]
    for sensitive in SENSITIVE_COLUMNS:
        if sensitive in record and sensitive not in allowed_columns:
            filtered[sensitive] = None
    return filtered


def filter_researcher_records(records: list[dict], claims: dict) -> dict:
    role = claims["role"]
    tier = get_user_tier(claims)
    tier_columns = TIER_COLUMN_VISIBILITY.get(tier, [])

    if role == "researcher":
        own_researcher_id = claims.get("researcher_id")
        results = []
        for record in records:
            if record.get("researcher_id") == own_researcher_id:
                results.append(_full_researcher_record(record, tier_columns))
            else:
                results.append(_public_researcher_record(record))
        return {"role": role, "tier": tier, "results": results}

    if role == "government":
        state_counts = Counter(record.get("state", "unknown") for record in records)
        area_counts = Counter(
            record.get("research_area", "unknown") for record in records if record.get("research_area")
        )
        return {
            "role": role,
            "tier": tier,
            "results": {
                "total_researchers": len(records),
                "state_distribution": dict(state_counts),
                "research_area_distribution": dict(area_counts),
                "sample_records": [_government_record(record, tier_columns) for record in records[:5]],
            },
        }

    if role == "industry":
        return {
            "role": role,
            "tier": tier,
            "results": [_licensed_researcher_record(record, tier_columns) for record in records],
        }

    raise HTTPException(status_code=403, detail="Unsupported role")


def _full_researcher_record(record: dict, tier_columns: list[str]) -> dict:
    if tier_columns:
        return _filter_columns_by_tier(record, tier_columns)
    return dict(record)


def _public_researcher_record(record: dict) -> dict:
    return {
        "researcher_id": record.get("researcher_id"),
        "name": record.get("name"),
        "institution_id": record.get("institution_id"),
        "department": record.get("department"),
        "state": record.get("state"),
        "research_area": record.get("research_area"),
        "secondary_research_areas": record.get("secondary_research_areas"),
        "years_experience": record.get("years_experience"),
        "year_joined": record.get("year_joined"),
        "h_index": record.get("h_index"),
        "email": None,
        "phone": None,
        "orcid": None,
    }


def _government_record(record: dict, tier_columns: list[str]) -> dict:
    base = {
        "institution_id": record.get("institution_id"),
        "state": record.get("state"),
        "research_area": record.get("research_area"),
        "department": record.get("department"),
        "years_experience": record.get("years_experience"),
        "year_joined": record.get("year_joined"),
        "h_index": record.get("h_index"),
    }
    if tier_columns:
        return _filter_columns_by_tier(base, tier_columns)
    return base


def _licensed_researcher_record(record: dict, tier_columns: list[str]) -> dict:
    base = {
        "researcher_id": record.get("researcher_id"),
        "name": record.get("name"),
        "institution_id": record.get("institution_id"),
        "department": record.get("department"),
        "state": record.get("state"),
        "research_area": record.get("research_area"),
        "years_experience": record.get("years_experience"),
        "year_joined": record.get("year_joined"),
        "h_index": record.get("h_index"),
        "licensed": True,
    }
    if tier_columns:
        result = _filter_columns_by_tier(base, tier_columns)
        result["licensed"] = True
        return result
    return base

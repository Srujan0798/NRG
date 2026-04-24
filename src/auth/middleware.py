"""FastAPI authentication middleware and RBAC helpers — policy-driven."""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from fastapi import Depends, Header, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.auth.jwt_handler import AuthError, JWTHandler
from src.auth.rbac import RBACPolicyEngine, get_policy_engine


def get_user_tier(claims: dict) -> int:
    """Extract tier from JWT claims, defaulting to most restrictive (tier 1)."""
    engine = get_policy_engine()
    policy = engine.resolve_tier_or_persona(claims)
    return policy.tier


def get_user_policy(claims: dict) -> Any:
    """Resolve the full RBACPolicy for the current user from JWT claims."""
    engine = get_policy_engine()
    return engine.resolve_tier_or_persona(claims)


def filter_researcher_records(records: list[dict], claims: dict) -> dict:
    """
    Filter researcher records according to the user's RBAC policy.

    Replaces hardcoded role/tier if/elif chains with policy-driven column
    visibility and PII masking.
    """
    engine = get_policy_engine()
    policy = engine.resolve_tier_or_persona(claims)

    if policy.output_format == "anonymized":
        return _anonymized_researcher_output(records, claims, policy)
    elif policy.output_format == "aggregated":
        return _aggregated_researcher_output(records, policy)
    else:
        return _full_researcher_output(records, claims, policy, engine)


def _full_researcher_output(
    records: list[dict],
    claims: dict,
    policy: Any,
    engine: RBACPolicyEngine,
) -> dict:
    """Tier 1 / full output — show own records fully, others with PII masked."""
    own_researcher_id = claims.get("researcher_id")
    results = []

    for record in records:
        if record.get("researcher_id") == own_researcher_id:
            filtered = engine.filter_row_by_policy(policy, "researchers", dict(record))
        else:
            filtered = _public_researcher_record(record)
        results.append(filtered)

    return {
        "role": claims.get("role"),
        "persona": policy.name,
        "tier": policy.tier,
        "results": results,
        "scope": policy.data_scope,
    }


def _aggregated_researcher_output(records: list[dict], policy: Any) -> dict:
    """Tier 2 / government — aggregated stats + sample records with masked PII."""
    state_counts = Counter(r.get("state", "unknown") for r in records)
    area_counts = Counter(
        r.get("research_area", "unknown") for r in records if r.get("research_area")
    )

    sample_records = []
    for record in records[:5]:
        masked = _mask_all_pii(record)
        sample_records.append({
            k: v for k, v in masked.items()
            if k in ("institution_id", "state", "research_area", "department",
                     "years_experience", "year_joined", "h_index")
        })

    return {
        "role": "government",
        "persona": policy.name,
        "tier": policy.tier,
        "scope": policy.data_scope,
        "results": {
            "total_researchers": len(records),
            "state_distribution": dict(state_counts),
            "research_area_distribution": dict(area_counts),
            "sample_records": sample_records,
        },
    }


def _anonymized_researcher_output(records: list[dict], claims: dict, policy: Any) -> dict:
    """Tier 3 / industry — anonymized summaries, no individual records."""
    if not records:
        return {
            "role": claims.get("role"),
            "persona": policy.name,
            "tier": policy.tier,
            "scope": policy.data_scope,
            "results": {"total_count": 0},
        }

    state_counts = Counter(r.get("state", "unknown") for r in records if r.get("state"))
    area_counts = Counter(
        r.get("research_area", "unknown") for r in records if r.get("research_area")
    )

    return {
        "role": claims.get("role"),
        "persona": policy.name,
        "tier": policy.tier,
        "scope": policy.data_scope,
        "results": {
            "total_researchers": len(records),
            "state_distribution": dict(state_counts),
            "research_area_distribution": dict(area_counts),
            "note": "Individual records anonymized per policy",
        },
    }


def _public_researcher_record(record: dict) -> dict:
    """Public researcher record — no PII."""
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


def _mask_all_pii(record: dict) -> dict:
    """Apply full PII mask to a record."""
    masked = dict(record)
    for key in list(masked.keys()):
        if any(
            k in key.lower()
            for k in ("email", "phone", "aadhaar", "pan", "dob", "date_of_birth",
                      "address", "orcid")
        ):
            masked[key] = None
    return masked


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Attach decoded auth claims + resolved RBAC policy to request state."""

    def __init__(self, app, jwt_handler: JWTHandler):
        super().__init__(app)
        self.jwt_handler = jwt_handler
        self._engine = get_policy_engine()

    async def dispatch(self, request: Request, call_next):
        request.state.auth_claims = None
        request.state.rbac_policy = None
        request.state.request_fingerprint = None
        authorization = request.headers.get("Authorization")
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")

        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "", 1)
            try:
                claims = self.jwt_handler.verify_access_token(token, client_ip=client_ip)
                request.state.auth_claims = claims
                request.state.rbac_policy = self._engine.resolve_tier_or_persona(claims)
                from src.audit.per_user_keys import build_request_fingerprint
                fp = build_request_fingerprint(client_ip=client_ip, user_agent=user_agent)
                request.state.request_fingerprint = fp
            except AuthError:
                request.state.auth_claims = None
                request.state.rbac_policy = None

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


def require_policy_access(
    endpoint_pattern: str | None = None,
    table: str | None = None,
) -> Callable[[dict], dict]:
    """
    Dependency that enforces RBAC policy endpoint/table access.

    Usage:
        @router.get("/data/{table}")
        def get_table(
            table: str,
            claims: dict = Depends(require_policy_access(table="{table}"))
        ):
            ...
    """

    def dependency(claims: dict = Depends(get_current_user)) -> dict:
        engine = get_policy_engine()
        policy = engine.resolve_tier_or_persona(claims)

        if endpoint_pattern and not engine.is_endpoint_allowed(policy, endpoint_pattern):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Endpoint '{endpoint_pattern}' not allowed for persona '{policy.name}'",
            )

        if table and not engine.is_table_allowed(policy, table):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Table '{table}' not allowed for persona '{policy.name}'",
            )

        return claims

    return dependency

"""Structured data endpoints for researchers, stats, publications, and related tables."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Optional, cast

from fastapi import APIRouter, Depends

from src.auth.middleware import TokenClaims, filter_researcher_records, get_current_user

router = APIRouter(tags=["data"])

JSONDict = dict[str, Any]
JSONRows = list[JSONDict]

_get_db: Callable[[], Any] | None = None
_api_cache: Any | None = None
_tier_response_filter: Callable[..., Any] | None = None
_query_result_cache_ttl_seconds = 300


def configure_data_router(
    *,
    db_getter: Callable[[], Any],
    api_cache: Any,
    tier_response_filter: Callable[..., Any],
    query_result_cache_ttl_seconds: int,
) -> None:
    """Bind data routes to app-level DB/cache/tier-filter implementations."""
    global _get_db, _api_cache, _tier_response_filter, _query_result_cache_ttl_seconds
    _get_db = db_getter
    _api_cache = api_cache
    _tier_response_filter = tier_response_filter
    _query_result_cache_ttl_seconds = query_result_cache_ttl_seconds


def _db() -> Any:
    if _get_db is None:
        raise RuntimeError("Data router is not configured with a DB getter")
    return _get_db()


def _cache() -> Any:
    if _api_cache is None:
        raise RuntimeError("Data router is not configured with an API cache")
    return _api_cache


def _apply_tier_response_filter(payload: Any, tier: int, **kwargs: Any) -> Any:
    if _tier_response_filter is None:
        raise RuntimeError("Data router is not configured with a tier response filter")
    return _tier_response_filter(payload, tier, **kwargs)


def _bucket_stats_for_tier3(stats: JSONDict) -> JSONDict:
    """Convert exact counts to anonymized bucketed ranges for Tier 3."""

    def bucket(count: int) -> str:
        if count == 0:
            return "0"
        if count <= 100:
            return "1-100"
        if count <= 500:
            return "101-500"
        if count <= 1000:
            return "501-1K"
        if count <= 5000:
            return "1K-5K"
        if count <= 10000:
            return "5K-10K"
        return "10K+"

    bucketed: JSONDict = {}
    for key, value in stats.items():
        if key == "research_areas":
            continue
        if isinstance(value, int):
            bucketed[key] = bucket(value)
        else:
            bucketed[key] = value
    return bucketed


@router.get("/researchers")
async def get_researchers(
    state: Optional[str] = None,
    research_area: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: TokenClaims = Depends(get_current_user),
) -> Any:
    """Protected endpoint with role-specific data shaping and pagination."""
    safe_limit = max(1, min(limit, 500))
    safe_offset = max(0, offset)
    cache_key = (
        f"researchers:{state}:{research_area}:{safe_limit}:{safe_offset}:"
        f"{token_payload.get('role','')}:tier:{token_payload.get('tier', 1)}:"
        f"user:{token_payload.get('sub','')}"
    )
    cached = _cache().get(cache_key)
    if cached is not None:
        return cached

    researchers = cast(
        list[TokenClaims],
        _db().query_researchers(
            state=state,
            research_area=research_area,
            limit=safe_limit,
            offset=safe_offset,
        ),
    )
    result = filter_researcher_records(researchers, token_payload)
    _cache().set(cache_key, result, ttl=15)
    return result


@router.get("/stats")
async def get_stats(token_payload: TokenClaims = Depends(get_current_user)) -> Any:
    """Get system statistics for dashboards."""
    cache_key = f"stats:{token_payload.get('role','')}:tier:{token_payload.get('tier', 1)}"
    tier = token_payload.get("tier", 1)
    cached = _cache().get(cache_key)
    if cached is not None:
        return _apply_tier_response_filter(
            cached,
            tier,
            user_id=token_payload.get("sub"),
            jwt_kid=token_payload.get("kid"),
            endpoint="/stats",
        )

    stats = cast(JSONDict, _db().get_stats())
    researcher_count = stats.get("researchers", 0)
    publication_count = stats.get("publications", 0)
    institution_count = stats.get("institutions", 0)
    lab_count = stats.get("labs", 0)
    research_areas = stats.get("research_areas", [])
    funding_total = stats.get("funding_records", 0)
    role = token_payload.get("role", "researcher")

    if role == "industry":
        result = {
            "total_researchers": researcher_count,
            "total_publications": publication_count,
            "research_areas": [ra["area"] for ra in cast(JSONRows, research_areas)[:5]],
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

    result = _apply_tier_response_filter(
        result,
        tier,
        user_id=token_payload.get("sub"),
        jwt_kid=token_payload.get("kid"),
        endpoint="/stats",
    )
    _cache().set(cache_key, result, ttl=_query_result_cache_ttl_seconds)
    return result


@router.get("/publications")
async def get_publications(
    year: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    token_payload: TokenClaims = Depends(get_current_user),
) -> Any:
    """Get publications list with pagination and tier-filtered columns."""
    cache_key = f"publications:{year}:{limit}:{offset}:{token_payload.get('role','')}:tier:{token_payload.get('tier', 1)}"
    tier = token_payload.get("tier", 1)
    cached = _cache().get(cache_key)
    if cached is not None:
        return _apply_tier_response_filter(
            cached,
            tier,
            user_id=token_payload.get("sub"),
            jwt_kid=token_payload.get("kid"),
            endpoint="/publications",
        )

    publications = cast(JSONRows, _db().query_publications(year=year, limit=limit, offset=offset))
    if tier >= 2:
        from src.auth.rbac import get_policy_engine

        engine = get_policy_engine()
        policy = engine.get_policy(tier=tier)
        filtered = [engine.filter_row_by_policy(policy, "publications", pub) for pub in publications]
        result = {"publications": filtered, "count": len(filtered), "tier": tier}
    else:
        result = {"publications": publications, "count": len(publications), "tier": tier}

    result = _apply_tier_response_filter(
        result,
        tier,
        user_id=token_payload.get("sub"),
        jwt_kid=token_payload.get("kid"),
        endpoint="/publications",
    )
    _cache().set(cache_key, result, ttl=20)
    return result


@router.get("/projects")
async def get_projects(
    status: Optional[str] = None,
    research_area: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: TokenClaims = Depends(get_current_user),
) -> Any:
    """Get projects with pagination and filtering."""
    cache_key = f"projects:{status}:{research_area}:{limit}:{offset}"
    cached = _cache().get(cache_key)
    if cached is not None:
        return cached

    projects = cast(JSONRows, _db().query_projects(status=status, research_area=research_area, limit=limit, offset=offset))
    result = {"projects": projects, "count": len(projects)}
    _cache().set(cache_key, result, ttl=20)
    return result


@router.get("/patents")
async def get_patents(
    status: Optional[str] = None,
    research_area: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: TokenClaims = Depends(get_current_user),
) -> Any:
    """Get patents with pagination and filtering."""
    cache_key = f"patents:{status}:{research_area}:{limit}:{offset}"
    cached = _cache().get(cache_key)
    if cached is not None:
        return cached

    patents = cast(JSONRows, _db().query_patents(status=status, research_area=research_area, limit=limit, offset=offset))
    result = {"patents": patents, "count": len(patents)}
    _cache().set(cache_key, result, ttl=20)
    return result


@router.get("/collaborations")
async def get_collaborations(
    partner_country: Optional[str] = None,
    collaboration_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: TokenClaims = Depends(get_current_user),
) -> Any:
    """Get collaborations with pagination and filtering."""
    cache_key = f"collaborations:{partner_country}:{collaboration_type}:{limit}:{offset}"
    cached = _cache().get(cache_key)
    if cached is not None:
        return cached

    collaborations = cast(
        JSONRows,
        _db().query_collaborations(
            partner_country=partner_country,
            collaboration_type=collaboration_type,
            limit=limit,
            offset=offset,
        ),
    )
    result = {"collaborations": collaborations, "count": len(collaborations)}
    _cache().set(cache_key, result, ttl=20)
    return result


@router.get("/funding")
async def get_funding(
    agency: Optional[str] = None,
    fiscal_year: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: TokenClaims = Depends(get_current_user),
) -> Any:
    """Get funding records with pagination and filtering."""
    cache_key = f"funding:{agency}:{fiscal_year}:{limit}:{offset}"
    cached = _cache().get(cache_key)
    if cached is not None:
        return cached

    funding = cast(JSONRows, _db().query_funding_records(agency=agency, fiscal_year=fiscal_year, limit=limit, offset=offset))
    result = {"funding_records": funding, "count": len(funding)}
    _cache().set(cache_key, result, ttl=20)
    return result


@router.get("/labs")
async def get_labs(
    state: Optional[str] = None,
    research_area: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: TokenClaims = Depends(get_current_user),
) -> Any:
    """Get labs with pagination and filtering."""
    cache_key = f"labs:{state}:{research_area}:{limit}:{offset}"
    cached = _cache().get(cache_key)
    if cached is not None:
        return cached

    labs = cast(JSONRows, _db().query_labs(state=state, research_area=research_area, limit=limit, offset=offset))
    result = {"labs": labs, "count": len(labs)}
    _cache().set(cache_key, result, ttl=20)
    return result


@router.get("/research-documents")
async def get_research_documents(
    year: Optional[int] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: TokenClaims = Depends(get_current_user),
) -> Any:
    """Get research documents with pagination and filtering."""
    cache_key = f"research_documents:{year}:{category}:{limit}:{offset}"
    cached = _cache().get(cache_key)
    if cached is not None:
        return cached

    docs = cast(JSONRows, _db().query_research_documents(year=year, category=category, limit=limit, offset=offset))
    result = {"research_documents": docs, "count": len(docs)}
    _cache().set(cache_key, result, ttl=20)
    return result

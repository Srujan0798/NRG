"""Data routes: /researchers, /publications, /stats, /projects, /patents, /collaborations, /funding, /labs, /research-documents."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from src.api.deps import get_current_user, get_db, get_api_cache, _apply_tier_response_filter, QUERY_RESULT_CACHE_TTL_SECONDS


router = APIRouter(tags=["data"])


def _bucket_stats_for_tier3(stats: dict) -> dict:
    def bucket(count: int) -> str:
        if count == 0: return "0"
        elif count <= 100: return "1-100"
        elif count <= 500: return "101-500"
        elif count <= 1000: return "501-1K"
        elif count <= 5000: return "1K-5K"
        elif count <= 10000: return "5K-10K"
        else: return "10K+"
    return {
        k: (bucket(v) if isinstance(v, int) and k != "research_areas" else v)
        for k, v in stats.items()
    }


@router.get("/researchers")
async def get_researchers(
    state: Optional[str] = None,
    research_area: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_payload: dict = Depends(get_current_user),
):
    safe_limit = max(1, min(limit, 500))
    safe_offset = max(0, offset)
    cache_key = f"researchers:{state}:{research_area}:{safe_limit}:{safe_offset}:{token_payload.get('role','')}"
    api_cache = get_api_cache()
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached
    db = get_db()
    researchers = db.query_researchers(state=state, research_area=research_area, limit=safe_limit, offset=safe_offset)
    from src.auth.middleware import filter_researcher_records
    result = filter_researcher_records(researchers, token_payload)
    api_cache.set(cache_key, result, ttl=15)
    return result


@router.get("/publications")
async def get_publications(
    year: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    token_payload: dict = Depends(get_current_user),
):
    cache_key = f"publications:{year}:{limit}:{offset}:{token_payload.get('role','')}:tier:{token_payload.get('tier', 1)}"
    api_cache = get_api_cache()
    cached = api_cache.get(cache_key)
    tier = token_payload.get("tier", 1)
    if cached is not None:
        return _apply_tier_response_filter(cached, tier,
            user_id=token_payload.get("sub"), jwt_kid=token_payload.get("kid"), endpoint="/publications")
    db = get_db()
    publications = db.query_publications(year=year, limit=limit, offset=offset)
    if tier >= 2:
        from src.auth.rbac import get_policy_engine
        engine = get_policy_engine()
        policy = engine.get_policy(tier=tier)
        filtered = [engine.filter_row_by_policy(policy, "publications", pub) for pub in publications]
        result = {"publications": filtered, "count": len(filtered), "tier": tier}
    else:
        result = {"publications": publications, "count": len(publications), "tier": tier}
    result = _apply_tier_response_filter(result, tier,
        user_id=token_payload.get("sub"), jwt_kid=token_payload.get("kid"), endpoint="/publications")
    api_cache.set(cache_key, result, ttl=20)
    return result


@router.get("/stats")
async def get_stats(token_payload: dict = Depends(get_current_user)):
    cache_key = f"stats:{token_payload.get('role','')}:tier:{token_payload.get('tier', 1)}"
    api_cache = get_api_cache()
    cached = api_cache.get(cache_key)
    tier = token_payload.get("tier", 1)
    if cached is not None:
        return _apply_tier_response_filter(cached, tier,
            user_id=token_payload.get("sub"), jwt_kid=token_payload.get("kid"), endpoint="/stats")
    db = get_db()
    stats = db.get_stats()
    role = token_payload.get("role", "researcher")
    if role == "industry":
        result = {
            "total_researchers": stats.get("researchers", 0),
            "total_publications": stats.get("publications", 0),
            "research_areas": [ra["area"] for ra in stats.get("research_areas", [])[:5]],
        }
    elif tier >= 2:
        result = {
            "total_researchers": stats.get("researchers", 0),
            "total_publications": stats.get("publications", 0),
            "total_institutions": stats.get("institutions", 0),
            "total_labs": stats.get("labs", 0),
            "total_funding_amount": stats.get("funding_records", 0),
            "research_area_distribution": stats.get("research_areas", [])[:10],
            "state_distribution": stats.get("state_distribution", [])[:10],
        }
    else:
        result = {
            "total_researchers": stats.get("researchers", 0),
            "total_publications": stats.get("publications", 0),
            "total_institutions": stats.get("institutions", 0),
        }
    if tier == 3:
        result = _bucket_stats_for_tier3(result)
    result = _apply_tier_response_filter(result, tier,
        user_id=token_payload.get("sub"), jwt_kid=token_payload.get("kid"), endpoint="/stats")
    api_cache.set(cache_key, result, ttl=QUERY_RESULT_CACHE_TTL_SECONDS)
    return result


@router.get("/projects")
async def get_projects(
    status: Optional[str] = None, research_area: Optional[str] = None,
    limit: int = 50, offset: int = 0,
    token_payload: dict = Depends(get_current_user),
):
    cache_key = f"projects:{status}:{research_area}:{limit}:{offset}"
    api_cache = get_api_cache()
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached
    db = get_db()
    projects = db.query_projects(status=status, research_area=research_area, limit=limit, offset=offset)
    result = {"projects": projects, "count": len(projects)}
    api_cache.set(cache_key, result, ttl=20)
    return result


@router.get("/patents")
async def get_patents(
    status: Optional[str] = None, research_area: Optional[str] = None,
    limit: int = 50, offset: int = 0,
    token_payload: dict = Depends(get_current_user),
):
    cache_key = f"patents:{status}:{research_area}:{limit}:{offset}"
    api_cache = get_api_cache()
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached
    db = get_db()
    patents = db.query_patents(status=status, research_area=research_area, limit=limit, offset=offset)
    result = {"patents": patents, "count": len(patents)}
    api_cache.set(cache_key, result, ttl=20)
    return result


@router.get("/collaborations")
async def get_collaborations(
    partner_country: Optional[str] = None, collaboration_type: Optional[str] = None,
    limit: int = 50, offset: int = 0,
    token_payload: dict = Depends(get_current_user),
):
    cache_key = f"collaborations:{partner_country}:{collaboration_type}:{limit}:{offset}"
    api_cache = get_api_cache()
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached
    db = get_db()
    collaborations = db.query_collaborations(partner_country=partner_country, collaboration_type=collaboration_type, limit=limit, offset=offset)
    result = {"collaborations": collaborations, "count": len(collaborations)}
    api_cache.set(cache_key, result, ttl=20)
    return result


@router.get("/funding")
async def get_funding(
    agency: Optional[str] = None, fiscal_year: Optional[str] = None,
    limit: int = 50, offset: int = 0,
    token_payload: dict = Depends(get_current_user),
):
    cache_key = f"funding:{agency}:{fiscal_year}:{limit}:{offset}"
    api_cache = get_api_cache()
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached
    db = get_db()
    funding = db.query_funding_records(agency=agency, fiscal_year=fiscal_year, limit=limit, offset=offset)
    result = {"funding_records": funding, "count": len(funding)}
    api_cache.set(cache_key, result, ttl=20)
    return result


@router.get("/labs")
async def get_labs(
    state: Optional[str] = None, research_area: Optional[str] = None,
    limit: int = 50, offset: int = 0,
    token_payload: dict = Depends(get_current_user),
):
    cache_key = f"labs:{state}:{research_area}:{limit}:{offset}"
    api_cache = get_api_cache()
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached
    db = get_db()
    labs = db.query_labs(state=state, research_area=research_area, limit=limit, offset=offset)
    result = {"labs": labs, "count": len(labs)}
    api_cache.set(cache_key, result, ttl=20)
    return result


@router.get("/research-documents")
async def get_research_documents(
    year: Optional[int] = None, category: Optional[str] = None,
    limit: int = 50, offset: int = 0,
    token_payload: dict = Depends(get_current_user),
):
    cache_key = f"research_documents:{year}:{category}:{limit}:{offset}"
    api_cache = get_api_cache()
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached
    db = get_db()
    docs = db.query_research_documents(year=year, category=category, limit=limit, offset=offset)
    result = {"research_documents": docs, "count": len(docs)}
    api_cache.set(cache_key, result, ttl=20)
    return result

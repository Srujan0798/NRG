"""Graph visualization and internal tier-diff endpoints."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.auth.middleware import get_current_user
from src.security.gateway.prompt_sanitiser import prompt_sanitiser
from src.security.rate_limiter import check_tier_rate_limit

router = APIRouter(tags=["graph"])

_get_db: Callable[[], Any] | None = None
_api_cache: Any | None = None
_tier_response_filter: Callable[..., Any] | None = None
_release_seed_graph: Callable[[str | None, int], dict[str, Any]] | None = None
_tier_history_snapshot: Callable[[], dict[str, Any]] | None = None
_query_result_cache_ttl_seconds = 300


class GraphQueryRequest(BaseModel):
    query: str
    depth: int = 2


def configure_graph_router(
    *,
    db_getter: Callable[[], Any],
    api_cache: Any,
    tier_response_filter: Callable[..., Any],
    release_seed_graph: Callable[[str | None, int], dict[str, Any]],
    tier_history_snapshot: Callable[[], dict[str, Any]],
    query_result_cache_ttl_seconds: int,
) -> None:
    """Bind graph routes to app-level DB/cache/filter helpers."""
    global _get_db, _api_cache, _tier_response_filter
    global _release_seed_graph, _tier_history_snapshot, _query_result_cache_ttl_seconds

    _get_db = db_getter
    _api_cache = api_cache
    _tier_response_filter = tier_response_filter
    _release_seed_graph = release_seed_graph
    _tier_history_snapshot = tier_history_snapshot
    _query_result_cache_ttl_seconds = query_result_cache_ttl_seconds


def _db() -> Any:
    if _get_db is None:
        raise RuntimeError("Graph router is not configured with a DB getter")
    return _get_db()


def _cache() -> Any:
    if _api_cache is None:
        raise RuntimeError("Graph router is not configured with an API cache")
    return _api_cache


def _apply_tier_response_filter(payload: Any, tier: int, **kwargs) -> Any:
    if _tier_response_filter is None:
        raise RuntimeError("Graph router is not configured with a tier response filter")
    return _tier_response_filter(payload, tier, **kwargs)


def _release_graph(topic: str | None, tier: int) -> dict[str, Any]:
    if _release_seed_graph is None:
        raise RuntimeError("Graph router is not configured with release seed graph data")
    return _release_seed_graph(topic, tier)


def _tier_snapshot() -> dict[str, Any]:
    if _tier_history_snapshot is None:
        raise RuntimeError("Graph router is not configured with a tier history snapshot")
    return _tier_history_snapshot()


@router.post("/query/graph")
async def post_graph_query(
    request: GraphQueryRequest,
    token_payload: dict = Depends(get_current_user),
    raw_request: Request = None,
):
    """Return a collaboration subgraph via recursive CTE where supported."""
    depth = min(max(request.depth, 1), 3)
    client_ip = raw_request.client.host if raw_request and raw_request.client else None
    user_id = token_payload.get("sub", "anonymous")

    allowed, _remaining, _reset_time, rate_headers = check_tier_rate_limit(
        user_id, token_payload.get("tier", 1), client_ip
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers=rate_headers)

    validation = prompt_sanitiser.validate_query({"query": request.query}, identifier=user_id or client_ip)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=f"Security violation: {validation['reason']}")

    db = _db()
    tier = token_payload.get("tier", 1)
    topic_pattern = f"%{request.query.strip()}%"

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    node_counter = 0
    node_ids: dict[str, str] = {}

    def add_node(label: str, node_type: str, **props) -> str:
        nonlocal node_counter
        node_id = f"{node_type[0]}{node_counter}"
        node_counter += 1
        nodes.append({"id": node_id, "label": label, "type": node_type, **props})
        return node_id

    with db.get_session() as session:
        from sqlalchemy import text as sa_text

        rcte = sa_text("""
            WITH RECURSIVE collab_network AS (
                SELECT
                    r.researcher_id AS start_rid,
                    r.name AS start_name,
                    r.research_area,
                    r.institution_id,
                    0 AS depth,
                    ARRAY[r.researcher_id] AS path
                FROM researchers r
                WHERE LOWER(COALESCE(r.research_area, '') || ' ' || COALESCE(r.name, '')) LIKE :pattern

                UNION ALL

                SELECT
                    next_r.researcher_id,
                    next_r.name,
                    next_r.research_area,
                    next_r.institution_id,
                    cn.depth + 1,
                    cn.path || next_r.researcher_id
                FROM collab_network cn
                JOIN researcher_publications rp1 ON rp1.researcher_id = cn.start_rid
                JOIN researcher_publications rp2 ON rp2.publication_id = rp1.publication_id
                JOIN researchers next_r ON next_r.researcher_id = rp2.researcher_id
                WHERE cn.depth < :max_depth
                  AND next_r.researcher_id != ALL(cn.path)
                  AND NOT (next_r.researcher_id = ANY(cn.path))
            )
            SELECT DISTINCT
                cn.start_rid AS researcher_id,
                cn.start_name AS name,
                cn.research_area,
                cn.institution_id,
                cn.depth,
                i.name AS institution_name,
                i.state AS institution_state
            FROM collab_network cn
            LEFT JOIN institutions i ON i.institution_id = cn.institution_id
            WHERE cn.depth <= :max_depth
            LIMIT 200
        """)

        try:
            result = session.execute(rcte, {"pattern": topic_pattern, "max_depth": depth})
        except Exception:
            rcte_fallback = sa_text("""
                SELECT DISTINCT
                    r.researcher_id,
                    r.name,
                    r.research_area,
                    r.institution_id,
                    0 AS depth,
                    i.name AS institution_name,
                    i.state AS institution_state
                FROM researchers r
                LEFT JOIN institutions i ON i.institution_id = r.institution_id
                WHERE LOWER(COALESCE(r.research_area, '') || ' ' || COALESCE(r.name, '')) LIKE :pattern
                LIMIT 200
            """)
            result = session.execute(rcte_fallback, {"pattern": topic_pattern})

        researcher_ids: set[str] = set()
        institution_ids: set[str] = set()

        for row in result:
            rid = row[0]
            name = row[1]
            area = row[2]
            inst_id = row[3]
            inst_name = row[5]
            inst_state = row[6]

            if rid not in node_ids:
                if tier == 3:
                    label = f"Researcher-{len(node_ids) + 1}"
                else:
                    label = name if name else f"Researcher-{len(node_ids) + 1}"
                node_key = add_node(label, "author", area=area or None)
                node_ids[rid] = node_key
                researcher_ids.add(rid)
                if inst_id:
                    institution_ids.add(inst_id)

            if inst_id and inst_id not in node_ids:
                node_key = add_node(inst_name or "Unknown Institution", "institution", state=inst_state)
                node_ids[inst_id] = node_key
                institution_ids.add(inst_id)

            if rid in node_ids and inst_id in node_ids:
                edges.append({
                    "source": node_ids[rid],
                    "target": node_ids[inst_id],
                    "type": "affiliated",
                    "weight": 1,
                })

        if researcher_ids:
            try:
                from sqlalchemy import bindparam

                collab_stmt = sa_text("""
                    SELECT DISTINCT r1.researcher_id AS rid1, r2.researcher_id AS rid2
                    FROM researcher_publications rp1
                    JOIN researcher_publications rp2 ON rp1.publication_id = rp2.publication_id
                    JOIN researchers r1 ON r1.researcher_id = rp1.researcher_id
                    JOIN researchers r2 ON r2.researcher_id = rp2.researcher_id
                    WHERE r1.researcher_id IN :researcher_ids
                      AND r2.researcher_id IN :researcher_ids
                      AND r1.researcher_id < r2.researcher_id
                    LIMIT 300
                """).bindparams(bindparam("researcher_ids", expanding=True))
                collab_result = session.execute(
                    collab_stmt,
                    {"researcher_ids": list(researcher_ids)},
                )
                for row in collab_result:
                    if row[0] in node_ids and row[1] in node_ids:
                        edges.append({
                            "source": node_ids[row[0]],
                            "target": node_ids[row[1]],
                            "type": "collaborated",
                            "weight": 1,
                        })
            except Exception:
                pass

    result_data: dict[str, Any] = {
        "nodes": nodes,
        "edges": edges,
        "query": request.query,
        "depth": depth,
        "tier": tier,
    }

    if not nodes and not edges:
        result_data["warnings"] = [{
            "message": f"No collaboration network found for '{request.query}'",
            "topic": request.query,
        }]

    return _apply_tier_response_filter(
        result_data,
        tier,
        user_id=token_payload.get("sub"),
        jwt_kid=token_payload.get("kid"),
        request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
        endpoint="/query/graph",
    )


@router.get("/query/graph")
async def get_graph_data(
    topic: Optional[str] = None,
    token_payload: dict = Depends(get_current_user),
):
    """Get graph data for research network visualization."""
    tier = token_payload.get("tier", 1)
    user_id = token_payload.get("sub", "anonymous")
    if topic:
        validation = prompt_sanitiser.validate_query({"query": topic}, identifier=user_id)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=f"Security violation: {validation['reason']}")

    cache_key = f"graph:{topic or 'all'}:tier:{tier}"
    cached = _cache().get(cache_key)
    if cached is not None:
        return _apply_tier_response_filter(
            cached,
            tier,
            user_id=token_payload.get("sub"),
            jwt_kid=token_payload.get("kid"),
            endpoint="/query/graph",
        )

    if topic and any(term in topic.lower() for term in ("hydrogen", "fuel cell", "renewable", "solar")):
        result = _apply_tier_response_filter(
            _release_graph(topic, tier),
            tier,
            user_id=token_payload.get("sub"),
            jwt_kid=token_payload.get("kid"),
            endpoint="/query/graph",
        )
        _cache().set(cache_key, result, ttl=_query_result_cache_ttl_seconds)
        return result

    db = _db()
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    node_counter = 0

    def add_node(label, node_type, **props):
        nonlocal node_counter
        node_id = f"{node_type[0]}{node_counter}"
        node_counter += 1
        nodes.append({"id": node_id, "label": label, "type": node_type, **props})
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
            topic_lower = topic.lower()
            if "hydrogen" in topic_lower or "fuel cell" in topic_lower:
                topic_pattern = "%hydrogen%"
            elif "renewable" in topic_lower:
                topic_pattern = "%renewable%"
            elif "computer science" in topic_lower:
                topic_pattern = "%computer%"
            else:
                topic_pattern = f"%{topic_lower}%"
            graph_query = sa_text("""
                SELECT DISTINCT r.researcher_id, r.name, r.research_area, r.state,
                r.institution_id, p.publication_id, p.title, p.year
                FROM researchers r
                LEFT JOIN researcher_publications rp ON r.researcher_id = rp.researcher_id
                LEFT JOIN publications p ON rp.publication_id = p.publication_id
                WHERE r.research_area IS NOT NULL
                AND (LOWER(r.research_area) LIKE :topic_pattern OR LOWER(p.title) LIKE :topic_pattern)
            """)
            params = {"topic_pattern": topic_pattern}

        graph_query_str = str(graph_query) + " LIMIT 50"
        result = session.execute(sa_text(graph_query_str), params)

        researchers = {}
        researcher_institution_ids = set()
        publications = {}

        for row in result:
            researcher_id = row[0]
            if researcher_id not in researchers:
                rid = add_node(row[1], "author", area=row[2], state=row[3])
                researchers[researcher_id] = rid
                if row[4]:
                    researcher_institution_ids.add(row[4])

            if row[5]:
                pub_id = row[5]
                if pub_id not in publications:
                    pid = add_node(row[6][:50] if row[6] else "", "paper", year=row[7])
                    publications[pub_id] = pid

                edges.append({
                    "source": researchers[researcher_id],
                    "target": publications[pub_id],
                    "type": "authored",
                    "weight": 1,
                })

    warnings = []
    if topic and not researchers:
        warnings.append({
            "message": f"No graph data found for topic '{topic}'",
            "topic": topic,
        })
        return _apply_tier_response_filter(
            {"nodes": [], "edges": [], "warnings": warnings},
            tier,
            user_id=token_payload.get("sub"),
            jwt_kid=token_payload.get("kid"),
            endpoint="/query/graph",
        )

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
            iid = add_node(row[1], "institution", state=row[2])
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
                    "weight": 1,
                })

    result = {"nodes": nodes, "edges": edges, "warnings": warnings}
    result = _apply_tier_response_filter(
        result,
        tier,
        user_id=token_payload.get("sub"),
        jwt_kid=token_payload.get("kid"),
        endpoint="/query/graph",
    )
    _cache().set(cache_key, result, ttl=_query_result_cache_ttl_seconds)
    return result


@router.get("/api/internal/tier_diff")
async def get_internal_tier_diff(
    token_payload: dict = Depends(get_current_user),
    raw_request: Request = None,
):
    """Return recent response-shape differences for Tier 1 operators."""
    tier = token_payload.get("tier", 1)
    if tier != 1:
        raise HTTPException(status_code=403, detail="Tier 1 access required")

    try:
        from src.audit import AuditEvent, get_audit_log

        get_audit_log().append(
            AuditEvent(
                event_type="tier_diff_access",
                user_id=token_payload.get("sub", "system"),
                result={"endpoint": "/api/internal/tier_diff"},
                jwt_kid=token_payload.get("kid"),
                request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Audit binding required") from exc

    return _tier_snapshot()

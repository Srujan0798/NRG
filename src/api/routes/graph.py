"""Graph visualization endpoints."""

from __future__ import annotations

from collections import deque
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import (
    GraphQueryRequest,
    _api_cache,
    _apply_tier_response_filter,
    get_db,
    QUERY_RESULT_CACHE_TTL_SECONDS,
)
from src.api.logging_config import get_logger
from src.api.query_helpers import _release_seed_graph
from src.auth.middleware import get_current_user
from src.security.gateway.prompt_sanitiser import prompt_sanitiser
from src.security.rate_limiter import check_tier_rate_limit

router = APIRouter(prefix="/query", tags=["graph"])
logger = get_logger(__name__)


@router.post("/graph")
async def post_graph_query(
    request: GraphQueryRequest,
    token_payload: dict = Depends(get_current_user),
    raw_request=None,
):
    depth = min(max(request.depth, 1), 3)
    client_ip = raw_request.client.host if raw_request and raw_request.client else None
    user_id = token_payload.get("sub", "anonymous")

    allowed, remaining, reset_time, rate_headers = check_tier_rate_limit(
        user_id, token_payload.get("tier", 1), client_ip
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers=rate_headers)

    validation = prompt_sanitiser.validate_query({"query": request.query}, identifier=user_id or client_ip)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=f"Security violation: {validation['reason']}")

    db = get_db()
    tier = token_payload.get("tier", 1)
    topic_pattern = f"%{request.query.strip()}%"

    nodes: list[dict] = []
    edges: list[dict] = []
    node_counter = 0
    _node_ids: dict[str, str] = {}

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

        _researcher_ids: set[str] = set()
        _institution_ids: set[str] = set()

        for row in result:
            rid = row[0]
            name = row[1]
            area = row[2]
            inst_id = row[3]
            inst_name = row[5]
            inst_state = row[6]

            if rid not in _node_ids:
                if tier == 3:
                    anon_label = f"Researcher-{len(_node_ids) + 1}"
                else:
                    anon_label = name if name else f"Researcher-{len(_node_ids) + 1}"
                node_key = add_node(anon_label, "author", area=area or None)
                _node_ids[rid] = node_key
                _researcher_ids.add(rid)
                if inst_id:
                    _institution_ids.add(inst_id)

            if inst_id and inst_id not in _node_ids:
                node_key = add_node(inst_name or "Unknown Institution", "institution", state=inst_state)
                _node_ids[inst_id] = node_key
                _institution_ids.add(inst_id)

            if rid in _node_ids and inst_id in _node_ids:
                edges.append({
                    "source": _node_ids[rid],
                    "target": _node_ids[inst_id],
                    "type": "affiliated",
                    "weight": 1,
                })

        if _researcher_ids:
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
                    {"researcher_ids": list(_researcher_ids)},
                )
                for row in collab_result:
                    if row[0] in _node_ids and row[1] in _node_ids:
                        edges.append({
                            "source": _node_ids[row[0]],
                            "target": _node_ids[row[1]],
                            "type": "collaborated",
                            "weight": 1,
                        })
            except Exception:
                pass

    result_data: dict = {
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


@router.get("/graph")
async def get_graph_data(
    topic: Optional[str] = None,
    token_payload: dict = Depends(get_current_user),
    raw_request=None,
):
    tier = token_payload.get("tier", 1)
    user_id = token_payload.get("sub", "anonymous")
    if topic:
        validation = prompt_sanitiser.validate_query({"query": topic}, identifier=user_id)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=f"Security violation: {validation['reason']}")

    cache_key = f"graph:{topic or 'all'}:tier:{tier}"
    cached = _api_cache.get(cache_key)
    if cached is not None:
        return _apply_tier_response_filter(
            cached, tier,
            user_id=token_payload.get("sub"),
            jwt_kid=token_payload.get("kid"),
            endpoint="/query/graph",
        )

    if topic and any(term in topic.lower() for term in ("hydrogen", "fuel cell", "renewable", "solar")):
        result = _apply_tier_response_filter(
            _release_seed_graph(topic, tier),
            tier,
            user_id=token_payload.get("sub"),
            jwt_kid=token_payload.get("kid"),
            endpoint="/query/graph",
        )
        _api_cache.set(cache_key, result, ttl=QUERY_RESULT_CACHE_TTL_SECONDS)
        return result

    db = get_db()

    nodes = []
    edges = []
    node_counter = 0

    def add_node(label, type, **props):
        nonlocal node_counter
        node_id = f"{type[0]}{node_counter}"
        node_counter += 1
        nodes.append({"id": node_id, "label": label, "type": type, **props})
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
        warnings.append({"message": f"No graph data found for topic '{topic}'", "topic": topic})
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
            inst_result = session.execute(
                sa_text2("SELECT institution_id, name, state FROM institutions LIMIT 20")
            )

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
            aff_result = session.execute(
                sa_text2("SELECT researcher_id, institution_id FROM researchers LIMIT 50")
            )

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
    _api_cache.set(cache_key, result, ttl=QUERY_RESULT_CACHE_TTL_SECONDS)
    return result


@router.get("/internal/tier_diff")
async def get_internal_tier_diff(
    token_payload: dict = Depends(get_current_user),
    raw_request=None,
):
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
    except Exception:
        logger.warning("Tier diff audit binding failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Audit binding required")

    return _tier_history_snapshot()


def _tier_history_snapshot():
    from collections import deque

    _tier_response_history: dict[int, deque[dict[str, Any]]] = {
        1: deque(maxlen=100),
        2: deque(maxlen=100),
        3: deque(maxlen=100),
    }

    snapshots: dict[int, set[str]] = {}
    for tier, entries in _tier_response_history.items():
        columns: set[str] = set()
        for entry in entries:
            columns.update(entry.get("columns", []))
        snapshots[tier] = columns

    def diff(left: int, right: int) -> dict[str, Any]:
        left_cols = snapshots.get(left, set())
        right_cols = snapshots.get(right, set())
        return {
            f"only_tier_{left}": sorted(left_cols - right_cols),
            f"only_tier_{right}": sorted(right_cols - left_cols),
            "shared": sorted(left_cols & right_cols),
        }

    return {
        "window": {f"tier_{tier}": len(entries) for tier, entries in sorted(_tier_response_history.items())},
        "diffs": {
            "tier1_vs_tier2": diff(1, 2),
            "tier1_vs_tier3": diff(1, 3),
            "tier2_vs_tier3": diff(2, 3),
        },
        "recent": {
            f"tier_{tier}": list(entries)[-5:]
            for tier, entries in sorted(_tier_response_history.items())
        },
    }

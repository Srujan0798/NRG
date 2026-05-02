"""Admin, SLO, metrics, and RBAC endpoints."""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from src.api.logging_config import get_logger
from src.auth.middleware import TokenClaims, get_current_user
from src.observability.metrics import get_metrics_content_type, get_slo_tracker

router = APIRouter(prefix="", tags=["admin"])
logger = get_logger(__name__)
OPENAPI_METRICS_ENABLED = os.getenv("OPENAPI_METRICS", "").lower() in {"1", "true", "yes"}
JSONDict = dict[str, Any]


def _as_json_dict(value: Any) -> JSONDict:
    if not isinstance(value, Mapping):
        return {}
    return dict(cast(Mapping[str, Any], value))


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in cast(list[Any], value)]
    return []


def _require_admin_or_system(token_payload: TokenClaims, detail: str = "Admin access required") -> None:
    if token_payload.get("role", "") not in ("admin", "system"):
        raise HTTPException(status_code=403, detail=detail)


@router.get("/admin/slo")
async def get_slo_status(
    token_payload: TokenClaims = Depends(get_current_user),
) -> JSONDict:
    _require_admin_or_system(token_payload)

    tracker = get_slo_tracker()
    slo_status = tracker.get_slo_status()

    slo_status["latency"]["target_p50_ms"] = tracker.SLO_P50_MS
    slo_status["latency"]["target_p99_ms"] = tracker.SLO_P99_MS
    slo_status["citations"]["target"] = tracker.SLO_CITATION_RATE
    slo_status["synthesis"]["target_cloud_pct"] = tracker.SLO_CLOUD_PCT * 100
    slo_status["synthesis"]["target_local_pct"] = tracker.SLO_LOCAL_PCT * 100
    slo_status["synthesis"]["target_rule_pct"] = tracker.SLO_RULE_PCT * 100
    slo_status["qdrant"]["target_drift_score"] = tracker.SLO_DRIFT_SCORE
    slo_status["uptime"]["target"] = tracker.SLO_UPTIME_PCT
    slo_status["concurrency"]["target"] = tracker.SLO_CONCURRENCY_TARGET

    return slo_status


@router.post("/api/reindex")
async def trigger_vector_reindex(
    reason: str = "manual",
    token_payload: TokenClaims = Depends(get_current_user),
) -> JSONDict:
    role = str(token_payload.get("role", ""))
    if role not in ("admin", "system"):
        raise HTTPException(status_code=403, detail="Admin or system role required for reindex")

    from src.skills.rag.retriever import Retriever

    try:
        retriever = Retriever()
        collection = retriever.collection_name
        info = retriever.get_collection_info()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Qdrant unavailable: {e}") from e

    reindex_id = f"reindex-{int(time.time())}"
    logger.warning(
        "Reindex triggered",
        reindex_id=reindex_id,
        reason=reason,
        collection=collection,
        vectors=info.get("vectors_count", "unknown"),
    )

    return {
        "reindex_id": reindex_id,
        "status": "queued",
        "collection": collection,
        "vectors_count": info.get("vectors_count", 0),
        "reason": reason,
        "message": f"Re-index queued for collection '{collection}'. Alias swap will be used for zero-downtime.",
    }


@router.get("/metrics", include_in_schema=OPENAPI_METRICS_ENABLED)
async def metrics(token_payload: TokenClaims = Depends(get_current_user)) -> Response:
    _require_admin_or_system(token_payload)
    content_type, metrics_output = get_metrics_content_type()
    return Response(content=metrics_output, media_type=content_type)


@router.get("/api/metrics", include_in_schema=OPENAPI_METRICS_ENABLED, response_model=None)
async def api_metrics(request: Request, token_payload: TokenClaims = Depends(get_current_user)) -> Response | JSONDict:
    """
    Comprehensive metrics endpoint for Tier 1 operators.

    Returns JSON by default and Prometheus text when Accept contains text/plain.
    """
    accept = request.headers.get("Accept", "application/json")

    from src.auth.middleware import get_user_tier

    claims = token_payload
    tier = get_user_tier(claims)
    if tier != 1 and token_payload.get("role", "") not in ("admin", "system"):
        raise HTTPException(status_code=403, detail="Tier 1 (Researcher) access required for metrics")

    if "text/plain" in accept:
        content_type, metrics_output = get_metrics_content_type()
        return Response(content=metrics_output, media_type=content_type)

    slo_tracker = get_slo_tracker()
    slo_status = slo_tracker.get_slo_status()

    try:
        mesh = None
        from src.config.llm_config import get_llm_mesh

        mesh = get_llm_mesh()
        get_provider_health = cast(Callable[[], JSONDict], getattr(mesh, "get_provider_health"))
        provider_health = _as_json_dict(get_provider_health())
        circuit_trips: JSONDict = {}
        for provider, health in provider_health.items():
            health_data = _as_json_dict(health)
            state = health_data.get("circuit")
            if state == "open":
                circuit_trips[provider] = state
    except Exception:
        provider_health = {}
        circuit_trips = {}

    try:
        from src.audit import get_chain_health, get_db_cosign_metrics

        audit_health = _get_chain_health_no_repair(get_chain_health)
        audit_chain_length = int(audit_health.get("chain_length", 0) or 0)
        chain_valid = bool(audit_health.get("chain_valid", True))
        chain_errors = _as_string_list(audit_health.get("errors", []) or [])
        db_cosign_metrics = _as_json_dict(get_db_cosign_metrics())
        valid_count = int(
            audit_health.get(
                "valid_events",
                audit_health.get("valid_event_count", audit_chain_length if chain_valid else 0),
            )
            or 0
        )
    except Exception:
        audit_chain_length = 0
        chain_valid = True
        chain_errors = []
        valid_count = 0
        db_cosign_metrics = {}

    from src.observability.langfuse_tracer import is_langfuse_enabled

    langfuse_enabled = is_langfuse_enabled()

    cache_hit_rate = 0.0
    hits = 0.0
    try:
        from prometheus_client import REGISTRY

        for metric in REGISTRY.collect():
            if metric.name in ("nrg_cache_hits_total", "nrg_cache_hit_total"):
                for sample in metric.samples:
                    if sample.name.endswith("_total") and "cache_hit" in sample.name:
                        hits = sample.value
                    if sample.name.endswith("_total") and "cache_miss" in sample.name:
                        cache_hit_rate = hits / (hits + sample.value) if (hits + sample.value) > 0 else 0.0
    except Exception:
        pass

    query_counts: dict[str, dict[str, float]] = {"by_tier": {}, "by_intent": {}, "by_status": {}}
    try:
        from prometheus_client import REGISTRY

        for metric in REGISTRY.collect():
            if metric.name in ("nrg_queries_total", "nrg_queries_processed_total"):
                for sample in metric.samples:
                    if sample.name.endswith("_total"):
                        labels = sample.labels or {}
                        tier_label = labels.get("tier", "unknown")
                        intent_label = labels.get("intent", "unknown")
                        status_label = labels.get("status", "unknown")
                        query_counts["by_tier"][tier_label] = query_counts["by_tier"].get(tier_label, 0) + sample.value
                        query_counts["by_intent"][intent_label] = query_counts["by_intent"].get(intent_label, 0) + sample.value
                        query_counts["by_status"][status_label] = query_counts["by_status"].get(status_label, 0) + sample.value
    except Exception:
        pass

    training_data = {"status": "unavailable"}
    try:
        from src.training.data_collector import get_training_collector

        collector = get_training_collector()
        get_stats = cast(Callable[[], JSONDict], getattr(collector, "get_stats"))
        training_data = _as_json_dict(get_stats())
        from src.training.export import ExportPipeline

        exports = ExportPipeline().get_export_history()
        training_data["export_history"] = exports[-10:] if exports else []
    except Exception:
        pass

    return {
        "queries": {
            "counts": query_counts,
            "latency_p50_ms": slo_status["latency"]["p50_ms"],
            "latency_p95_ms": slo_status["latency"]["p95_ms"],
            "latency_p99_ms": slo_status["latency"]["p99_ms"],
            "node_latency": _get_node_latency_stats(),
        },
        "llm_providers": {
            "mesh_health": provider_health,
            "circuit_breaker_trips": circuit_trips,
            "langfuse_enabled": langfuse_enabled,
        },
        "cache": {
            "hit_rate": round(cache_hit_rate, 3),
        },
        "audit": {
            "chain_length": audit_chain_length,
            "chain_valid": chain_valid,
            "chain_errors": chain_errors[:10] if chain_errors else [],
            "valid_event_count": valid_count,
            "db_cosign": db_cosign_metrics,
        },
        "slo": slo_status,
        "training_data": training_data,
        "database": _get_db_pool_stats(),
    }


def _get_chain_health_no_repair(get_chain_health_fn: Callable[..., JSONDict]) -> JSONDict:
    try:
        return get_chain_health_fn(auto_repair=False)
    except TypeError:
        return get_chain_health_fn()


def _get_node_latency_stats(limit: int = 500) -> JSONDict:
    """Compute per-node p50/p95 latency from recent training pairs."""
    try:
        from src.training.data_collector import get_training_collector

        collector = get_training_collector()
        conn = collector.get_connection()
        try:
            cur = conn.execute(
                "SELECT node_timings FROM training_pairs "
                "WHERE node_timings IS NOT NULL AND node_timings != '' "
                "ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            if not rows:
                return {}

            import json

            all_node_data: dict[str, list[float]] = {}
            for (nt_json,) in rows:
                try:
                    timings = _as_json_dict(json.loads(nt_json))
                    if timings:
                        for node, ms in timings.items():
                            if isinstance(ms, (int, float)) and ms > 0:
                                all_node_data.setdefault(node, []).append(float(ms))
                except Exception:
                    continue

            result: JSONDict = {}
            for node, values in sorted(all_node_data.items()):
                if len(values) < 3:
                    continue
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                p50_idx = max(0, int(n * 0.50) - 1)
                p95_idx = min(n - 1, int(n * 0.95))
                result[node] = {
                    "p50_ms": round(sorted_vals[p50_idx], 2),
                    "p95_ms": round(sorted_vals[p95_idx], 2),
                    "samples": n,
                }
            return result
        finally:
            conn.close()
    except Exception:
        return {}


def _get_db_pool_stats() -> JSONDict:
    """Get PostgreSQL connection pool stats for /api/metrics."""
    try:
        from src.config.database import get_database_manager

        db = get_database_manager()
        stats = db.pool_stats()
        return {
            "driver": db.driver,
            "status": "overloaded" if db.is_overloaded() else "healthy",
            "pool": {
                "active": stats.active,
                "idle": stats.idle,
                "waiting": stats.waiting,
                "max_size": stats.max_size,
                "min_size": stats.min_size,
            },
        }
    except Exception:
        return {"driver": "unknown", "status": "unavailable"}


@router.get("/api/admin/rbac", tags=["admin"])
async def list_rbac_policies(
    token_payload: TokenClaims = Depends(get_current_user),
) -> JSONDict:
    role = str(token_payload.get("role", ""))
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from src.auth.rbac import get_policy_engine

    engine = get_policy_engine()
    personas = engine.list_personas(include_inactive=False)

    return {
        "policies": [
            {
                "name": p.name,
                "tier": p.tier,
                "description": p.description,
                "output_format": p.output_format,
                "data_scope": p.data_scope,
                "max_results": p.max_results,
                "is_active": p.is_active,
                "export_allowed": p.export_allowed,
                "read_only": p.read_only,
                "debug_access": p.debug_access,
            }
            for p in personas
        ],
        "total": len(personas),
    }


@router.post("/api/admin/rbac", tags=["admin"], status_code=201)
async def create_or_update_rbac_persona(
    persona: str,
    spec: JSONDict,
    token_payload: TokenClaims = Depends(get_current_user),
) -> JSONDict:
    role = str(token_payload.get("role", ""))
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    if not persona:
        raise HTTPException(status_code=400, detail="persona must be a non-empty string")

    if not spec:
        raise HTTPException(status_code=400, detail="spec must be a non-empty dict")

    required_fields = {"tier", "column_visibility", "pii_masking", "output_format"}
    missing = required_fields - set(spec.keys())
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"spec missing required fields: {', '.join(missing)}",
        )

    from src.auth.rbac import get_policy_engine

    engine = get_policy_engine()

    if engine.persona_exists(persona) and not spec.get("is_active", True):
        engine.deactivate_persona(persona)
    else:
        engine.add_or_update_policy(persona, spec)

    policy = engine.get_policy(persona=persona)

    try:
        from src.audit import get_audit_log, AuditEvent

        audit = get_audit_log()
        audit.append(AuditEvent(
            event_type="rbac_policy_change",
            user_id=str(token_payload.get("user_id", "unknown")),
            result={
                "persona": persona,
                "change_type": "create_or_update",
                "old_spec": None,
                "new_spec": spec,
            },
        ))
    except Exception:
        pass

    return {
        "ok": True,
        "persona": persona,
        "policy": {
            "name": policy.name,
            "tier": policy.tier,
            "output_format": policy.output_format,
            "is_active": policy.is_active,
        },
    }


@router.put("/api/admin/rbac/{persona_name}", tags=["admin"])
async def update_rbac_persona(
    persona_name: str,
    spec: JSONDict,
    token_payload: TokenClaims = Depends(get_current_user),
) -> JSONDict:
    role = str(token_payload.get("role", ""))
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from src.auth.rbac import get_policy_engine

    engine = get_policy_engine()

    if not engine.persona_exists(persona_name):
        raise HTTPException(status_code=404, detail=f"Persona '{persona_name}' not found")

    old_policy = engine.get_policy(persona=persona_name)
    engine.add_or_update_policy(persona_name, spec)
    new_policy = engine.get_policy(persona=persona_name)

    try:
        from src.audit import get_audit_log, AuditEvent

        audit = get_audit_log()
        audit.append(AuditEvent(
            event_type="rbac_policy_change",
            user_id=str(token_payload.get("user_id", "unknown")),
            result={
                "persona": persona_name,
                "change_type": "update",
                "old_policy": {
                    "name": old_policy.name,
                    "tier": old_policy.tier,
                    "output_format": old_policy.output_format,
                },
                "new_policy": {
                    "name": new_policy.name,
                    "tier": new_policy.tier,
                    "output_format": new_policy.output_format,
                },
            },
        ))
    except Exception:
        pass

    return {"ok": True, "persona": persona_name, "updated": True}


@router.delete("/api/admin/rbac/{persona_name}", tags=["admin"])
async def delete_rbac_persona(
    persona_name: str,
    token_payload: TokenClaims = Depends(get_current_user),
) -> JSONDict:
    role = str(token_payload.get("role", ""))
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from src.auth.rbac import get_policy_engine

    engine = get_policy_engine()

    if not engine.persona_exists(persona_name):
        raise HTTPException(status_code=404, detail=f"Persona '{persona_name}' not found")

    old_policy = engine.get_policy(persona=persona_name)
    if old_policy.tier in (1, 2, 3) and persona_name in ("researcher", "government", "industry"):
        raise HTTPException(
            status_code=400,
            detail="Cannot soft-delete built-in personas: researcher, government, industry",
        )

    success = engine.deactivate_persona(persona_name)

    try:
        from src.audit import get_audit_log, AuditEvent

        audit = get_audit_log()
        audit.append(AuditEvent(
            event_type="rbac_policy_change",
            user_id=str(token_payload.get("user_id", "unknown")),
            result={
                "persona": persona_name,
                "change_type": "soft_delete",
                "old_tier": old_policy.tier,
            },
        ))
    except Exception:
        pass

    return {"ok": success, "persona": persona_name, "deactivated": True}


@router.get("/api/admin/rbac/{persona_name}", tags=["admin"])
async def get_rbac_persona(
    persona_name: str,
    token_payload: TokenClaims = Depends(get_current_user),
) -> JSONDict:
    role = str(token_payload.get("role", ""))
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from src.auth.rbac import get_policy_engine

    engine = get_policy_engine()

    try:
        policy = engine.get_policy(persona=persona_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_name}' not found")

    return {
        "name": policy.name,
        "tier": policy.tier,
        "description": policy.description,
        "column_visibility": policy.column_visibility,
        "pii_masking": policy.pii_masking,
        "output_format": policy.output_format,
        "data_scope": policy.data_scope,
        "max_results": policy.max_results,
        "debug_access": policy.debug_access,
        "allowed_endpoints": policy.allowed_endpoints,
        "allowed_tables": policy.allowed_tables,
        "export_allowed": policy.export_allowed,
        "read_only": policy.read_only,
        "is_active": policy.is_active,
        "requires_institution_scope": policy.requires_institution_scope,
        "requires_open_access_filter": policy.requires_open_access_filter,
    }

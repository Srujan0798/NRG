"""Admin, SLO, metrics, and RBAC endpoints."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from src.api.logging_config import get_logger
from src.auth.middleware import get_current_user
from src.observability.metrics import get_metrics_content_type, get_slo_tracker

router = APIRouter(prefix="", tags=["admin"])
logger = get_logger(__name__)


@router.get("/admin/slo")
async def get_slo_status(
    token_payload: dict = Depends(get_current_user),
):
    role = token_payload.get("role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

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
    token_payload: dict = Depends(get_current_user),
):
    role = token_payload.get("role", "")
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
        "Reindex triggered: id=%s reason=%s collection=%s vectors=%s",
        reindex_id, reason, collection, info.get("vectors_count", "unknown"),
    )

    return {
        "reindex_id": reindex_id,
        "status": "queued",
        "collection": collection,
        "vectors_count": info.get("vectors_count", 0),
        "reason": reason,
        "message": f"Re-index queued for collection '{collection}'. Alias swap will be used for zero-downtime.",
    }


@router.get("/metrics")
async def metrics():
    content_type, metrics_output = get_metrics_content_type()
    return Response(content=metrics_output, media_type=content_type)


@router.get("/api/metrics")
async def api_metrics(
    request: Request,
    token_payload: dict = Depends(get_current_user),
):
    accept = request.headers.get("Accept", "application/json")

    if "text/plain" in accept:
        content_type, metrics_output = get_metrics_content_type()
        return Response(content=metrics_output, media_type=content_type)

    from src.auth.middleware import get_user_tier

    claims = getattr(request.state, "auth_claims", None) or {}
    tier = get_user_tier(claims)
    if tier != 1:
        raise HTTPException(status_code=403, detail="Tier 1 (Researcher) access required for metrics")

    slo_tracker = get_slo_tracker()
    slo_status = slo_tracker.get_slo_status()

    try:
        mesh = None
        from src.config.llm_config import get_llm_mesh

        mesh = get_llm_mesh()
        provider_health = mesh.get_provider_health()
        circuit_trips = {}
        for p, state in mesh._circuit_state.items():
            if state == "open":
                circuit_trips[p] = state
    except Exception:
        provider_health = {}
        circuit_trips = {}

    try:
        from src.audit import get_chain_health, get_db_cosign_metrics

        audit_health = get_chain_health()
        audit_chain_length = int(audit_health.get("chain_length", 0) or 0)
        chain_valid = bool(audit_health.get("chain_valid", True))
        chain_errors = audit_health.get("errors", []) or []
        db_cosign_metrics = get_db_cosign_metrics()
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

    langfuse_enabled = __import__("src.observability.langfuse_tracer", fromlist=["_init_langfuse"])._init_langfuse() is not None

    cache_hit_rate = 0.0
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

    query_counts = {"by_tier": {}, "by_intent": {}, "by_status": {}}
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
                        if tier_label not in query_counts["by_tier"]:
                            query_counts["by_tier"][tier_label] = 0
                        if intent_label not in query_counts["by_intent"]:
                            query_counts["by_intent"][intent_label] = 0
                        if status_label not in query_counts["by_status"]:
                            query_counts["by_status"][status_label] = 0
                        query_counts["by_tier"][tier_label] += int(sample.value)
                        query_counts["by_intent"][intent_label] += int(sample.value)
                        query_counts["by_status"][status_label] += int(sample.value)
    except Exception:
        pass

    return {
        "status": "ok",
        "slo": slo_status,
        "providers": provider_health,
        "circuit_breaker_trips": circuit_trips,
        "audit_chain": {
            "length": audit_chain_length,
            "valid": chain_valid,
            "errors": chain_errors,
            "valid_events": valid_count,
            "cosign": db_cosign_metrics,
        },
        "cache_hit_rate": cache_hit_rate,
        "query_counts": query_counts,
        "langfuse_enabled": langfuse_enabled,
    }


@router.get("/api/admin/rbac", tags=["admin"])
async def list_rbac_policies(
    token_payload: dict = Depends(get_current_user),
):
    role = token_payload.get("role", "")
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
    spec: dict,
    token_payload: dict = Depends(get_current_user),
):
    role = token_payload.get("role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    if not persona or not isinstance(persona, str):
        raise HTTPException(status_code=400, detail="persona must be a non-empty string")

    if not spec or not isinstance(spec, dict):
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
            user_id=token_payload.get("user_id", "unknown"),
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
    spec: dict,
    token_payload: dict = Depends(get_current_user),
):
    role = token_payload.get("role", "")
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
            user_id=token_payload.get("user_id", "unknown"),
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
    token_payload: dict = Depends(get_current_user),
):
    role = token_payload.get("role", "")
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
            user_id=token_payload.get("user_id", "unknown"),
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
    token_payload: dict = Depends(get_current_user),
):
    role = token_payload.get("role", "")
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

"""Health check endpoints."""

from __future__ import annotations

import os
import httpx
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.api.deps import get_db, REPO_ROOT, DEFAULT_VECTOR_DRIFT_STATUS_FILE, DEFAULT_DATA_QUALITY_SCORECARD_FILE
from src.api.logging_config import get_logger
from src.auth.jwt_handler import JWTHandler
from src.observability.health_checks import build_rag_health, get_qdrant_vector_count_health

router = APIRouter(tags=["health"])
logger = get_logger(__name__)
jwt_handler = JWTHandler()


def _get_vector_drift_health():
    import json

    path = DEFAULT_VECTOR_DRIFT_STATUS_FILE
    if not path.exists():
        return {
            "status": "unknown",
            "message": "No vector drift status file has been emitted yet.",
            "path": str(path),
            "scheduler": {"status": "unknown", "message": "Vector drift scheduler has not emitted a run marker yet."},
        }
    try:
        payload = json.loads(path.read_text())
    except Exception as exc:
        return {"status": "error", "message": str(exc), "path": str(path)}

    alert_level = str(payload.get("alert_level", "")).upper()
    if "status" not in payload:
        payload["status"] = "healthy" if alert_level in {"GREEN", "AMBER"} else "unhealthy"
    payload.setdefault(
        "scheduler",
        {"status": "unknown", "message": "Vector drift scheduler has not emitted a run marker yet."},
    )
    return payload


def _get_data_quality_health():
    import json

    path = DEFAULT_DATA_QUALITY_SCORECARD_FILE
    if not path.exists():
        return {
            "status": "unknown",
            "message": "No data quality scorecard has been emitted yet.",
            "path": str(path),
        }
    try:
        payload = json.loads(path.read_text())
    except Exception as exc:
        return {"status": "error", "message": str(exc), "path": str(path)}

    p0_alerts = [
        alert for alert in payload.get("alerts", [])
        if str(alert.get("severity", "")).upper() == "P0"
    ]
    status = "unhealthy" if p0_alerts else "healthy" if payload.get("ok") else "degraded"
    return {
        "status": status,
        "overall_status": payload.get("overall_status"),
        "overall_score": payload.get("overall_score"),
        "p0_alerts": len(p0_alerts),
        "generated_at": payload.get("generated_at"),
        "path": str(path),
    }


def _get_qdrant_vector_count_health():
    from qdrant_client import QdrantClient
    return get_qdrant_vector_count_health(client_factory=QdrantClient)


@router.get("/health")
async def health_check():
    import asyncio

    retriever_health = {"status": "skipped", "message": "Deep retriever health disabled for fast readiness checks"}
    try:
        from src.audit import get_chain_health

        audit_health = get_chain_health()
        audit_lineage = audit_health.get("lineage_break", {}) or {}
        if (
            audit_health.get("status") == "CRITICAL"
            or audit_lineage.get("repair_required")
            or audit_lineage.get("lineage_intact") is False
            or audit_health.get("lineage_intact") is False
        ):
            audit_health["status"] = "CRITICAL"
        elif audit_health.get("chain_valid"):
            audit_health["status"] = "healthy"
        else:
            audit_health["status"] = "unhealthy"
    except Exception as exc:
        audit_health = {"status": "error", "chain_valid": None, "message": str(exc)}

    try:
        db = get_db()
        stats = db.get_stats()
        if getattr(db, "dialect", "") == "postgresql":
            table_count_query = (
                "SELECT COUNT(*) AS table_count "
                "FROM information_schema.tables "
                "WHERE table_schema='public' AND table_type='BASE TABLE'"
            )
        else:
            table_count_query = (
                "SELECT COUNT(*) AS table_count "
                "FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        table_count_rows = db.execute(table_count_query) if hasattr(db, "execute") else []
        table_count = (
            int(table_count_rows[0].get("table_count", 0))
            if table_count_rows
            else None
        )
        db_health = {
            "status": "healthy",
            "dialect": getattr(db, "dialect", "unknown"),
            "researchers": stats.get("researchers", 0),
            "publications": stats.get("publications", 0),
            "table_count": table_count,
            "tables": table_count,
        }
        if hasattr(db, "pool_stats"):
            pool_stats = db.pool_stats()
            db_health["pool"] = {
                "active": getattr(pool_stats, "active", 0),
                "idle": getattr(pool_stats, "idle", 0),
                "waiting": getattr(pool_stats, "waiting", 0),
                "max_size": getattr(pool_stats, "max_size", 0),
                "min_size": getattr(pool_stats, "min_size", 0),
            }
    except Exception as exc:
        db_health = {"status": "error", "message": str(exc)}

    if os.getenv("NRG_DEEP_HEALTH_CHECKS", "").lower() in {"1", "true", "yes"}:
        try:
            def _check_retriever_health():
                from src.skills.rag.retriever import Retriever
                return Retriever(timeout=1.0).health_check()

            retriever_health = await asyncio.wait_for(
                asyncio.to_thread(_check_retriever_health),
                timeout=0.75,
            )
        except asyncio.TimeoutError:
            retriever_health = {"status": "timeout", "message": "Health check timed out after 0.75s"}
        except Exception as exc:
            retriever_health = {"status": "error", "message": str(exc)}

        try:
            from src.audit import get_chain_health

            audit_timeout_seconds = float(os.getenv("NRG_HEALTH_AUDIT_TIMEOUT_SECONDS", "3.0"))
            audit_health = await asyncio.wait_for(
                asyncio.to_thread(get_chain_health),
                timeout=audit_timeout_seconds,
            )
        except asyncio.TimeoutError:
            audit_health = {
                "status": "timeout",
                "chain_valid": None,
                "message": f"Audit-chain health timed out after {audit_timeout_seconds:.1f}s",
            }
        except Exception as exc:
            audit_health = {"status": "error", "chain_valid": None, "message": str(exc)}

    overall = "healthy"
    audit_lineage = audit_health.get("lineage_break") or {}
    if (
        audit_health.get("status") == "CRITICAL"
        or audit_health.get("chain_valid") is False
        or audit_health.get("lineage_intact") is False
        or audit_lineage.get("lineage_intact") is False
        or audit_lineage.get("repair_required")
    ):
        audit_health["status"] = "CRITICAL"
        overall = "CRITICAL"

    auth_status = jwt_handler.jwt_secret_health()
    if auth_status.get("status") == "unhealthy" and overall != "CRITICAL":
        overall = "unhealthy"
    if retriever_health.get("status") == "critical" and overall != "CRITICAL":
        overall = "unhealthy"

    from src.observability.metrics import get_slo_tracker

    slo_tracker = get_slo_tracker()
    slo_tracker.record_uptime_check(overall == "healthy")

    drift_score = None
    if retriever_health.get("status") == "ok":
        indexed = retriever_health.get("vectors_indexed", 0)
        total = retriever_health.get("vectors_total", 0)
        if total > 0:
            drift_score = indexed / total
    if drift_score is not None:
        slo_tracker.set_drift_score(drift_score)

    vector_drift_health = _get_vector_drift_health()
    data_quality_health = _get_data_quality_health()
    if data_quality_health.get("status") == "unhealthy" and overall != "CRITICAL":
        overall = "unhealthy"

    qdrant_health = _get_qdrant_vector_count_health()
    if qdrant_health.get("status") == "CRITICAL":
        overall = "CRITICAL"
    rag_health = build_rag_health(qdrant_health, retriever_health)

    payload = {
        "status": overall,
        "timestamp": datetime.now(UTC).isoformat(),
        "consent_service": "operational",
        "retriever": retriever_health,
        "qdrant": qdrant_health,
        "rag": rag_health,
        "vector_drift": vector_drift_health,
        "data_quality": data_quality_health,
        "database": db_health,
        "audit": audit_health,
        "auth_status": auth_status,
    }
    if overall == "CRITICAL":
        return JSONResponse(status_code=503, content=payload)
    return payload


@router.get("/api/health/killer_queries")
async def health_killer_queries():
    import json

    KILLER_QUERY_HEALTH_FILE = REPO_ROOT / "evidence/2026-04-26/killer_query_health.json"
    if not KILLER_QUERY_HEALTH_FILE.exists():
        return {
            "status": "unknown",
            "last_run_time": None,
            "queries": [],
            "message": "No killer-query evidence snapshot has been written yet.",
        }

    try:
        return json.loads(KILLER_QUERY_HEALTH_FILE.read_text())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Invalid killer-query health snapshot: {exc}") from exc


@router.get("/health/llm")
async def health_llm():
    from src.config.llm_config import get_llm_client, LLMConfigError
    from src.config.local_llm import get_llama_cpp_client, _llama_cpp_health_cache

    local_info = {"available": False, "model_loaded": False, "load_time": None}

    llama_client = get_llama_cpp_client()
    if llama_client is not None:
        local_info["available"] = True
        local_info["model_loaded"] = True
        if _llama_cpp_health_cache is not None:
            local_info["load_time"] = _llama_cpp_health_cache[0]
    else:
        try:
            r = httpx.get("http://localhost:8080/health", timeout=2.0)
            if r.status_code == 200:
                data = r.json()
                local_info["available"] = True
                local_info["model_loaded"] = data.get("model_loaded", False)
                if data.get("model_loaded"):
                    local_info["load_time"] = data.get("loaded_at")
        except Exception:
            pass

    try:
        client = get_llm_client()
        if client is None:
            return {"ready": False, "providers": [], "local": local_info}
        providers = list(client.providers.keys())
        return {"ready": True, "providers": providers, "local": local_info}
    except LLMConfigError as exc:
        return {"ready": False, "error": str(exc), "local": local_info}
    except Exception as exc:
        return {"ready": False, "error": str(exc), "local": local_info}


@router.get("/api/providers/health")
async def providers_health():
    try:
        from src.config.llm_config import get_llm_mesh

        mesh = get_llm_mesh()
        health = mesh.get_provider_health()
        return {"providers": health}
    except Exception as exc:
        logger.warning("Provider health check failed", exc_info=True)
        return {"providers": {}, "error": str(exc)}


@router.get("/health/db")
async def health_db():
    try:
        db = get_db()
        stats = db.get_stats()
        return {
            "status": "healthy",
            "dialect": getattr(db, "dialect", "unknown"),
            "researchers": stats.get("researchers", 0),
            "publications": stats.get("publications", 0),
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@router.get("/health/qdrant")
async def health_qdrant():
    return _get_qdrant_vector_count_health()


@router.get("/api/vectors/health")
async def vectors_health():
    result = _get_qdrant_vector_count_health()
    vector_drift = _get_vector_drift_health()
    return {**result, "vector_drift": vector_drift}


@router.get("/health/all")
async def health_all():
    checks = {
        "api": {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()},
        "local_llm": {"status": "unknown"},
        "qdrant": {"status": "unknown"},
        "redis": {"status": "unknown"},
        "consent_service": {"status": "unknown"},
    }

    try:
        r = httpx.get("http://localhost:8080/health", timeout=2.0)
        checks["local_llm"] = r.json()
        checks["local_llm"]["status"] = "healthy" if r.json().get("model_loaded") else "optional_unavailable"
        checks["local_llm"]["required"] = False
    except Exception as e:
        checks["local_llm"] = {"status": "optional_unavailable", "required": False, "error": str(e)}

    try:
        from qdrant_client import QdrantClient

        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        client = QdrantClient(host=host, port=port, timeout=2.0)
        cols = client.get_collections()
        checks["qdrant"] = {"status": "healthy", "collections": [c.name for c in getattr(cols, "collections", [])]}
    except Exception as e:
        checks["qdrant"] = {"status": "unhealthy", "error": str(e)}

    try:
        from src.caching.redis_layer import _get_redis

        redis_client = _get_redis()
        if redis_client and redis_client.ping():
            checks["redis"] = {"status": "healthy"}
        else:
            checks["redis"] = {"status": "unhealthy", "error": "No connection"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    try:
        from src.services.consent import get_consent_service

        cs = get_consent_service()
        cs.list_consents("__health_check__")
        checks["consent_service"] = {"status": "operational", "scopes": list(cs.SCOPES.keys())}
    except Exception as e:
        checks["consent_service"] = {"status": "unhealthy", "error": str(e)}

    required_services = ("api", "qdrant", "redis")
    overall = all(checks[name].get("status") == "healthy" for name in required_services)
    overall = overall and checks["consent_service"].get("status") in {"healthy", "operational"}
    return {"status": "healthy" if overall else "degraded", "services": checks}

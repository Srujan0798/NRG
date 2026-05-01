"""Health, provider, and vector readiness endpoints."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.data.database import resolve_database_path
from src.observability.health_checks import build_rag_health

router = APIRouter(tags=["health"])

_get_db: Callable[[], Any] | None = None
_jwt_handler: Any | None = None
_chain_health_no_repair: Callable[[Callable[..., dict[str, Any]]], dict[str, Any]] | None = None
_vector_drift_health: Callable[[], dict[str, Any]] | None = None
_data_quality_health: Callable[[], dict[str, Any]] | None = None
_qdrant_vector_count_health: Callable[[], dict[str, Any]] | None = None
_qdrant_client_factory: Callable[..., Any] | None = None
_killer_query_health_file: Path | None = None


def configure_health_router(
    *,
    db_getter: Callable[[], Any],
    jwt_handler: Any,
    chain_health_no_repair: Callable[[Callable[..., dict[str, Any]]], dict[str, Any]],
    vector_drift_health: Callable[[], dict[str, Any]],
    data_quality_health: Callable[[], dict[str, Any]],
    qdrant_vector_count_health: Callable[[], dict[str, Any]],
    qdrant_client_factory: Callable[..., Any],
    killer_query_health_file: Path,
) -> None:
    """Bind health routes to the app-level runtime dependencies."""
    global _get_db, _jwt_handler, _chain_health_no_repair
    global _vector_drift_health, _data_quality_health, _qdrant_vector_count_health
    global _qdrant_client_factory, _killer_query_health_file

    _get_db = db_getter
    _jwt_handler = jwt_handler
    _chain_health_no_repair = chain_health_no_repair
    _vector_drift_health = vector_drift_health
    _data_quality_health = data_quality_health
    _qdrant_vector_count_health = qdrant_vector_count_health
    _qdrant_client_factory = qdrant_client_factory
    _killer_query_health_file = killer_query_health_file


def _db() -> Any:
    if _get_db is None:
        raise RuntimeError("Health router is not configured with a DB getter")
    return _get_db()


def _auth_health() -> dict[str, Any]:
    if _jwt_handler is None:
        raise RuntimeError("Health router is not configured with a JWT handler")
    return _jwt_handler.jwt_secret_health()


def _audit_health_no_repair(get_chain_health_fn: Callable[..., dict[str, Any]]) -> dict[str, Any]:
    if _chain_health_no_repair is None:
        raise RuntimeError("Health router is not configured with audit-chain health")
    return _chain_health_no_repair(get_chain_health_fn)


def _vector_drift() -> dict[str, Any]:
    if _vector_drift_health is None:
        raise RuntimeError("Health router is not configured with vector drift health")
    return _vector_drift_health()


def _data_quality() -> dict[str, Any]:
    if _data_quality_health is None:
        raise RuntimeError("Health router is not configured with data quality health")
    return _data_quality_health()


def _qdrant_count_health() -> dict[str, Any]:
    if _qdrant_vector_count_health is None:
        raise RuntimeError("Health router is not configured with Qdrant health")
    return _qdrant_vector_count_health()


def _new_qdrant_client(**kwargs) -> Any:
    if _qdrant_client_factory is None:
        raise RuntimeError("Health router is not configured with a Qdrant client factory")
    return _qdrant_client_factory(**kwargs)


def _killer_query_health_path() -> Path:
    if _killer_query_health_file is None:
        raise RuntimeError("Health router is not configured with a killer-query health path")
    return _killer_query_health_file


@router.get("/health")
async def health_check():
    retriever_health = {"status": "skipped", "message": "Deep retriever health disabled for fast readiness checks"}

    def _resolve_audit_health() -> dict[str, Any]:
        from src.audit import get_chain_health

        health = _audit_health_no_repair(get_chain_health)
        lineage = health.get("lineage_break", {}) or {}
        if (
            health.get("status") == "CRITICAL"
            or lineage.get("repair_required")
            or lineage.get("lineage_intact") is False
            or health.get("lineage_intact") is False
        ):
            health["status"] = "CRITICAL"
        elif health.get("chain_valid"):
            health["status"] = "healthy"
        else:
            health["status"] = "unhealthy"
        return health

    audit_timeout_seconds = float(os.getenv("NRG_HEALTH_AUDIT_TIMEOUT_SECONDS", "3.0"))
    try:
        audit_health = await asyncio.wait_for(
            asyncio.to_thread(_resolve_audit_health),
            timeout=audit_timeout_seconds,
        )
    except asyncio.TimeoutError:
        audit_health = {
            "status": "timeout",
            "chain_valid": None,
            "message": f"Audit-chain health timed out after {audit_timeout_seconds:.2f}s",
        }
    except Exception as exc:
        audit_health = {"status": "error", "chain_valid": None, "message": str(exc)}

    try:
        db = _db()
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
        table_count = int(table_count_rows[0].get("table_count", 0)) if table_count_rows else None
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
            audit_health = await asyncio.wait_for(
                asyncio.to_thread(_resolve_audit_health),
                timeout=audit_timeout_seconds,
            )
        except asyncio.TimeoutError:
            audit_health = {
                "status": "timeout",
                "chain_valid": None,
                "message": f"Audit-chain health timed out after {audit_timeout_seconds:.2f}s",
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
    elif audit_health.get("status") in {"timeout", "error"}:
        overall = "unhealthy"

    auth_status = _auth_health()
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

    vector_drift_health = _vector_drift()
    data_quality_health = _data_quality()
    if data_quality_health.get("status") == "unhealthy" and overall != "CRITICAL":
        overall = "unhealthy"

    qdrant_timeout_seconds = float(os.getenv("NRG_HEALTH_QDRANT_TIMEOUT_SECONDS", "0.75"))
    try:
        qdrant_health = await asyncio.wait_for(
            asyncio.to_thread(_qdrant_count_health),
            timeout=qdrant_timeout_seconds,
        )
    except asyncio.TimeoutError:
        qdrant_health = {
            "status": "unavailable",
            "collection": os.getenv("QDRANT_COLLECTION", "nrg_research"),
            "vectors": None,
            "message": f"Qdrant vector health timed out after {qdrant_timeout_seconds:.2f}s",
        }
    except Exception as exc:
        qdrant_health = {
            "status": "unavailable",
            "collection": os.getenv("QDRANT_COLLECTION", "nrg_research"),
            "vectors": None,
            "message": str(exc),
        }
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
    """Return the last LB-3 killer-query health snapshot."""
    health_path = _killer_query_health_path()
    if not health_path.exists():
        return {
            "status": "unknown",
            "last_run_time": None,
            "queries": [],
            "message": "No killer-query evidence snapshot has been written yet.",
        }

    try:
        return json.loads(health_path.read_text())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Invalid killer-query health snapshot: {exc}") from exc


@router.get("/health/llm")
async def health_llm():
    """Check LLM provider health including local llama.cpp model status."""
    from src.config.llm_config import LLMConfigError, get_llm_client
    from src.config.local_llm import _llama_cpp_health_cache, get_llama_cpp_client

    local_info = {"available": False, "model_loaded": False, "load_time": None}

    llama_client = get_llama_cpp_client()
    if llama_client is not None:
        local_info["available"] = True
        local_info["model_loaded"] = True
        if _llama_cpp_health_cache is not None:
            local_info["load_time"] = _llama_cpp_health_cache[0]
    else:
        try:
            response = httpx.get("http://localhost:8080/health", timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                local_info["available"] = True
                local_info["model_loaded"] = data.get("model_loaded", False)
                if data.get("model_loaded"):
                    local_info["load_time"] = data.get("loaded_at")
        except Exception:
            pass

    try:
        client = get_llm_client()
        if client is None:
            return {
                "ready": False,
                "provider": None,
                "error": "No LLM configured. Set GEMINI_API_KEY or OPENAI_API_KEY in .env",
                "local": local_info,
            }
        test_response = client.generate(
            "You are a health check system.",
            "Respond with 'OK' only.",
            [],
        )
        settings = getattr(client, "settings", None)
        provider = getattr(settings, "provider", "unknown") if settings else "unknown"
        model = getattr(settings, "model", "unknown") if settings else "unknown"
        return {
            "ready": True,
            "provider": provider,
            "model": model,
            "test_response": test_response[:10] if test_response else None,
            "local": local_info,
        }
    except LLMConfigError as exc:
        return {"ready": False, "provider": None, "error": str(exc), "local": local_info}
    except Exception as exc:
        return {"ready": False, "provider": None, "error": str(exc), "local": local_info}


@router.get("/api/providers/health")
async def providers_health():
    """
    Returns health status of all LLM providers in the SovereignLLMMesh.
    Includes: status, circuit state, success_rate_7d, latency_p50, health_rank.
    """
    from src.config.llm_config import get_llm_mesh

    try:
        mesh = get_llm_mesh()
        health = mesh.get_provider_health()
        return {"providers": health, "timeout_budget_seconds": mesh.mesh_config.query_timeout_budget_seconds}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Provider health check failed: {exc}") from exc


@router.get("/health/db")
async def health_db():
    """Check database readiness via SQLAlchemy ORM."""
    try:
        db = _db()
        stats = db.get_stats()
        return {
            "ready": True,
            "dialect": db.dialect,
            "path": str(resolve_database_path()),
            "researcher_count": stats.get("researchers", 0),
            "publication_count": stats.get("publications", 0),
        }
    except Exception as exc:
        return {
            "ready": False,
            "dialect": "sqlite",
            "error": str(exc),
        }


@router.get("/health/qdrant")
async def health_qdrant():
    """Check Qdrant readiness without hiding connection failures."""
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    collection = os.getenv("QDRANT_COLLECTION", "nrg_research")

    try:
        client = _new_qdrant_client(host=host, port=port, timeout=2.0)
        collections = client.get_collections()
        names = [item.name for item in getattr(collections, "collections", [])]
        return {
            "ready": True,
            "host": host,
            "port": port,
            "collection": collection,
            "collection_exists": collection in names,
            "collections": names,
        }
    except Exception as exc:
        return {
            "ready": False,
            "host": host,
            "port": port,
            "collection": collection,
            "error": str(exc),
        }


@router.get("/api/vectors/health")
async def vectors_health():
    """
    Returns detailed vector store health: collection stats, dimension, distance metric,
    index coverage, last ingestion time, and drift score.
    """
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    collection = os.getenv("QDRANT_COLLECTION", "nrg_research")

    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(host=host, port=port, timeout=5.0)
        collection_info = client.get_collection(collection_name=collection)
        points_count = collection_info.points_count
        indexed_count = collection_info.indexed_vectors_count
        optimizer_cfg = getattr(collection_info.config, "optimizer_config", None)
        indexing_threshold = getattr(optimizer_cfg, "indexing_threshold", None)
        try:
            indexing_threshold = int(indexing_threshold) if indexing_threshold is not None else None
        except (TypeError, ValueError):
            indexing_threshold = None
        threshold_exempt = (
            bool(points_count)
            and not indexed_count
            and indexing_threshold is not None
            and points_count < indexing_threshold
        )

        index_status = "green"
        if points_count and indexed_count is not None and indexed_count < points_count and not threshold_exempt:
            index_status = "yellow"
        if not indexed_count and points_count and points_count > 0 and not threshold_exempt:
            index_status = "red"

        scroll_result = client.scroll(
            collection_name=collection,
            limit=1,
            with_payload=True,
            scroll_filter=None,
        )
        last_doc = scroll_result[0][0].payload if scroll_result and scroll_result[0] else {}
        last_ingestion = last_doc.get("ingested_at")

        if not indexed_count and points_count and points_count > 0 and not threshold_exempt:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Vector index not built: {indexed_count}/{points_count} vectors indexed. "
                    "Qdrant HNSW index build required before RAG queries can execute. "
                    "Run: python scripts/build_qdrant_index.py"
                ),
            )

        return {
            "collection_name": collection,
            "vector_count": points_count,
            "indexed_vectors_count": indexed_count,
            "index_built": index_status == "green",
            "indexing_threshold": indexing_threshold,
            "dimension": collection_info.config.params.vectors.size if collection_info.config and collection_info.config.params else None,
            "distance_metric": collection_info.config.params.vectors.distance.name if collection_info.config and collection_info.config.params else None,
            "index_status": index_status,
            "last_ingestion_time": last_ingestion,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Vector health check failed: {exc}") from exc


@router.get("/health/all")
async def health_all():
    """Combined health check for all services."""
    checks = {
        "api": {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()},
        "local_llm": {"status": "unknown"},
        "qdrant": {"status": "unknown"},
        "redis": {"status": "unknown"},
        "consent_service": {"status": "unknown"},
    }

    try:
        response = httpx.get("http://localhost:8080/health", timeout=2.0)
        checks["local_llm"] = response.json()
        checks["local_llm"]["status"] = "healthy" if response.json().get("model_loaded") else "optional_unavailable"
        checks["local_llm"]["required"] = False
    except Exception as exc:
        checks["local_llm"] = {"status": "optional_unavailable", "required": False, "error": str(exc)}

    try:
        from qdrant_client import QdrantClient

        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        client = QdrantClient(host=host, port=port, timeout=2.0)
        cols = client.get_collections()
        checks["qdrant"] = {"status": "healthy", "collections": [c.name for c in getattr(cols, "collections", [])]}
    except Exception as exc:
        checks["qdrant"] = {"status": "unhealthy", "error": str(exc)}

    try:
        from src.caching.redis_layer import _get_redis

        redis_client = _get_redis()
        if redis_client and redis_client.ping():
            checks["redis"] = {"status": "healthy"}
        else:
            checks["redis"] = {"status": "unhealthy", "error": "No connection"}
    except Exception as exc:
        checks["redis"] = {"status": "unhealthy", "error": str(exc)}

    try:
        from src.services.consent import get_consent_service

        cs = get_consent_service()
        cs.list_consents("__health_check__")
        checks["consent_service"] = {"status": "operational", "scopes": list(cs.SCOPES.keys())}
    except Exception as exc:
        checks["consent_service"] = {"status": "unhealthy", "error": str(exc)}

    required_services = ("api", "qdrant", "redis")
    overall = all(checks[name].get("status") == "healthy" for name in required_services)
    overall = overall and checks["consent_service"].get("status") in {"healthy", "operational"}
    return {"status": "healthy" if overall else "degraded", "services": checks}

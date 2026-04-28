"""Shared health-check helpers used by API and audit tooling."""

from __future__ import annotations

import os
from typing import Any, Callable


def get_qdrant_vector_count_health(
    *,
    client_factory: Callable[..., Any] | None = None,
    collection: str | None = None,
    host: str | None = None,
    port: int | None = None,
    timeout: float = 1.0,
) -> dict:
    """Return honest Qdrant vector health without auto-repair side effects."""
    if client_factory is None:
        from qdrant_client import QdrantClient

        client_factory = QdrantClient

    resolved_host = host or os.getenv("QDRANT_HOST", "localhost")
    resolved_port = port if port is not None else int(os.getenv("QDRANT_PORT", "6333"))
    resolved_collection = collection or os.getenv("QDRANT_COLLECTION", "nrg_research")

    try:
        client = client_factory(host=resolved_host, port=resolved_port, timeout=timeout)
    except Exception as exc:
        return {
            "status": "unavailable",
            "collection": resolved_collection,
            "vectors": None,
            "message": f"Qdrant vector count unavailable: {exc}",
        }

    try:
        collection_info = client.get_collection(collection_name=resolved_collection)
        vector_count = getattr(collection_info, "vectors_count", None)
        if vector_count is None:
            vector_count = getattr(collection_info, "points_count", None)
    except Exception:
        vector_count = None

    if vector_count is None:
        try:
            count_result = client.count(collection_name=resolved_collection, exact=True)
            vector_count = getattr(count_result, "count", 0)
        except Exception as exc:
            return {
                "status": "unavailable",
                "collection": resolved_collection,
                "vectors": None,
                "message": f"Qdrant vector count unavailable: {exc}",
            }

    try:
        vector_count = int(vector_count or 0)
    except (TypeError, ValueError) as exc:
        return {
            "status": "unavailable",
            "collection": resolved_collection,
            "vectors": None,
            "message": f"Qdrant vector count unavailable: {exc}",
        }

    if vector_count == 0:
        return {
            "status": "CRITICAL",
            "collection": resolved_collection,
            "vectors": 0,
            "message": "Collection is empty - ingestion required",
        }

    return {
        "status": "healthy",
        "collection": resolved_collection,
        "vectors": vector_count,
    }

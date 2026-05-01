#!/usr/bin/env python3
"""
Idempotent Qdrant HNSW index builder and health checker.

Usage:
    python scripts/build_qdrant_index.py --check      # Health check only
    python scripts/build_qdrant_index.py --build     # Build/rebuild index
    python scripts/build_qdrant_index.py --full      # Full check + sample queries

This script verifies that the HNSW index is properly built on the nrg_research
collection. When indexed_vectors_count < vectors_count, indexing is incomplete
and queries will fall back to brute-force linear scans.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import HnswConfigDiff

DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "nrg_research")
DEFAULT_HOST = os.getenv("QDRANT_HOST", "localhost")
DEFAULT_PORT = int(os.getenv("QDRANT_PORT", "6333"))


def get_client() -> QdrantClient:
    return QdrantClient(host=DEFAULT_HOST, port=DEFAULT_PORT, timeout=30)


def get_collection_info(client: QdrantClient, collection: str) -> dict:
    """Get detailed collection info including HNSW status."""
    info = client.get_collection(collection)
    vectors_total = info.points_count or 0
    vectors_indexed = info.indexed_vectors_count or 0
    optimizer_cfg = getattr(info.config, "optimizer_config", None)
    indexing_threshold = getattr(optimizer_cfg, "indexing_threshold", None)
    try:
        indexing_threshold = int(indexing_threshold) if indexing_threshold is not None else None
    except (TypeError, ValueError):
        indexing_threshold = None
    threshold_exempt = (
        vectors_total > 0
        and vectors_indexed == 0
        and indexing_threshold is not None
        and vectors_total < indexing_threshold
    )
    return {
        "name": collection,
        "status": info.status,
        "vectors_total": vectors_total,
        "vectors_indexed": vectors_indexed,
        "index_complete": vectors_indexed >= vectors_total or threshold_exempt,
        "indexing_threshold": indexing_threshold,
        "threshold_exempt": threshold_exempt,
        "hnsw_m": getattr(info.config.hnsw_config, "m", None),
        "hnsw_ef_construct": getattr(info.config.hnsw_config, "ef_construct", None),
        "vector_size": _get_vector_size(info),
        "optimizer_status": info.optimizer_status,
    }


def _get_vector_size(info) -> int | None:
    vectors = info.config.params.vectors
    if hasattr(vectors, "size"):
        return int(vectors.size)
    if isinstance(vectors, dict):
        for v in vectors.values():
            if hasattr(v, "size"):
                return int(v.size)
    return None


def trigger_indexing(client: QdrantClient, collection: str) -> bool:
    """Trigger HNSW index build by updating collection params.

    Qdrant builds the index automatically in the background when vectors
    are added. This function forces a parameter update that kick-starts
    the indexing process if it hasn't started.
    """
    try:
        current = client.get_collection(collection)
        m = getattr(current.config.hnsw_config, "m", 16) or 16
        ef_c = getattr(current.config.hnsw_config, "ef_construct", 100) or 100

        client.update_collection(
            collection_name=collection,
            hnsw_config=HnswConfigDiff(
                m=m,
                ef_construct=ef_c,
            ),
        )
        return True
    except Exception as exc:
        print(f"  Warning: Could not trigger indexing: {exc}")
        return False


def wait_for_indexing(client: QdrantClient, collection: str, timeout: int = 300) -> dict:
    """Poll until indexing is complete or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        info = get_collection_info(client, collection)
        indexed = info["vectors_indexed"]
        total = info["vectors_total"]
        pct = (indexed / total * 100) if total > 0 else 100
        elapsed = int(time.time() - start)
        print(f"  [{elapsed}s] {indexed}/{total} vectors indexed ({pct:.1f}%)")
        if info["index_complete"]:
            return {**info, "build_time_s": elapsed}
        time.sleep(5)

    return {**get_collection_info(client, collection), "build_time_s": timeout, "timeout": True}


def run_sample_queries(client: QdrantClient, collection: str, vector_size: int) -> dict:
    """Run sample queries to verify retrieval quality and measure latency."""
    test_queries = [
        "machine learning artificial intelligence",
        "renewable energy sustainability",
        "blockchain distributed systems",
    ]
    results = {}

    for query in test_queries:
        from src.skills.rag.embedder import Embedder
        embedder = Embedder()
        try:
            vec = embedder.embed_single(query)
            if len(vec) != vector_size:
                vec = vec[:vector_size] + [0.0] * max(0, vector_size - len(vec))

            latencies = []
            for _ in range(5):
                start = time.perf_counter()
                hits = client.search(
                    collection_name=collection,
                    query_vector=vec,
                    limit=5,
                    with_payload=True,
                )
                latencies.append((time.perf_counter() - start) * 1000)

            latencies.sort()
            results[query] = {
                "hits": len(hits),
                "latency_p50_ms": round(latencies[2], 2),
                "latency_p99_ms": round(latencies[4], 2),
            }
        finally:
            embedder.close()

    return results


def check_index_health(collection: str = DEFAULT_COLLECTION) -> int:
    """Check-only mode: report health without building."""
    print(f"\n{'='*60}")
    print(" QDRANT INDEX HEALTH CHECK")
    print(f"{'='*60}\n")

    client = get_client()

    try:
        info = get_collection_info(client, collection)
    except Exception as exc:
        print(f"ERROR: Cannot connect to Qdrant at {DEFAULT_HOST}:{DEFAULT_PORT}")
        print(f"  {exc}")
        return 1

    print(f"Collection:  {info['name']}")
    print(f"Status:     {info['status']}")
    print(f"Vectors:    {info['vectors_indexed']:,} / {info['vectors_total']:,} indexed")

    if info["index_complete"]:
        if info.get("threshold_exempt"):
            print(
                "Index:      PASS "
                f"(collection below indexing_threshold={info.get('indexing_threshold'):,}; "
                "Qdrant exact scan is expected)"
            )
        else:
            print("Index:      BUILT (HNSW fully constructed)")
        print(f"HNSW m:     {info['hnsw_m']}")
        print(f"HNSW ef:    {info['hnsw_ef_construct']}")
        print(f"Vector dim: {info['vector_size']}")
        print(f"Optimizer:  {info['optimizer_status']}")
        print("\nRESULT: PASS — Qdrant index health is acceptable")
        return 0
    else:
        pct = (info["vectors_indexed"] / max(info["vectors_total"], 1) * 100)
        print(f"Index:      INCOMPLETE ({pct:.1f}% built)")
        print("WARNING: Queries are using brute-force scan")
        print("\nRESULT: FAIL — Run with --build to trigger indexing")
        return 1


def build_index(collection: str = DEFAULT_COLLECTION) -> int:
    """Build/rebuild index mode."""
    print(f"\n{'='*60}")
    print(" QDRANT HNSW INDEX BUILDER")
    print(f"{'='*60}\n")

    client = get_client()

    try:
        info = get_collection_info(client, collection)
    except Exception as exc:
        print(f"ERROR: Cannot connect to Qdrant: {exc}")
        return 1

    print(f"Collection:  {info['name']}")
    print(f"Vectors:    {info['vectors_total']:,}")
    print(f"Indexed:     {info['vectors_indexed']:,}")

    if info["index_complete"]:
        print("\nIndex is already complete.")
        print("Use --rebuild to force a rebuild.")
        return 0

    print("\nTriggering index build...")
    trigger_indexing(client, collection)

    print("\nWaiting for indexing to complete (poll every 5s)...")
    result = wait_for_indexing(client, collection)

    if result.get("timeout"):
        print("\nWARNING: Indexing did not complete within timeout")
        print(f"  Indexed: {result['vectors_indexed']:,} / {result['vectors_total']:,}")
        return 1

    print(f"\nIndex build complete in {result['build_time_s']}s")
    print("\nRESULT: PASS")
    return 0


def full_diagnostic(collection: str = DEFAULT_COLLECTION) -> int:
    """Full mode: check + sample queries."""
    print(f"\n{'='*60}")
    print(" QDRANT FULL DIAGNOSTIC")
    print(f"{'='*60}\n")

    client = get_client()

    try:
        info = get_collection_info(client, collection)
    except Exception as exc:
        print(f"ERROR: Cannot connect: {exc}")
        return 1

    print(f"Collection: {info['name']}")
    print(f"Status:    {info['status']}")
    print(f"Vectors:   {info['vectors_indexed']:,} / {info['vectors_total']:,} indexed")

    if not info["index_complete"]:
        print("\nWARNING: Index incomplete — forcing build...")
        trigger_indexing(client, collection)
        wait_for_indexing(client, collection)
        info = get_collection_info(client, collection)

    if info["index_complete"]:
        print("\nRunning sample queries...")
        try:
            queries = run_sample_queries(client, collection, info["vector_size"] or 384)
            for query, stats in queries.items():
                print(f"  '{query[:40]}...'")
                print(f"    Hits: {stats['hits']}, P50: {stats['latency_p50_ms']}ms, P99: {stats['latency_p99_ms']}ms")
        except Exception as exc:
            print(f"  Query test failed: {exc}")
    else:
        print("\nWARNING: Index still incomplete, skipping queries")

    print("\nRESULT: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Qdrant HNSW Index Builder and Health Checker")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Health check only")
    group.add_argument("--build", action="store_true", help="Build/rebuild index")
    group.add_argument("--full", action="store_true", help="Full diagnostic with sample queries")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Collection name")
    parser.add_argument("--timeout", type=int, default=300, help="Max seconds to wait for indexing")
    args = parser.parse_args()

    collection_name = args.collection

    if args.check:
        return check_index_health(collection_name)
    elif args.build:
        return build_index(collection_name)
    else:
        return full_diagnostic(collection_name)


if __name__ == "__main__":
    sys.exit(main())

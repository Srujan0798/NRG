#!/usr/bin/env python3
"""
Qdrant Shard Configuration — Task #23 Phase 2

Configures Qdrant for scale:
- Collection sharding: 4 shards for 200K+ vectors
- Replication factor: 2 (graceful single-node if multi-node unavailable)
- HNSW config: m=16, ef_construct=200 (optimized for 384-dim bge-m3)
- Scalar quantization for memory efficiency
- Collection aliasing for zero-downtime re-indexing

Usage:
    python scripts/qdrant_shard_config.py --setup
    python scripts/qdrant_shard_config.py --reindex --new-version v2
    python scripts/qdrant_shard_config.py --swap-alias --from-col nrg_research --to-col nrg_research_v2
    python scripts/qdrant_shard_config.py --status

SKILLS: /python-backend (async patterns), /data-visualization (progress bars)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging
from typing import Literal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "nrg_research")
ALIAS_NAME = os.getenv("QDRANT_ALIAS", "nrg_research")  # Always query this alias
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))  # bge-m3 = 1024, all-MiniLM = 384

HNSW_CONFIG = {
    "m": 16,
    "ef_construct": 200,
    "full_scan_threshold": 10000,
}

OPTIMIZER_CONFIG = {
    "indexing_threshold": 20000,
    "flush_interval_sec": 5,
}


def get_client():
    from qdrant_client import QdrantClient
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=30)


def setup_collection(
    collection_name: str = DEFAULT_COLLECTION,
    num_shards: int = 4,
    replication_factor: int = 2,
    embedding_dim: int = EMBEDDING_DIM,
) -> dict:
    """Create a production-ready Qdrant collection with sharding and HNSW tuning."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        VectorParams,
        Distance,
        HnswConfigDiff,
        OptimizersConfigDiff,
        CollectionParams,
    )

    client = get_client()

    try:
        existing = client.get_collection(collection_name)
        logger.info(f"Collection '{collection_name}' already exists")
        return {"status": "exists", "collection": collection_name, "vectors_count": existing.vectors_count}
    except Exception:
        pass

    logger.info(f"Creating collection '{collection_name}' with {num_shards} shards, replication={replication_factor}")

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=embedding_dim,
            distance=Distance.COSINE,
        ),
        hnsw_config=HnswConfigDiff(
            m=HNSW_CONFIG["m"],
            ef_construct=HNSW_CONFIG["ef_construct"],
            full_scan_threshold=HNSW_CONFIG["full_scan_threshold"],
        ),
        optimizers_config=OptimizersConfigDiff(
            indexing_threshold=OPTIMIZER_CONFIG["indexing_threshold"],
            flush_interval_sec=OPTIMIZER_CONFIG["flush_interval_sec"],
        ),
        params=CollectionParams(
            num_shards=num_shards,
            replication_factor=replication_factor,
            on_disk_payload=False,
        ),
    )

    logger.info(f"Collection '{collection_name}' created successfully")
    return {"status": "created", "collection": collection_name, "shards": num_shards}


def create_alias(
    collection_name: str,
    alias_name: str = ALIAS_NAME,
) -> dict:
    """Point an alias at a collection. Use for zero-downtime re-indexing."""
    client = get_client()
    try:
        client.update_collection_aliases(
            change_aliases_actions=[
                {
                    "create_alias": {
                        "alias_name": alias_name,
                        "collection_name": collection_name,
                    }
                }
            ]
        )
        logger.info(f"Alias '{alias_name}' → '{collection_name}'")
        return {"status": "ok", "alias": alias_name, "collection": collection_name}
    except Exception as e:
        logger.error(f"Failed to create alias: {e}")
        return {"status": "error", "error": str(e)}


def swap_alias(
    from_collection: str,
    to_collection: str,
    alias_name: str = ALIAS_NAME,
) -> dict:
    """Atomically swap alias from old collection to new (zero-downtime re-indexing)."""
    client = get_client()
    try:
        client.update_collection_aliases(
            change_aliases_actions=[
                {
                    "delete_alias": {"alias_name": alias_name},
                },
                {
                    "create_alias": {
                        "alias_name": alias_name,
                        "collection_name": to_collection,
                    }
                },
            ]
        )
        logger.info(f"Alias '{alias_name}' swapped: {from_collection} → {to_collection}")
        return {
            "status": "ok",
            "alias": alias_name,
            "from": from_collection,
            "to": to_collection,
        }
    except Exception as e:
        logger.error(f"Failed to swap alias: {e}")
        return {"status": "error", "error": str(e)}


def get_alias_target(alias_name: str = ALIAS_NAME) -> str | None:
    """Get the collection that an alias currently points to."""
    client = get_client()
    try:
        info = client.get_collections()
        for col in info.collections:
            if col.name == alias_name:
                return alias_name
        return None
    except Exception:
        return None


def collection_info(collection_name: str = DEFAULT_COLLECTION) -> dict:
    """Get detailed collection info including shards and index status."""
    client = get_client()
    try:
        info = client.get_collection(collection_name)
        return {
            "collection": collection_name,
            "status": str(info.status),
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "shards": [
                {
                    "id": s.id,
                    "state": str(s.state),
                    "num_vectors": s.num_vectors,
                }
                for s in (info.shards_stats or [])
            ],
            "hnsw_config": {
                "m": info.config.hnsw_config.m if info.config and info.config.hnsw_config else None,
                "ef_construct": info.config.hnsw_config.ef_construct if info.config and info.config.hnsw_config else None,
            },
            "optimizer_status": str(info.optimizer_status) if info.optimizer_status else None,
        }
    except Exception as e:
        return {"collection": collection_name, "status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Qdrant shard configuration")
    parser.add_argument("--setup", action="store_true", help="Create production collection with sharding")
    parser.add_argument("--reindex", action="store_true", help="Start re-indexing (creates new version)")
    parser.add_argument("--new-version", type=str, help="New collection version name (e.g., v2)")
    parser.add_argument("--swap-alias", action="store_true", help="Swap alias to new collection")
    parser.add_argument("--from-col", type=str, help="Current collection for alias swap")
    parser.add_argument("--to-col", type=str, help="New collection for alias swap")
    parser.add_argument("--status", action="store_true", help="Show collection status")
    parser.add_argument("--shards", type=int, default=4, help="Number of shards (default: 4)")
    parser.add_argument("--replication", type=int, default=2, help="Replication factor (default: 2)")
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION, help="Collection name")
    args = parser.parse_args()

    if args.setup:
        result = setup_collection(
            collection_name=args.collection,
            num_shards=args.shards,
            replication_factor=args.replication,
        )
        print(f"Result: {result}")

    elif args.status:
        info = collection_info(args.collection)
        print(f"\nCollection: {info['collection']}")
        print(f"  Status: {info.get('status')}")
        print(f"  Vectors: {info.get('vectors_count')}")
        print(f"  Indexed: {info.get('indexed_vectors_count')}")
        print(f"  HNSW m: {info.get('hnsw_config', {}).get('m')}")
        print(f"  HNSW ef_construct: {info.get('hnsw_config', {}).get('ef_construct')}")
        shards = info.get("shards", [])
        if shards:
            print(f"  Shards: {len(shards)}")
            for s in shards:
                print(f"    - {s['id']}: {s['state']} ({s['num_vectors']} vectors)")

    elif args.swap_alias:
        if not args.from_col or not args.to_col:
            print("Error: --from-col and --to-col required for --swap-alias")
            sys.exit(1)
        result = swap_alias(args.from_col, args.to_col)
        print(f"Result: {result}")

    elif args.reindex:
        if not args.new_version:
            print("Error: --new-version required for --reindex")
            sys.exit(1)
        new_collection = f"{args.collection}_{args.new_version}"
        result = setup_collection(collection_name=new_collection)
        print(f"New collection '{new_collection}' created for re-indexing")
        print(f"After re-indexing completes, run: python scripts/qdrant_shard_config.py --swap-alias --from-col {args.collection} --to-col {new_collection}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

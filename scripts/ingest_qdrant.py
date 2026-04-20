#!/usr/bin/env python3
"""
Ingest 3,310 research documents into Qdrant.

Source: /Users/srujansai/Desktop/NRG DB/National_Research_Database/Research_Documents/
Each .txt file has YAML frontmatter followed by full text.

Process:
1. Parse frontmatter + body from each .txt
2. Chunk body into 512-token chunks with 50-token overlap
3. Embed chunks with bge-m3 (1024-dim)
4. Upsert to Qdrant with metadata for RBAC filtering
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

import yaml
from tqdm import tqdm

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.skills.rag.embedder import Embedder, SemanticChunker
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)

DEFAULT_SOURCE_DIR = "/Users/srujansai/Desktop/NRG DB/National_Research_Database/Research_Documents"
DEFAULT_COLLECTION = "nrg_research"
DEFAULT_BATCH_SIZE = 100
CHUNK_MAX_TOKENS = 512
CHUNK_STRIDE = 50


def parse_document_txt(path: Path) -> dict[str, Any] | None:
    """Parse a .txt file with YAML frontmatter and markdown body."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Failed to read %s: %s", path, exc)
        return None

    if not text.startswith("---"):
        logger.warning("No YAML frontmatter in %s", path)
        return None

    parts = text.split("---", 2)
    if len(parts) < 3:
        logger.warning("Malformed frontmatter in %s", path)
        return None

    try:
        frontmatter = yaml.safe_load(parts[1])
    except Exception as exc:
        logger.warning("YAML parse error in %s: %s", path, exc)
        return None

    body = parts[2].strip()
    return {
        "document_id": frontmatter.get("document_id", path.stem),
        "title": frontmatter.get("title", ""),
        "researcher_ids": frontmatter.get("researcher_ids", []),
        "affiliation": frontmatter.get("affiliation", ""),
        "publication_year": frontmatter.get("publication_year", ""),
        "abstract": frontmatter.get("abstract", ""),
        "keywords": frontmatter.get("keywords", []),
        "research_area_tags": frontmatter.get("research_area_tags", []),
        "access_tier": frontmatter.get("access_tier", "Tier3"),
        "body": body,
    }


def access_tier_to_int(tier: str | int) -> int:
    """Convert tier string like 'Tier1' to integer."""
    if isinstance(tier, int):
        return tier
    mapping = {"Tier1": 1, "Tier2": 2, "Tier3": 3}
    return mapping.get(str(tier), 3)


def discover_txt_files(source_dir: Path) -> list[Path]:
    """Discover all .txt files in source directory, sorted."""
    files = sorted(source_dir.glob("*.txt"), key=lambda p: p.name)
    return files


def load_prebuilt_payload(path: Path) -> list[dict[str, Any]]:
    """Load pre-built Qdrant payload JSON."""
    import json

    logger.info("Loading pre-built payload from %s", path)
    data = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for entry in data:
        meta = entry.get("metadata", {})
        payload = entry.get("payload", {})
        records.append(
            {
                "document_id": meta.get("document_id", entry.get("id", "")),
                "title": meta.get("title", ""),
                "researcher_ids": meta.get("researcher_ids", []),
                "affiliation": meta.get("affiliation", ""),
                "publication_year": meta.get("publication_year", ""),
                "abstract": meta.get("abstract", payload.get("abstract", "")),
                "keywords": meta.get("keywords", []),
                "research_area_tags": meta.get("research_area_tags", []),
                "access_tier": meta.get("access_tier", "Tier3"),
                "body": payload.get("full_text", payload.get("abstract", "")),
            }
        )
    return records


def ensure_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    distance: Distance = Distance.COSINE,
) -> None:
    """Create or recreate Qdrant collection with correct vector size."""
    collections = [c.name for c in client.get_collections().collections]
    if collection_name in collections:
        info = client.get_collection(collection_name)
        existing_size = info.config.params.vectors.size  # type: ignore[union-attr]
        if existing_size != vector_size:
            logger.warning(
                "Collection %s exists with vector size %d, expected %d. Recreating...",
                collection_name,
                existing_size,
                vector_size,
            )
            client.delete_collection(collection_name)
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance),
            )
        else:
            logger.info("Collection %s already exists with correct vector size.", collection_name)
    else:
        logger.info("Creating collection %s with vector size %d", collection_name, vector_size)
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest research documents into Qdrant")
    parser.add_argument("--source-dir", type=Path, default=Path(DEFAULT_SOURCE_DIR))
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--qdrant-host", default=os.getenv("QDRANT_HOST", "localhost"))
    parser.add_argument("--qdrant-port", type=int, default=int(os.getenv("QDRANT_PORT", "6333")))
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--limit", type=int, default=0, help="Limit number of documents to process (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="Parse and chunk but do not upsert")
    parser.add_argument("--use-prebuilt", type=Path, default=None, help="Path to pre-built payload JSON")
    parser.add_argument("--recreate", action="store_true", help="Delete and recreate collection")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Initialize embedder and chunker
    logger.info("Loading embedding model...")
    embedder = Embedder()
    vector_size = embedder.get_dimension()
    logger.info("Embedding model ready: %s (dim=%d)", embedder.model_name, vector_size)

    chunker = SemanticChunker(max_tokens=CHUNK_MAX_TOKENS, stride=CHUNK_STRIDE)

    # Initialize Qdrant
    client = QdrantClient(host=args.qdrant_host, port=args.qdrant_port)

    if args.recreate:
        logger.warning("Deleting collection %s...", args.collection)
        client.delete_collection(args.collection)

    ensure_collection(client, args.collection, vector_size)

    # Load documents
    if args.use_prebuilt:
        documents = load_prebuilt_payload(args.use_prebuilt)
    else:
        txt_files = discover_txt_files(args.source_dir)
        if args.limit > 0:
            txt_files = txt_files[: args.limit]
        logger.info("Found %d .txt files to process", len(txt_files))
        documents = []
        for path in tqdm(txt_files, desc="Parsing documents"):
            doc = parse_document_txt(path)
            if doc:
                documents.append(doc)
        logger.info("Successfully parsed %d documents", len(documents))

    if args.limit > 0 and len(documents) > args.limit:
        documents = documents[: args.limit]

    # Process: chunk, embed, collect points
    all_points: list[PointStruct] = []
    total_chunks = 0

    for doc in tqdm(documents, desc="Chunking & embedding"):
        body = doc["body"]
        if not body:
            continue

        chunks = chunker.chunk_text(body)
        if not chunks:
            continue

        # Also prepend abstract to first chunk for better context
        if doc.get("abstract"):
            chunks[0] = f"{doc['abstract']}\n\n{chunks[0]}"

        embeddings = embedder.embed(chunks)
        total_chunks += len(chunks)

        for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = f"{doc['document_id']}_{idx}"
            payload = {
                "document_id": doc["document_id"],
                "chunk_index": idx,
                "title": doc["title"],
                "researcher_ids": doc.get("researcher_ids", []),
                "affiliation": doc.get("affiliation", ""),
                "publication_year": doc.get("publication_year", ""),
                "research_area_tags": doc.get("research_area_tags", []),
                "keywords": doc.get("keywords", []),
                "access_tier": access_tier_to_int(doc.get("access_tier", "Tier3")),
                "text": chunk_text,
            }
            all_points.append(
                PointStruct(id=point_id, vector=embedding, payload=payload)
            )

    logger.info(
        "Prepared %d points from %d documents (%d chunks)",
        len(all_points),
        len(documents),
        total_chunks,
    )

    if args.dry_run:
        logger.info("DRY RUN: Would upsert %d points to %s", len(all_points), args.collection)
        for p in all_points[:3]:
            logger.info("Sample point: id=%s payload_keys=%s vector_dim=%d", p.id, list(p.payload.keys()), len(p.vector))
        return

    # Batch upsert
    batch_size = args.batch_size
    for i in tqdm(range(0, len(all_points), batch_size), desc="Upserting to Qdrant"):
        batch = all_points[i : i + batch_size]
        client.upsert(collection_name=args.collection, points=batch)

    # Verify
    info = client.get_collection(args.collection)
    logger.info(
        "Ingest complete. Collection %s now has %d points.",
        args.collection,
        info.points_count,
    )


if __name__ == "__main__":
    main()

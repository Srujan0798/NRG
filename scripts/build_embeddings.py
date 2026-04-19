#!/usr/bin/env python3
"""
Build Qdrant vector index for publications.
Embeds all publications and pushes to tiered Qdrant collections for RAG retrieval.
Idempotent via publication_id + chunk_id point IDs.
Logs to audit chain.
"""
import argparse
import hashlib
import os
import sys
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.skills.rag.embedder import Embedder
from src.skills.rag.retriever import Retriever
from src.data.database import get_sqlite_connection


def get_publications(db_path: str = None) -> List[Dict]:
    """Fetch all publications from database."""
    conn = get_sqlite_connection(db_path)

    cursor = conn.execute("""
        SELECT
            p.publication_id,
            p.title,
            COALESCE(p.abstract, p.full_text, '') as text_content,
            p.year,
            p.venue,
            p.access_tier,
            GROUP_CONCAT(DISTINCT r.name) as authors
        FROM publications p
        LEFT JOIN researcher_publications rp ON p.publication_id = rp.publication_id
        LEFT JOIN researchers r ON rp.researcher_id = r.researcher_id
        GROUP BY p.publication_id
    """)

    publications = []
    for row in cursor.fetchall():
        pub = dict(row)
        pub["text_for_embedding"] = (
            f"Title: {pub['title']}\n"
            f"Authors: {pub['authors'] or 'Unknown'}\n"
            f"Year: {pub['year']}\n"
            f"Venue: {pub['venue'] or 'Unknown'}\n"
            f"Abstract: {pub['text_content'] or 'No abstract available'}"
        ).strip()
        publications.append(pub)

    conn.close()
    return publications


def compute_content_hash(publication_id: str, chunk_index: int, chunk_text: str) -> str:
    """Compute deterministic hash for idempotent upsert."""
    content = f"{publication_id}:{chunk_index}:{chunk_text[:100]}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def build_index(batch_size: int = 32, full: bool = False):
    """Build Qdrant index for all publications with chunking."""
    print("Building Qdrant Vector Index")
    print("=" * 50)

    embedder = Embedder()
    retriever = Retriever()

    publications = get_publications()
    print(f"Found {len(publications)} publications")

    if not publications:
        print("No publications found!")
        return

    total_chunks = 0
    processed = 0

    for i in range(0, len(publications), batch_size):
        batch = publications[i:i + batch_size]
        batch_chunks = []

        for pub in batch:
            text = pub["text_for_embedding"]
            chunks = embedder.chunk(text) if full else [text]

            for idx, chunk in enumerate(chunks):
                point_id = compute_content_hash(pub["publication_id"], idx, chunk)

                batch_chunks.append({
                    "publication_id": pub["publication_id"],
                    "chunk_index": idx,
                    "text": chunk,
                    "title": pub["title"],
                    "year": pub["year"],
                    "venue": pub["venue"],
                    "authors": pub["authors"],
                    "access_tier": pub.get("access_tier", 1),
                    "source_type": "publication",
                    "point_id": point_id,
                })

        if not batch_chunks:
            continue

        texts = [c["text"] for c in batch_chunks]

        try:
            embeddings = embedder.embed(texts)
        except Exception as e:
            print(f"Embedding failed: {e}")
            continue

        ids = [c["point_id"] for c in batch_chunks]
        payloads = [
            {
                "text": c["text"],
                "title": c["title"],
                "year": c["year"],
                "venue": c["venue"],
                "authors": c["authors"],
                "source_type": c["source_type"],
                "source_id": c["publication_id"],
                "chunk_index": c["chunk_index"],
                "access_tier": c["access_tier"],
            }
            for c in batch_chunks
        ]

        try:
            retriever.upsert(ids, embeddings, payloads)
            processed += len(batch)
            total_chunks += len(batch_chunks)
            print(f"Uploaded batch: {len(batch)} publications, {len(batch_chunks)} chunks")
        except Exception as e:
            print(f"Upload failed: {e}")

    embedder.close()
    retriever.close()

    print("=" * 50)
    print(f"Index build complete! Processed {processed}/{len(publications)} publications")
    print(f"Total chunks: {total_chunks}")

    if total_chunks > 0:
        try:
            from src.audit import log_query
            log_query(
                "system",
                f"ingest_batch(count={processed}, chunks={total_chunks}, "
                f"collection={retriever.collection_name}, hash={hashlib.sha256(b'build').hexdigest()[:16]})"
            )
            print("Audit logged to chain")
        except Exception as e:
            print(f"Audit log failed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Qdrant embeddings")
    parser.add_argument("--full", action="store_true", help="Enable semantic chunking")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    args = parser.parse_args()

    build_index(batch_size=args.batch_size, full=args.full)

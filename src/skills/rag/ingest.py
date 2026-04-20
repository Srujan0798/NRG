"""Batch ingestion pipeline from SQLite publications to Qdrant."""

from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Any

from src.audit import get_audit_log, AuditEvent
from src.data.database import get_sqlite_connection
from src.skills.rag.embedder import Embedder
from src.skills.rag.retriever import Retriever

logger = logging.getLogger(__name__)


def ingest_publications(limit: int | None = None, batch_size: int = 64) -> dict[str, Any]:
    """Read publications, chunk abstracts/full text, embed, and upsert to Qdrant."""
    embedder = Embedder()
    retriever = Retriever()
    total_chunks = 0
    total_publications = 0

    try:
        for publication_batch in _publication_batches(limit=limit, batch_size=batch_size):
            ids: list[str] = []
            texts: list[str] = []
            payloads: list[dict[str, Any]] = []

            for publication in publication_batch:
                text = (
                    publication.get("full_text")
                    or publication.get("full_text_uri")
                    or publication.get("abstract")
                    or publication.get("title")
                    or ""
                )
                if not text:
                    continue

                chunks = embedder.chunk(str(text)) or [str(text)]
                total_publications += 1
                for index, chunk in enumerate(chunks):
                    point_id = _point_id(str(publication["publication_id"]), index)
                    ids.append(point_id)
                    texts.append(chunk)
                    payloads.append(
                        {
                            "publication_id": publication["publication_id"],
                            "chunk_id": f"ch_{index}",
                            "chunk_text": chunk,
                            "title": publication.get("title"),
                            "year": publication.get("year"),
                            "access_tier": int(publication.get("access_tier") or 1),
                            "source_id": publication["publication_id"],
                            "source_type": "publication",
                        }
                    )

            if not texts:
                continue

            embeddings = embedder.embed(texts)
            retriever.upsert(ids, embeddings, payloads)
            total_chunks += len(texts)
            _audit_ingest(len(texts), retriever.collection_name, payloads)

        return {
            "publications": total_publications,
            "chunks": total_chunks,
            "collection": retriever.collection_name,
        }
    finally:
        embedder.close()
        retriever.close()


def _publication_batches(limit: int | None, batch_size: int):
    conn = get_sqlite_connection()
    try:
        sql = "SELECT * FROM publications ORDER BY publication_id"
        params: list[Any] = []
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        rows = [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()

    for start in range(0, len(rows), batch_size):
        yield rows[start : start + batch_size]


def _point_id(publication_id: str, chunk_index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"nrg:{publication_id}:{chunk_index}"))


def _audit_ingest(count: int, collection: str, payloads: list[dict[str, Any]]) -> None:
    digest = hashlib.sha256(repr(payloads).encode()).hexdigest()
    try:
        get_audit_log().append(
            AuditEvent(
                event_type="ingest_batch",
                user_id="system",
                result={"count": count, "collection": collection, "sha256": digest},
            )
        )
    except Exception:
        logger.warning("Failed to audit ingest batch", exc_info=True)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Ingest publications into Qdrant")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    print(json.dumps(ingest_publications(limit=args.limit, batch_size=args.batch_size), indent=2))

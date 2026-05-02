"""Batch ingestion pipeline from SQLite publications to Qdrant."""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, UTC
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
                            "chunk_index": index,
                            "chunk_id": f"ch_{index}",
                            "chunk_text": chunk,
                            "title": publication.get("title"),
                            "year": publication.get("year"),
                            "access_tier": int(publication.get("access_tier") or 1),
                            "source_id": publication["publication_id"],
                            "source_type": "publication",
                            "content_sha256": hashlib.sha256(chunk.encode()).hexdigest(),
                            "indexed_at": datetime.now(UTC).isoformat(),
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


def ingest_documents(
    documents: list[dict[str, Any]],
    *,
    embedder: Embedder | None = None,
    retriever: Retriever | None = None,
) -> dict[str, Any]:
    """Embed and upsert newly supplied documents into the vector store.

    This path is intentionally small and testable: callers pass new documents,
    every non-empty chunk is embedded, and deterministic point IDs make repeated
    ingests idempotent while still updating changed payloads in Qdrant.
    """
    owns_embedder = embedder is None
    owns_retriever = retriever is None
    active_embedder = embedder or Embedder()
    active_retriever = retriever or Retriever()

    ids: list[str] = []
    texts: list[str] = []
    payloads: list[dict[str, Any]] = []
    docs_seen = 0

    try:
        for document in documents:
            document_id = str(
                document.get("document_id")
                or document.get("publication_id")
                or document.get("source_id")
                or uuid.uuid5(uuid.NAMESPACE_URL, repr(document))
            )
            text = str(
                document.get("full_text")
                or document.get("content")
                or document.get("abstract")
                or document.get("title")
                or ""
            ).strip()
            if not text:
                continue
            docs_seen += 1
            chunks = active_embedder.chunk(text) or [text]
            for index, chunk in enumerate(chunks):
                ids.append(_point_id(document_id, index))
                texts.append(chunk)
                payloads.append(
                    {
                        "document_id": document_id,
                        "publication_id": document.get("publication_id"),
                        "chunk_index": index,
                        "chunk_id": f"ch_{index}",
                        "chunk_text": chunk,
                        "title": document.get("title"),
                        "year": document.get("year"),
                        "access_tier": int(document.get("access_tier") or 1),
                        "source_id": document.get("source_id") or document_id,
                        "source_type": document.get("source_type") or "document",
                        "content_sha256": hashlib.sha256(chunk.encode()).hexdigest(),
                        "indexed_at": datetime.now(UTC).isoformat(),
                    }
                )

        if texts:
            embeddings = active_embedder.embed(texts)
            active_retriever.upsert(ids, embeddings, payloads)
            _audit_ingest(len(texts), active_retriever.collection_name, payloads)

        return {
            "documents": docs_seen,
            "chunks": len(texts),
            "vectors_upserted": len(texts),
            "collection": active_retriever.collection_name,
        }
    finally:
        if owns_embedder:
            active_embedder.close()
        if owns_retriever:
            active_retriever.close()


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

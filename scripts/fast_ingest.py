#!/usr/bin/env python3
"""Fast Qdrant ingestion using deterministic test embedder.

Populates the nrg_research collection with real publication data from SQLite,
using the test embedder to avoid downloading large models.
Run this for PoC demos where real embeddings aren't critical.
"""

import os
import sys
import json
import uuid

# Force test embedder mode
os.environ["PYTEST_CURRENT_TEST"] = "fast_ingest"

from src.data.database import get_sqlite_connection
from src.skills.rag.embedder import Embedder
from src.skills.rag.retriever import Retriever


def fast_ingest(limit: int | None = None):
    embedder = Embedder()
    retriever = Retriever()

    conn = get_sqlite_connection()
    rows = conn.execute(
        "SELECT publication_id, title, abstract, year, access_tier FROM publications ORDER BY publication_id LIMIT ?",
        (limit or 999999,),
    ).fetchall()
    conn.close()

    ids = []
    texts = []
    payloads = []

    for row in rows:
        pub_id, title, abstract, year, tier = row
        text = abstract or title or ""
        if not text:
            continue

        ids.append(str(uuid.uuid5(uuid.NAMESPACE_URL, f"nrg:{pub_id}")))
        texts.append(text[:1000])  # Limit chunk size
        payloads.append({
            "publication_id": str(pub_id),
            "chunk_id": "ch_0",
            "chunk_text": text[:1000],
            "title": title,
            "year": year,
            "access_tier": int(tier or 1),
            "source_id": str(pub_id),
            "source_type": "publication",
        })

    if not texts:
        return {"publications": 0, "chunks": 0}

    # Embed in batches to avoid memory issues
    batch_size = 64
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        all_embeddings.extend(embedder.embed(batch))

    retriever.upsert(ids, all_embeddings, payloads)
    embedder.close()
    retriever.close()

    return {"publications": len(rows), "chunks": len(texts), "collection": "nrg_research"}


if __name__ == "__main__":
    result = fast_ingest()
    print(json.dumps(result, indent=2))

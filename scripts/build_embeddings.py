#!/usr/bin/env python3
"""
Build Qdrant vector index for publications.
Embeds all publications and pushes to Qdrant for RAG retrieval.
"""

import os
import sys
import sqlite3
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.skills.rag.embedder import Embedder
from src.skills.rag.retriever import Retriever


def get_publications(db_path: str = "nrg_research.db") -> List[Dict]:
    """Fetch all publications from database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cursor = conn.execute("""
        SELECT
            p.publication_id,
            p.title,
            p.abstract,
            p.year,
            p.venue,
            GROUP_CONCAT(r.name) as authors
        FROM publications p
        LEFT JOIN researcher_publications rp ON p.publication_id = rp.publication_id
        LEFT JOIN researchers r ON rp.researcher_id = r.researcher_id
        GROUP BY p.publication_id
    """)

    publications = []
    for row in cursor.fetchall():
        pub = dict(row)
        # Create rich text for embedding
        pub['text_for_embedding'] = f"""
Title: {pub['title']}
Authors: {pub['authors'] or 'Unknown'}
Year: {pub['year']}
Venue: {pub['venue'] or 'Unknown'}
Abstract: {pub['abstract'] or 'No abstract available'}
""".strip()
        publications.append(pub)

    conn.close()
    return publications


def build_index(batch_size: int = 32):
    """Build Qdrant index for all publications."""
    print("🔧 Building Qdrant Vector Index")
    print("=" * 50)

    # Initialize embedder and retriever
    print("📦 Loading embedding model...")
    embedder = Embedder()
    retriever = Retriever()

    # Get publications
    print("📚 Fetching publications from database...")
    publications = get_publications()
    print(f"✅ Found {len(publications)} publications")

    if not publications:
        print("❌ No publications found!")
        return

    # Process in batches
    total = len(publications)
    processed = 0

    for i in range(0, total, batch_size):
        batch = publications[i:i+batch_size]
        texts = [p['text_for_embedding'] for p in batch]
        ids = [p['publication_id'] for p in batch]

        # Generate embeddings
        print(f"  Embedding batch {i//batch_size + 1}/{(total-1)//batch_size + 1} ({len(batch)} items)...")
        try:
            embeddings = embedder.embed(texts)
        except Exception as e:
            print(f"  ❌ Embedding failed: {e}")
            continue

        # Prepare payloads
        payloads = []
        for pub in batch:
            payloads.append({
                "title": pub['title'],
                "year": pub['year'],
                "venue": pub['venue'],
                "authors": pub['authors'],
                "source_type": "publication",
                "access_tier": 1,  # All publications are tier 1
            })

        # Upload to Qdrant
        try:
            retriever.upsert(ids, embeddings, payloads)
            processed += len(batch)
            print(f"  ✅ Uploaded {len(batch)} vectors")
        except Exception as e:
            print(f"  ❌ Upload failed: {e}")

    embedder.close()
    retriever.close()

    print("=" * 50)
    print(f"🎉 Index build complete! Processed {processed}/{total} publications")

    # Test retrieval
    print("\n🧪 Testing retrieval...")
    retriever = Retriever()
    test_query = embedder.embed_single("machine learning research")
    results = retriever.retrieve(test_query, user_tier=1, top_k=3)
    print(f"✅ Test query returned {len(results.get('chunks', []))} results")
    retriever.close()


if __name__ == "__main__":
    build_index()

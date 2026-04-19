#!/usr/bin/env python3
"""
Generate embeddings from SQLite database and upload to Qdrant
"""

import json
import logging
import os
import sys
from pathlib import Path

from src.data.database import get_sqlite_connection

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_PATH = "nrg_research.db"


def get_db_connection():
    return get_sqlite_connection(DB_PATH)


def fetch_researchers(conn):
    cur = conn.execute("""
        SELECT researcher_id, name, institution_id, state, research_area, email, orcid
        FROM researchers
    """)
    rows = cur.fetchall()
    logger.info(f"Fetched {len(rows)} researchers")
    return [
        {
            "id": r[0],
            "name": r[1],
            "institution_id": r[2],
            "state": r[3],
            "research_area": r[4] or "",
            "email": r[5] or "",
            "orcid": r[6] or "",
            "entity_type": "researcher",
        }
        for r in rows
    ]


def fetch_publications(conn):
    cur = conn.execute("""
        SELECT publication_id, title, abstract, venue, year, doi
        FROM publications
    """)
    rows = cur.fetchall()
    logger.info(f"Fetched {len(rows)} publications")
    return [
        {
            "id": p[0],
            "title": p[1] or "",
            "abstract": p[2] or "",
            "venue": p[3] or "",
            "year": p[4] or 0,
            "doi": p[5] or "",
            "entity_type": "publication",
        }
        for p in rows
    ]


def fetch_labs(conn):
    cur = conn.execute("""
        SELECT lab_id, name, institution_id, research_area, website
        FROM labs
    """)
    rows = cur.fetchall()
    logger.info(f"Fetched {len(rows)} labs")
    return [
        {
            "id": l[0],
            "name": l[1],
            "institution_id": l[2],
            "research_area": l[3] or "",
            "website": l[4] or "",
            "entity_type": "lab",
        }
        for l in rows
    ]


def fetch_funding(conn):
    cur = conn.execute("""
        SELECT funding_id, title, agency, amount, start_date, researcher_id, institution_id
        FROM funding_records
    """)
    rows = cur.fetchall()
    logger.info(f"Fetched {len(rows)} funding records")
    return [
        {
            "id": f[0],
            "title": f[1] or "",
            "agency": f[2] or "",
            "amount": f[3] or 0,
            "start_date": f[4] or "",
            "researcher_id": f[5] or "",
            "institution_id": f[6] or "",
            "entity_type": "funding",
        }
        for f in rows
    ]


def create_text_representation(entity):
    """Create searchable text from entity data"""
    entity_type = entity["entity_type"]

    if entity_type == "researcher":
        return f"Researcher: {entity.get('name', '')}. Research Area: {entity.get('research_area', '')}. State: {entity.get('state', '')}."
    elif entity_type == "publication":
        return f"Publication: {entity.get('title', '')}. Abstract: {entity.get('abstract', '')}. Venue: {entity.get('venue', '')}."
    elif entity_type == "lab":
        return f"Lab: {entity.get('name', '')}. Research Area: {entity.get('research_area', '')}. Website: {entity.get('website', '')}."
    elif entity_type == "funding":
        return f"Funding: {entity.get('title', '')}. Agency: {entity.get('agency', '')}. Amount: {entity.get('amount', 0)}."
    return ""


def generate_embeddings(entities):
    """Generate embeddings using sentence-transformers"""
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

        texts = [create_text_representation(e) for e in entities]
        embeddings = model.encode(texts, show_progress_bar=True)

        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        sys.exit(1)


def upload_to_qdrant(entities, embeddings):
    """Upload entities and embeddings to Qdrant"""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import PointStruct

        client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
        )
        collection_name = os.getenv("QDRANT_COLLECTION", "nrg_research")

        points = []
        for i, entity in enumerate(entities):
            payload = {k: v for k, v in entity.items() if k != "id"}
            payload["text"] = create_text_representation(entity)

            point = PointStruct(id=i + 1, vector=embeddings[i], payload=payload)
            points.append(point)

        # Clear existing points and upload new ones
        client.upsert(collection_name=collection_name, points=points)

        logger.info(f"Uploaded {len(points)} points to Qdrant")
        return True

    except Exception as e:
        logger.error(f"Failed to upload to Qdrant: {e}")
        return False


def main():
    logger.info("Starting embedding generation from database")

    conn = get_db_connection()

    # Fetch all entities
    entities = []
    entities.extend(fetch_researchers(conn))
    entities.extend(fetch_publications(conn))
    entities.extend(fetch_labs(conn))
    entities.extend(fetch_funding(conn))

    conn.close()

    logger.info(f"Total entities: {len(entities)}")

    # Generate embeddings
    logger.info("Generating embeddings...")
    embeddings = generate_embeddings(entities)

    # Upload to Qdrant
    logger.info("Uploading to Qdrant...")
    if upload_to_qdrant(entities, embeddings):
        logger.info("SUCCESS: Embeddings uploaded to Qdrant")
    else:
        logger.error("FAILED: Could not upload to Qdrant")
        sys.exit(1)


if __name__ == "__main__":
    main()

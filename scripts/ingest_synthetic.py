"""Generate 1GB synthetic researcher data for Phase 1 PoC."""

import argparse
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

import numpy as np
from faker import Faker
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.skills.rag.embedder import Embedder


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fake = Faker(["en_IN", "en_US"])

RESEARCH_AREAS = [
    "Artificial Intelligence",
    "Machine Learning",
    "Robotics",
    "Computer Vision",
    "Natural Language Processing",
    "Data Science",
    "Cybersecurity",
    "Blockchain",
    "Internet of Things",
    "Quantum Computing",
    "Sustainable Energy",
    "Bioinformatics",
    "Materials Science",
    "Nanotechnology",
    "Aerospace",
    "Mechanical Engineering",
    "Electrical Engineering",
    "Civil Engineering",
    "Chemical Engineering",
    "Physics",
    "Chemistry",
    "Mathematics",
]

INSTITUTIONS = [
    ("IIT Gandhinagar", "Gujarat"),
    ("IIT Bombay", "Maharashtra"),
    ("IIT Delhi", "Delhi"),
    ("IIT Madras", "Tamil Nadu"),
    ("IIT Kharagpur", "West Bengal"),
    ("IIT Roorkee", "Uttarakhand"),
    ("IIT Kanpur", "Uttar Pradesh"),
    ("IIT Hyderabad", "Telangana"),
    ("NIT Trichy", "Tamil Nadu"),
    ("NIT Surathkal", "Karnataka"),
    ("IISc Bangalore", "Karnataka"),
    ("IIIT Hyderabad", "Telangana"),
]


def generate_researcher(i: int) -> dict:
    """Generate synthetic researcher profile."""
    institution, state = random.choice(INSTITUTIONS)
    area = random.choice(RESEARCH_AREAS)

    return {
        "source_id": f"res_{i:06d}",
        "source_type": "researcher",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": f"researcher{i}@{institution.lower().replace(' ', '')}.ac.in",
        "specialization": area,
        "topics": [area, random.choice(RESEARCH_AREAS)],
        "institution": institution,
        "state": state,
        "access_tier": random.choice([1, 2, 3]),
        "orcid": f"0000-0002-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
        "position": random.choice(
            ["Assistant Professor", "Associate Professor", "Professor", "PhD Scholar"]
        ),
        "bio": fake.paragraph(nb_sentences=3),
    }


def generate_publication(i: int) -> dict:
    """Generate synthetic publication."""
    area = random.choice(RESEARCH_AREAS)
    year = random.randint(2019, 2024)

    return {
        "source_id": f"pub_{i:06d}",
        "source_type": "publication",
        "title": f"Research on {area}: {fake.sentence(nb_words=8)}",
        "abstract": fake.paragraph(nb_sentences=5),
        "year": year,
        "journal": random.choice(
            ["Nature", "Science", "IEEE Transactions", "Springer", "Elsevier"]
        ),
        "authors": [fake.name() for _ in range(random.randint(2, 6))],
        "topics": [area, random.choice(RESEARCH_AREAS)],
        "access_tier": random.choice([1, 2, 3]),
        "citation_count": random.randint(0, 500),
        "doi": f"10.1000/{random.randint(100, 999)}.{random.randint(100, 999)}",
    }


def generate_lab(i: int) -> dict:
    """Generate synthetic lab."""
    institution, state = random.choice(INSTITUTIONS)
    area = random.choice(RESEARCH_AREAS)

    return {
        "source_id": f"lab_{i:06d}",
        "source_type": "lab",
        "name": f"{area} Lab",
        "acronym": f"{area[:3].upper()}{random.randint(10, 99)}",
        "research_area": area,
        "institution": institution,
        "head": fake.name(),
        "topics": [area],
        "access_tier": random.choice([1, 2, 3]),
        "description": fake.paragraph(nb_sentences=3),
    }


def main():
    parser = argparse.ArgumentParser(description="Generate and ingest synthetic data")
    parser.add_argument("--size", default="1gb", help="Target size (1gb)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--target-vectors", type=int, default=50000, help="Target vector count"
    )

    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    logger.info(f"Generating {args.target_vectors} synthetic records...")

    embedder = Embedder()
    dimension = embedder.get_dimension()

    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    client = QdrantClient(host=qdrant_host, port=qdrant_port)

    collection_name = os.getenv("QDRANT_COLLECTION", "nrg_research")

    try:
        client.delete_collection(collection_name)
        logger.info(f"Deleted existing collection: {collection_name}")
    except:
        pass

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
    )
    logger.info(f"Created collection: {collection_name}")

    all_records = []

    logger.info("Generating researcher profiles...")
    for i in range(args.target_vectors // 3):
        all_records.append(generate_researcher(i))

    logger.info("Generating publications...")
    for i in range(args.target_vectors // 3):
        all_records.append(generate_publication(i))

    logger.info("Generating labs...")
    for i in range(args.target_vectors // 3):
        all_records.append(generate_lab(i))

    random.shuffle(all_records)

    logger.info(f"Embedding {len(all_records)} records...")

    batch_size = 100
    for batch_start in range(0, len(all_records), batch_size):
        batch = all_records[batch_start : batch_start + batch_size]

        texts = [
            r.get("title") or r.get("name") or f"{r['first_name']} {r['last_name']}"
            for r in batch
        ]
        texts = [t for t in texts if t]

        if texts:
            embeddings = embedder.embed(texts)

            points = []
            for i, record in enumerate(batch):
                text = (
                    record.pop("title", None)
                    or record.pop("name", None)
                    or f"{record.get('first_name', '')} {record.get('last_name', '')}"
                )
                if text:
                    points.append(
                        PointStruct(
                            id=batch_start + i,
                            vector=embeddings[i]
                            if i < len(embeddings)
                            else embedder.embed_single(text),
                            payload=record,
                        )
                    )

            if points:
                client.upsert(collection_name=collection_name, points=points)

        if (batch_start + batch_size) % 1000 == 0:
            logger.info(f"Processed {batch_start + batch_size} records...")

    info = client.get_collection(collection_name)
    logger.info(f"Collection populated: {info.points_count} vectors")

    logger.info("Synthetic data generation complete!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Insert test data into PostgreSQL and Qdrant
"""

import os
import sys
import uuid
from datetime import date
import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import numpy as np

from src.skills.rag.embedder import Embedder


def insert_postgres_test_data():
    """Insert test data into PostgreSQL."""
    conn = psycopg2.connect(
        "postgresql://nrg_user:nrg_password@localhost:5432/nrg_research"
    )
    cur = conn.cursor()

    # Insert institutions
    institutions = [
        ("IIT Bombay", "IIT", "Maharashtra", "Mumbai", 1958),
        ("IIT Delhi", "IIT", "Delhi", "New Delhi", 1961),
        ("IIT Madras", "IIT", "Tamil Nadu", "Chennai", 1959),
        ("IIT Kanpur", "IIT", "Uttar Pradesh", "Kanpur", 1959),
        ("IIT Kharagpur", "IIT", "West Bengal", "Kharagpur", 1951),
    ]

    for name, inst_type, state, city, year in institutions:
        cur.execute(
            "INSERT INTO institutions (name, type, state, city, established_year) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (name, inst_type, state, city, year),
        )

    # Insert researchers
    researchers = [
        ("Arjun", "Sharma", "arjun@iitb.ac.in", "Machine Learning", "Professor", 1),
        (
            "Priya",
            "Patel",
            "priya@iitd.ac.in",
            "Computer Vision",
            "Associate Professor",
            1,
        ),
        ("Rahul", "Kumar", "rahul@iitm.ac.in", "NLP", "Assistant Professor", 1),
        ("Sneha", "Reddy", "sneha@iitk.ac.in", "Robotics", "Professor", 2),
        (
            "Vikram",
            "Singh",
            "vikram@iitkgp.ac.in",
            "Data Science",
            "Associate Professor",
            2,
        ),
    ]

    for first, last, email, spec, position, tier in researchers:
        cur.execute(
            "INSERT INTO researchers (first_name, last_name, email, specialization, current_position, access_tier) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (first, last, email, spec, position, str(tier)),
        )

    # Insert publications
    publications = [
        ("Deep Learning for Image Classification", "IEEE Transactions", 2023, 45, 1),
        ("Natural Language Processing Survey", "ACM Computing Surveys", 2022, 120, 1),
        ("Robotics in Manufacturing", "Springer", 2023, 30, 2),
        ("Data Mining Techniques", "Elsevier", 2021, 85, 1),
        ("AI in Healthcare", "Nature Medicine", 2024, 200, 1),
    ]

    for title, journal, year, citations, tier in publications:
        cur.execute(
            "INSERT INTO publications (title, journal, year, citation_count, access_tier) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (title, journal, year, citations, str(tier)),
        )

    # Insert funding
    funding = [
        ("AI Research Initiative", "DST", 50000000, "active"),
        ("Machine Learning Project", "DBT", 25000000, "active"),
        ("Robotics Development", "CSIR", 15000000, "completed"),
    ]

    for title, agency, amount, status in funding:
        cur.execute(
            "INSERT INTO funding (title, agency, amount_inr, status) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (title, agency, amount, status),
        )

    conn.commit()
    cur.close()
    conn.close()

    print("Inserted test data into PostgreSQL")


def insert_qdrant_test_data():
    """Insert test vectors into Qdrant."""
    client = QdrantClient(
        host=os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
    )
    collection_name = os.getenv("QDRANT_COLLECTION", "nrg_research")
    embedder = Embedder()
    dimension = embedder.get_dimension()
    point_count = 128
    vectors = np.random.rand(point_count, dimension).tolist()
    points = [
        PointStruct(
            id=i + 100, # Avoid collision with synthetic papers
            vector=vectors[i],
            payload={
                "access_tier": 1 if i < 5 else 2,
                "source_type": "researcher" if i < 3 else "publication",
                "institution": "IIT Bombay" if i < 4 else "IIT Delhi",
                "topic": "Machine Learning" if i % 2 == 0 else "Computer Vision",
                "text": f"Sample text for point {i}"
            },
        )
        for i in range(point_count)
    ]
    client.upsert(collection_name=collection_name, points=points)
    print("Inserted test vectors into Qdrant")
    result = client.get_collection(collection_name)
    print(f"Collection has {result.points_count} points")


if __name__ == "__main__":
    insert_postgres_test_data()
    insert_qdrant_test_data()
    print("Test data insertion complete")

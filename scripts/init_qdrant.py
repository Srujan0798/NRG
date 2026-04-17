#!/usr/bin/env python3
"""
Initialize Qdrant collection for National Research Graph
"""

import sys
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

COLLECTION_NAME = "nrg_production"
VECTOR_SIZE = 384  # sentence-transformers default


def init_qdrant():
    """Initialize Qdrant collection."""
    client = QdrantClient(host="localhost", port=6333)

    # Check if collection exists
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]

    if COLLECTION_NAME in collection_names:
        print(f"Collection '{COLLECTION_NAME}' already exists")
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection")

    # Create collection
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )

    print(f"Created collection '{COLLECTION_NAME}' with vector size {VECTOR_SIZE}")

    # Verify
    collection_info = client.get_collection(COLLECTION_NAME)
    print(f"Collection status: {collection_info.status}")

    return 0


if __name__ == "__main__":
    sys.exit(init_qdrant())

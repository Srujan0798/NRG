#!/usr/bin/env python3
"""
Initialize Qdrant collection for National Research Graph
"""

import sys
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from src.skills.rag.embedder import Embedder

DEFAULT_COLLECTION_NAME = "nrg_research"


def init_qdrant():
    """Initialize Qdrant collection."""
    collection_name = os.getenv("QDRANT_COLLECTION", DEFAULT_COLLECTION_NAME)
    client = QdrantClient(
        host=os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
    )
    embedder = Embedder()
    vector_size = embedder.get_dimension()
    embedder.close()

    # Check if collection exists
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]

    if collection_name in collection_names:
        print(f"Collection '{collection_name}' already exists")
        client.delete_collection(collection_name)
        print(f"Deleted existing collection")

    # Create collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

    print(f"Created collection '{collection_name}' with vector size {vector_size}")

    # Verify
    collection_info = client.get_collection(collection_name)
    print(f"Collection status: {collection_info.status}")

    return 0


if __name__ == "__main__":
    sys.exit(init_qdrant())

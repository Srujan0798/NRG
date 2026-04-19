"""RAG Retriever - Local Qdrant retrieval with RBAC metadata filtering."""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range


logger = logging.getLogger(__name__)


class RetrieverUnavailable(RuntimeError):
    """Raised when the vector store cannot serve retrieval requests."""


class Retriever:
    """Local Qdrant retriever with access-tier filtering."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))

        self.client = QdrantClient(host=self.host, port=self.port)
        self.collection_name = "nrg_research"

    def _build_filter(
        self,
        user_tier: int,
        institution: Optional[str] = None,
        topics: Optional[List[str]] = None,
    ) -> Filter:
        """Build filter for access control."""
        must_conditions = []

        must_conditions.append(
            FieldCondition(key="access_tier", range=Range(lte=user_tier))
        )

        if institution:
            must_conditions.append(
                FieldCondition(key="institution", match=MatchValue(value=institution))
            )

        if topics:
            for topic in topics:
                must_conditions.append(
                    FieldCondition(key="topics", match=MatchValue(value=topic))
                )

        if len(must_conditions) == 1:
            return Filter(must=must_conditions)
        elif must_conditions:
            return Filter(must=must_conditions)
        return Filter(must=[])

    def retrieve(
        self,
        query_vector: List[float],
        user_tier: int = 1,
        top_k: int = 5,
        institution: Optional[str] = None,
        topics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant chunks with RBAC filtering.

        Returns chunks with source_id and access_tier metadata.
        """
        filter_obj = self._build_filter(user_tier, institution, topics)

        try:
            if hasattr(self.client, "search"):
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=filter_obj,
                    limit=top_k,
                    with_payload=True,
                    with_vectors=False,
                )
            else:
                # Fallback to query_points for newer qdrant-client versions
                search_result = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=filter_obj,
                    limit=top_k,
                    with_payload=True,
                )
                results = search_result.points
        except Exception as e:
            logger.error("Qdrant search failed: %s", e, exc_info=True)
            raise RetrieverUnavailable(f"Qdrant search failed: {e}") from e

        chunks = []
        metadata = []
        scores = []

        for result in results:
            payload = result.payload or {}

            if "text" in payload:
                chunks.append(payload["text"])
            elif "content" in payload:
                chunks.append(payload["content"])
            elif "abstract" in payload:
                chunks.append(payload["abstract"])
            elif "description" in payload:
                chunks.append(payload["description"])

            metadata.append(
                {
                    "source_id": str(payload.get("source_id", "")),
                    "source_type": payload.get("source_type", ""),
                    "access_tier": payload.get("access_tier", 3),
                    "institution": payload.get("institution", ""),
                    "topics": payload.get("topics", []),
                }
            )
            scores.append(result.score)

        return {"chunks": chunks, "metadata": metadata, "scores": scores}

    def retrieve_text(
        self, query_text: str, embedder, user_tier: int = 1, top_k: int = 5
    ) -> Dict[str, Any]:
        """Retrieve by text query (uses embedder internally)."""
        query_vector = embedder.embed_single(query_text)
        return self.retrieve(query_vector, user_tier, top_k)

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection metadata."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
            }
        except Exception:
            return {"name": self.collection_name, "status": "not_found"}

    def upsert(self, ids: List[str], embeddings: List[List[float]], payloads: List[Dict[str, Any]]):
        """Upsert vectors into Qdrant collection."""
        try:
            # Check if collection exists, create if not
            from qdrant_client.models import VectorParams, Distance

            try:
                self.client.get_collection(self.collection_name)
            except Exception:
                # Collection doesn't exist, create it
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=len(embeddings[0]),
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")

            # Upsert points
            from qdrant_client.models import PointStruct

            points = [
                PointStruct(
                    id=ids[i],
                    vector=embeddings[i],
                    payload=payloads[i]
                )
                for i in range(len(ids))
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            raise

    def close(self):
        pass


def main():
    """Test retriever."""
    retriever = Retriever()
    info = retriever.get_collection_info()
    print(f"Collection: {info}")


if __name__ == "__main__":
    main()

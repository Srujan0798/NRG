"""RAG Retriever - Local Qdrant retrieval with RBAC metadata filtering."""

import os
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue


logger = logging.getLogger(__name__)


class RetrieverUnavailable(RuntimeError):
    """Raised when the vector store cannot serve retrieval requests."""


class Retriever:
    """Local Qdrant retriever with access-tier filtering."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))

        self.client = QdrantClient(host=self.host, port=self.port)
        self.collection_name = os.getenv("QDRANT_COLLECTION", "nrg_research")

    def _build_filter(
        self,
        user_tier: int,
        institution: Optional[str] = None,
        topics: Optional[List[str]] = None,
    ) -> Filter:
        """Build filter for access control."""
        allowed_tiers = self._allowed_access_tiers(user_tier)
        must_conditions: list[Any] = [
            FieldCondition(key="access_tier", match=MatchAny(any=allowed_tiers))
        ]

        if institution:
            must_conditions.append(
                FieldCondition(key="institution", match=MatchValue(value=institution))
            )

        if topics:
            for topic in topics:
                must_conditions.append(
                    FieldCondition(key="topics", match=MatchValue(value=topic))
                )

        return Filter(must=must_conditions)

    def _allowed_access_tiers(self, user_tier: int) -> list[int]:
        """Return data tiers visible to a user tier.

        Tier 1 is the most privileged persona, tier 3 is public/industry-shaped.
        """
        if user_tier == 1:
            return [1, 2, 3]
        if user_tier == 2:
            return [2, 3]
        if user_tier == 3:
            return [3]
        return [3]

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
        query_vector = self._coerce_test_vector_dimension(query_vector)
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

            chunk_text = (
                payload.get("text")
                or payload.get("content")
                or payload.get("abstract")
                or payload.get("description")
                or payload.get("title")
                or ""
            )
            chunks.append(chunk_text)

            metadata.append(
                {
                    "source_id": str(payload.get("source_id", payload.get("document_id", ""))),
                    "document_id": str(payload.get("document_id", payload.get("source_id", ""))),
                    "chunk_index": payload.get("chunk_index"),
                    "chunk_id": payload.get("chunk_id"),
                    "title": payload.get("title", ""),
                    "publication_year": payload.get("publication_year", payload.get("year")),
                    "researcher_ids": payload.get("researcher_ids", []),
                    "keywords": payload.get("keywords", []),
                    "source_type": payload.get("source_type", payload.get("type", "")),
                    "access_tier": payload.get("access_tier", 3),
                    "institution": payload.get("institution", payload.get("affiliation", "")),
                    "affiliation": payload.get("affiliation", payload.get("institution", "")),
                    "topics": payload.get("topics", payload.get("research_area_tags", [])),
                    "research_area_tags": payload.get("research_area_tags", payload.get("topics", [])),
                }
            )
            scores.append(result.score)

        return {"chunks": chunks, "metadata": metadata, "scores": scores}

    def _coerce_test_vector_dimension(self, query_vector: List[float]) -> List[float]:
        """Pad/truncate vectors to match the active Qdrant collection size.

        This ensures embeddings work regardless of whether they were generated
        by the test embedder (768-dim) or a production model (e.g. 1024-dim).
        """
        expected_dim = self._collection_vector_size()
        if not expected_dim or len(query_vector) == expected_dim:
            return query_vector

        if len(query_vector) > expected_dim:
            return query_vector[:expected_dim]

        return [*query_vector, *([0.0] * (expected_dim - len(query_vector)))]

    def _collection_vector_size(self) -> int | None:
        try:
            info = self.client.get_collection(self.collection_name)
            vectors = info.config.params.vectors
        except Exception:
            return None

        size = getattr(vectors, "size", None)
        if size:
            return int(size)

        if isinstance(vectors, dict):
            for vector_config in vectors.values():
                size = getattr(vector_config, "size", None)
                if size:
                    return int(size)
                if isinstance(vector_config, dict) and vector_config.get("size"):
                    return int(vector_config["size"])

        return None

    def retrieve_text(
        self, query_text: str, embedder, user_tier: int = 1, top_k: int = 5
    ) -> Dict[str, Any]:
        """Retrieve by text query (uses embedder internally)."""
        query_vector = embedder.embed_single(query_text)
        return self.retrieve(query_vector, user_tier, top_k)

    def query(self, query_text: str, user_tier: int = 1, top_k: int = 5) -> Dict[str, Any]:
        """Convenience method: embed text and retrieve in one call."""
        from .embedder import Embedder
        embedder = Embedder()
        try:
            return self.retrieve_text(query_text, embedder, user_tier, top_k)
        finally:
            embedder.close()

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

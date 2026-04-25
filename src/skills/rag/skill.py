"""RAG Skill - Offline RAG module with local Qdrant for Phase 1 PoC."""

import json
import logging
import os
from typing import Dict, Any

from .embedder import Embedder, FALLBACK_MODEL
from .retriever import Retriever
from src.observability.langfuse_tracer import _init_langfuse


logger = logging.getLogger(__name__)


class RAGSkill:
    """Sovereign RAG module - fully offline, RBAC filtering."""

    def __init__(self):
        self.retriever = Retriever()
        self.embedder = Embedder(model_name=self._select_embedding_model())

    def _select_embedding_model(self) -> str | None:
        """Match the query embedder to the active Qdrant collection when possible."""
        configured_model = os.getenv("EMBEDDING_MODEL")
        if configured_model:
            return configured_model

        try:
            collection_dim = self.retriever._collection_vector_size()
        except Exception:
            collection_dim = None

        if collection_dim == 384:
            return os.getenv("EMBEDDING_FALLBACK_MODEL", FALLBACK_MODEL)
        return None

    def retrieve(
        self, query: str, user_tier: int = 1, top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve relevant chunks for query.

        Returns top-K chunks with source_ids and metadata.
        No external API calls at any point.
        """
        client = _init_langfuse()
        trace = None
        span = None
        if client:
            try:
                trace = client.trace(name="nrg.rag")
                span = trace.span(name="rag_retrieval")
            except Exception:
                client = None

        try:
            query_vector = self.embedder.embed_single(query)

            results: Dict[str, Any] = self.retriever.retrieve(
                query_vector=query_vector,
                user_tier=user_tier,
                top_k=top_k,
                query_text=query,
            )

            chunks = results.get("chunks", [])
            if span:
                span.update(metadata={"latency_ms": 0, "chunks_retrieved": len(chunks), "node": "rag"})
            if trace:
                trace.update(metadata={"node": "rag", "chunks_retrieved": len(chunks)})

            return results
        except Exception as e:
            if span:
                span.update(status="error", output=str(e))
            if trace:
                trace.update(status="error", metadata={"error": str(e)})
            raise
        finally:
            if span:
                span.end()

    def search(self, query: str, user_tier: int = 1, top_k: int = 5) -> list[dict[str, Any]]:
        """Return flattened search results for scripts and smoke checks."""
        results = self.retrieve(query=query, user_tier=user_tier, top_k=top_k)
        chunks = results.get("chunks", [])
        metadata = results.get("metadata", [])
        scores = results.get("scores", [])

        flattened: list[dict[str, Any]] = []
        for index, chunk in enumerate(chunks):
            meta = metadata[index] if index < len(metadata) else {}
            flattened.append(
                {
                    "document_id": meta.get("document_id") or meta.get("source_id", ""),
                    "chunk_index": meta.get("chunk_index"),
                    "chunk_id": meta.get("chunk_id"),
                    "title": meta.get("title", ""),
                    "score": scores[index] if index < len(scores) else None,
                    "text": chunk,
                    "access_tier": meta.get("access_tier"),
                    "researcher_ids": meta.get("researcher_ids", []),
                    "affiliation": meta.get("affiliation") or meta.get("institution", ""),
                    "publication_year": meta.get("publication_year"),
                    "research_area_tags": meta.get("research_area_tags") or meta.get("topics", []),
                }
            )
        return flattened

    def get_status(self) -> Dict[str, Any]:
        """Get skill status."""
        info = self.retriever.get_collection_info()

        return {
            "embedder": self.embedder.model_name,
            "collection": info.get("name"),
            "vectors_count": info.get("vectors_count"),
            "points_count": info.get("points_count"),
            "offline_mode": True,
        }

    def close(self):
        """Clean up resources."""
        self.embedder.close()
        self.retriever.close()


def main():
    """Demo entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="NRG RAG Skill")
    parser.add_argument("--example-query", type=str, help="Example query for testing")

    args = parser.parse_args()

    skill = RAGSkill()

    if args.example_query:
        result = skill.retrieve(args.example_query)
        print(json.dumps(result, indent=2, default=str))
    else:
        status = skill.get_status()
        print(json.dumps(status, indent=2))

    skill.close()


if __name__ == "__main__":
    main()

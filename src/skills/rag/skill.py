"""RAG Skill - Offline RAG module with local Qdrant for Phase 1 PoC."""

import json
import logging
from typing import Dict, Any

from .embedder import Embedder
from .retriever import Retriever


logger = logging.getLogger(__name__)


class RAGSkill:
    """Sovereign RAG module - fully offline, RBAC filtering."""

    def __init__(self):
        self.embedder = Embedder()
        self.retriever = Retriever()

    def retrieve(
        self, query: str, user_tier: int = 1, top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve relevant chunks for query.

        Returns top-K chunks with source_ids and metadata.
        No external API calls at any point.
        """
        query_vector = self.embedder.embed_single(query)

        results: Dict[str, Any] = self.retriever.retrieve(
            query_vector=query_vector, user_tier=user_tier, top_k=top_k
        )

        return results

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
    parser.add_argument("--demo", type=str, help="Demo query")

    args = parser.parse_args()

    skill = RAGSkill()

    if args.demo:
        result = skill.retrieve(args.demo)
        print(json.dumps(result, indent=2, default=str))
    else:
        status = skill.get_status()
        print(json.dumps(status, indent=2))

    skill.close()


if __name__ == "__main__":
    main()

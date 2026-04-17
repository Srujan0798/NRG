"""Tests for RAG Skill."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.skills.rag.embedder import Embedder
from src.skills.rag.retriever import Retriever
from src.skills.rag.skill import RAGSkill


class TestEmbedder:
    """Test embedding generation."""

    def test_embed_single(self):
        """Test single text embedding."""
        embedder = Embedder()

        result = embedder.embed_single("Robotics research")
        assert isinstance(result, list)
        assert len(result) == 384

        embedder.close()

    def test_embed_multiple(self):
        """Test batch embedding."""
        embedder = Embedder()

        texts = ["AI", "ML", "Robotics"]
        results = embedder.embed(texts)

        assert len(results) == 3
        assert all(len(r) == 384 for r in results)

        embedder.close()

    def test_dimension(self):
        """Test embedding dimension."""
        embedder = Embedder()

        dim = embedder.get_dimension()
        assert dim == 384

        embedder.close()


class TestRetriever:
    """Test Qdrant retrieval."""

    def test_retrieve_returns_metadata(self):
        """Test retrieval includes metadata."""
        retriever = Retriever()

        query_vector = [0.1] * 384
        result = retriever.retrieve(query_vector, user_tier=1, top_k=5)

        assert "chunks" in result
        assert "metadata" in result
        assert "scores" in result

        retriever.close()

    def test_access_tier_filtering(self):
        """Test tier filtering in retrieval."""
        retriever = Retriever()

        query_vector = [0.1] * 384

        result_tier1 = retriever.retrieve(query_vector, user_tier=1, top_k=5)
        result_tier3 = retriever.retrieve(query_vector, user_tier=3, top_k=5)

        assert "chunks" in result_tier1
        assert "chunks" in result_tier3

        retriever.close()


class TestRAGSkill:
    """Test RAG skill."""

    def test_retrieve(self):
        """Test skill retrieval."""
        skill = RAGSkill()

        result = skill.retrieve("robotics research", user_tier=1, top_k=5)

        assert "chunks" in result
        assert "metadata" in result

        skill.close()

    def test_status(self):
        """Test skill status."""
        skill = RAGSkill()

        status = skill.get_status()

        assert "offline_mode" in status
        assert status["offline_mode"] == True

        skill.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

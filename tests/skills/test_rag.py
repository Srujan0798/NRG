"""Tests for RAG Skill."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.skills.rag.embedder import Embedder
from src.skills.rag.retriever import Retriever
from src.skills.rag.skill import RAGSkill


class _FakeScoredPoint:
    def __init__(self, payload, score=0.91):
        self.payload = payload
        self.score = score


class _FakeQdrantClient:
    def __init__(self):
        self.search_calls = []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return [
            _FakeScoredPoint(
                {
                    "document_id": "DOC-1",
                    "chunk_index": 0,
                    "chunk_id": "DOC-1_0",
                    "title": "Robotics Research in India",
                    "text": "Robotics research evidence chunk.",
                    "access_tier": 1,
                    "researcher_ids": ["RES-1"],
                    "affiliation": "IIT",
                    "publication_year": 2025,
                    "research_area_tags": ["Robotics"],
                }
            )
        ]

    def get_collection(self, collection_name):
        class _Vectors:
            size = 768

        class _Params:
            vectors = _Vectors()

        class _Config:
            params = _Params()

        class _Info:
            config = _Config()
            vectors_count = 1
            points_count = 1

        return _Info()


class _FakeRetriever:
    def __init__(self):
        self.client = _FakeQdrantClient()
        self.collection_name = "nrg_research"

    def _collection_vector_size(self):
        return 768

    def retrieve(self, query_vector, user_tier=1, top_k=5):
        return {
            "chunks": ["Robotics research evidence chunk."],
            "metadata": [
                {
                    "document_id": "DOC-1",
                    "source_id": "DOC-1",
                    "chunk_index": 0,
                    "chunk_id": "DOC-1_0",
                    "title": "Robotics Research in India",
                    "access_tier": user_tier,
                    "researcher_ids": ["RES-1"],
                    "affiliation": "IIT",
                    "publication_year": 2025,
                    "research_area_tags": ["Robotics"],
                }
            ],
            "scores": [0.91],
        }

    def get_collection_info(self):
        return {"name": self.collection_name, "vectors_count": 1, "points_count": 1}

    def close(self):
        pass


class TestEmbedder:
    """Test embedding generation."""

    def test_embed_single(self):
        """Test single text embedding."""
        embedder = Embedder()

        result = embedder.embed_single("Robotics research")
        assert isinstance(result, list)
        # IndicBERT produces 768-dim embeddings
        assert len(result) == 768

        embedder.close()

    def test_embed_multiple(self):
        """Test batch embedding."""
        embedder = Embedder()

        texts = ["AI", "ML", "Robotics"]
        results = embedder.embed(texts)

        assert len(results) == 3
        # IndicBERT produces 768-dim embeddings
        assert all(len(r) == 768 for r in results)

        embedder.close()

    def test_dimension(self):
        """Test embedding dimension."""
        embedder = Embedder()

        dim = embedder.get_dimension()
        # IndicBERT produces 768-dim embeddings
        assert dim == 768

        embedder.close()


class TestRetriever:
    """Test Qdrant retrieval."""

    def test_retrieve_returns_metadata(self):
        """Test retrieval includes metadata."""
        retriever = Retriever()
        retriever.client = _FakeQdrantClient()

        # IndicBERT uses 768-dim embeddings
        query_vector = [0.1] * 768
        result = retriever.retrieve(query_vector, user_tier=1, top_k=5)

        assert "chunks" in result
        assert "metadata" in result
        assert "scores" in result
        assert result["metadata"][0]["document_id"] == "DOC-1"
        assert result["metadata"][0]["chunk_id"] == "DOC-1_0"
        assert result["metadata"][0]["access_tier"] == 1

        retriever.close()

    def test_access_tier_filtering(self):
        """Test tier filtering in retrieval."""
        retriever = Retriever()
        retriever.client = _FakeQdrantClient()

        # IndicBERT uses 768-dim embeddings
        query_vector = [0.1] * 768

        result_tier1 = retriever.retrieve(query_vector, user_tier=1, top_k=5)
        result_tier3 = retriever.retrieve(query_vector, user_tier=3, top_k=5)

        assert "chunks" in result_tier1
        assert "chunks" in result_tier3
        tier1_filter = retriever.client.search_calls[0]["query_filter"]
        tier3_filter = retriever.client.search_calls[1]["query_filter"]
        assert tier1_filter.must[0].match.any == [1, 2, 3]
        assert tier3_filter.must[0].match.any == [3]

        retriever.close()


class TestRAGSkill:
    """Test RAG skill."""

    def test_retrieve(self, monkeypatch):
        """Test skill retrieval."""
        monkeypatch.setattr("src.skills.rag.skill.Retriever", _FakeRetriever)
        skill = RAGSkill()

        result = skill.retrieve("robotics research", user_tier=1, top_k=5)

        assert "chunks" in result
        assert "metadata" in result
        assert result["metadata"][0]["document_id"] == "DOC-1"

        skill.close()

    def test_search_flattens_results(self):
        """Test script-friendly search response shape."""
        skill = RAGSkill()
        skill.retrieve = lambda query, user_tier=1, top_k=5: {
            "chunks": ["chunk text"],
            "metadata": [
                {
                    "document_id": "DOC-1",
                    "chunk_index": 0,
                    "title": "Title",
                    "access_tier": 1,
                    "researcher_ids": ["RES-1"],
                    "affiliation": "IIT",
                    "publication_year": 2025,
                    "research_area_tags": ["AI"],
                }
            ],
            "scores": [0.91],
        }

        result = skill.search("query")

        assert result == [
            {
                "document_id": "DOC-1",
                "chunk_index": 0,
                "chunk_id": None,
                "title": "Title",
                "score": 0.91,
                "text": "chunk text",
                "access_tier": 1,
                "researcher_ids": ["RES-1"],
                "affiliation": "IIT",
                "publication_year": 2025,
                "research_area_tags": ["AI"],
            }
        ]
        skill.close()

    def test_status(self):
        """Test skill status."""
        skill = RAGSkill()

        status = skill.get_status()

        assert "offline_mode" in status
        assert status["offline_mode"] is True

        skill.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

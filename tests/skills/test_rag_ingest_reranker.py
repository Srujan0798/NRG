"""Tests for RAG ingest pipeline with mocked Qdrant and embeddings."""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import sqlite3


class TestIngestPublications:
    @patch("src.skills.rag.ingest.Retriever")
    @patch("src.skills.rag.ingest.Embedder")
    @patch("src.skills.rag.ingest.get_sqlite_connection")
    @patch("src.skills.rag.ingest.get_audit_log")
    def test_ingest_empty_db(self, mock_audit, mock_get_conn, mock_embedder_cls, mock_retriever_cls):
        from src.skills.rag.ingest import ingest_publications

        conn = MagicMock()
        conn.execute.return_value.fetchall.return_value = []
        conn.close = MagicMock()
        mock_get_conn.return_value = conn

        embedder = MagicMock()
        embedder.chunk.return_value = ["chunk1"]
        embedder.embed.return_value = [[0.1, 0.2, 0.3]]
        embedder.close = MagicMock()
        mock_embedder_cls.return_value = embedder

        retriever = MagicMock()
        retriever.upsert = MagicMock()
        retriever.close = MagicMock()
        retriever.collection_name = "nrg_research"
        mock_retriever_cls.return_value = retriever

        mock_log = MagicMock()
        mock_audit.return_value = mock_log

        result = ingest_publications(limit=0)
        assert result["publications"] == 0
        assert result["chunks"] == 0

    @patch("src.skills.rag.ingest.Retriever")
    @patch("src.skills.rag.ingest.Embedder")
    @patch("src.skills.rag.ingest.get_sqlite_connection")
    @patch("src.skills.rag.ingest.get_audit_log")
    def test_ingest_with_publications(self, mock_audit, mock_get_conn, mock_embedder_cls, mock_retriever_cls):
        from src.skills.rag.ingest import ingest_publications

        rows = [
            {"publication_id": "pub1", "title": "Test Paper", "abstract": "Abstract text", "year": 2024, "access_tier": 1, "full_text": None, "full_text_uri": None},
            {"publication_id": "pub2", "title": "Another Paper", "abstract": "More text", "year": 2023, "access_tier": 1, "full_text": None, "full_text_uri": None},
        ]
        conn = MagicMock()
        conn.execute.return_value.fetchall.return_value = rows
        conn.close = MagicMock()
        mock_get_conn.return_value = conn

        embedder = MagicMock()
        embedder.chunk.return_value = ["chunk1"]
        embedder.embed.return_value = [[0.1] * 384, [0.2] * 384]
        embedder.close = MagicMock()
        mock_embedder_cls.return_value = embedder

        retriever = MagicMock()
        retriever.upsert = MagicMock()
        retriever.close = MagicMock()
        retriever.collection_name = "nrg_research"
        mock_retriever_cls.return_value = retriever

        mock_log = MagicMock()
        mock_audit.return_value = mock_log

        result = ingest_publications(limit=2, batch_size=64)
        assert result["publications"] == 2
        assert result["chunks"] == 2
        retriever.upsert.assert_called()

    @patch("src.skills.rag.ingest.Retriever")
    @patch("src.skills.rag.ingest.Embedder")
    @patch("src.skills.rag.ingest.get_sqlite_connection")
    @patch("src.skills.rag.ingest.get_audit_log")
    def test_ingest_skips_empty_text(self, mock_audit, mock_get_conn, mock_embedder_cls, mock_retriever_cls):
        from src.skills.rag.ingest import ingest_publications

        rows = [
            {"publication_id": "pub1", "title": "", "abstract": None, "year": 2024, "access_tier": 1, "full_text": None, "full_text_uri": None},
        ]
        conn = MagicMock()
        conn.execute.return_value.fetchall.return_value = rows
        conn.close = MagicMock()
        mock_get_conn.return_value = conn

        embedder = MagicMock()
        embedder.chunk.return_value = []
        embedder.embed.return_value = []
        embedder.close = MagicMock()
        mock_embedder_cls.return_value = embedder

        retriever = MagicMock()
        retriever.upsert = MagicMock()
        retriever.close = MagicMock()
        retriever.collection_name = "nrg_research"
        mock_retriever_cls.return_value = retriever

        result = ingest_publications(limit=1)
        assert result["publications"] == 0
        assert result["chunks"] == 0


class TestReranker:
    def test_rerank_empty_candidates(self):
        from src.skills.rag.reranker import Reranker
        reranker = Reranker(fallback=True)
        assert reranker.rerank("query", []) == []

    def test_rerank_fallback_preserves_order(self):
        from src.skills.rag.reranker import Reranker
        reranker = Reranker(fallback=True)
        candidates = [{"chunk_text": f"text{i}"} for i in range(5)]
        result = reranker.rerank("query", candidates, top_k=3)
        assert len(result) == 3

    def test_rerank_no_fallback_raises(self):
        from src.skills.rag.reranker import RerankerUnavailable, Reranker
        with patch.dict("sys.modules", {"sentence_transformers": None}):
            with pytest.raises(RerankerUnavailable):
                Reranker(fallback=False)

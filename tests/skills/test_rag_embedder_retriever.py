"""Tests for RAG embedder and retriever modules."""

import os
import pytest
from unittest.mock import patch, MagicMock
import numpy as np


class TestSemanticChunker:
    def test_chunk_text_basic(self):
        from src.skills.rag.embedder import SemanticChunker
        chunker = SemanticChunker(max_tokens=10, stride=2)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunker.chunk_text(text)
        assert isinstance(chunks, list)
        assert len(chunks) >= 1

    def test_chunk_text_empty(self):
        from src.skills.rag.embedder import SemanticChunker
        chunker = SemanticChunker()
        chunks = chunker.chunk_text("")
        assert chunks == []

    def test_split_sentences(self):
        from src.skills.rag.embedder import SemanticChunker
        chunker = SemanticChunker()
        sentences = chunker._split_sentences("Hello world. How are you? Fine!")
        assert len(sentences) >= 2

    def test_estimate_tokens(self):
        from src.skills.rag.embedder import SemanticChunker
        chunker = SemanticChunker()
        assert chunker._estimate_tokens("abcdefgh") == 2


class TestEmbedder:
    @patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "1"})
    def test_embedder_initialization(self):
        from src.skills.rag.embedder import Embedder
        embedder = Embedder()
        assert embedder._primary_model is not None

    @patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "1"})
    def test_embedder_embed_single(self):
        from src.skills.rag.embedder import Embedder
        embedder = Embedder()
        result = embedder.embed_single("test text")
        assert isinstance(result, list)
        assert len(result) == 768

    @patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "1"})
    def test_embedder_embed_multiple(self):
        from src.skills.rag.embedder import Embedder
        embedder = Embedder()
        result = embedder.embed(["text1", "text2"])
        assert len(result) == 2

    @patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "1"})
    def test_embedder_chunk(self):
        from src.skills.rag.embedder import Embedder
        embedder = Embedder()
        chunks = embedder.chunk("This is a test sentence for chunking purposes.")
        assert isinstance(chunks, list)
        assert len(chunks) >= 1

    @patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "1"})
    def test_embedder_chunk_and_embed(self):
        from src.skills.rag.embedder import Embedder
        embedder = Embedder()
        text = "First sentence here. Second sentence here. Third one too."
        result = embedder.chunk_and_embed(text)
        assert isinstance(result, list)
        assert len(result) >= 1
        chunk, embedding = result[0]
        assert isinstance(chunk, str)
        assert isinstance(embedding, list)

    @patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "1"})
    def test_embedder_get_dimension(self):
        from src.skills.rag.embedder import Embedder
        embedder = Embedder()
        assert embedder.get_dimension() == 768

    @patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "1"})
    def test_embedder_close(self):
        from src.skills.rag.embedder import Embedder
        embedder = Embedder()
        embedder.close()

    def test_embedder_unavailable_no_models(self):
        from src.skills.rag.embedder import Embedder, EmbedderUnavailable
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "1"}):
            embedder = Embedder()
        embedder._primary_model = None
        embedder._indic_model = None
        with pytest.raises(EmbedderUnavailable):
            embedder.embed(["test"])


class TestRetriever:
    @patch("src.skills.rag.retriever.QdrantClient")
    def test_retriever_initialization(self, mock_qc):
        from src.skills.rag.retriever import Retriever
        mock_client = MagicMock()
        mock_qc.return_value = mock_client
        retriever = Retriever()
        assert retriever.client is not None
        assert retriever.host == "localhost"
        assert retriever.port == 6333

    @patch("src.skills.rag.retriever.QdrantClient")
    def test_retriever_close(self, mock_qc):
        from src.skills.rag.retriever import Retriever
        mock_client = MagicMock()
        mock_qc.return_value = mock_client
        retriever = Retriever()
        retriever.close()

    @patch("src.skills.rag.retriever.QdrantClient")
    def test_retriever_get_collection_info(self, mock_qc):
        from src.skills.rag.retriever import Retriever
        mock_client = MagicMock()
        mock_qc.return_value = mock_client
        mock_info = MagicMock()
        mock_info.vectors_count = 100
        mock_info.points_count = 100
        mock_client.get_collection.return_value = mock_info
        retriever = Retriever()
        info = retriever.get_collection_info()
        assert info["name"] == "nrg_research"
        assert info["vectors_count"] == 100

    @patch("src.skills.rag.retriever.QdrantClient")
    def test_retriever_get_collection_info_not_found(self, mock_qc):
        from src.skills.rag.retriever import Retriever
        mock_client = MagicMock()
        mock_qc.return_value = mock_client
        mock_client.get_collection.side_effect = Exception("not found")
        retriever = Retriever()
        info = retriever.get_collection_info()
        assert info["status"] == "not_found"

    @patch("src.skills.rag.retriever.QdrantClient")
    def test_retriever_warns_on_zero_vectors(self, mock_qc, caplog):
        from src.skills.rag.retriever import Retriever

        mock_client = MagicMock()
        mock_qc.return_value = mock_client
        mock_info = MagicMock()
        mock_info.points_count = 0
        mock_info.indexed_vectors_count = 0
        mock_info.config.params.vectors.size = 1024
        mock_info.config.hnsw_config = None
        mock_client.get_collection.return_value = mock_info

        retriever = Retriever()
        result = retriever.health_check()

        assert result["status"] == "critical"
        assert result["vectors_total"] == 0
        assert result["vectors_indexed"] == 0
        assert "CRITICAL: Qdrant collection empty" in result["issues"]
        assert "CRITICAL: Qdrant collection empty" in caplog.text

    @patch("src.skills.rag.retriever.QdrantClient")
    def test_retriever_does_not_treat_small_unindexed_collection_as_empty(self, mock_qc):
        from src.skills.rag.retriever import Retriever

        mock_client = MagicMock()
        mock_qc.return_value = mock_client
        mock_info = MagicMock()
        mock_info.points_count = 1800
        mock_info.indexed_vectors_count = 0
        mock_info.config.params.vectors.size = 1024
        mock_info.config.hnsw_config = None
        mock_info.config.optimizer_config.indexing_threshold = 20000
        mock_client.get_collection.return_value = mock_info

        retriever = Retriever()
        result = retriever.health_check()

        assert result["status"] == "ok"
        assert result["vectors_total"] == 1800
        assert result["vectors_indexed"] == 0
        assert result["index_built"] is True
        assert result["issues"] == []

    @patch("src.skills.rag.retriever.QdrantClient")
    def test_retriever_build_filter(self, mock_qc):
        from src.skills.rag.retriever import Retriever
        mock_client = MagicMock()
        mock_qc.return_value = mock_client
        retriever = Retriever()
        f = retriever._build_filter(user_tier=2, institution="IIT")
        assert f is not None
        assert f.must[0].match.any == [2, 3]

    @patch("src.skills.rag.retriever.QdrantClient")
    def test_retriever_custom_host_port(self, mock_qc):
        from src.skills.rag.retriever import Retriever
        mock_client = MagicMock()
        mock_qc.return_value = mock_client
        retriever = Retriever(host="custom-host", port=9999)
        assert retriever.host == "custom-host"
        assert retriever.port == 9999


class TestDeterministicTestEmbeddingModel:
    def test_deterministic_encode(self):
        from src.skills.rag.embedder import _DeterministicTestEmbeddingModel
        model = _DeterministicTestEmbeddingModel(dimension=128)
        result = model.encode("test text", convert_to_numpy=True)
        assert result.shape == (128,)
        assert result.dtype == np.float32

    def test_deterministic_get_dimension(self):
        from src.skills.rag.embedder import _DeterministicTestEmbeddingModel
        model = _DeterministicTestEmbeddingModel(dimension=256)
        assert model.get_sentence_embedding_dimension() == 256

    def test_deterministic_encode_without_numpy(self):
        from src.skills.rag.embedder import _DeterministicTestEmbeddingModel
        model = _DeterministicTestEmbeddingModel(dimension=64)
        result = model.encode("test", convert_to_numpy=False)
        assert isinstance(result, list)
        assert len(result) == 64

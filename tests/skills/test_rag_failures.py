from src.skills.rag import retriever as retriever_module
from src.skills.rag.embedder import Embedder, EmbedderUnavailable
from src.skills.rag.retriever import Retriever, RetrieverUnavailable


class FailingQdrantClient:
    def __init__(self, *args, **kwargs):
        return None

    def search(self, *args, **kwargs):
        raise RuntimeError("connection refused")


class FakeModel:
    def encode(self, text, convert_to_numpy=True, show_progress_bar=False):
        raise RuntimeError("model unavailable")


def test_retriever_raises_visible_unavailable_error(monkeypatch):
    monkeypatch.setattr(retriever_module, "QdrantClient", FailingQdrantClient)
    retriever = Retriever()

    try:
        retriever.retrieve([0.1] * 8, user_tier=1, top_k=5)
    except RetrieverUnavailable as exc:
        assert "Qdrant search failed" in str(exc)
    else:
        raise AssertionError("retriever must not silently return empty results")


def test_embedder_raises_visible_unavailable_error_without_dummy_vectors():
    embedder = Embedder.__new__(Embedder)
    embedder._primary_model = None
    embedder._indic_model = None

    try:
        embedder.embed(["robotics research"])
    except EmbedderUnavailable as exc:
        assert "No embedding models loaded" in str(exc)
    else:
        raise AssertionError("embedder must not return dummy vectors")


def test_embedder_raises_when_selected_model_fails():
    embedder = Embedder.__new__(Embedder)
    embedder._primary_model = FakeModel()
    embedder._indic_model = None
    embedder._detect_language = lambda _text: "en"

    try:
        embedder.embed(["robotics research"])
    except EmbedderUnavailable as exc:
        assert "Embedding generation failed" in str(exc)
    else:
        raise AssertionError("embedder must surface model execution failures")

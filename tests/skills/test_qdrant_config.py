from types import SimpleNamespace


def test_retriever_collection_name_comes_from_env(monkeypatch):
    from src.skills.rag.retriever import Retriever

    monkeypatch.setenv("QDRANT_COLLECTION", "custom_collection")

    retriever = Retriever()

    assert retriever.collection_name == "custom_collection"


def test_init_qdrant_uses_env_collection_and_active_embedder_dimension(monkeypatch):
    import scripts.init_qdrant as init_qdrant

    created = {}

    class FakeEmbedder:
        def get_dimension(self):
            return 1024

        def close(self):
            return None

    class FakeClient:
        def __init__(self, host, port):
            created["host"] = host
            created["port"] = port

        def get_collections(self):
            return SimpleNamespace(collections=[])

        def create_collection(self, collection_name, vectors_config):
            created["collection_name"] = collection_name
            created["vector_size"] = vectors_config.size

        def get_collection(self, collection_name):
            return SimpleNamespace(status="green")

    monkeypatch.setenv("QDRANT_COLLECTION", "nrg_research")
    monkeypatch.setattr(init_qdrant, "Embedder", FakeEmbedder)
    monkeypatch.setattr(init_qdrant, "QdrantClient", FakeClient)

    assert init_qdrant.init_qdrant() == 0
    assert created["collection_name"] == "nrg_research"
    assert created["vector_size"] == 1024

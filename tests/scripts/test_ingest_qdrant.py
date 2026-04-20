from __future__ import annotations

from types import SimpleNamespace

import scripts.ingest_qdrant as ingest_module


def test_chunking_uses_512_with_50_overlap():
    text = " ".join(f"t{i}" for i in range(620))
    chunks = ingest_module._chunk_abstract(text, chunk_tokens=512, overlap_tokens=50)

    assert len(chunks) == 2
    first = chunks[0].split()
    second = chunks[1].split()
    assert len(first) == 512
    assert second[:50] == first[-50:]


def test_dry_run_reports_ready_message(monkeypatch, capsys):
    monkeypatch.setattr(
        ingest_module,
        "_fetch_publications",
        lambda _db: [
            ingest_module.PublicationRecord(
                pub_id="PUB-1",
                title="Paper 1",
                abstract=" ".join("w" for _ in range(600)),
                year=2024,
                institution="IIT",
                keywords=["ai"],
            )
        ],
    )

    publications, chunks = ingest_module.ingest(
        database_url="sqlite:///src/data/nrg_research.db",
        qdrant_host="localhost",
        qdrant_port=6333,
        collection="nrg_research",
        dry_run=True,
        batch_size=128,
    )
    output = capsys.readouterr().out

    assert publications == 1
    assert chunks == 2
    assert "Ready to ingest 2 chunks from 1 publications" in output


def test_non_dry_run_upserts_with_idempotent_point_ids(monkeypatch):
    monkeypatch.setattr(
        ingest_module,
        "_fetch_publications",
        lambda _db: [
            ingest_module.PublicationRecord(
                pub_id="PUB-42",
                title="Paper 42",
                abstract=" ".join("w" for _ in range(520)),
                year=2025,
                institution="IIT Bombay",
                keywords=["ml"],
            )
        ],
    )

    class FakeEmbedder:
        def __init__(self, model_name: str):  # noqa: ARG002
            pass

        def embed(self, texts):
            return [[0.1, 0.2] for _ in texts]

        def get_dimension(self):
            return 2

        def close(self):
            return None

    created = {}
    upserts = []

    class FakeQdrantClient:
        def __init__(self, host: str, port: int):  # noqa: ARG002
            pass

        def get_collections(self):
            return SimpleNamespace(collections=[])

        def create_collection(self, collection_name, vectors_config):
            created["name"] = collection_name
            created["size"] = vectors_config.size

        def upsert(self, collection_name, points):
            upserts.append((collection_name, points))

    monkeypatch.setattr(ingest_module, "Embedder", FakeEmbedder)
    monkeypatch.setattr(ingest_module, "QdrantClient", FakeQdrantClient)

    publications, chunks = ingest_module.ingest(
        database_url="sqlite:///src/data/nrg_research.db",
        qdrant_host="localhost",
        qdrant_port=6333,
        collection="nrg_research",
        dry_run=False,
        batch_size=128,
    )

    assert publications == 1
    assert chunks >= 1
    assert created["name"] == "nrg_research"
    first_point = upserts[0][1][0]
    assert str(first_point.id).startswith("PUB-42:")
    assert first_point.payload["pub_id"] == "PUB-42"

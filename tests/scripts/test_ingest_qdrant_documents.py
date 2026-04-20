from __future__ import annotations

import json
import uuid
from pathlib import Path
from types import SimpleNamespace

from scripts.ingest_qdrant import (
    access_tier_to_int,
    ingest_qdrant,
    load_prebuilt_payload,
    parse_document_txt,
)


class FakeEmbedder:
    model_name = "fake-bge-m3"
    dimension = 1024

    def embed(self, texts):
        return [[0.1] * self.dimension for _ in texts]


class FakeQdrantClient:
    def __init__(self):
        self.created = []
        self.upserts = []
        self.points_count = 0

    def get_collections(self):
        return SimpleNamespace(collections=[])

    def create_collection(self, collection_name, vectors_config):
        self.created.append((collection_name, vectors_config.size))

    def delete_collection(self, collection_name):
        return None

    def upsert(self, collection_name, points):
        self.upserts.append((collection_name, points))
        self.points_count += len(points)

    def get_collection(self, collection_name):
        vectors = SimpleNamespace(size=1024)
        return SimpleNamespace(
            points_count=self.points_count,
            config=SimpleNamespace(params=SimpleNamespace(vectors=vectors)),
        )


def _write_doc(path: Path) -> None:
    body = " ".join(f"token{i}" for i in range(620))
    path.write_text(
        """---
document_id: DOC-TEST
title: Hydrogen Catalysis in India
researcher_ids: ['RES-1', 'RES-2']
affiliation: IIT Gandhinagar
publication_year: 2025
abstract: Catalysis abstract.
keywords: ['hydrogen', 'catalysis']
research_area_tags: ['Energy', 'Chemistry']
access_tier: Tier2
category: Energy
---
"""
        + body,
        encoding="utf-8",
    )


def test_parse_document_txt_reads_frontmatter(tmp_path):
    path = tmp_path / "DOC-TEST.txt"
    _write_doc(path)

    doc = parse_document_txt(path)

    assert doc is not None
    assert doc.document_id == "DOC-TEST"
    assert doc.researcher_ids == ["RES-1", "RES-2"]
    assert doc.publication_year == 2025
    assert doc.access_tier == "Tier2"


def test_access_tier_mapping():
    assert access_tier_to_int("Tier1") == 1
    assert access_tier_to_int("tier-2") == 2
    assert access_tier_to_int(None) == 3


def test_parse_legacy_metadata_block(tmp_path):
    path = tmp_path / "doc_ai_robotics_001.txt"
    path.write_text(
        """Metadata:
{
  "document_id": "doc_ai_robotics_001",
  "title": "Traffic AI",
  "researcher_ids": ["RES-A"],
  "affiliation": "IIT Gandhinagar",
  "publication_year": 2024,
  "keywords": ["traffic"],
  "research_area_tags": ["AI/ML"],
  "access_tier": "Tier1"
}

# Traffic AI

**Abstract:**
Urban traffic research.
""",
        encoding="utf-8",
    )

    doc = parse_document_txt(path)

    assert doc is not None
    assert doc.document_id == "doc_ai_robotics_001"
    assert doc.abstract == "Urban traffic research."


def test_parse_json_fenced_metadata_with_blank_arrays(tmp_path):
    path = tmp_path / "DOC_AI_88310.txt"
    path.write_text(
        """```json
{
  "document_id": "DOC_AI_88310",
  "title": "Robot Control",
  "researcher_ids":,
  "keywords":,
  "research_area_tags":,
  "access_tier": "Tier1"
}
```

### Abstract
Robot disaster response research.
""",
        encoding="utf-8",
    )

    doc = parse_document_txt(path)

    assert doc is not None
    assert doc.document_id == "DOC_AI_88310"
    assert doc.researcher_ids == []
    assert doc.abstract == "Robot disaster response research."


def test_dry_run_prepares_points_without_qdrant(tmp_path):
    _write_doc(tmp_path / "DOC-TEST.txt")

    summary = ingest_qdrant(
        source_dir=tmp_path,
        collection="test_collection",
        dry_run=True,
        embedder=FakeEmbedder(),
        show_progress=False,
    )

    assert summary["documents"] == 1
    assert summary["points"] == 3
    assert summary["vector_size"] == 1024
    assert summary["dry_run"] is True


def test_ingest_upserts_idempotent_point_ids_and_metadata(tmp_path):
    _write_doc(tmp_path / "DOC-TEST.txt")
    client = FakeQdrantClient()

    summary = ingest_qdrant(
        source_dir=tmp_path,
        collection="test_collection",
        dry_run=False,
        batch_size=1,
        embedder=FakeEmbedder(),
        client=client,
        show_progress=False,
    )

    assert summary["collection_points"] == 3
    assert client.created == [("test_collection", 1024)]
    first_point = client.upserts[0][1][0]
    uuid.UUID(str(first_point.id))
    assert first_point.payload["point_id"] == "DOC-TEST_0"
    assert first_point.payload["access_tier"] == 2
    assert first_point.payload["access_tier_label"] == "Tier2"
    assert first_point.payload["document_id"] == "DOC-TEST"


def test_prebuilt_payload_without_vectors_flows_through_embedding(tmp_path):
    payload_path = tmp_path / "qdrant_ready_payload.json"
    payload_path.write_text(
        json.dumps(
            [
                {
                    "id": "DOC-PRE",
                    "metadata": {
                        "document_id": "DOC-PRE",
                        "title": "Prebuilt Payload",
                        "researcher_ids": ["RES-3"],
                        "access_tier": "Tier1",
                    },
                    "payload": {"abstract": "A", "full_text": " ".join(["x"] * 20)},
                }
            ]
        ),
        encoding="utf-8",
    )

    records = load_prebuilt_payload(payload_path)
    assert records[0][0].document_id == "DOC-PRE"
    assert records[0][1] is None

    summary = ingest_qdrant(
        source_dir=tmp_path,
        use_prebuilt=payload_path,
        dry_run=True,
        embedder=FakeEmbedder(),
        show_progress=False,
    )
    assert summary["documents"] == 1
    assert summary["points"] == 1
    assert summary["prebuilt_vectors"] == 0

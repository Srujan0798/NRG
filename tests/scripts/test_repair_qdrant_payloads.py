from types import SimpleNamespace

import scripts.repair_qdrant_payloads as repair


def test_infer_public_metadata_defaults_missing_vectors_to_tier3():
    payload = {
        "abstract": (
            "IIT Gandhinagar researchers describe machine learning and robotics "
            "for field deployment."
        ),
        "full_text": "The work advances artificial intelligence for Indian research missions.",
    }

    metadata = repair.infer_public_metadata("point-1", payload)

    assert metadata["access_tier"] == 3
    assert metadata["access_tier_label"] == "Tier3"
    assert metadata["source_id"] == "point-1"
    assert metadata["institution"] == "IIT Gandhinagar"
    assert "machine learning" in metadata["topics"]
    assert "robotics" in metadata["topics"]
    assert metadata["metadata_repair"]["default_access_tier"] == 3


def test_repair_collection_dry_run_reports_stale_points(monkeypatch):
    class FakeClient:
        def scroll(self, collection_name, limit, offset, with_payload, with_vectors):  # noqa: ARG002
            if offset is not None:
                return [], None
            return [
                SimpleNamespace(
                    id="point-1",
                    payload={"abstract": "Machine learning at IIT Gandhinagar"},
                    vector=[0.0, 0.0, 0.0],
                )
            ], None

    result = repair.repair_collection(
        collection="nrg_research",
        host="localhost",
        port=6333,
        model_name="test-model",
        batch_size=8,
        dry_run=True,
        client=FakeClient(),
    )

    assert result["points_scanned"] == 1
    assert result["repairable_points"] == 1
    assert result["zero_vector_points"] == 1
    assert result["missing_access_tier_points"] == 1


def test_repair_collection_upserts_enriched_vectors():
    upserts = []

    class FakeClient:
        def scroll(self, collection_name, limit, offset, with_payload, with_vectors):  # noqa: ARG002
            if offset is not None:
                return [], None
            return [
                SimpleNamespace(
                    id="point-1",
                    payload={"abstract": "Quantum computing research at IISc"},
                    vector=[0.0, 0.0, 0.0],
                )
            ], None

        def upsert(self, collection_name, points):
            upserts.append((collection_name, points))

    class FakeVector:
        def tolist(self):
            return [0.2, 0.3, 0.4]

    class FakeModel:
        def encode(self, texts, batch_size, convert_to_numpy, show_progress_bar):  # noqa: ARG002
            assert texts == ["Quantum computing research at IISc"]
            return [FakeVector()]

    result = repair.repair_collection(
        collection="nrg_research",
        host="localhost",
        port=6333,
        model_name="test-model",
        batch_size=8,
        dry_run=False,
        client=FakeClient(),
        model=FakeModel(),
    )

    assert result["points_updated"] == 1
    assert upserts[0][0] == "nrg_research"
    point = upserts[0][1][0]
    assert point.vector == [0.2, 0.3, 0.4]
    assert point.payload["access_tier"] == 3
    assert point.payload["institution"] == "IISc"
    assert "quantum computing" in point.payload["topics"]

from types import SimpleNamespace

from scripts.build_qdrant_index import get_collection_info


def test_get_collection_info_treats_small_threshold_exempt_collection_as_complete():
    class FakeClient:
        def get_collection(self, collection):
            return SimpleNamespace(
                status="green",
                points_count=1800,
                indexed_vectors_count=0,
                optimizer_status="ok",
                config=SimpleNamespace(
                    hnsw_config=SimpleNamespace(m=16, ef_construct=100),
                    optimizer_config=SimpleNamespace(indexing_threshold=20000),
                    params=SimpleNamespace(vectors=SimpleNamespace(size=1024)),
                ),
            )

    info = get_collection_info(FakeClient(), "nrg_research")

    assert info["index_complete"] is True
    assert info["threshold_exempt"] is True

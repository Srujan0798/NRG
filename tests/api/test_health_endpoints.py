from fastapi.testclient import TestClient
import json

import src.api.main as api_main


class FakeCollection:
    name = "nrg_research"


class FakeCollections:
    collections = [FakeCollection()]


class FakeQdrantClient:
    def __init__(self, host: str, port: int, timeout: float):
        self.host = host
        self.port = port
        self.timeout = timeout

    def get_collections(self):
        return FakeCollections()


class FakeQdrantCount:
    count = 0


class EmptyQdrantCountClient(FakeQdrantClient):
    def count(self, collection_name: str, exact: bool = True):
        assert collection_name == "nrg_research"
        assert exact is True
        return FakeQdrantCount()


class EmptyQdrantCollectionInfo:
    vectors_count = 0
    points_count = 0


class EmptyQdrantCollectionClient(FakeQdrantClient):
    def get_collection(self, collection_name: str):
        assert collection_name == "nrg_research"
        return EmptyQdrantCollectionInfo()


def test_db_health_endpoint_uses_canonical_database(monkeypatch):
    class FakeDB:
        dialect = "sqlite"
        def get_stats(self):
            return {"researchers": 42, "publications": 100}

    monkeypatch.setattr(api_main, "_get_db", FakeDB)
    client = TestClient(api_main.app)

    response = client.get("/health/db")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["dialect"] == "sqlite"
    assert payload["researcher_count"] >= 0


def test_root_health_uses_canonical_database(monkeypatch):
    class FakeDB:
        dialect = "sqlite"
        def get_stats(self):
            return {"researchers": 42, "publications": 100}

    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(api_main, "QdrantClient", FakeQdrantClient)
    monkeypatch.setattr(
        "src.audit.get_chain_health",
        lambda: {"chain_valid": True, "chain_length": 1, "valid_events": 1, "error_count": 0},
    )
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["database"]["status"] == "healthy"
    assert payload["database"]["dialect"] == "sqlite"
    assert payload["database"]["researchers"] == 42
    assert payload["database"]["publications"] == 100


def test_root_health_reports_table_count_and_fast_audit_status(monkeypatch):
    class PoolStats:
        active = 3
        idle = 17
        waiting = 1
        max_size = 40
        min_size = 20

    class FakeDB:
        dialect = "postgresql"

        def get_stats(self):
            return {"researchers": 50_000, "publications": 50_000}

        def execute(self, query: str):
            assert "information_schema.tables" in query
            return [{"table_count": 75}]

        def pool_stats(self):
            return PoolStats()

    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(
        "src.audit.get_chain_health",
        lambda: {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0},
    )
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["database"]["table_count"] == 75
    assert payload["database"]["tables"] == 75
    assert payload["database"]["pool"] == {
        "active": 3,
        "idle": 17,
        "waiting": 1,
        "max_size": 40,
        "min_size": 20,
    }
    assert payload["audit"]["chain_valid"] is True
    assert payload["audit"]["chain_length"] == 7


def test_root_health_reports_audit_lineage_repair_required_as_unhealthy(monkeypatch):
    class FakeDB:
        dialect = "sqlite"

        def get_stats(self):
            return {"researchers": 42, "publications": 100}

        def execute(self, query: str):
            return [{"table_count": 1}]

    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(
        "src.audit.get_chain_health",
        lambda: {
            "chain_valid": False,
            "chain_length": 2,
            "valid_events": 0,
            "error_count": 1,
            "errors": ["Line 1: hash mismatch"],
            "lineage_break": {"repair_required": True, "lineage_intact": False},
        },
    )
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "CRITICAL"
    assert payload["audit"]["status"] == "CRITICAL"


def test_root_health_reports_broken_audit_lineage_as_critical(monkeypatch):
    class FakeDB:
        dialect = "sqlite"

        def get_stats(self):
            return {"researchers": 42, "publications": 100}

        def execute(self, query: str):
            return [{"table_count": 1}]

    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(
        "src.audit.get_chain_health",
        lambda: {
            "chain_valid": True,
            "chain_length": 2,
            "valid_events": 2,
            "error_count": 0,
            "lineage_intact": False,
            "lineage_break": {"repair_required": False, "lineage_intact": False},
        },
    )
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "CRITICAL"
    assert payload["audit"]["status"] == "CRITICAL"


def test_health_fails_when_qdrant_empty(monkeypatch):
    class FakeDB:
        dialect = "sqlite"

        def get_stats(self):
            return {"researchers": 42, "publications": 100}

        def execute(self, query: str):
            return [{"table_count": 1}]

    class EmptyRetriever:
        def __init__(self, timeout: float):
            self.timeout = timeout

        def health_check(self):
            return {
                "status": "critical",
                "collection": "nrg_research",
                "qdrant_reachable": True,
                "collection_exists": True,
                "index_built": False,
                "vectors_indexed": 0,
                "vectors_total": 0,
                "issues": ["CRITICAL: Qdrant collection empty"],
            }

    monkeypatch.setenv("NRG_DEEP_HEALTH_CHECKS", "true")
    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
    monkeypatch.setattr("src.skills.rag.retriever.Retriever", EmptyRetriever)
    monkeypatch.setattr(
        "src.audit.get_chain_health",
        lambda: {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0},
    )
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "unhealthy"
    assert payload["retriever"]["status"] == "critical"
    assert "CRITICAL: Qdrant collection empty" in payload["retriever"]["issues"]


def test_root_health_reports_zero_vector_qdrant_as_critical(monkeypatch):
    class FakeDB:
        dialect = "sqlite"

        def get_stats(self):
            return {"researchers": 42, "publications": 100}

        def execute(self, query: str):
            return [{"table_count": 1}]

    monkeypatch.setenv("QDRANT_COLLECTION", "nrg_research")
    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(api_main, "QdrantClient", EmptyQdrantCountClient)
    monkeypatch.setattr(
        "src.audit.get_chain_health",
        lambda: {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0},
    )
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "CRITICAL"
    assert payload["qdrant"] == {
        "status": "CRITICAL",
        "collection": "nrg_research",
        "vectors": 0,
        "message": "Collection is empty - ingestion required",
    }


def test_qdrant_zero_vectors(monkeypatch):
    class FakeDB:
        dialect = "sqlite"

        def get_stats(self):
            return {"researchers": 42, "publications": 100}

        def execute(self, query: str):
            return [{"table_count": 1}]

    monkeypatch.setenv("QDRANT_COLLECTION", "nrg_research")
    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(api_main, "QdrantClient", EmptyQdrantCountClient)
    monkeypatch.setattr(
        "src.audit.get_chain_health",
        lambda: {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0},
    )
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "CRITICAL"
    assert payload["qdrant"]["status"] == "CRITICAL"


def test_root_health_reports_zero_vectors_from_collection_metadata_as_critical(monkeypatch):
    class FakeDB:
        dialect = "sqlite"

        def get_stats(self):
            return {"researchers": 42, "publications": 100}

        def execute(self, query: str):
            return [{"table_count": 1}]

    monkeypatch.setenv("QDRANT_COLLECTION", "nrg_research")
    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(api_main, "QdrantClient", EmptyQdrantCollectionClient)
    monkeypatch.setattr(
        "src.audit.get_chain_health",
        lambda: {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0},
    )
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "CRITICAL"
    assert payload["qdrant"]["status"] == "CRITICAL"
    assert payload["qdrant"]["vectors"] == 0


def test_query_result_cache_ttl_is_long_enough_for_load_review():
    assert api_main.QUERY_RESULT_CACHE_TTL_SECONDS >= 300


def test_root_health_reports_vector_drift_status_file(monkeypatch, tmp_path):
    class FakeDB:
        dialect = "postgresql"

        def get_stats(self):
            return {"researchers": 50_000, "publications": 50_000}

        def execute(self, query: str):
            return [{"table_count": 75}]

    status_file = tmp_path / "vector_drift_status.json"
    status_file.write_text(
        json.dumps(
            {
                "status": "healthy",
                "alert_level": "GREEN",
                "drift_score": 0.91,
                "timestamp": "2026-04-27T00:00:00Z",
            }
        )
    )

    monkeypatch.setenv("NRG_VECTOR_DRIFT_STATUS_FILE", str(status_file))
    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(
        "src.audit.get_chain_health",
        lambda: {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0},
    )
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["vector_drift"]["status"] == "healthy"
    assert payload["vector_drift"]["drift_score"] == 0.91
    assert payload["vector_drift"]["scheduler"]["status"] == "unknown"


def test_qdrant_health_endpoint_reports_readiness(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setattr(api_main, "QdrantClient", FakeQdrantClient)
    client = TestClient(api_main.app)

    response = client.get("/health/qdrant")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["host"] == "localhost"
    assert payload["collection"] == "nrg_research"


class TestAPIMemoryCache:
    def test_cache_get_set(self):
        cache = api_main._APIMemoryCache(default_ttl=60)
        cache.set("key1", {"data": 42})
        assert cache.get("key1") == {"data": 42}

    def test_cache_expires(self):
        cache = api_main._APIMemoryCache(default_ttl=0)
        cache.set("key1", {"data": 42})
        import time
        time.sleep(0.05)
        assert cache.get("key1") is None

    def test_cache_invalidate_prefix(self):
        cache = api_main._APIMemoryCache(default_ttl=60)
        cache.set("stats:researcher", 1)
        cache.set("stats:industry", 2)
        cache.set("researchers:gujarat", 3)
        cache.invalidate(prefix="stats:")
        assert cache.get("stats:researcher") is None
        assert cache.get("stats:industry") is None
        assert cache.get("researchers:gujarat") == 3

    def test_cache_invalidate_all(self):
        cache = api_main._APIMemoryCache(default_ttl=60)
        cache.set("a", 1)
        cache.invalidate()
        assert cache.get("a") is None

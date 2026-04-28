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
    class FakeDB:
        dialect = "postgresql"

        def get_stats(self):
            return {"researchers": 50_000, "publications": 50_000}

        def execute(self, query: str):
            assert "information_schema.tables" in query
            return [{"table_count": 75}]

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
    assert payload["audit"]["chain_valid"] is True
    assert payload["audit"]["chain_length"] == 7


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

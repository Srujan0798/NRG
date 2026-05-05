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
        lambda **_: {"chain_valid": True, "chain_length": 1, "valid_events": 1, "error_count": 0},
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
        lambda **_: {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0},
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


def test_root_health_times_out_slow_audit_check(monkeypatch):
    import time

    class FakeDB:
        dialect = "sqlite"

        def get_stats(self):
            return {"researchers": 42, "publications": 100}

        def execute(self, query: str):
            return [{"table_count": 10}]

    def slow_chain_health(**_):
        time.sleep(0.2)
        return {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0}

    monkeypatch.setenv("NRG_HEALTH_AUDIT_TIMEOUT_SECONDS", "0.01")
    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(
        api_main,
        "_get_qdrant_vector_count_health",
        lambda: {"status": "healthy", "collection": "nrg_research", "vectors": 1},
    )
    monkeypatch.setattr("src.audit.get_chain_health", slow_chain_health)
    client = TestClient(api_main.app)

    start = time.perf_counter()
    response = client.get("/health")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    payload = response.json()
    assert elapsed < 1.0
    assert payload["audit"]["status"] == "timeout"
    assert payload["status"] == "unhealthy"


def test_root_health_times_out_slow_qdrant_check(monkeypatch):
    import time

    class FakeDB:
        dialect = "sqlite"

        def get_stats(self):
            return {"researchers": 42, "publications": 100}

        def execute(self, query: str):
            return [{"table_count": 10}]

    def slow_qdrant_health():
        time.sleep(0.2)
        return {"status": "healthy", "collection": "nrg_research", "vectors": 1}

    monkeypatch.setenv("NRG_HEALTH_QDRANT_TIMEOUT_SECONDS", "0.01")
    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(
        "src.audit.get_chain_health",
        lambda **_: {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0},
    )
    monkeypatch.setattr(api_main, "_get_qdrant_vector_count_health", slow_qdrant_health)
    client = TestClient(api_main.app)

    start = time.perf_counter()
    response = client.get("/health")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    payload = response.json()
    assert elapsed < 1.0
    assert payload["qdrant"]["status"] == "unavailable"
    assert payload["rag"]["status"] == "degraded"
    assert "timed out" in payload["qdrant"]["message"]


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
        lambda **_: {
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
        lambda **_: {
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
        lambda **_: {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0},
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
        lambda **_: {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0},
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
        lambda **_: {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0},
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
        lambda **_: {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0},
    )
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "CRITICAL"
    assert payload["qdrant"]["status"] == "CRITICAL"
    assert payload["qdrant"]["vectors"] == 0


def test_root_health_reports_explicit_rag_status_when_qdrant_unavailable(monkeypatch):
    class FakeDB:
        dialect = "sqlite"

        def get_stats(self):
            return {"researchers": 42, "publications": 100}

        def execute(self, query: str):
            return [{"table_count": 1}]

    class UnavailableQdrantClient:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("qdrant offline")

    monkeypatch.setenv("QDRANT_COLLECTION", "nrg_research")
    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(api_main, "QdrantClient", UnavailableQdrantClient)
    monkeypatch.setattr(
        "src.audit.get_chain_health",
        lambda **_: {"chain_valid": True, "chain_length": 1, "valid_events": 1, "error_count": 0},
    )
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["qdrant"]["status"] == "unavailable"
    assert payload["rag"]["status"] == "degraded"
    assert payload["rag"]["retrieval_enabled"] is False
    assert payload["rag"]["collection"] == "nrg_research"
    assert "RAG retrieval is disabled" in payload["rag"]["warning"]


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
        lambda **_: {"chain_valid": True, "chain_length": 7, "valid_events": 7, "error_count": 0},
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


def test_qdrant_health_endpoint_reports_not_ready_when_collection_missing(monkeypatch):
    class OtherCollection:
        name = "other_collection"

    class OtherCollections:
        collections = [OtherCollection()]

    class MissingCollectionQdrantClient(FakeQdrantClient):
        def get_collections(self):
            return OtherCollections()

        def get_collection(self, collection_name: str):
            raise RuntimeError(f"Collection {collection_name} not found")

    monkeypatch.setenv("QDRANT_COLLECTION", "nrg_research")
    monkeypatch.setattr(api_main, "QdrantClient", MissingCollectionQdrantClient)
    client = TestClient(api_main.app)

    response = client.get("/health/qdrant")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is False
    assert payload["healthy"] is False
    assert payload["collection_exists"] is False


def test_qdrant_health_endpoint_accepts_alias_collection(monkeypatch):
    class AliasOnlyQdrantClient(FakeQdrantClient):
        def get_collections(self):
            return FakeCollections()

        def get_collection(self, collection_name: str):
            assert collection_name == "nrg_research_dev"
            return {"status": "green"}

    monkeypatch.setenv("QDRANT_COLLECTION", "nrg_research_dev")
    monkeypatch.setattr(api_main, "QdrantClient", AliasOnlyQdrantClient)
    client = TestClient(api_main.app)

    response = client.get("/health/qdrant")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["collection"] == "nrg_research_dev"
    assert payload["collection_exists"] is True


def test_health_endpoints_share_status_and_healthy_contract(monkeypatch, tmp_path):
    class FakeDB:
        dialect = "sqlite"

        def get_stats(self):
            return {"researchers": 42, "publications": 100}

        def execute(self, query: str):
            return [{"table_count": 1}]

    class FakeProviderMesh:
        class mesh_config:
            query_timeout_budget_seconds = 5

        def get_provider_health(self):
            return {"local": {"status": "healthy"}}

    class FakeDistance:
        name = "Cosine"

    class FakeVectors:
        size = 384
        distance = FakeDistance()

    class FakeParams:
        vectors = FakeVectors()

    class FakeOptimizer:
        indexing_threshold = 10000

    class FakeConfig:
        params = FakeParams()
        optimizer_config = FakeOptimizer()

    class FakeCollectionInfo:
        points_count = 1
        indexed_vectors_count = 1
        config = FakeConfig()

    class FakePoint:
        payload = {"ingested_at": "2026-05-02T00:00:00Z"}

    class FakeVectorClient(FakeQdrantClient):
        def get_collection(self, collection_name: str):
            assert collection_name == "nrg_research"
            return FakeCollectionInfo()

        def scroll(self, **kwargs):
            return ([FakePoint()], None)

    health_file = tmp_path / "killer_health.json"
    health_file.write_text('{"status":"healthy","queries":[]}')

    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(api_main, "QdrantClient", FakeVectorClient)
    monkeypatch.setattr("qdrant_client.QdrantClient", FakeVectorClient)
    monkeypatch.setattr(
        api_main,
        "_get_qdrant_vector_count_health",
        lambda: {"status": "healthy", "collection": "nrg_research", "vectors": 1},
    )
    monkeypatch.setattr("src.api.routes.health._killer_query_health_file", health_file)
    monkeypatch.setattr(
        "src.audit.get_chain_health",
        lambda **_: {"chain_valid": True, "chain_length": 1, "valid_events": 1, "error_count": 0},
    )
    monkeypatch.setattr("src.config.llm_config.get_llm_client", lambda: None)
    monkeypatch.setattr("src.config.llm_config.get_llm_mesh", lambda: FakeProviderMesh())
    monkeypatch.setattr("src.config.local_llm.get_llama_cpp_client", lambda: None)

    client = TestClient(api_main.app)
    endpoints = [
        "/health",
        "/health/db",
        "/health/qdrant",
        "/health/llm",
        "/health/all",
        "/api/health/killer_queries",
        "/api/providers/health",
        "/api/vectors/health",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code in {200, 503}, endpoint
        payload = response.json()
        assert "status" in payload, endpoint
        assert "healthy" in payload, endpoint
        assert isinstance(payload["healthy"], bool), endpoint


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

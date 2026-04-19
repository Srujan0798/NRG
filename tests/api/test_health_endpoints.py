from fastapi.testclient import TestClient

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


def test_db_health_endpoint_uses_canonical_database():
    client = TestClient(api_main.app)

    response = client.get("/health/db")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["dialect"] == "sqlite"
    assert payload["researcher_count"] >= 0


def test_qdrant_health_endpoint_reports_readiness(monkeypatch):
    monkeypatch.setattr(api_main, "QdrantClient", FakeQdrantClient)
    client = TestClient(api_main.app)

    response = client.get("/health/qdrant")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["host"] == "localhost"
    assert payload["collection"] == "nrg_research"

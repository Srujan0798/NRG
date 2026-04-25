"""Regression tests for /researchers pagination guardrails."""

from fastapi.testclient import TestClient

import src.api.main as api_main


class CapturingDB:
    def __init__(self):
        self.limit_seen = None

    def query_researchers(self, state=None, research_area=None, limit=50, offset=0):
        self.limit_seen = limit
        return []


def test_researchers_endpoint_caps_bulk_limit(monkeypatch):
    fake_db = CapturingDB()
    monkeypatch.setattr(api_main, "_get_db", lambda: fake_db)
    api_main._api_cache.invalidate()

    client = TestClient(api_main.app)
    login = client.post(
        "/login",
        json={"username": "researcher_user", "password": "researcher-pass"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    response = client.get(
        "/researchers?limit=10000",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert fake_db.limit_seen == 500

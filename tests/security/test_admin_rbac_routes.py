"""Admin route RBAC regressions."""

from fastapi.testclient import TestClient

import src.api.main as api_main


def _industry_token(client: TestClient) -> str:
    response = client.post(
        "/login",
        json={"username": "industry_user", "password": "industry-pass"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_tier3_is_blocked_from_admin_and_metrics_routes():
    client = TestClient(api_main.app)
    token = _industry_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    probes = [
        ("GET", "/admin/slo"),
        ("POST", "/api/reindex"),
        ("GET", "/metrics"),
        ("GET", "/api/metrics"),
        ("GET", "/api/admin/rbac"),
        ("GET", "/admin/dpdp/stats"),
    ]

    for method, path in probes:
        response = client.request(method, path, headers=headers)
        assert response.status_code == 403, f"{method} {path} returned {response.status_code}"

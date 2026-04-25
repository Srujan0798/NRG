"""Regression tests for lightweight /api/metrics audit reporting."""

from fastapi.testclient import TestClient

import src.api.main as api_main


def test_api_metrics_uses_cached_audit_health(monkeypatch):
    client = TestClient(api_main.app)
    login = client.post(
        "/login",
        json={"username": "researcher_user", "password": "researcher-pass"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    import src.audit as audit_module

    def fail_full_verify(*args, **kwargs):
        raise AssertionError("full verify_chain should not run in /api/metrics")

    monkeypatch.setattr(audit_module, "verify_chain", fail_full_verify)
    monkeypatch.setattr(
        audit_module,
        "get_chain_health",
        lambda: {
            "chain_valid": True,
            "chain_length": 123,
            "valid_events": 123,
            "error_count": 0,
        },
    )

    response = client.get(
        "/api/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["audit"]["chain_length"] == 123
    assert payload["audit"]["chain_valid"] is True
    assert payload["audit"]["valid_event_count"] == 123

from fastapi.testclient import TestClient

import src.api.main as api_main
from src import audit as audit_module
from src.audit import AuditEvent, get_audit_log


def _auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/login",
        json={"username": "researcher_user", "password": "researcher-pass"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_single_audit_event_endpoint_returns_recent_chain_event(monkeypatch, tmp_path):
    monkeypatch.setenv("NRG_AUDIT_DIR", str(tmp_path / "audit"))
    audit_module.ImmutableAuditLog._reset()

    event_hash = get_audit_log().append(
        AuditEvent(
            event_type="query",
            user_id="researcher_user",
            query="best quantum researchers",
            result={"citations": [{"id": "nrg-researchers"}]},
        )
    )

    client = TestClient(api_main.app)
    response = client.get(f"/audit/event/{event_hash}", headers=_auth_headers(client))

    assert response.status_code == 200
    event = response.json()["event"]
    assert event["hmac"] == event_hash
    assert event["current_hmac"] == event_hash
    assert event["query"] == "best quantum researchers"
    assert event["action"] == "query"
    assert event["actor"] == "researcher_user"
    assert event["integrity_status"] == "intact"
    assert event["status"] == "success"
    assert event["evidence_count"] == 1


def test_single_audit_event_endpoint_returns_pending_reference_for_old_hash(monkeypatch, tmp_path):
    monkeypatch.setenv("NRG_AUDIT_DIR", str(tmp_path / "audit"))
    audit_module.ImmutableAuditLog._reset()

    client = TestClient(api_main.app)
    response = client.get(
        "/audit/event/old-response-hash-no-longer-in-window",
        headers=_auth_headers(client),
    )

    assert response.status_code == 200
    event = response.json()["event"]
    assert event["hmac"] == "old-response-hash-no-longer-in-window"
    assert event["integrity_status"] == "pending"
    assert event["status"] == "reference_only"


def test_single_audit_event_endpoint_hides_other_user_event(monkeypatch, tmp_path):
    monkeypatch.setenv("NRG_AUDIT_DIR", str(tmp_path / "audit"))
    audit_module.ImmutableAuditLog._reset()

    event_hash = get_audit_log().append(
        AuditEvent(
            event_type="query",
            user_id="another_user",
            query="private query",
        )
    )

    client = TestClient(api_main.app)
    response = client.get(f"/audit/event/{event_hash}", headers=_auth_headers(client))

    assert response.status_code == 404

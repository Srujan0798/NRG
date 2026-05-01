import json

from fastapi.testclient import TestClient

import src.api.main as api_main


def test_fast_requests_do_not_emit_high_volume_info_logs_by_default(monkeypatch):
    monkeypatch.delenv("NRG_LOG_ALL_REQUESTS", raising=False)
    monkeypatch.setenv("NRG_SLOW_REQUEST_LOG_MS", "999999")

    messages: list[str] = []

    def capture_info(message, *args, **kwargs):
        messages.append(str(message))

    monkeypatch.setattr(api_main.logger, "info", capture_info)
    client = TestClient(api_main.app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "request completed" not in messages


def test_pii_redaction_does_not_emit_high_volume_info_logs(monkeypatch):
    messages: list[str] = []

    def capture_info(message, *args, **kwargs):
        messages.append(str(message))

    monkeypatch.setattr(api_main.logger, "info", capture_info)

    redacted, redacted_types = api_main._redact_pii_from_response(
        {"response": "Contact researcher@example.edu for details."}
    )

    assert "researcher@example.edu" not in redacted["response"]
    assert "EMAIL" in redacted_types
    assert messages == []


def test_request_envelope_profile_writes_jsonl(monkeypatch, tmp_path):
    profile_file = tmp_path / "request_envelope.jsonl"
    monkeypatch.setenv("NRG_REQUEST_ENVELOPE_PROFILE", "1")
    monkeypatch.setenv("NRG_REQUEST_ENVELOPE_PROFILE_FILE", str(profile_file))

    client = TestClient(api_main.app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = json.loads(profile_file.read_text().strip())
    assert payload["method"] == "GET"
    assert payload["path"] == "/openapi.json"
    assert payload["status"] == 200
    assert payload["duration_ms"] >= 0
    assert payload["response_content_length"] is not None

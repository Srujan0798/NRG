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

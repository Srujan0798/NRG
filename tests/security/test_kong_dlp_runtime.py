import json
import subprocess
import time

import pytest
import requests


ADMIN_URL = "http://localhost:8002"
PROXY_URL = "http://localhost:8000"
KONG_CONTAINER = "nrg-kong-gateway"
JSON_DECODER = json.JSONDecoder()


def _login(role: str = "researcher") -> str:
    credentials = {
        "researcher": ("researcher_user", "researcher-pass"),
        "government": ("gov_user", "government-pass"),
        "industry": ("industry_user", "industry-pass"),
    }
    username, password = credentials[role]
    response = requests.post(
        f"{PROXY_URL}/login",
        json={"username": username, "password": password},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()["access_token"]


@pytest.mark.skip(reason="requires Kong Gateway running")
@pytest.mark.integration
def test_kong_loads_custom_dlp_plugin(kong_stack):
    response = requests.get(f"{ADMIN_URL}/plugins/enabled", timeout=5)
    response.raise_for_status()

    enabled_plugins = response.json().get("enabled_plugins", [])
    assert "dlp" in enabled_plugins


@pytest.mark.skip(reason="requires Kong Gateway running")
@pytest.mark.integration
@pytest.mark.parametrize(
    ("query", "detected_type"),
    [
        ("Find researcher with Aadhaar 1234-5678-9012", "aadhaar"),
        ("PAN number ABCDE1234F details", "pan"),
        ("Contact researcher at 9876543210", "phone"),
    ],
)
def test_kong_dlp_blocks_pii_and_reports_type(kong_stack, query, detected_type):
    token = _login()
    response = requests.post(
        f"{PROXY_URL}/query",
        json={"query": query},
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )

    assert response.status_code == 400, response.text
    assert response.json() == {
        "error": "DLP_VIOLATION",
        "message": f"PII detected in query: {detected_type}",
        "detected_type": detected_type,
    }


@pytest.mark.skip(reason="requires Kong Gateway running")
@pytest.mark.integration
def test_blocked_request_emits_audit_log(kong_stack):
    request_id = f"dlp-audit-{int(time.time())}"
    token = _login()

    response = requests.post(
        f"{PROXY_URL}/query",
        json={"query": "Find researcher with Aadhaar 1234-5678-9012"},
        headers={
            "Authorization": f"Bearer {token}",
            "X-Request-ID": request_id,
        },
        timeout=5,
    )
    assert response.status_code == 400, response.text

    deadline = time.time() + 15
    while time.time() < deadline:
        logs = subprocess.run(
            ["docker", "logs", KONG_CONTAINER],
            capture_output=True,
            text=True,
            check=True,
        )
        combined_logs = f"{logs.stdout}\n{logs.stderr}"

        for line in combined_logs.splitlines():
            if request_id not in line or "dlp_blocked" not in line:
                continue

            payload_start = line.find("{")
            assert payload_start >= 0, line

            log_payload, _ = JSON_DECODER.raw_decode(line[payload_start:])
            assert log_payload["event"] == "dlp_blocked"
            assert log_payload["request_id"] == request_id
            assert log_payload["block_reason"] == "DLP_VIOLATION"
            assert log_payload["detected_type"] == "aadhaar"
            return

        time.sleep(1)

    raise AssertionError("Did not find structured audit log for blocked request")

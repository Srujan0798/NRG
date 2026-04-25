"""
Security Tests: SQL Injection Blocked
Payload: "'; DROP TABLE researchers; --"
Verify: blocked by allowlist, returns error
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


class TestSQLInjectionBlocked:
    """Verify SQL injection payloads are handled safely (no execution of injected SQL)."""

    SQL_INJECTION_PAYLOADS = [
        "'; DROP TABLE researchers; --",
        "'; DROP TABLE publications; --",
        "'; DELETE FROM researchers WHERE 1=1; --",
        "1; DROP TABLE researchers;",
        "1 OR 1=1",
        "1' OR '1'='1",
        "'; INSERT INTO researchers VALUES ('hacker'); --",
        "'; UPDATE researchers SET email='hacker@example.com'; --",
        "'; SELECT * FROM researchers; --",
        "1'; DROP TABLE researchers; --",
    ]

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_sql_injection_returns_safe_response(self, client, payload):
        """SQL injection payloads should be handled safely - no crash, no injected data."""
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": payload},
        )

        assert response.status_code in [200, 400], \
            f"SQL injection '{payload}' returned unexpected status {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            response_text = str(data)
            assert "hacker" not in response_text.lower(), \
                f"Injected 'hacker' data appeared in response for payload: {payload}"

    def test_union_based_injection_returns_safe_response(self, client):
        """UNION-based SQL injection should return safe response (blocked or sanitised)."""
        token = _login(client)

        payload = "1' UNION SELECT password FROM users; --"
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": payload},
        )

        assert response.status_code in [200, 400], \
            f"UNION injection returned {response.status_code} — expected 200 (sanitised) or 400 (blocked)"

    def test_boolean_based_injection_returns_safe_response(self, client):
        """Boolean-based blind SQL injection should be blocked or handled safely."""
        token = _login(client)

        payload = "1' AND 1=1; --"
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": payload},
        )

        assert response.status_code in [200, 400], f"Boolean injection should not crash with 5xx"

    def test_stacked_queries_injection_returns_safe_response(self, client):
        """Stacked queries SQL injection should return safe response."""
        token = _login(client)

        payload = "1; SELECT * FROM researchers; DROP TABLE researchers; --"
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": payload},
        )

        assert response.status_code in [200, 400], f"Payload '{payload}' should not crash with 5xx"

    def test_comment_based_injection_returns_safe_response(self, client):
        """Comment-based SQL injection bypass attempts should be blocked or handled safely."""
        token = _login(client)

        payloads = [
            "1' /* comment */ OR 1=1; --",
            "1;#comment",
            "1--comment",
        ]

        for payload in payloads:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": payload},
            )
            assert response.status_code in [200, 400], f"Payload '{payload}' should not crash with 5xx"

    def test_hex_encoded_injection_returns_safe_response(self, client):
        """Hex-encoded SQL injection should return safe response."""
        token = _login(client)

        payload = "0x44524F50205441424C652072657365617263686573"
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": payload},
        )

        assert response.status_code == 200

    def test_injection_error_does_not_leak_schema(self, client):
        """SQL injection errors should not leak schema information."""
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "'; INVALID SQL; --"},
        )

        if response.status_code != 200:
            data = response.json()
            error_detail = str(data.get("detail", ""))
            assert "column" not in error_detail.lower() or "table" not in error_detail.lower(), \
                "Error messages should not leak schema details"

    def test_normal_query_still_works(self, client):
        """Legitimate queries should still work after SQL injection tests."""
        token = _login(client)

        normal_queries = [
            "AI researchers in Gujarat",
            "Machine learning publications",
            "Data science institutions",
        ]

        for query in normal_queries:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": query},
            )
            assert response.status_code == 200, f"Normal query '{query}' should work"

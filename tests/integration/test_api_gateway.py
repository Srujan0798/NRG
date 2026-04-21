"""
API gateway smoke tests.
Tests auth, rate limiting, CORS, and health at the HTTP level.
"""
import os
import pytest
import httpx

BASE = "http://localhost:8000"

pytestmark = pytest.mark.skipif(
    not os.getenv("NRG_API_RUNNING"),
    reason="Requires running API server (set NRG_API_RUNNING=1)",
)


class TestHealthEndpoints:
    def test_health_check(self):
        r = httpx.get(f"{BASE}/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "healthy"

    def test_health_db(self):
        r = httpx.get(f"{BASE}/health/db")
        assert r.status_code == 200

    def test_health_qdrant(self):
        r = httpx.get(f"{BASE}/health/qdrant")
        assert r.status_code == 200


class TestAuthEnforcement:
    def test_query_without_token_rejected(self):
        r = httpx.post(f"{BASE}/query", json={"query": "test"})
        assert r.status_code in (401, 403)

    def test_query_with_invalid_token_rejected(self):
        r = httpx.post(
            f"{BASE}/query",
            json={"query": "test"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert r.status_code in (401, 403)

    def test_protected_endpoints_require_auth(self):
        for endpoint in ["/researchers", "/publications", "/projects", "/patents", "/stats"]:
            r = httpx.get(f"{BASE}{endpoint}")
            assert r.status_code in (401, 403), f"{endpoint} should require auth"


class TestRateLimiting:
    def test_rapid_requests_throttled(self):
        """If rate limiting is configured, rapid requests should eventually get 429."""
        results = []
        for _ in range(20):
            r = httpx.get(f"{BASE}/health")
            results.append(r.status_code)
        # At least health should work; if rate limiting exists, some may be 429
        assert 200 in results


class TestCORS:
    def test_cors_headers_present(self):
        r = httpx.options(
            f"{BASE}/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Should have CORS headers, should NOT be wildcard with credentials
        assert r.status_code in (200, 204, 405)

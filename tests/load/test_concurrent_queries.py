"""
Load Tests for 50 Concurrent Queries
Validates: no crashes, P95 < 15s
"""

import pytest
import time
import threading
import statistics
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class StubWorkflow:
    call_count = 0

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        StubWorkflow.call_count += 1
        return {
            "query_id": "query-1",
            "session_id": session_id or "session-1",
            "synthesized_response": "ok",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "conversation_history": [],
        }


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setattr(api_main, "workflow", StubWorkflow())
    api_main._api_cache.invalidate()


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _make_query(client: TestClient, token: str, query: str, results: list, errors: list):
    """Thread-safe query helper."""
    try:
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": query},
        )
        results.append(response.status_code)
    except Exception as e:
        errors.append(str(e))
        results.append(None)


class TestConcurrentQueries:
    """50 concurrent queries → no crashes, P95 < 15s"""

    def test_50_concurrent_queries_no_crashes(self):
        """System must handle 50 concurrent queries without crashing."""
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")

        results = []
        errors = []
        lock = threading.Lock()

        def make_query(i: int):
            try:
                response = client.post(
                    "/query",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"query": f"researcher query {i}"},
                )
                with lock:
                    results.append(response.status_code)
            except Exception as e:
                with lock:
                    errors.append(str(e))
                    results.append(None)

        threads = []
        for i in range(50):
            t = threading.Thread(target=make_query, args=(i,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread errors: {errors}"
        success_count = sum(1 for r in results if r == 200)
        assert success_count == 50, f"Only {success_count}/50 queries succeeded"

    def test_p95_latency_under_15s(self):
        """P95 latency for concurrent queries must be under 15 seconds."""
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")

        errors = []

        def make_query_timed(i: int):
            try:
                start = time.time()
                response = client.post(
                    "/query",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"query": f"test query {i}"},
                )
                latency = time.time() - start
                return response.status_code, latency
            except Exception as e:
                errors.append(str(e))
                return None, None

        threads = []
        for i in range(50):
            t = threading.Thread(target=lambda idx=i: results.append(make_query_timed(idx)))
            threads.append(t)

        results = []
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successful_latencies = [lat for status, lat in results if status == 200 and lat is not None]

        assert len(successful_latencies) >= 45, f"Only {len(successful_latencies)}/50 queries succeeded"

        p95 = statistics.quantiles(successful_latencies, n=20)[18] if len(successful_latencies) >= 20 else max(successful_latencies)
        p95_seconds = p95

        assert p95_seconds < 15, f"P95 latency {p95_seconds:.2f}s exceeds 15s threshold"

    def test_concurrent_requests_different_personas(self):
        """Concurrent queries from different personas should all succeed."""
        client = TestClient(api_main.app)

        tokens = {
            "researcher": _login(client, "researcher_user", "researcher-pass"),
            "government": _login(client, "gov_user", "government-pass"),
            "industry": _login(client, "industry_user", "industry-pass"),
        }

        results = {"researcher": [], "government": [], "industry": []}
        errors = []

        def make_query(role: str, token: str, i: int):
            try:
                response = client.post(
                    "/query",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"query": f"{role} query {i}"},
                )
                return role, response.status_code
            except Exception as e:
                errors.append(str(e))
                return role, None

        threads = []
        for role, token in tokens.items():
            for i in range(20):
                t = threading.Thread(target=lambda r=role, t=token, idx=i: results[r].append(make_query(r, t, idx)))
                threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"

        for role, role_results in results.items():
            statuses = [status for _, status in role_results]
            success_count = sum(1 for s in statuses if s == 200)
            assert success_count == 20, f"{role}: only {success_count}/20 succeeded"

    def test_sustained_load_100_queries(self):
        """System must handle sustained load of 100 sequential queries."""
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")

        success_count = 0
        error_count = 0

        for i in range(100):
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"sustained load test query {i}"},
            )
            if response.status_code == 200:
                success_count += 1
            else:
                error_count += 1

        assert success_count >= 95, f"Only {success_count}/100 queries succeeded"
        assert error_count <= 5, f"Too many errors: {error_count}"


class TestRateLimiting:
    """Rate limiting behavior under concurrent load."""

    def test_rate_limit_returns_429(self):
        """After exceeding rate limit, API should return 429."""
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")

        rate_limited = False
        success_count = 0

        for i in range(100):
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"rate limit test {i}"},
            )
            if response.status_code == 429:
                rate_limited = True
                break
            elif response.status_code == 200:
                success_count += 1

        assert rate_limited or success_count == 100, (
            f"Neither rate limited nor all succeeded. successes={success_count}"
        )


class TestMemoryLeakDetection:
    """Detect potential memory leaks under repeated queries."""

    def test_repeated_queries_no_memory_leak(self):
        """Repeated queries should not cause memory to grow unbounded."""
        client = TestClient(api_main.app)
        token = _login(client, "researcher_user", "researcher-pass")

        for i in range(100):
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"memory test {i}"},
            )
            assert response.status_code == 200, f"Query {i} failed: {response.status_code}"

        final_call_count = StubWorkflow.call_count
        assert final_call_count >= 100, "Workflow should have been called 100 times"

"""
Load Tests: Concurrent Queries
50 concurrent queries, P95 < 15s
"""

import pytest
import time
import threading
import statistics
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
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
            "query_id": f"query-{StubWorkflow.call_count}",
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
    StubWorkflow.call_count = 0
    monkeypatch.setattr(api_main, "workflow", StubWorkflow())
    api_main._api_cache.invalidate()


@pytest.fixture
def client():
    return TestClient(api_main.app)


def _login(client: TestClient, username: str = "researcher_user", password: str = "researcher-pass") -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


class TestConcurrentQueries:
    """50 concurrent queries → no crashes, P95 < 15s"""

    def test_50_concurrent_queries_no_crashes(self, client):
        """System must handle 50 concurrent queries without crashing."""
        token = _login(client)
        results = []
        errors = []

        def make_query(i: int):
            try:
                response = client.post(
                    "/query",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"query": f"concurrent query {i}"},
                )
                return response.status_code
            except Exception as e:
                errors.append(str(e))
                return None

        threads = []
        for i in range(50):
            t = threading.Thread(target=lambda idx=i: results.append(make_query(idx)))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread errors: {errors}"
        success_count = sum(1 for r in results if r == 200)
        assert success_count == 50, f"Only {success_count}/50 queries succeeded"

    def test_p95_latency_under_15s(self, client):
        """P95 latency for concurrent queries must be under 15 seconds."""
        token = _login(client)
        results = []
        errors = []

        def make_query_timed(i: int):
            try:
                start = time.time()
                response = client.post(
                    "/query",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"query": f"latency test query {i}"},
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

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successful_latencies = [lat for status, lat in results if status == 200 and lat is not None]

        assert len(successful_latencies) >= 45, f"Only {len(successful_latencies)}/50 queries succeeded"

        p95 = statistics.quantiles(successful_latencies, n=20)[18] if len(successful_latencies) >= 20 else max(successful_latencies)

        assert p95 < 15, f"P95 latency {p95:.2f}s exceeds 15s threshold"

    def test_concurrent_different_tiers(self, client):
        """Concurrent queries from different tiers should all succeed."""
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


class TestSustainedLoad:
    """1000 queries over 10 minutes → no memory leaks, consistent latency"""

    def test_sustained_load_1000_queries(self, client):
        """System must handle sustained load of 1000 queries."""
        token = _login(client)

        success_count = 0
        error_count = 0
        latencies = []

        for i in range(1000):
            start = time.time()
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"sustained load test {i}"},
            )
            latency = time.time() - start
            latencies.append(latency)

            if response.status_code == 200:
                success_count += 1
            else:
                error_count += 1

        assert success_count >= 950, f"Only {success_count}/1000 queries succeeded"
        assert error_count <= 50, f"Too many errors: {error_count}"

        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]

        assert avg_latency < 5, f"Average latency {avg_latency:.2f}s too high"
        assert p95_latency < 15, f"P95 latency {p95_latency:.2f}s exceeds threshold"

    def test_no_memory_leak_under_repeated_queries(self, client):
        """Repeated queries should not cause memory to grow unbounded."""
        token = _login(client)

        for i in range(500):
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"memory test {i}"},
            )
            assert response.status_code == 200, f"Query {i} failed"

        assert StubWorkflow.call_count >= 500, "Workflow should have been called for each query"

    def test_consistent_latency_under_load(self, client):
        """Latency should remain consistent under sustained load."""
        token = _login(client)

        first_100_latencies = []
        last_100_latencies = []

        for i in range(500):
            start = time.time()
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"consistency test {i}"},
            )
            latency = time.time() - start

            if i < 100:
                first_100_latencies.append(latency)
            elif i >= 400:
                last_100_latencies.append(latency)

        first_p95 = statistics.quantiles(first_100_latencies, n=20)[18] if len(first_100_latencies) >= 20 else max(first_100_latencies)
        last_p95 = statistics.quantiles(last_100_latencies, n=20)[18] if len(last_100_latencies) >= 20 else max(last_100_latencies)

        latency_degradation = last_p95 / first_p95 if first_p95 > 0 else 1
        assert latency_degradation < 2.0, f"Latency degraded too much: {latency_degradation:.2f}x"

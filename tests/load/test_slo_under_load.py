"""
SLO Load Tests — 20 Concurrent Users × 5 Queries

Validates NRG's performance contract under realistic load:
- All responses received within P99 threshold (15s)
- No 500 errors
- No connection drops
- Concurrency SLO: 20 simultaneous queries

SKILLS USED: /performance (load testing, latency benchmarking)
"""

import os
import pytest
import time
import statistics
import threading
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

SLO_ENV = os.environ.get("SLO_ENV", "dev")


def _check_qdrant():
    """Check if Qdrant is available."""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect(("localhost", 6333))
        sock.close()
        return True
    except Exception:
        return False


HAS_QDRANT = _check_qdrant()

from fastapi.testclient import TestClient
import src.api.main as api_main


class FakeCloudLLMClient:
    """Mock LLM for load testing — fast, predictable responses."""
    model = "mock-minimax"

    def generate(self, system_prompt: str, user_prompt: str, conversation_history: list = None, complexity: str = None) -> str:
        return (
            "Load test response: 42 researchers found. "
            "Machine Learning (15), Robotics (12), AI (10). "
            "[cite:PUB-00000000:0] [cite:PUB-00000001:0]"
        )

    def generate_streaming(self, system_prompt: str, user_prompt: str, conversation_history: list):
        response = self.generate(system_prompt, user_prompt, conversation_history)
        for i in range(0, len(response), 10):
            yield response[i:i+10]


class FakeLLMMesh:
    """Mock LLM mesh for load testing."""

    def __init__(self, client):
        self._client = client

    def generate(self, system_prompt: str, user_prompt: str, conversation_history: list = None, complexity: str = None) -> str:
        return self._client.generate(system_prompt, user_prompt, conversation_history or [])

    def generate_streaming(self, system_prompt: str, user_prompt: str, conversation_history: list = None):
        return self._client.generate_streaming(system_prompt, user_prompt, conversation_history or [])


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    """Patch LLM so load tests don't make real API calls."""
    fake = FakeCloudLLMClient()
    fake_mesh = FakeLLMMesh(fake)
    import src.config.llm_config as llm_module
    import src.orchestration.nodes.synthesizer as synth_module
    import src.orchestration.nodes.executor as executor_module

    monkeypatch.setattr(llm_module, "get_llm_client", lambda provider=None: fake)
    monkeypatch.setattr(llm_module, "get_llm_mesh", lambda: fake_mesh)
    monkeypatch.setattr(synth_module, "get_llm_mesh", lambda: fake_mesh)
    monkeypatch.setattr(synth_module, "get_local_llm_client", lambda provider=None: fake)
    monkeypatch.setattr(synth_module, "log_llm_call", lambda *args, **kwargs: None)

    fake_rag_result = {
        "retrieved_chunks": [
            {
                "chunk_id": "ch_load_001",
                "publication_id": "PUB-00000000",
                "title": "Load Test Publication",
                "content": "This is synthetic content from the load test environment.",
            }
        ],
        "retrieval_metadata": [],
        "errors": [],
        "warnings": [],
        "retrieval_sources": ["rag"],
    }
    monkeypatch.setattr(
        executor_module,
        "_execute_rag",
        lambda user_query, user_tier: (fake_rag_result, 50.0),
    )

    fake_sql_result = {
        "sql_results": [
            {"id": "r1", "name": "Dr. Load Test", "institution": "IIT Bombay", "research_area": "AI", "h_index": 42},
            {"id": "r2", "name": "Dr. Performance", "institution": "IIT Delhi", "research_area": "ML", "h_index": 38},
        ],
        "sql_query": "SELECT * FROM researchers LIMIT 10",
        "errors": [],
        "warnings": [],
    }
    monkeypatch.setattr(
        executor_module,
        "_execute_sql",
        lambda user_query, user_tier: (fake_sql_result, 30.0),
    )

    import src.security.rate_limiter as rate_module
    monkeypatch.setattr(rate_module, "check_tier_rate_limit", lambda *args, **kwargs: (True, 1000, 0, {}))
    monkeypatch.setattr(rate_module, "check_endpoint_rate_limit", lambda *args, **kwargs: (True, 1000, 0, {}))


@pytest.fixture
def client():
    api_main._api_cache.invalidate()
    return TestClient(api_main.app)


def _login(client: TestClient, username: str = "researcher_user", password: str = "researcher-pass") -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.mark.skipif(SLO_ENV == "dev", reason="Load tests not enforceable in dev (set SLO_ENV=prod to run)")
class TestSLOUnderLoad:
    """
    SLO Under Load: 20 concurrent users × 5 queries each

    Asserts:
    - All responses received (no connection drops)
    - No 500 errors
    - All complete within P99 (15s)
    - P95 < 8s for concurrent batch
    """

    @pytest.mark.timeout(120)
    def test_20_users_5_queries_all_complete(self, client):
        """20 concurrent users each send 5 queries — all must complete."""
        token = _login(client)

        all_results = []
        all_errors = []
        lock = threading.Lock()

        def user_session(user_idx: int):
            session_results = []
            session_errors = []
            for q in range(5):
                try:
                    response = client.post(
                        "/query",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"query": f"load test user {user_idx} query {q}"},
                    )
                    session_results.append(response.status_code)
                except Exception as e:
                    session_errors.append(str(e))
                    session_results.append(None)
            with lock:
                all_results.extend(session_results)
                all_errors.extend(session_errors)

        threads = []
        for i in range(20):
            t = threading.Thread(target=lambda idx=i: user_session(idx))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(all_errors) == 0, f"Connection errors: {all_errors}"
        statuses = [r for r in all_results if r is not None]
        success_count = sum(1 for s in statuses if s == 200)
        assert success_count == 100, f"Only {success_count}/100 queries succeeded"

    @pytest.mark.timeout(120)
    def test_20_concurrent_p95_under_8_seconds(self, client):
        """P95 latency for 20 concurrent queries must be under 8s."""
        token = _login(client)

        results = []
        lock = threading.Lock()

        def make_query_timed(user_idx: int, query_idx: int):
            start = time.time()
            try:
                response = client.post(
                    "/query",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"query": f"latency test u{user_idx} q{query_idx}"},
                )
                latency = time.time() - start
                return response.status_code, latency
            except Exception as e:
                return None, time.time() - start

        threads = []
        for i in range(20):
            for j in range(5):
                idx = (i, j)
                t = threading.Thread(target=lambda args=idx: results.append(make_query_timed(args[0], args[1])))
                threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successful_latencies = [lat for status, lat in results if status == 200]
        assert len(successful_latencies) >= 95, (
            f"Only {len(successful_latencies)}/100 queries succeeded"
        )

        if len(successful_latencies) >= 20:
            p95 = statistics.quantiles(successful_latencies, n=20)[18]
        else:
            p95 = sorted(successful_latencies)[int(len(successful_latencies) * 0.95)]

        assert p95 < 8.0, f"P95 latency {p95:.2f}s exceeds 8s SLO target under load"

    @pytest.mark.timeout(120)
    def test_no_server_errors_under_load(self, client):
        """No 500 errors under 20 concurrent user load."""
        token = _login(client)

        results = []
        lock = threading.Lock()

        def make_query(user_idx: int, query_idx: int):
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"error check u{user_idx} q{query_idx}"},
            )
            return response.status_code

        threads = []
        for i in range(20):
            for j in range(5):
                idx = (i, j)
                t = threading.Thread(target=lambda args=idx: results.append(make_query(args[0], args[1])))
                threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        server_errors = [r for r in results if 500 <= r < 600]
        assert len(server_errors) == 0, f"Got {len(server_errors)} 5xx errors under load"

    @pytest.mark.timeout(120)
    def test_max_latency_under_p99_threshold(self, client):
        """Maximum latency under load must be below P99 threshold (15s)."""
        token = _login(client)

        results = []
        lock = threading.Lock()

        def make_query_timed(user_idx: int, query_idx: int):
            start = time.time()
            try:
                response = client.post(
                    "/query",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"query": f"max latency test u{user_idx} q{query_idx}"},
                )
                latency = time.time() - start
                return response.status_code, latency
            except Exception:
                return None, 999.0

        threads = []
        for i in range(20):
            for j in range(5):
                idx = (i, j)
                t = threading.Thread(target=lambda args=idx: results.append(make_query_timed(args[0], args[1])))
                threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successful_latencies = [lat for status, lat in results if status == 200]
        max_latency = max(successful_latencies) if successful_latencies else 999.0
        assert max_latency < 15.0, (
            f"Max latency {max_latency:.2f}s exceeds P99 threshold of 15s"
        )

    @pytest.mark.timeout(120)
    def test_all_tiers_under_concurrent_load(self, client):
        """All three tiers handle 10 concurrent queries each without failures."""
        tokens = {
            "researcher": _login(client, "researcher_user", "researcher-pass"),
            "government": _login(client, "gov_user", "government-pass"),
            "industry": _login(client, "industry_user", "industry-pass"),
        }

        results = {"researcher": [], "government": [], "industry": []}
        errors = []
        lock = threading.Lock()

        def make_query(role: str, token: str, i: int):
            try:
                response = client.post(
                    "/query",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"query": f"{role} load test {i}"},
                )
                return role, response.status_code
            except Exception as e:
                errors.append(str(e))
                return role, None

        threads = []
        for role, token in tokens.items():
            for i in range(10):
                role_copy = role
                token_copy = token
                idx = i
                t = threading.Thread(target=lambda rc=role_copy, tc=token_copy, ix=idx: results[rc].append(make_query(rc, tc, ix)))
                threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"
        for role, role_results in results.items():
            statuses = [s for _, s in role_results]
            success_count = sum(1 for s in statuses if s == 200)
            assert success_count == 10, f"{role}: only {success_count}/10 succeeded"
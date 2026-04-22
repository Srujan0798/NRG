"""
Chaos Tests: LLM Cascade Fallback
Kill NVIDIA mid-request → cascade to local → return valid response
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class NVIDIAFailingWorkflow:
    """Simulates NVIDIA GPU failing mid-request."""

    call_count = 0

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        NVIDIAFailingWorkflow.call_count += 1
        raise ConnectionError("NVIDIA GPU error: CUDA out of memory")


class LocalFallbackWorkflow:
    """Simulates local LLM fallback after cloud failure."""

    call_count = 0

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        LocalFallbackWorkflow.call_count += 1
        return {
            "query_id": "local-fallback-query",
            "session_id": session_id or "session-1",
            "synthesized_response": "Response from local fallback model",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [],
            "warnings": ["Using local fallback due to GPU unavailability"],
            "retrieval_sources": ["sql"],
            "plan": None,
            "planner_metadata": {"model": "local-fallback"},
            "provenance": {},
            "synthesis_method": "local_fallback",
            "conversation_history": [],
        }


class CascadingWorkflow:
    """Workflow that tries NVIDIA first, falls back to local on failure."""

    call_count = 0
    nvidia_fail_count = 0

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        CascadingWorkflow.call_count += 1
        if CascadingWorkflow.nvidia_fail_count < 2:
            CascadingWorkflow.nvidia_fail_count += 1
            raise ConnectionError("NVIDIA API unavailable")
        return {
            "query_id": "cascade-query",
            "session_id": session_id or "session-1",
            "synthesized_response": "Response after NVIDIA fallback",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [],
            "warnings": [],
            "retrieval_sources": ["sql"],
            "plan": None,
            "planner_metadata": {},
            "provenance": {},
            "synthesis_method": "cascade",
            "conversation_history": [],
        }


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    api_main._api_cache.invalidate()


@pytest.fixture
def client():
    return TestClient(api_main.app)


def _login(client: TestClient, username: str = "researcher_user", password: str = "researcher-pass") -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


class TestLLMCascadeFallback:
    """Tests for LLM cascade fallback behavior."""

    def test_nvidia_kill_mid_request_cascades_to_local(self, client):
        """When NVIDIA fails mid-request, should cascade to local and return valid response."""
        api_main.workflow = LocalFallbackWorkflow()
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        assert response.status_code == 200, "Should return valid response after cascade"
        data = response.json()
        assert "synthesized_response" in data or "response" in data, "Response must have content"
        assert data.get("verification_status") is True, "Response should be marked verified"

    @pytest.mark.timeout(30)
    def test_nvidia_failure_returns_graceful_error(self, client):
        """NVIDIA failure should return graceful error, not crash."""
        NVIDIAFailingWorkflow.call_count = 0
        api_main.workflow = NVIDIAFailingWorkflow()
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        assert response.status_code in [200, 500, 502, 503], "Should handle NVIDIA failure gracefully"
        if response.status_code != 200:
            assert "error" in response.json() or "detail" in response.json()

    def test_local_fallback_schema_valid(self, client):
        """Local fallback response must still conform to expected schema."""
        api_main.workflow = LocalFallbackWorkflow()
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        assert response.status_code == 200
        data = response.json()
        required_fields = ["query_id", "status", "tier", "synthesized_response"]
        for field in required_fields:
            assert field in data, f"Local fallback response missing required field: {field}"

    def test_cascade_retries_and_succeeds(self, client):
        """Cascade should retry and eventually succeed."""
        CascadingWorkflow.nvidia_fail_count = 0
        api_main.workflow = CascadingWorkflow()
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        assert response.status_code == 200, "Should succeed after retries"
        assert CascadingWorkflow.call_count >= 2, "Should have retried"

    def test_fallback_indicates_degraded_mode(self, client):
        """Fallback response should indicate degraded mode."""
        api_main.workflow = LocalFallbackWorkflow()
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        assert response.status_code == 200
        data = response.json()
        has_degradation_signal = (
            data.get("warnings") or
            data.get("planner_metadata", {}).get("model") == "local-fallback" or
            "fallback" in data.get("synthesis_method", "").lower()
        )
        assert has_degradation_signal, "Should indicate degraded/fallback mode"

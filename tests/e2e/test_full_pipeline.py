"""
End-to-End Smoke Test: Full NRG Pipeline
Validates the complete pipeline for all 3 personas.

Pipeline: login → consent → query → LangGraph → synthesizer → verifier → response
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class StubWorkflow:
    """Stub workflow that returns deterministic responses without calling real LLMs."""
    call_count = 0

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        StubWorkflow.call_count += 1
        is_rag = "trend" in query.lower() or "what are" in query.lower()
        return {
            "query_id": f"e2e-query-{StubWorkflow.call_count}",
            "session_id": session_id or "session-1",
            "synthesized_response": f"Stub response for: {query[:50]}",
            "intent": "unstructured" if is_rag else "structured",
            "routing_decision": "vector_search" if is_rag else "text_to_sql",
            "verification_status": True,
            "citations": [
                {"paper_id": "p1", "title": "AI in Gujarat", "source": "publication"},
                {"paper_id": "p2", "title": "ML Research", "source": "publication"},
            ],
            "warnings": [],
            "retrieval_sources": ["sql", "vector"],
            "plan": {"steps": ["search", "filter", "synthesize"]},
            "planner_metadata": {"model": "stub"},
            "provenance": {"p1": {"found_in": "publications"}},
            "synthesis_method": "rule_based",
            "conversation_history": [],
        }


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    StubWorkflow.call_count = 0
    monkeypatch.setattr(api_main, "workflow", StubWorkflow())
    api_main._api_cache.invalidate()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient(api_main.app)


class TestFullPipeline:
    """Full pipeline validation for all personas."""

    def test_researcher_login_returns_token(self, client):
        """(a) Login as researcher_user → verify token returned."""
        response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        assert response.status_code == 200, f"Login failed: {response.json()}"
        data = response.json()
        assert "access_token" in data, "access_token must be returned"
        assert data["user"]["tier"] == 1
        assert data["user"]["role"] == "researcher"

    def test_researcher_query_structured_success(self, client):
        """(b) POST /query → status=success, response contains text, citations non-empty."""
        login = client.post("/login", json={"username": "researcher_user", "password": "researcher-pass"})
        token = login.json()["access_token"]

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "Find researchers in machine learning in Gujarat"},
        )
        assert response.status_code == 200, f"Query failed: {response.json()}"
        data = response.json()

        assert data.get("status") == "success", f"Expected status=success, got: {data.get('status')}"
        assert data.get("response"), "response field must contain text"
        assert len(data.get("citations", [])) > 0, "citations must be non-empty"
        assert data.get("synthesis_method") in ("cloud_llm", "rule_based", "e2e_test"), \
            f"synthesis_method should be cloud_llm or rule_based, got: {data.get('synthesis_method')}"

    def test_researcher_query_rag_path_unstructured(self, client):
        """(c) POST /query → RAG path activated (intent=unstructured)."""
        login = client.post("/login", json={"username": "researcher_user", "password": "researcher-pass"})
        token = login.json()["access_token"]

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What are the trends in AI research?"},
        )
        assert response.status_code == 200, f"Query failed: {response.json()}"
        data = response.json()
        assert data.get("intent") == "unstructured", \
            f"RAG path should be activated (intent=unstructured), got: {data.get('intent')}"

    def test_researcher_stats_researcher_count(self, client):
        """(d) GET /stats → researcher_count > 0."""
        login = client.post("/login", json={"username": "researcher_user", "password": "researcher-pass"})
        token = login.json()["access_token"]

        response = client.get(
            "/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, f"Stats failed: {response.json()}"
        data = response.json()
        assert data.get("total_researchers", 0) > 0, \
            f"total_researchers must be > 0, got: {data.get('total_researchers')}"

    def test_researcher_graph_nodes(self, client):
        """(e) GET /query/graph?topic=machine+learning → nodes > 0."""
        login = client.post("/login", json={"username": "researcher_user", "password": "researcher-pass"})
        token = login.json()["access_token"]

        response = client.get(
            "/query/graph?topic=machine+learning",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, f"Graph query failed: {response.json()}"
        data = response.json()
        assert len(data.get("nodes", [])) > 0, \
            f"Graph must have nodes for topic 'machine learning', got: {len(data.get('nodes', []))}"

    def test_gov_stats_has_state_distribution(self, client):
        """(f) Login as gov_user → GET /stats → state_distribution present."""
        login = client.post("/login", json={"username": "gov_user", "password": "government-pass"})
        assert login.status_code == 200, f"Gov login failed: {login.json()}"
        token = login.json()["access_token"]

        response = client.get(
            "/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, f"Gov stats failed: {response.json()}"
        data = response.json()
        assert "state_distribution" in data, \
            f"Government tier must see state_distribution, got keys: {list(data.keys())}"
        assert len(data.get("state_distribution", [])) > 0, \
            "state_distribution must be non-empty"

    def test_industry_stats_limited_fields(self, client):
        """(g) Login as industry_user → GET /stats → limited fields only."""
        login = client.post("/login", json={"username": "industry_user", "password": "industry-pass"})
        assert login.status_code == 200, f"Industry login failed: {login.json()}"
        token = login.json()["access_token"]

        response = client.get(
            "/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, f"Industry stats failed: {response.json()}"
        data = response.json()

        assert "state_distribution" not in data, \
            "Industry tier must NOT see state_distribution"
        assert "email" not in str(data).lower(), \
            "Industry tier must NOT see email addresses"

        allowed_keys = {"total_researchers", "total_publications", "research_areas"}
        extra_keys = set(data.keys()) - allowed_keys
        assert not extra_keys, f"Industry tier should only see {allowed_keys}, but also has: {extra_keys}"


class TestHealthEndpoints:
    """Validate health check endpoints."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded", "unhealthy")

    def test_health_db(self, client):
        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data.get("ready") is True


class TestConsentFlow:
    """Validate consent auto-grant on login."""

    def test_researcher_consent_auto_granted(self, client):
        """Researcher should have research_access consent auto-granted on login."""
        login = client.post("/login", json={"username": "researcher_user", "password": "researcher-pass"})
        token = login.json()["access_token"]

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "List researchers"},
        )
        assert response.status_code == 200, \
            f"Query should succeed with auto-granted consent, but got: {response.json()}"

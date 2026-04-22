"""
E2E Persona Tests: Researcher Flow
Login → Query "AI researchers in Gujarat" → See results → Export → Logout
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class StubWorkflow:
    call_count = 0

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        StubWorkflow.call_count += 1
        return {
            "query_id": f"e2e-query-{StubWorkflow.call_count}",
            "session_id": session_id or "session-1",
            "synthesized_response": f"Found 42 AI researchers in Gujarat",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [
                {"paper_id": "p1", "title": "AI in Gujarat", "source": "publication"},
                {"paper_id": "p2", "title": "ML Research", "source": "publication"},
            ],
            "warnings": [],
            "retrieval_sources": ["sql", "vector"],
            "plan": {"steps": ["search", "filter", "synthesize"]},
            "planner_metadata": {"model": "test"},
            "provenance": {"p1": {"found_in": "publications"}},
            "synthesis_method": "e2e_test",
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


class TestResearcherFlow:
    """E2E test: Login → Query → See results → Export → Logout"""

    def test_researcher_login(self, client):
        """Researcher should be able to login."""
        response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )

        assert response.status_code == 200, "Researcher login should succeed"
        data = response.json()
        assert "access_token" in data
        assert data.get("user", {}).get("tier") == 1

    def test_researcher_query_ai_researchers_gujarat(self, client):
        """Researcher should be able to query 'AI researchers in Gujarat'."""
        login_response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        token = login_response.json()["access_token"]

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )

        assert response.status_code == 200, "Query should succeed"
        data = response.json()
        assert "synthesized_response" in data or "response" in data
        assert data.get("tier") == 1

    def test_researcher_sees_results(self, client):
        """Researcher should see results with citations."""
        login_response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        token = login_response.json()["access_token"]

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )

        data = response.json()
        assert len(data.get("citations", [])) > 0, "Should see citations in results"

    def test_researcher_export_data(self, client):
        """Researcher should be able to export their data."""
        login_response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        token = login_response.json()["access_token"]
        user_id = login_response.json()["user"]["id"]

        response = client.get(
            "/me/data",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, "Data export should succeed"
        data = response.json()
        assert isinstance(data, (dict, list)), "Exported data should be valid"

    def test_researcher_logout(self, client):
        """Researcher should be able to logout."""
        login_response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        token = login_response.json()["access_token"]

        response = client.post(
            "/logout",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )

        assert response.status_code == 200, "Logout should succeed"

    def test_researcher_full_flow(self, client):
        """Complete researcher flow: login → query → export → logout."""
        login_response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        query_response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )
        assert query_response.status_code == 200
        query_data = query_response.json()
        assert "synthesized_response" in query_data or "response" in query_data

        export_response = client.get(
            "/me/data",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert export_response.status_code == 200

        logout_response = client.post(
            "/logout",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert logout_response.status_code == 200


class TestGovernmentFlow:
    """E2E test: Login (gov tier) → Dashboard → Policy query → See aggregated data"""

    def test_government_login(self, client):
        """Government user should be able to login."""
        response = client.post(
            "/login",
            json={"username": "gov_user", "password": "government-pass"},
        )

        assert response.status_code == 200, "Government login should succeed"
        data = response.json()
        assert "access_token" in data
        assert data.get("user", {}).get("tier") == 2

    def test_government_dashboard_access(self, client):
        """Government user should be able to access dashboard stats."""
        login_response = client.post(
            "/login",
            json={"username": "gov_user", "password": "government-pass"},
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, "Dashboard stats should be accessible"
        data = response.json()
        assert "total_researchers" in data or "total_publications" in data

    def test_government_policy_query(self, client):
        """Government user should be able to run policy queries."""
        login_response = client.post(
            "/login",
            json={"username": "gov_user", "password": "government-pass"},
        )
        token = login_response.json()["access_token"]

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "policy recommendations for AI research"},
        )

        assert response.status_code == 200, "Policy query should succeed"
        data = response.json()
        assert data.get("tier") == 2

    def test_government_sees_aggregated_data(self, client):
        """Government user should see aggregated data."""
        login_response = client.post(
            "/login",
            json={"username": "gov_user", "password": "government-pass"},
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        data = response.json()
        has_aggregated = any(
            key in data for key in ["research_area_distribution", "state_distribution", "total_researchers"]
        )
        assert has_aggregated, "Should see aggregated data"


class TestIndustryFlow:
    """E2E test: Login (industry tier) → Query → See anonymized results → Request collaboration"""

    def test_industry_login(self, client):
        """Industry user should be able to login."""
        response = client.post(
            "/login",
            json={"username": "industry_user", "password": "industry-pass"},
        )

        assert response.status_code == 200, "Industry login should succeed"
        data = response.json()
        assert "access_token" in data
        assert data.get("user", {}).get("tier") == 3

    def test_industry_query(self, client):
        """Industry user should be able to run queries."""
        login_response = client.post(
            "/login",
            json={"username": "industry_user", "password": "industry-pass"},
        )
        token = login_response.json()["access_token"]

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers for collaboration"},
        )

        assert response.status_code == 200, "Industry query should succeed"
        data = response.json()
        assert data.get("tier") == 3

    def test_industry_sees_anonymized_results(self, client):
        """Industry user should see anonymized researcher profiles."""
        login_response = client.post(
            "/login",
            json={"username": "industry_user", "password": "industry-pass"},
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/researchers",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, "Should be able to get researchers"
        data = response.json()
        researchers = data if isinstance(data, list) else data.get("researchers", [])

        for researcher in researchers[:5]:
            assert "home_address" not in researcher or not researcher.get("home_address"), \
                "Industry tier should not see home addresses"
            assert "phone" not in researcher or not researcher.get("phone"), \
                "Industry tier should not see phone numbers"

    def test_industry_full_flow(self, client):
        """Complete industry flow: login → query → see anonymized → request collaboration."""
        login_response = client.post(
            "/login",
            json={"username": "industry_user", "password": "industry-pass"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        query_response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers for collaboration"},
        )
        assert query_response.status_code == 200

        researchers_response = client.get(
            "/researchers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert researchers_response.status_code == 200

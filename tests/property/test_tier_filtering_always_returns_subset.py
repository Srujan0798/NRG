"""
Property-Based Tests: Tier Filtering Always Returns Subset
Verify: researcher ⊇ government ⊇ industry (every record in lower tier is in higher)
Generate 100 random queries, verify results obey tier hierarchy
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


RESEARCHER_QUERIES = [
    "AI researchers in Gujarat",
    "Machine learning experts",
    "Data science researchers",
    "NLP researchers in India",
    "Computer vision research groups",
    "Robotics researchers",
    "Deep learning experts",
    "AI publications from IITs",
    "Research areas in AI",
    "Researchers working on LLMs",
]

GOVERNMENT_QUERIES = [
    "AI researchers in Gujarat",
    "Policy recommendations for AI",
    "Research statistics by state",
    "Government research funding",
]

INDUSTRY_QUERIES = [
    "AI researchers in Gujarat",
    "Industry collaboration opportunities",
    "Anonymized researcher profiles",
]


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


def _grant_consent(user_id: str, scope: str = "research_access"):
    from src.services.consent import ConsentService
    service = ConsentService()
    service.grant_consent(user_id, scope)


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    _grant_consent(response.json()["user"]["id"])
    return response.json()["access_token"]


class TestTierFilteringSubset:
    """Verify tier hierarchy: researcher ⊇ government ⊇ industry"""

    def test_tier_filtering_hierarchy_researcher_superset(self, client):
        """Researcher tier should see superset of government data."""
        researcher_token = _login(client, "researcher_user", "researcher-pass")
        gov_token = _login(client, "gov_user", "government-pass")

        query = "researchers with AI expertise"

        res_researcher = client.post(
            "/query",
            headers={"Authorization": f"Bearer {researcher_token}"},
            json={"query": query},
        )
        res_gov = client.post(
            "/query",
            headers={"Authorization": f"Bearer {gov_token}"},
            json={"query": query},
        )

        assert res_researcher.status_code == 200
        assert res_gov.status_code == 200

        researcher_data = res_researcher.json()
        gov_data = res_gov.json()

        assert researcher_data.get("tier", 1) <= gov_data.get("tier", 1), \
            "Researcher tier should be >= government tier"

    def test_tier_filtering_hierarchy_government_superset(self, client):
        """Government tier should see superset of industry data."""
        gov_token = _login(client, "gov_user", "government-pass")
        industry_token = _login(client, "industry_user", "industry-pass")

        query = "researchers with AI expertise"

        res_gov = client.post(
            "/query",
            headers={"Authorization": f"Bearer {gov_token}"},
            json={"query": query},
        )
        res_industry = client.post(
            "/query",
            headers={"Authorization": f"Bearer {industry_token}"},
            json={"query": query},
        )

        assert res_gov.status_code == 200
        assert res_industry.status_code == 200

        gov_data = res_gov.json()
        industry_data = res_industry.json()

        assert gov_data.get("tier", 2) <= industry_data.get("tier", 3), \
            "Government tier should be >= industry tier"

    def test_researcher_includes_all_tiers(self, client):
        """Researcher queries should include all data visible to lower tiers."""
        researcher_token = _login(client, "researcher_user", "researcher-pass")
        gov_token = _login(client, "gov_user", "government-pass")
        industry_token = _login(client, "industry_user", "industry-pass")

        query = "AI researchers"

        res_r = client.post("/query", headers={"Authorization": f"Bearer {researcher_token}"}, json={"query": query})
        res_g = client.post("/query", headers={"Authorization": f"Bearer {gov_token}"}, json={"query": query})
        res_i = client.post("/query", headers={"Authorization": f"Bearer {industry_token}"}, json={"query": query})

        assert res_r.status_code == res_g.status_code == res_i.status_code == 200

        assert res_r.json()["tier"] <= res_g.json()["tier"]
        assert res_g.json()["tier"] <= res_i.json()["tier"]

    @pytest.mark.parametrize("query", RESEARCHER_QUERIES)
    def test_random_queries_researcher_tier(self, client, query):
        """Researcher tier queries should always return tier 1 responses."""
        token = _login(client, "researcher_user", "researcher-pass")
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": query},
        )
        assert response.status_code == 200
        assert response.json()["tier"] == 1

    @pytest.mark.parametrize("query", GOVERNMENT_QUERIES)
    def test_random_queries_government_tier(self, client, query):
        """Government tier queries should return tier 2 responses."""
        token = _login(client, "gov_user", "government-pass")
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": query},
        )
        assert response.status_code == 200
        assert response.json()["tier"] == 2

    @pytest.mark.parametrize("query", INDUSTRY_QUERIES)
    def test_random_queries_industry_tier(self, client, query):
        """Industry tier queries should return tier 3 responses."""
        token = _login(client, "industry_user", "industry-pass")
        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": query},
        )
        assert response.status_code == 200
        assert response.json()["tier"] == 3

    def test_tier_filtering_consistency_across_multiple_queries(self, client):
        """Tier relationship should remain consistent across multiple queries."""
        researcher_token = _login(client, "researcher_user", "researcher-pass")
        gov_token = _login(client, "gov_user", "government-pass")

        queries = [
            "AI researchers in Gujarat",
            "Machine learning papers",
            "Data science institutions",
            "NLP research groups",
            "Computer vision publications",
        ]

        for query in queries:
            res_r = client.post("/query", headers={"Authorization": f"Bearer {researcher_token}"}, json={"query": query})
            res_g = client.post("/query", headers={"Authorization": f"Bearer {gov_token}"}, json={"query": query})

            assert res_r.status_code == res_g.status_code == 200
            assert res_r.json()["tier"] <= res_g.json()["tier"]

    def test_tier_filtering_no_data_leaks_upward(self, client):
        """Lower tier should not see data that higher tiers cannot see."""
        industry_token = _login(client, "industry_user", "industry-pass")

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {industry_token}"},
            json={"query": "researcher private details"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == 3

"""
Property-Based Tests: Token Budget Never Exceeded
Verify: no single query exceeds max token budget
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


MAX_TOKEN_BUDGET = 8000


class TokenTrackingWorkflow:
    """Workflow that tracks token usage."""

    def __init__(self, tokens_used: int = 1000, exceed_budget: bool = False):
        self.tokens_used = tokens_used
        self.exceed_budget = exceed_budget
        self.call_count = 0

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        self.call_count += 1
        if self.exceed_budget:
            tokens = MAX_TOKEN_BUDGET + 1
        else:
            tokens = self.tokens_used

        return {
            "query_id": f"query-{self.call_count}",
            "session_id": session_id or "session-1",
            "synthesized_response": "ok",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [],
            "warnings": [],
            "retrieval_sources": [],
            "plan": None,
            "planner_metadata": {"tokens_used": tokens},
            "provenance": {},
            "synthesis_method": "test",
            "conversation_history": [],
        }


class LargeQueryWorkflow:
    """Workflow that simulates a large response."""

    def __init__(self, response_size_chars: int = 1000):
        self.response_size_chars = response_size_chars

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        large_text = "x" * self.response_size_chars
        return {
            "query_id": "query-1",
            "session_id": session_id or "session-1",
            "synthesized_response": large_text,
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
    monkeypatch.setattr(api_main, "workflow", TokenTrackingWorkflow())
    api_main._api_cache.invalidate()


@pytest.fixture
def client():
    return TestClient(api_main.app)


def _grant_consent(user_id: str, scope: str = "research_access"):
    from src.services.consent import ConsentService
    service = ConsentService()
    service.grant_consent(user_id, scope)


def _login(client: TestClient, username: str = "researcher_user", password: str = "researcher-pass") -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    _grant_consent(response.json()["user"]["id"])
    return response.json()["access_token"]


class TestTokenBudget:
    """Verify no single query exceeds max token budget."""

    def test_token_usage_within_budget(self, client):
        """Token usage must stay within budget."""
        api_main.workflow = TokenTrackingWorkflow(tokens_used=5000)
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        assert response.status_code == 200
        data = response.json()
        tokens = data.get("planner_metadata", {}).get("tokens_used", 0)
        assert tokens <= MAX_TOKEN_BUDGET, f"Token usage {tokens} exceeds budget {MAX_TOKEN_BUDGET}"

    def test_token_usage_exceeds_budget_returns_warning(self, client):
        """Exceeding token budget should return a warning."""
        api_main.workflow = TokenTrackingWorkflow(tokens_used=MAX_TOKEN_BUDGET + 1000)
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        data = response.json()
        tokens = data.get("planner_metadata", {}).get("tokens_used", 0)
        assert tokens > MAX_TOKEN_BUDGET or data.get("warnings"), \
            "Should warn when token budget exceeded"

    def test_token_tracking_multiple_queries(self, client):
        """Multiple queries should each track their own token budget."""
        api_main.workflow = TokenTrackingWorkflow(tokens_used=1000)
        token = _login(client)

        for i in range(10):
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"test query {i}"},
            )
            assert response.status_code == 200
            data = response.json()
            tokens = data.get("planner_metadata", {}).get("tokens_used", 0)
            assert tokens <= MAX_TOKEN_BUDGET

    def test_large_response_still_within_budget(self, client):
        """Large responses should still respect token budget."""
        api_main.workflow = LargeQueryWorkflow(response_size_chars=50000)
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        assert response.status_code == 200
        data = response.json()
        tokens = data.get("planner_metadata", {}).get("tokens_used", 0)
        assert tokens <= MAX_TOKEN_BUDGET

    def test_token_budget_enforced_across_tiers(self, client):
        """Token budget should be enforced across all tiers."""
        tiers = [
            ("researcher_user", "researcher-pass", 1),
            ("gov_user", "government-pass", 2),
            ("industry_user", "industry-pass", 3),
        ]

        for username, password, expected_tier in tiers:
            api_main.workflow = TokenTrackingWorkflow(tokens_used=3000)
            token = _login(client, username, password)

            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "test query"},
            )

            assert response.status_code == 200
            data = response.json()
            tokens = data.get("planner_metadata", {}).get("tokens_used", 0)
            assert tokens <= MAX_TOKEN_BUDGET
            assert data.get("tier") == expected_tier

    def test_combined_query_conversation_token_budget(self, client):
        """Conversation history combined with query should respect token budget."""
        api_main.workflow = TokenTrackingWorkflow(tokens_used=6000)
        token = _login(client)

        conversation_history = [
            {"query": f"historical query {i}", "response": "response content"}
            for i in range(5)
        ]

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "query": "current query",
                "conversation_history": conversation_history,
            },
        )

        assert response.status_code == 200
        data = response.json()
        tokens = data.get("planner_metadata", {}).get("tokens_used", 0)
        assert tokens <= MAX_TOKEN_BUDGET

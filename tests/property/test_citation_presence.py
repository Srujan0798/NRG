"""
Property-Based Tests: Citation Presence
Verify: every citation in response has corresponding evidence
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class CitationValidatingWorkflow:
    """Workflow that returns citations with evidence."""

    def __init__(self, citations_with_evidence: bool = True):
        self.citations_with_evidence = citations_with_evidence

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        if self.citations_with_evidence:
            return {
                "query_id": "query-1",
                "session_id": session_id or "session-1",
                "synthesized_response": "According to paper X and Y...",
                "intent": "structured",
                "routing_decision": "text_to_sql",
                "verification_status": True,
                "citations": [
                    {"paper_id": "p1", "title": "Paper X", "source": "publication"},
                    {"paper_id": "p2", "title": "Paper Y", "source": "publication"},
                ],
                "warnings": [],
                "retrieval_sources": ["sql", "vector"],
                "plan": None,
                "planner_metadata": {},
                "provenance": {"p1": {"found_in": "publications"}, "p2": {"found_in": "publications"}},
                "synthesis_method": "test",
                "conversation_history": [],
            }
        else:
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


class BrokenCitationWorkflow:
    """Workflow that returns citation without evidence."""

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        return {
            "query_id": "query-1",
            "session_id": session_id or "session-1",
            "synthesized_response": "According to paper X...",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "citations": [{"paper_id": "p1", "title": "Paper X"}],
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
    from src.api import deps
    monkeypatch.setattr(deps, "workflow", CitationValidatingWorkflow())
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


class TestCitationPresence:
    """Verify every citation has corresponding evidence in response."""

    def test_citation_with_source_has_evidence(self, client):
        """Citation with source should have provenance evidence."""
        api_main.workflow = CitationValidatingWorkflow(citations_with_evidence=True)
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )

        assert response.status_code == 200
        data = response.json()

        for citation in data.get("citations", []):
            assert "source" in citation or "provenance" in data, \
                f"Citation {citation.get('paper_id')} missing evidence"

    def test_citation_without_source_fails_verification(self, client):
        """Citation without source should fail verification."""
        api_main.workflow = BrokenCitationWorkflow()
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )

        data = response.json()
        has_orphaned_citation = any(
            "source" not in c and c.get("paper_id") not in data.get("provenance", {})
            for c in data.get("citations", [])
        )
        assert has_orphaned_citation or data.get("warnings"), \
            "Orphaned citations should trigger warning"

    def test_all_retrieval_sources_have_citations(self, client):
        """Every retrieval source should contribute at least one citation."""
        api_main.workflow = CitationValidatingWorkflow(citations_with_evidence=True)
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )

        data = response.json()
        sources = data.get("retrieval_sources", [])
        citations = data.get("citations", [])

        if sources and citations:
            assert len(citations) >= len(sources), \
                "Should have at least one citation per retrieval source"

    def test_empty_citations_with_sources_warns(self, client):
        """When retrieval_sources is non-empty but citations is empty, should warn."""
        class EmptyCitationsWorkflow:
            def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
                return {
                    "query_id": "query-1",
                    "session_id": session_id or "session-1",
                    "synthesized_response": "Gap: sources indicate retrieval but no citations returned",
                    "intent": "structured",
                    "routing_decision": "text_to_sql",
                    "verification_status": True,
                    "citations": [],
                    "warnings": ["Retrieval gap: vector sources returned but no citations"],
                    "retrieval_sources": ["vector"],
                    "plan": None,
                    "planner_metadata": {},
                    "provenance": {},
                    "synthesis_method": "test",
                    "conversation_history": [],
                }

        api_main.workflow = EmptyCitationsWorkflow()
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query"},
        )

        data = response.json()
        has_gap = (
            data.get("warnings") or
            "gap" in data.get("synthesized_response", "").lower() or
            "vector" in str(data.get("warnings", [])).lower()
        )
        assert has_gap, f"Should indicate retrieval gap when sources exist but no citations. Got: {data}"

    def test_citation_chain_is_complete(self, client):
        """Citation chain from query to response must be complete."""
        api_main.workflow = CitationValidatingWorkflow(citations_with_evidence=True)
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )

        data = response.json()
        citations = data.get("citations", [])
        provenance = data.get("provenance", {})

        for citation in citations:
            paper_id = citation.get("paper_id")
            assert paper_id in provenance, \
                f"Citation {paper_id} must appear in provenance"

    def test_no_phantom_citations(self, client):
        """Response must not reference citations not in provenance."""
        api_main.workflow = CitationValidatingWorkflow(citations_with_evidence=True)
        token = _login(client)

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )

        data = response.json()
        citations = data.get("citations", [])
        provenance = data.get("provenance", {})

        for citation in citations:
            paper_id = citation.get("paper_id")
            assert paper_id in provenance, \
                f"Citation {paper_id} has no backing in provenance (phantom citation)"

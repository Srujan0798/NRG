"""
Pytest Configuration for NRG Test Suite
Defines markers, fixtures, and test categorization for CI blocking gates.
"""

import os
os.environ["NRG_ENV"] = "dev"
os.environ["NRG_QUOTA_DISABLED"] = "1"

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "regression(bug_id, description): regression test for a fixed bug"
    )
    config.addinivalue_line(
        "markers", "security: security tests that block deployment"
    )
    config.addinivalue_line(
        "markers", "contract: API contract validation tests"
    )
    config.addinivalue_line(
        "markers", "chaos: chaos engineering tests"
    )
    config.addinivalue_line(
        "markers", "load: load and performance tests that block on thresholds"
    )
    config.addinivalue_line(
        "markers", "e2e: end-to-end persona flow tests"
    )
    config.addinivalue_line(
        "markers", "slow: slow-running tests that can be skipped locally"
    )
    config.addinivalue_line(
        "markers", "requires_qdrant: tests that require Qdrant vector DB (skipped if unavailable)"
    )
    config.addinivalue_line(
        "markers", "requires_llm: tests that require LLM API access (skipped if unavailable)"
    )
    config.addinivalue_line(
        "markers", "requires_redis: tests that require Redis (skipped if unavailable)"
    )
    config.addinivalue_line(
        "markers", "requires_db: tests that require a live database (skipped if unavailable)"
    )


def _is_service_available(env_var: str) -> bool:
    """Check if an external service is reachable via environment variable or connection."""
    val = os.environ.get(env_var, "").lower()
    if val in ("1", "true", "yes"):
        return True
    return False


def pytest_collection_modifyitems(items):
    """Auto-mark tests based on their location; skip tests requiring unavailable services."""
    for item in items:
        if "test_security" in item.nodeid or "/security/" in item.nodeid:
            item.add_marker(pytest.mark.security)
        if "test_contract" in item.nodeid or "/contract/" in item.nodeid:
            item.add_marker(pytest.mark.contract)
        if "test_chaos" in item.nodeid or "/chaos/" in item.nodeid:
            item.add_marker(pytest.mark.chaos)
        if "test_load" in item.nodeid or "/load/" in item.nodeid:
            item.add_marker(pytest.mark.load)
        if "test_e2e" in item.nodeid or "/e2e/" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        if "test_regression" in item.nodeid or "/regression/" in item.nodeid:
            item.add_marker(pytest.mark.regression)

        if item.get_closest_marker("requires_qdrant"):
            if not _is_service_available("QDRANT_AVAILABLE"):
                item.add_marker(pytest.mark.skip(reason="Qdrant not available (set QDRANT_AVAILABLE=1 to enable)"))
        if item.get_closest_marker("requires_llm"):
            if not _is_service_available("LLM_AVAILABLE"):
                item.add_marker(pytest.mark.skip(reason="LLM not available (set LLM_AVAILABLE=1 to enable)"))
        if item.get_closest_marker("requires_redis"):
            if not _is_service_available("REDIS_AVAILABLE"):
                item.add_marker(pytest.mark.skip(reason="Redis not available (set REDIS_AVAILABLE=1 to enable)"))
        if item.get_closest_marker("requires_db"):
            if not _is_service_available("DB_AVAILABLE"):
                item.add_marker(pytest.mark.skip(reason="Database not available (set DB_AVAILABLE=1 to enable)"))


@pytest.fixture
def sample_researcher_records():
    """Standard sample researcher records for testing."""
    return [
        {
            "researcher_id": "researcher-1",
            "name": "Dr. Owner",
            "institution_id": "iitgn",
            "state": "GJ",
            "research_area": "Robotics",
            "year_joined": 2020,
            "email": "owner@example.com",
            "phone": "9876543210",
            "orcid": "0000-0001",
            "home_address": "Gandhinagar, Gujarat",
        },
        {
            "researcher_id": "researcher-2",
            "name": "Dr. Public",
            "institution_id": "iisc",
            "state": "KA",
            "research_area": "AI",
            "year_joined": 2019,
            "email": "public@example.com",
            "phone": "9123456780",
            "orcid": "0000-0002",
            "home_address": "Bangalore, Karnataka",
        },
    ]


@pytest.fixture
def stub_workflow():
    """Standard stub workflow for tests."""
    class StubWorkflow:
        def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
            return {
                "query_id": "query-1",
                "session_id": session_id or "session-1",
                "synthesized_response": "ok",
                "intent": "structured",
                "routing_decision": "text_to_sql",
                "verification_status": True,
                "conversation_history": [],
            }
    return StubWorkflow()

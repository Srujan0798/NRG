"""
Pytest Configuration for NRG Test Suite
Defines markers, fixtures, and test categorization for CI blocking gates.
"""

import os
from pathlib import Path

os.environ["NRG_ENV"] = "dev"
os.environ["NRG_QUOTA_DISABLED"] = "1"
os.environ.setdefault("DATABASE_URL", "sqlite:///nrg_research.db")

import pytest


PATH_CATEGORY_MARKERS: dict[str, tuple[str, ...]] = {
    "chaos": ("chaos",),
    "contract": ("contract",),
    "e2e": ("e2e",),
    "evals": ("evals",),
    "load": ("load",),
    "performance": ("load",),
    "property": ("property",),
    "regression": ("regression",),
    "security": ("security",),
    "uat": ("uat",),
}

INTEGRATION_DIRS = frozenset(
    {
        "api",
        "chaos",
        "contract",
        "evals",
        "ingestion",
        "integration",
        "load",
        "performance",
        "regression",
    }
)
E2E_DIRS = frozenset({"e2e", "uat"})

XDIST_GROUP_BY_DIR = {
    "api": "api-stack",
    "audit": "audit-chain",
    "chaos": "external-service",
    "e2e": "e2e-stack",
    "integration": "api-stack",
    "load": "load-stack",
    "performance": "load-stack",
    "uat": "e2e-stack",
}


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: tests that exercise external services or API boundaries"
    )
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
        "markers", "evals: evaluation tests for model quality"
    )
    config.addinivalue_line(
        "markers", "property: property-based tests for invariants"
    )
    config.addinivalue_line(
        "markers", "slow: slow-running tests that can be skipped locally"
    )
    config.addinivalue_line(
        "markers", "uat: user acceptance tests against live API"
    )
    config.addinivalue_line(
        "markers", "xdist_group(name): keep tests with shared services/state on the same xdist worker"
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


def _test_subdir(item: pytest.Item) -> str:
    """Return the first path component under tests/ for a collected item."""
    path = Path(str(item.fspath))
    parts = path.parts
    if "tests" not in parts:
        return ""
    tests_index = parts.index("tests")
    if len(parts) <= tests_index + 1:
        return ""
    return parts[tests_index + 1]


def _add_marker_once(item: pytest.Item, marker_name: str) -> None:
    if not item.get_closest_marker(marker_name):
        item.add_marker(getattr(pytest.mark, marker_name))


def _add_xdist_group(item: pytest.Item, group_name: str) -> None:
    item.add_marker(pytest.mark.xdist_group(group_name))


def _apply_tier_marker(item: pytest.Item, subdir: str) -> None:
    """Ensure every test has a unit/integration/e2e tier marker."""
    if item.get_closest_marker("e2e") or subdir in E2E_DIRS:
        _add_marker_once(item, "e2e")
        return
    if (
        item.get_closest_marker("integration")
        or item.get_closest_marker("contract")
        or item.get_closest_marker("chaos")
        or item.get_closest_marker("load")
        or subdir in INTEGRATION_DIRS
    ):
        _add_marker_once(item, "integration")
        return
    _add_marker_once(item, "unit")


def pytest_collection_modifyitems(items):
    """Auto-mark tests based on their location; skip tests requiring unavailable services."""
    for item in items:
        subdir = _test_subdir(item)

        for marker_name in PATH_CATEGORY_MARKERS.get(subdir, ()):
            _add_marker_once(item, marker_name)
        if "test_security" in item.nodeid:
            _add_marker_once(item, "security")
        if "test_contract" in item.nodeid:
            _add_marker_once(item, "contract")
        if "test_chaos" in item.nodeid:
            _add_marker_once(item, "chaos")
        if "test_load" in item.nodeid:
            _add_marker_once(item, "load")
        if "test_e2e" in item.nodeid:
            _add_marker_once(item, "e2e")
        if "test_regression" in item.nodeid:
            _add_marker_once(item, "regression")

        _apply_tier_marker(item, subdir)

        if subdir in XDIST_GROUP_BY_DIR:
            _add_xdist_group(item, XDIST_GROUP_BY_DIR[subdir])
        if item.get_closest_marker("requires_qdrant"):
            _add_xdist_group(item, "external-service")
        if item.get_closest_marker("requires_redis"):
            _add_xdist_group(item, "external-service")
        if item.get_closest_marker("requires_db"):
            _add_xdist_group(item, "external-service")
        if "kong" in item.nodeid:
            _add_xdist_group(item, "external-service")

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

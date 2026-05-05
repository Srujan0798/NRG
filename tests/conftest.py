"""
Pytest Configuration for NRG Test Suite
Defines markers, fixtures, and test categorization for CI blocking gates.
"""

import os
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

os.environ["NRG_ENV"] = "dev"
os.environ["NRG_QUOTA_DISABLED"] = "1"
os.environ.setdefault("DATABASE_URL", "sqlite:///nrg_research.db")


def _configure_isolated_audit_dir() -> None:
    """Give each xdist worker its own audit chain when the suite asks for isolation."""
    if os.environ.get("NRG_TEST_ISOLATE_AUDIT") != "1":
        return
    base = Path(os.environ.get("NRG_TEST_AUDIT_BASE", ".pytest_audit"))
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
    audit_dir = base / worker_id
    audit_dir.mkdir(parents=True, exist_ok=True)
    os.environ["NRG_AUDIT_DIR"] = str(audit_dir)


_configure_isolated_audit_dir()


def _prepare_ci_sqlite_database() -> None:
    """Build the ignored local SQLite mirror on GitHub runners before collection."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    if os.environ.get("NRG_SKIP_CI_SQLITE_PREP") == "1":
        return

    repo_root = Path(__file__).resolve().parents[1]
    default_root_urls = {
        "",
        "sqlite:///nrg_research.db",
        f"sqlite:///{repo_root / 'nrg_research.db'}",
    }
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url in default_root_urls:
        db_url = "sqlite:///data/nrg_research.db"
        os.environ["DATABASE_URL"] = db_url
    os.environ.setdefault("NRG_TEST_DATABASE_URL", db_url)
    if not db_url.startswith("sqlite:///"):
        return

    raw_path = Path(db_url.removeprefix("sqlite:///"))
    db_path = raw_path if raw_path.is_absolute() else repo_root / raw_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    marker = db_path.with_suffix(db_path.suffix + ".ci-ready")
    lock_dir = db_path.with_suffix(db_path.suffix + ".lock")
    deadline = time.monotonic() + 60

    while True:
        try:
            lock_dir.mkdir()
            break
        except FileExistsError:
            if marker.exists():
                return
            if time.monotonic() > deadline:
                raise RuntimeError(f"Timed out waiting for CI SQLite seed lock: {lock_dir}")
            time.sleep(0.2)

    try:
        if marker.exists():
            return
        existing_root_db = repo_root / "nrg_research.db"
        if existing_root_db.exists() and not db_path.exists():
            shutil.copyfile(existing_root_db, db_path)
        subprocess.run(
            [
                sys.executable,
                str(repo_root / "scripts" / "seed_production_subset.py"),
                "--profile",
                "ci",
                "--no-audit",
            ],
            cwd=repo_root,
            check=True,
        )
        marker.write_text("ready\n", encoding="utf-8")
    finally:
        try:
            lock_dir.rmdir()
        except OSError:
            pass


_prepare_ci_sqlite_database()

import pytest  # noqa: E402


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
LIVE_API_TEST_PREFIXES = (
    "tests/api/test_tier_isolation_live.py",
    "tests/security/test_red_team_v41.py",
)
_LIVE_API_REACHABLE: bool | None = None


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


def _live_api_base_url() -> str:
    return (
        os.environ.get("API_URL")
        or os.environ.get("NRG_BASE_URL")
        or os.environ.get("NRG_API_URL")
        or "http://localhost:8000"
    ).rstrip("/")


def _is_live_api_reachable() -> bool:
    """Return whether the local/live API is ready for request-based tests."""
    global _LIVE_API_REACHABLE
    if _LIVE_API_REACHABLE is not None:
        return _LIVE_API_REACHABLE

    try:
        timeout = float(os.environ.get("NRG_LIVE_API_HEALTH_TIMEOUT", "5"))
        with urllib.request.urlopen(f"{_live_api_base_url()}/health/db", timeout=timeout) as response:
            if not (200 <= response.status < 500):
                _LIVE_API_REACHABLE = False
            else:
                payload = json.loads(response.read().decode("utf-8"))
                _LIVE_API_REACHABLE = payload.get("ready") is True
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        _LIVE_API_REACHABLE = False
    return _LIVE_API_REACHABLE


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


def _is_live_api_test(item: pytest.Item) -> bool:
    nodeid = item.nodeid.replace("\\", "/")
    return any(nodeid.startswith(prefix) for prefix in LIVE_API_TEST_PREFIXES)


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


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items):
    """Auto-mark tests based on their location; skip tests requiring unavailable services."""
    for item in items:
        subdir = _test_subdir(item)
        live_api_test = _is_live_api_test(item)

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
        if live_api_test:
            _add_marker_once(item, "uat")
            _add_xdist_group(item, "live-api")
            if os.environ.get("NRG_REQUIRE_LIVE_API") != "1" and not _is_live_api_reachable():
                item.add_marker(
                    pytest.mark.skip(
                        reason=(
                            "Live API not reachable; run "
                            "`scripts/run_test_suite.sh --live-api` for managed live API tests"
                        )
                    )
                )

        _apply_tier_marker(item, subdir)

        if subdir in XDIST_GROUP_BY_DIR and not live_api_test:
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

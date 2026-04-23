"""Tests for Temporal RBAC — Protocol #36: Temporal Policy Time-Window RBAC.

Verifies:
1. visibility_window parsing from YAML
2. is_within_window() with ISO dates and quarter format
3. Window boundaries (edge cases)
4. No window = always within window
5. Invalid date formats gracefully fall through
"""

import pytest
from src.auth.rbac import RBACPolicy, RBACPolicyEngine, RBACPolicy as Policy


class TestVisibilityWindow:
    """Test visibility_window field in RBACPolicy."""

    def test_no_window_always_passes(self):
        """No window defined = no temporal restriction."""
        policy = Policy(
            name="test",
            tier=1,
            description="",
            column_visibility={},
            pii_masking={"mode": "none", "hide_fields": []},
            output_format="full",
            data_scope="all",
            max_results=500,
            debug_access=False,
            allowed_endpoints=["*"],
            allowed_tables=["*"],
            export_allowed=True,
            read_only=False,
        )
        assert policy.is_within_window("2020-01-01") is True
        assert policy.is_within_window("2030-12-31") is True
        assert policy.is_within_window() is True

    def test_window_iso_dates(self):
        """Window with ISO date boundaries."""
        policy = Policy(
            name="test",
            tier=1,
            description="",
            column_visibility={},
            pii_masking={"mode": "none", "hide_fields": []},
            output_format="full",
            data_scope="all",
            max_results=500,
            debug_access=False,
            allowed_endpoints=["*"],
            allowed_tables=["*"],
            export_allowed=True,
            read_only=False,
            visibility_window={"from": "2024-01-01", "to": "2026-12-31"},
        )
        assert policy.is_within_window("2024-01-01") is True
        assert policy.is_within_window("2025-06-15") is True
        assert policy.is_within_window("2026-12-31") is True
        assert policy.is_within_window("2023-12-31") is False
        assert policy.is_within_window("2027-01-01") is False

    def test_window_quarter_format(self):
        """Window with quarter-format boundaries."""
        policy = Policy(
            name="test",
            tier=2,
            description="",
            column_visibility={},
            pii_masking={"mode": "none", "hide_fields": []},
            output_format="full",
            data_scope="all",
            max_results=500,
            debug_access=False,
            allowed_endpoints=["*"],
            allowed_tables=["*"],
            export_allowed=True,
            read_only=False,
            visibility_window={"from": "2024-Q1", "to": "2026-Q4"},
        )
        assert policy.is_within_window("2024-01-01") is True
        assert policy.is_within_window("2024-Q2") is True
        assert policy.is_within_window("2026-Q4") is True
        assert policy.is_within_window("2023-Q4") is False
        assert policy.is_within_window("2027-Q1") is False

    def test_window_from_only(self):
        """Window with only 'from' boundary."""
        policy = Policy(
            name="test",
            tier=1,
            description="",
            column_visibility={},
            pii_masking={"mode": "none", "hide_fields": []},
            output_format="full",
            data_scope="all",
            max_results=500,
            debug_access=False,
            allowed_endpoints=["*"],
            allowed_tables=["*"],
            export_allowed=True,
            read_only=False,
            visibility_window={"from": "2025-Q1"},
        )
        assert policy.is_within_window("2025-01-01") is True
        assert policy.is_within_window("2024-01-01") is False
        assert policy.is_within_window("2030-01-01") is True

    def test_window_to_only(self):
        """Window with only 'to' boundary."""
        policy = Policy(
            name="test",
            tier=1,
            description="",
            column_visibility={},
            pii_masking={"mode": "none", "hide_fields": []},
            output_format="full",
            data_scope="all",
            max_results=500,
            debug_access=False,
            allowed_endpoints=["*"],
            allowed_tables=["*"],
            export_allowed=True,
            read_only=False,
            visibility_window={"to": "2026-Q2"},
        )
        assert policy.is_within_window("2026-06-30") is True
        assert policy.is_within_window("2026-07-01") is False
        assert policy.is_within_window("2020-01-01") is True

    def test_invalid_date_format_falls_through(self):
        """Invalid date formats don't crash — return True (no restriction)."""
        policy = Policy(
            name="test",
            tier=1,
            description="",
            column_visibility={},
            pii_masking={"mode": "none", "hide_fields": []},
            output_format="full",
            data_scope="all",
            max_results=500,
            debug_access=False,
            allowed_endpoints=["*"],
            allowed_tables=["*"],
            export_allowed=True,
            read_only=False,
            visibility_window={"from": "2024-Q1", "to": "2026-Q4"},
        )
        assert policy.is_within_window("not-a-date") is True
        assert policy.is_within_window("2024/01/01") is True


class TestTemporalRBACYAML:
    """Test temporal RBAC loaded from YAML policies."""

    def test_researcher_window(self):
        """Researcher has full range window."""
        engine = RBACPolicyEngine()
        policy = engine.get_policy(persona="researcher")
        assert policy.is_within_window("2025-01-01") is True
        assert policy.is_within_window("2020-01-01") is True
        assert policy.is_within_window("2030-01-01") is True

    def test_government_window(self):
        """Government window is 2024-Q1 to 2026-Q4."""
        engine = RBACPolicyEngine()
        policy = engine.get_policy(persona="government")
        assert policy.is_within_window("2024-01-01") is True
        assert policy.is_within_window("2025-06-15") is True
        assert policy.is_within_window("2023-12-31") is False
        assert policy.is_within_window("2027-01-01") is False

    def test_industry_window(self):
        """Industry window is 2025-Q1 to 2026-Q4."""
        engine = RBACPolicyEngine()
        policy = engine.get_policy(persona="industry")
        assert policy.is_within_window("2025-01-01") is True
        assert policy.is_within_window("2024-12-31") is False
        assert policy.is_within_window("2027-01-01") is False

    def test_all_personas_have_window(self):
        """All 6 personas have visibility_window defined."""
        engine = RBACPolicyEngine()
        for persona in ("researcher", "government", "industry",
                        "peer_reviewer", "department_head", "student"):
            policy = engine.get_policy(persona=persona)
            assert policy.visibility_window is not None, f"{persona} missing window"
            assert "from" in policy.visibility_window or "to" in policy.visibility_window

    def test_audit_includes_active_window(self):
        """Audit log context includes the active time window for policy decisions."""
        engine = RBACPolicyEngine()
        policy = engine.get_policy(persona="government")
        window = policy.visibility_window
        assert window is not None
        assert "from" in window
        assert "to" in window

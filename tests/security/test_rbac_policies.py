"""Security Tests — RBAC Policy Engine (YAML-driven)."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auth.rbac import (
    RBACPolicyEngine,
    reset_policy_engine,
)

MINIMAL_TEST_POLICIES = {
    "researcher": {
        "tier": 1,
        "description": "Researcher",
        "column_visibility": {
            "researchers": ["*"],
            "institutions": ["*"],
            "labs": ["*"],
            "publications": ["*"],
        },
        "pii_masking": {"mode": "none", "hide_fields": []},
        "output_format": "full",
        "data_scope": "all",
        "max_results": 1000,
        "debug_access": True,
        "allowed_endpoints": ["*"],
        "allowed_tables": ["*"],
        "export_allowed": True,
        "read_only": False,
    },
    "government": {
        "tier": 2,
        "description": "Government",
        "column_visibility": {
            "researchers": ["institution_id", "state", "research_area"],
            "institutions": ["name", "type", "state"],
        },
        "pii_masking": {
            "mode": "aggregate",
            "hide_fields": ["email", "phone"],
        },
        "output_format": "aggregated",
        "data_scope": "all",
        "max_results": 500,
        "debug_access": False,
        "allowed_endpoints": ["*"],
        "allowed_tables": ["*"],
        "export_allowed": True,
        "read_only": True,
    },
    "industry": {
        "tier": 3,
        "description": "Industry",
        "column_visibility": {
            "researchers": ["researcher_id", "name", "institution_id", "research_area"],
            "institutions": ["name", "type"],
        },
        "pii_masking": {
            "mode": "full",
            "hide_fields": ["email", "phone", "aadhaar_number", "pan_number"],
        },
        "output_format": "anonymized",
        "data_scope": "anonymized",
        "max_results": 100,
        "debug_access": False,
        "allowed_endpoints": ["*"],
        "allowed_tables": ["researchers", "institutions"],
        "export_allowed": False,
        "read_only": True,
    },
}


class TestRBACPolicyEngineBasics:
    """Phase 1: Verify YAML-driven policy engine loads correctly."""

    def setup_method(self):
        reset_policy_engine()

    def teardown_method(self):
        reset_policy_engine()

    def test_loads_from_yaml(self):
        """Verify engine loads from bundled rbac_policies.yaml."""
        engine = RBACPolicyEngine()
        personas = engine.list_personas()
        assert len(personas) >= 3
        names = {p.name for p in personas}
        assert "researcher" in names
        assert "government" in names
        assert "industry" in names

    def test_loads_from_dict(self):
        """Verify engine can load from a dict (for testing/runtime)."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        personas = engine.list_personas()
        assert len(personas) == 3

    def test_resolve_by_tier_int(self):
        """Integer tier 1/2/3 maps to researcher/government/industry."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)

        p1 = engine.get_policy(tier=1)
        assert p1.name == "researcher"
        assert p1.output_format == "full"

        p2 = engine.get_policy(tier=2)
        assert p2.name == "government"
        assert p2.output_format == "aggregated"

        p3 = engine.get_policy(tier=3)
        assert p3.name == "industry"
        assert p3.output_format == "anonymized"

    def test_resolve_by_persona_name(self):
        """Direct lookup by persona name."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)

        p = engine.get_policy(persona="government")
        assert p.tier == 2
        assert p.output_format == "aggregated"

    def test_unknown_persona_raises(self):
        """Unknown persona name raises KeyError."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        with pytest.raises(KeyError):
            engine.get_policy(persona="nonexistent_persona")

    def test_unknown_tier_raises(self):
        """Unknown tier level raises KeyError."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        with pytest.raises(KeyError):
            engine.get_policy(tier=99)

    def test_resolve_tier_or_persona__int_claim(self):
        """resolve_tier_or_persona accepts integer tier in claims."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        policy = engine.resolve_tier_or_persona({"tier": 2})
        assert policy.name == "government"

    def test_resolve_tier_or_persona__string_claim(self):
        """resolve_tier_or_persona accepts persona string in claims."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        policy = engine.resolve_tier_or_persona({"persona": "industry"})
        assert policy.name == "industry"

    def test_resolve_tier_or_persona__persona_precedence(self):
        """Persona name takes precedence over integer tier in claims."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        policy = engine.resolve_tier_or_persona({"persona": "researcher", "tier": 3})
        assert policy.name == "researcher"

    def test_resolve_tier_or_persona__defaults_to_researcher(self):
        """Invalid claims default to researcher (tier 1)."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        policy = engine.resolve_tier_or_persona({})
        assert policy.name == "researcher"

    def test_tier_for_persona(self):
        """tier_for_persona returns the tier number for a named persona."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        assert engine.tier_for_persona("government") == 2
        assert engine.tier_for_persona("nonexistent") is None


class TestBackwardCompatibility:
    """Verify all 3 existing tiers work identically through policy engine (zero regression)."""

    def setup_method(self):
        reset_policy_engine()

    def teardown_method(self):
        reset_policy_engine()

    def test_researcher_tier1__full_access(self):
        """Tier 1 researcher: all columns visible, no PII masking."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        p = engine.get_policy(tier=1)

        assert p.output_format == "full"
        assert p.data_scope == "all"
        assert p.max_results == 1000
        assert p.export_allowed is True
        assert p.read_only is False
        assert p.debug_access is True

        cols = engine.get_visible_columns(p, "researchers")
        assert cols == ["*"]

    def test_government_tier2__aggregated(self):
        """Tier 2 government: aggregated output, masked PII."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        p = engine.get_policy(tier=2)

        assert p.output_format == "aggregated"
        assert p.data_scope == "all"
        assert p.max_results == 500
        assert p.export_allowed is True
        assert p.read_only is True
        assert p.debug_access is False

        cols = engine.get_visible_columns(p, "researchers")
        assert "institution_id" in cols
        assert "email" not in cols

        assert p.should_mask_field("email") is True
        assert p.should_mask_field("name") is False

    def test_industry_tier3__anonymized(self):
        """Tier 3 industry: anonymized output, full PII masking."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        p = engine.get_policy(tier=3)

        assert p.output_format == "anonymized"
        assert p.data_scope == "anonymized"
        assert p.max_results == 100
        assert p.export_allowed is False
        assert p.read_only is True
        assert p.debug_access is False

        cols = engine.get_visible_columns(p, "researchers")
        assert "name" in cols
        assert "email" not in cols
        assert "phone" not in cols

        assert p.should_mask_field("email") is True
        assert p.should_mask_field("phone") is True
        assert p.should_mask_field("aadhaar_number") is True


class TestColumnFiltering:
    """Column visibility per table and persona."""

    def setup_method(self):
        reset_policy_engine()

    def teardown_method(self):
        reset_policy_engine()

    def test_wildcard_shows_all_columns(self):
        """[*] visibility means all columns visible (subject to PII masking)."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        p = engine.get_policy(persona="researcher")
        cols = engine.get_visible_columns(p, "researchers")
        assert cols == ["*"]

    def test_explicit_column_list(self):
        """Explicit column list restricts visibility."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        p = engine.get_policy(persona="government")
        cols = engine.get_visible_columns(p, "researchers")
        assert set(cols) == {"institution_id", "state", "research_area"}

    def test_empty_list_hides_table(self):
        """Empty column list means table is fully hidden."""
        engine = RBACPolicyEngine(policies={
            "student": {
                **MINIMAL_TEST_POLICIES["industry"],
                "name": "student",
                "tier": 3,
                "column_visibility": {
                    "publications": ["publication_id", "title", "year"],
                    "researchers": [],  # Fully hidden
                },
            },
        })
        p = engine.get_policy(persona="student")
        assert engine.get_visible_columns(p, "researchers") == []
        assert p.is_table_visible("researchers") is False

    def test_filter_row_by_policy__wildcard(self):
        """Filter row with [*] visibility applies PII masking only."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        p = engine.get_policy(persona="researcher")

        row = {
            "researcher_id": "R001",
            "name": "Dr. Smith",
            "email": "smith@iit.edu",
            "phone": "9876543210",
            "state": "Gujarat",
        }

        filtered = engine.filter_row_by_policy(p, "researchers", row)
        assert filtered["name"] == "Dr. Smith"
        assert filtered["email"] == "smith@iit.edu"

    def test_filter_row_by_policy__government(self):
        """Filter row for government: visible columns only. Columns not in visibility list are dropped."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        p = engine.get_policy(persona="government")

        row = {
            "researcher_id": "R001",
            "name": "Dr. Smith",
            "email": "smith@iit.edu",
            "phone": "9876543210",
            "state": "Gujarat",
            "research_area": "AI",
        }

        filtered = engine.filter_row_by_policy(p, "researchers", row)
        assert "name" not in filtered
        assert "email" not in filtered
        assert "phone" not in filtered
        assert filtered["state"] == "Gujarat"
        assert filtered["research_area"] == "AI"

    def test_filter_row_by_policy__industry_anon(self):
        """Filter row for industry: visible columns only. Columns in hide_fields but visible are masked."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        p = engine.get_policy(persona="industry")

        row = {
            "researcher_id": "R001",
            "name": "Dr. Smith",
            "email": "smith@iit.edu",
            "phone": "9876543210",
            "state": "Gujarat",
            "research_area": "AI",
        }

        filtered = engine.filter_row_by_policy(p, "researchers", row)
        assert filtered["name"] == "Dr. Smith"
        assert "email" not in filtered
        assert "phone" not in filtered


class TestEndpointAccess:
    """Endpoint and table access control."""

    def setup_method(self):
        reset_policy_engine()

    def teardown_method(self):
        reset_policy_engine()

    def test_wildcard_allows_all_endpoints(self):
        """[*] allowed_endpoints permits all paths."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        p = engine.get_policy(persona="researcher")
        assert engine.is_endpoint_allowed(p, "/api/researchers") is True
        assert engine.is_endpoint_allowed(p, "/api/admin/rbac") is True

    def test_industry_table_restriction(self):
        """Industry persona is restricted to specific tables."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        p = engine.get_policy(persona="industry")
        assert engine.is_table_allowed(p, "researchers") is True
        assert engine.is_table_allowed(p, "funding_records") is False
        assert engine.is_table_allowed(p, "publications") is False


class TestPolicyCache:
    """Policy cache ensures hot-reload without re-parse."""

    def setup_method(self):
        reset_policy_engine()

    def teardown_method(self):
        reset_policy_engine()

    def test_cache_returns_same_policy_instance(self):
        """Multiple get_policy calls return same RBACPolicy instance."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        p1 = engine.get_policy(persona="government")
        p2 = engine.get_policy(persona="government")
        assert p1 is p2

    def test_add_or_update_runtime(self):
        """add_or_update_policy modifies cache at runtime (no YAML change)."""
        engine = RBACPolicyEngine(policies=dict(MINIMAL_TEST_POLICIES))
        assert not engine.persona_exists("student")

        engine.add_or_update_policy("student", {
            "tier": 3,
            "description": "Student",
            "column_visibility": {"researchers": [], "publications": ["*"]},
            "pii_masking": {"mode": "full", "hide_fields": ["email", "phone"]},
            "output_format": "anonymized",
            "data_scope": "open_access",
            "max_results": 50,
            "debug_access": False,
            "allowed_endpoints": ["*"],
            "allowed_tables": ["publications"],
            "export_allowed": False,
            "read_only": True,
        })

        assert engine.persona_exists("student")
        p = engine.get_policy(persona="student")
        assert p.tier == 3
        assert p.max_results == 50

    def test_deactivate_persona(self):
        """deactivate_persona sets is_active=False for non-built-in personas."""
        engine = RBACPolicyEngine(policies=dict(MINIMAL_TEST_POLICIES))

        engine.add_or_update_policy("custom_reviewer", {
            "tier": 1, "description": "Custom",
            "column_visibility": {"researchers": ["*"]},
            "pii_masking": {"mode": "none", "hide_fields": []},
            "output_format": "full", "data_scope": "all", "max_results": 500,
            "debug_access": False, "allowed_endpoints": ["*"], "allowed_tables": ["*"],
            "export_allowed": False, "read_only": True,
        })

        success = engine.deactivate_persona("custom_reviewer")
        assert success is True

        success2 = engine.deactivate_persona("custom_reviewer")
        assert success2 is False

        with pytest.raises(KeyError):
            engine.get_policy(persona="custom_reviewer")

    def test_cannot_deactivate_nonexistent(self):
        """Deactivating nonexistent persona returns False."""
        engine = RBACPolicyEngine(policies=MINIMAL_TEST_POLICIES)
        success = engine.deactivate_persona("nonexistent")
        assert success is False

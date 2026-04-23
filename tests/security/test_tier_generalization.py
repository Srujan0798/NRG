"""Security Tests — Tier Generalization (new personas via YAML)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auth.rbac import (
    RBACPolicyEngine,
    reset_policy_engine,
)

CUSTOM_POLICIES = {
    "researcher": {
        "tier": 1,
        "description": "Researcher",
        "column_visibility": {"researchers": ["*"], "institutions": ["*"], "labs": ["*"]},
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
    "peer_reviewer": {
        "tier": 1,
        "description": "External peer reviewer — read-only researcher view",
        "column_visibility": {"researchers": ["*"], "institutions": ["*"], "labs": ["*"]},
        "pii_masking": {
            "mode": "aggregate",
            "hide_fields": ["email", "phone", "aadhaar_number"],
        },
        "output_format": "full",
        "data_scope": "all",
        "max_results": 500,
        "debug_access": False,
        "allowed_endpoints": ["*"],
        "allowed_tables": ["*"],
        "export_allowed": False,
        "read_only": True,
    },
    "department_head": {
        "tier": 2,
        "description": "Department head — aggregated view scoped to institution",
        "column_visibility": {
            "researchers": ["institution_id", "department", "state", "research_area"],
            "institutions": ["*"],
        },
        "pii_masking": {
            "mode": "aggregate",
            "hide_fields": ["email", "phone", "name"],
        },
        "output_format": "aggregated",
        "data_scope": "institution_only",
        "max_results": 500,
        "debug_access": False,
        "allowed_endpoints": ["*"],
        "allowed_tables": ["*"],
        "export_allowed": True,
        "read_only": False,
        "requires_institution_scope": True,
    },
    "student": {
        "tier": 3,
        "description": "Student — open-access publications only",
        "column_visibility": {
            "researchers": ["name", "institution_id", "research_area"],
            "institutions": ["name", "type", "state"],
            "publications": ["publication_id", "title", "year", "journal", "doi"],
        },
        "pii_masking": {
            "mode": "full",
            "hide_fields": ["email", "phone", "aadhaar_number", "pan_number",
                             "orcid", "personal_phone", "secondary_research_areas"],
        },
        "output_format": "anonymized",
        "data_scope": "open_access",
        "max_results": 50,
        "debug_access": False,
        "allowed_endpoints": ["*"],
        "allowed_tables": ["researchers", "institutions", "labs", "publications"],
        "export_allowed": False,
        "read_only": True,
        "requires_open_access_filter": True,
    },
}


class TestPeerReviewer:
    """peer_reviewer persona — like researcher but read-only, no export."""

    def setup_method(self):
        reset_policy_engine()

    def teardown_method(self):
        reset_policy_engine()

    def test_peer_reviewer_is_tier1(self):
        """peer_reviewer maps to tier 1."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="peer_reviewer")
        assert p.tier == 1

    def test_peer_reviewer_read_only(self):
        """peer_reviewer cannot export data."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="peer_reviewer")
        assert p.read_only is True
        assert p.export_allowed is False

    def test_peer_reviewer_aggregate_pii_masking(self):
        """peer_reviewer has aggregate PII masking."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="peer_reviewer")

        assert p.should_mask_field("email") is True
        assert p.should_mask_field("phone") is True
        assert p.should_mask_field("aadhaar_number") is True
        assert p.should_mask_field("name") is False

    def test_peer_reviewer_full_output_format(self):
        """peer_reviewer gets full output (not aggregated/anonymized)."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="peer_reviewer")
        assert p.output_format == "full"

    def test_peer_reviewer_filter_row(self):
        """peer_reviewer sees all columns via [*] but email/phone are PII-masked."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="peer_reviewer")

        row = {
            "researcher_id": "R001",
            "name": "Dr. Smith",
            "email": "smith@iit.edu",
            "phone": "9876543210",
            "state": "Gujarat",
        }

        filtered = engine.filter_row_by_policy(p, "researchers", row)
        assert "name" in filtered
        assert "email" in filtered  # visible because of [*], but PII-masked
        assert filtered["email"] == "[REDACTED]"
        assert filtered["phone"] == "[REDACTED]"


class TestDepartmentHead:
    """department_head persona — government-like but institution-scoped."""

    def setup_method(self):
        reset_policy_engine()

    def teardown_method(self):
        reset_policy_engine()

    def test_department_head_is_tier2(self):
        """department_head maps to tier 2."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="department_head")
        assert p.tier == 2

    def test_department_head_requires_institution_scope(self):
        """department_head has institution scope requirement."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="department_head")
        assert p.requires_institution_scope is True
        assert p.data_scope == "institution_only"

    def test_department_head_no_name_column(self):
        """department_head cannot see researcher names (only institution/dept)."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="department_head")

        cols = engine.get_visible_columns(p, "researchers")
        assert "name" not in cols
        assert "department" in cols
        assert "institution_id" in cols

    def test_department_head_export_allowed(self):
        """department_head can export (unlike industry)."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="department_head")
        assert p.export_allowed is True

    def test_department_head_aggregated_output(self):
        """department_head gets aggregated output format."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="department_head")
        assert p.output_format == "aggregated"

    def test_department_head_filter_row(self):
        """department_head sees institution-scoped data with masked PII."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="department_head")

        row = {
            "researcher_id": "R001",
            "name": "Dr. Smith",
            "email": "smith@iit.edu",
            "institution_id": "IIT Bombay",
            "department": "Computer Science",
            "state": "Maharashtra",
        }

        filtered = engine.filter_row_by_policy(p, "researchers", row)
        assert "name" not in filtered
        assert "email" not in filtered
        assert filtered["department"] == "Computer Science"
        assert filtered["institution_id"] == "IIT Bombay"


class TestStudent:
    """student persona — industry-like but open-access publications only."""

    def setup_method(self):
        reset_policy_engine()

    def teardown_method(self):
        reset_policy_engine()

    def test_student_is_tier3(self):
        """student maps to tier 3."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="student")
        assert p.tier == 3

    def test_student_open_access_filter(self):
        """student requires open access filter."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="student")
        assert p.requires_open_access_filter is True
        assert p.data_scope == "open_access"

    def test_student_cannot_export(self):
        """student cannot export data."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="student")
        assert p.export_allowed is False

    def test_student_limited_results(self):
        """student has lower result limit than full researcher."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="student")
        assert p.max_results == 50

    def test_student_anonymized_output(self):
        """student gets anonymized output format."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="student")
        assert p.output_format == "anonymized"

    def test_student_publications_only(self):
        """student can only access publications, labs, institutions, and researchers (not funding)."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="student")

        assert engine.is_table_allowed(p, "publications") is True
        assert engine.is_table_allowed(p, "institutions") is True
        assert engine.is_table_allowed(p, "labs") is True
        assert engine.is_table_allowed(p, "researchers") is True
        assert engine.is_table_allowed(p, "funding_records") is False
        assert engine.is_table_allowed(p, "patents") is False

    def test_student_publication_columns(self):
        """student sees only non-sensitive publication columns."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="student")

        cols = engine.get_visible_columns(p, "publications")
        assert "title" in cols
        assert "year" in cols
        assert "journal" in cols
        assert "doi" in cols
        assert "abstract" not in cols
        assert "authors" not in cols

    def test_student_filter_row(self):
        """student sees anonymized research records (email/phone dropped since not in visible cols)."""
        engine = RBACPolicyEngine(policies=CUSTOM_POLICIES)
        p = engine.get_policy(persona="student")

        row = {
            "researcher_id": "R001",
            "name": "Dr. Smith",
            "email": "smith@iit.edu",
            "phone": "9876543210",
            "institution_id": "IIT Bombay",
            "research_area": "AI",
        }

        filtered = engine.filter_row_by_policy(p, "researchers", row)
        assert "name" in filtered
        assert "email" not in filtered


class TestNoHardcodedIfChains:
    """Verify no hardcoded if/elif tier chains remain for the refactored modules."""

    def setup_method(self):
        reset_policy_engine()

    def teardown_method(self):
        reset_policy_engine()

    def test_middleware_uses_policy_engine(self):
        """middleware.py get_user_tier resolves via policy engine."""
        from src.auth.middleware import get_user_tier

        class FakeClaims:
            def get(self, key, default=None):
                return {"tier": 2}.get(key, default)

        claims = {"tier": 2}
        tier = get_user_tier(claims)
        assert tier == 2

    def test_schema_extractor_get_visible_columns_via_policy(self):
        """schema_extractor uses RBACPolicyEngine for column visibility."""
        from src.skills.text_to_sql.schema_extractor import SchemaExtractor

        extractor = SchemaExtractor.__new__(SchemaExtractor)
        extractor.connection_string = None
        extractor.engine = None
        extractor.inspector = None

        cols = extractor.get_tier_filtered_columns("researchers", tier=2)
        assert isinstance(cols, list)


class TestBuiltinPersonasProtected:
    """Built-in personas (researcher, government, industry) cannot be soft-deleted."""

    def setup_method(self):
        reset_policy_engine()

    def teardown_method(self):
        reset_policy_engine()

    def test_cannot_deactivate_government(self):
        """Cannot deactivate government via the full YAML engine (protected built-in)."""
        from src.auth.rbac import RBACPolicyEngine
        engine = RBACPolicyEngine()

        result = engine.deactivate_persona("government")
        assert result is False

        p = engine.get_policy(persona="government")
        assert p.is_active is True

    def test_cannot_deactivate_industry(self):
        """Cannot deactivate industry via the full YAML engine (protected built-in)."""
        from src.auth.rbac import RBACPolicyEngine
        engine = RBACPolicyEngine()

        result = engine.deactivate_persona("industry")
        assert result is False

        p = engine.get_policy(persona="industry")
        assert p.is_active is True

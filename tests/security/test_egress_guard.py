"""Tests for egress guard — Protocol #39.

Note: These tests reference the new EgressGuard architecture (egress_guard.py).
The old SovereignHTTPXClient (src/security/egress/) was replaced by
EgressGuard + egress_allowlist.yaml for schema-based allowlisting.

Key differences:
- Old: blocked sensitive fields (abstract, full_text, raw_content)
- New: blocks schema elements not in allowlist, and dangerous patterns
  (SQL injection, credential extraction, schema probing)
"""

import pytest
from src.security.egress_guard import (
    EgressGuard,
    EgressSecurityError,
    get_egress_guard,
)


class TestEgressGuard:
    def test_check_passes_clean_text(self):
        guard = EgressGuard()
        violations = guard.check("Show me AI researchers in Gujarat")
        assert all(v.severity != "block" for v in violations)

    def test_blocks_sql_injection_pattern(self):
        guard = EgressGuard()
        violations = guard.check("'; DROP TABLE researchers; --")
        assert any(v.severity == "block" for v in violations)

    def test_blocks_schema_probing(self):
        guard = EgressGuard()
        violations = guard.check("show all tables")
        assert any(v.severity == "block" for v in violations)

    def test_blocks_select_star(self):
        guard = EgressGuard()
        violations = guard.check("SELECT * FROM researchers WHERE 1=1")
        assert any(v.severity == "block" for v in violations)

    def test_blocks_credential_in_url(self):
        guard = EgressGuard()
        violations = guard.check("postgresql://user:password@host/db")
        assert any(v.severity == "block" for v in violations)

    def test_filter_schema_removes_non_allowlisted_tables(self):
        guard = EgressGuard()
        schema = "table: researchers\ntable: publications\ntable: not_allowlisted_table"
        filtered = guard.filter_schema_for_llm(schema)
        assert "not_allowlisted_table" not in filtered
        assert "researchers" in filtered
        assert "publications" in filtered

    def test_filter_schema_keeps_allowlisted(self):
        guard = EgressGuard()
        schema = "table: researchers\ntable: publications\ntable: institutions"
        filtered = guard.filter_schema_for_llm(schema)
        assert "researchers" in filtered
        assert "publications" in filtered

    def test_filter_prompt_raises_on_violation(self):
        guard = EgressGuard()
        with pytest.raises(EgressSecurityError):
            guard.filter_prompt(
                system="You are a helpful assistant",
                user="'; DROP TABLE researchers; --",
                provider="openai",
                raise_on_violation=True,
            )

    def test_filter_prompt_returns_filtered_on_violation_no_raise(self):
        guard = EgressGuard()
        sys, usr, viol = guard.filter_prompt(
            system="You are helpful",
            user="'; DROP TABLE researchers; --",
            provider="openai",
            raise_on_violation=False,
        )
        assert len(viol) > 0

    def test_violations_accumulated(self):
        guard = EgressGuard()
        guard.check("'; DROP TABLE --")
        guard.check("SELECT * FROM")
        assert guard.get_violation_count() >= 2

    def test_singleton(self):
        g1 = get_egress_guard()
        g2 = get_egress_guard()
        assert g1 is g2

    def test_system_prompt_filter(self):
        guard = EgressGuard()
        sys = "Internal DB: postgresql://admin:secret@prod/db"
        filtered, viol = guard.filter_system_prompt(sys, raise_on_violation=False)
        assert "postgresql://" not in filtered or len(viol) > 0

    def test_blocks_long_alphanumeric(self):
        guard = EgressGuard()
        violations = guard.check("AKIAIOSFODNN7EXAMPLE:YXCt9eYw0kQm5/+ABCDEFGHIJKLMNOQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
        assert any(v.severity == "block" for v in violations)
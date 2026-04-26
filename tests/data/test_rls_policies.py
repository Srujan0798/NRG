"""LB-6 regression tests for database row policy migration."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_migration():
    path = Path("alembic/versions/lb6_schema_parity_indexes_rls_001.py")
    spec = importlib.util.spec_from_file_location("lb6_schema_parity_indexes_rls_001", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MIGRATION = _load_migration()
MIGRATION_SOURCE = Path("alembic/versions/lb6_schema_parity_indexes_rls_001.py").read_text(
    encoding="utf-8"
)


def test_lb6_rls_covers_pii_bearing_tables():
    assert set(MIGRATION.RLS_TABLES) == {
        "expertise",
        "combined_ipo_patent_data",
        "user_registration",
        "user_registration_old",
    }


def test_lb6_rls_uses_database_session_tier():
    assert "current_setting('nrg.user_tier', true)" in MIGRATION_SOURCE
    assert "RETURNS integer" in MIGRATION_SOURCE
    assert "nrg_current_tier() = 1" in MIGRATION_SOURCE


class _FakeAutocommitBlock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeContext:
    dialect = type("Dialect", (), {"name": "postgresql"})()

    def autocommit_block(self):
        return _FakeAutocommitBlock()


class _FakeOp:
    def __init__(self):
        self.statements: list[str] = []

    def execute(self, statement: str):
        self.statements.append(statement.strip())

    def get_context(self):
        return _FakeContext()


def test_lb6_rls_enables_policies_for_each_table(monkeypatch):
    fake_op = _FakeOp()
    monkeypatch.setattr(MIGRATION, "op", fake_op)

    MIGRATION._create_rls()

    for table in MIGRATION.RLS_TABLES:
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in fake_op.statements


def test_lb6_patent_policy_masks_email_fields_for_lower_tiers():
    assert "CREATE POLICY lb6_patents_tier_select" in MIGRATION_SOURCE
    assert "email_record IS NULL" in MIGRATION_SOURCE
    assert "additional_email IS NULL" in MIGRATION_SOURCE
    assert "status = 'Granted'" in MIGRATION_SOURCE


def test_lb6_user_registration_only_selectable_by_tier_one():
    assert "CREATE POLICY lb6_user_registration_tier_select" in MIGRATION_SOURCE
    assert "CREATE POLICY lb6_user_registration_old_tier_select" in MIGRATION_SOURCE
    assert "FOR SELECT USING (nrg_current_tier() = 1)" in MIGRATION_SOURCE


def test_lb6_downgrade_removes_policy_state(monkeypatch):
    fake_op = _FakeOp()
    monkeypatch.setattr(MIGRATION, "op", fake_op)

    MIGRATION.downgrade()

    for table in MIGRATION.RLS_TABLES:
        assert f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY" in fake_op.statements

    assert "DROP FUNCTION IF EXISTS nrg_current_tier()" in fake_op.statements
    assert "DROP VIEW IF EXISTS vw_innovations_trl" in fake_op.statements

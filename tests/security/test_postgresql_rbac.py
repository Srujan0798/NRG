"""Tests for PostgreSQL RBAC implementation."""

import pytest

import src.security.rbac.postgresql_rbac as postgresql_rbac_module


class FakeCursor:
    def __init__(self):
        self.executed = []

    def execute(self, sql):
        self.executed.append(sql)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class FakeConnection:
    def __init__(self):
        self.closed = False
        self._cursor = FakeCursor()

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        self.closed = True


def test_postgresql_rbac_connects_and_closes(monkeypatch):
    fake_conn = FakeConnection()
    monkeypatch.setattr(
        postgresql_rbac_module.psycopg2, "connect", lambda cs: fake_conn
    )

    rbac = postgresql_rbac_module.PostgreSQLRBAC("postgresql://fake")
    assert rbac.connection is fake_conn
    rbac.close()
    assert fake_conn.closed


def test_setup_rls_policies(monkeypatch):
    fake_conn = FakeConnection()
    monkeypatch.setattr(
        postgresql_rbac_module.psycopg2, "connect", lambda cs: fake_conn
    )

    rbac = postgresql_rbac_module.PostgreSQLRBAC("postgresql://fake")
    cursor = fake_conn.cursor()
    rbac.setup_rls_policies()

    executed = cursor.executed
    assert any("ALTER TABLE researchers ENABLE ROW LEVEL SECURITY" in s for s in executed)
    assert any("CREATE POLICY researchers_tier1_policy" in s for s in executed)
    assert any("CREATE POLICY institutions_tier1_policy" in s for s in executed)
    assert any("CREATE POLICY publications_tier1_policy" in s for s in executed)
    assert any("CREATE POLICY funding_tier1_policy" in s for s in executed)
    assert any("CREATE POLICY labs_tier1_policy" in s for s in executed)
    assert any("CREATE POLICY keywords_tier1_policy" in s for s in executed)


def test_setup_user_groups(monkeypatch):
    fake_conn = FakeConnection()
    monkeypatch.setattr(
        postgresql_rbac_module.psycopg2, "connect", lambda cs: fake_conn
    )

    rbac = postgresql_rbac_module.PostgreSQLRBAC("postgresql://fake")
    cursor = fake_conn.cursor()
    rbac.setup_user_groups()

    executed = cursor.executed
    assert any("researchers_tier1_group" in s for s in executed)
    assert any("publications_tier3_group" in s for s in executed)


def test_setup_rls_policies_rollback_on_error(monkeypatch):
    fake_conn = FakeConnection()
    monkeypatch.setattr(
        postgresql_rbac_module.psycopg2, "connect", lambda cs: fake_conn
    )

    class BrokenCursor:
        def execute(self, sql):
            raise RuntimeError("DB error")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    fake_conn.cursor = lambda: BrokenCursor()
    rbac = postgresql_rbac_module.PostgreSQLRBAC("postgresql://fake")

    with pytest.raises(RuntimeError):
        rbac.setup_rls_policies()

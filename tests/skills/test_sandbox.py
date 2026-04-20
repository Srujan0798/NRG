"""Tests for Text-to-SQL Sandbox."""

import pytest

import src.skills.text_to_sql.sandbox as sandbox_module


class FakeResult:
    def __init__(self, rows, columns):
        self._rows = rows
        self._keys = columns

    def keys(self):
        return self._keys

    def fetchall(self):
        return self._rows


class FakeConn:
    def __init__(self, rows=None, columns=None):
        self._rows = rows or []
        self._columns = columns or []

    def execute(self, sql):
        return FakeResult(self._rows, self._columns)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class FakeEngine:
    def __init__(self, rows=None, columns=None):
        self._rows = rows or []
        self._columns = columns or []

    def connect(self):
        return FakeConn(self._rows, self._columns)

    def dispose(self):
        pass


def test_execute_readonly_blocks_non_select(monkeypatch, tmp_path):
    monkeypatch.setattr(
        sandbox_module, "create_engine", lambda cs, **kw: FakeEngine()
    )
    sb = sandbox_module.Sandbox("sqlite:///:memory:")
    with pytest.raises(PermissionError):
        sb.execute_readonly("INSERT INTO x VALUES (1)")


def test_execute_readonly_allows_select(monkeypatch, tmp_path):
    monkeypatch.setattr(
        sandbox_module, "create_engine", lambda cs, **kw: FakeEngine(
            rows=[("r1",)], columns=["name"]
        )
    )
    sb = sandbox_module.Sandbox("sqlite:///:memory:")
    result = sb.execute_readonly("SELECT * FROM researchers")
    assert result["row_count"] == 1
    assert result["results"][0]["name"] == "r1"


def test_execute_readonly_logs_error(monkeypatch, tmp_path):
    class BadEngine:
        def connect(self):
            raise RuntimeError("db down")

        def dispose(self):
            pass

    monkeypatch.setattr(sandbox_module, "create_engine", lambda cs, **kw: BadEngine())
    sb = sandbox_module.Sandbox("sqlite:///:memory:")
    with pytest.raises(RuntimeError):
        sb.execute_readonly("SELECT 1")


def test_test_connection_ok(monkeypatch):
    monkeypatch.setattr(
        sandbox_module, "create_engine", lambda cs, **kw: FakeEngine()
    )
    sb = sandbox_module.Sandbox("sqlite:///:memory:")
    assert sb.test_connection() is True


def test_test_connection_fail(monkeypatch):
    class BadEngine:
        def connect(self):
            raise RuntimeError("fail")

        def dispose(self):
            pass

    monkeypatch.setattr(sandbox_module, "create_engine", lambda cs, **kw: BadEngine())
    sb = sandbox_module.Sandbox("sqlite:///:memory:")
    assert sb.test_connection() is False


def test_get_tables(monkeypatch):
    monkeypatch.setattr(
        sandbox_module, "create_engine", lambda cs, **kw: FakeEngine(
            rows=[("researchers",), ("publications",)], columns=["table_name"]
        )
    )
    sb = sandbox_module.Sandbox("sqlite:///:memory:")
    tables = sb.get_tables()
    assert "researchers" in tables
    assert "publications" in tables


def test_close_disposes_engine(monkeypatch):
    disposed = []

    class TrackEngine:
        def connect(self):
            return FakeConn()

        def dispose(self):
            disposed.append(True)

    monkeypatch.setattr(sandbox_module, "create_engine", lambda cs, **kw: TrackEngine())
    sb = sandbox_module.Sandbox("sqlite:///:memory:")
    sb.close()
    assert disposed == [True]

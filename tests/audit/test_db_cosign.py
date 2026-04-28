"""Tests for src.audit.db_cosign — GAP-A closure.

These tests verify the DB co-sign module without requiring a live PostgreSQL
instance. They test the pure functions (compute_db_cosign_hmac,
build_db_cosign_message) and the verify_db_cosign convenience function using
mocked DATABASE_URL.

Minimum 4 test cases per TP-001:
  1. verify_db_cosign returns True when signature is valid
  2. verify_db_cosign returns False when row is tampered
  3. verify_db_cosign reports disabled when PostgreSQL is unavailable
  4. verify_db_cosign detects missing signature (None)
"""

import logging
import os
import tempfile
from typing import Optional

import pytest

from src.audit.db_cosign import (
    compute_db_cosign_hmac,
    build_db_cosign_message,
    verify_db_cosign,
    cosign_event,
    DBCoSignStore,
)


@pytest.fixture(autouse=True)
def reset_db_cosign_singleton():
    """Keep DB co-sign tests independent from DATABASE_URL mutations."""
    DBCoSignStore._instance = None
    yield
    DBCoSignStore._instance = None


class TestComputeDbCosignHmac:
    """Unit tests for compute_db_cosign_hmac."""

    def test_returns_hex_string(self):
        """Computed HMAC is a 64-char hex string (SHA-256)."""
        result = compute_db_cosign_hmac(
            event_id="evt_123",
            chain_hash="abc123",
            per_user_binding="user_abc",
            db_secret="test-secret-key",
        )
        assert isinstance(result, str)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_inputs_produce_same_output(self):
        """Deterministic: identical inputs always yield the same HMAC."""
        kwargs = dict(
            event_id="evt_456",
            chain_hash="hash_def",
            per_user_binding="user_xyz",
            db_secret="secret-abc",
        )
        result_a = compute_db_cosign_hmac(**kwargs)
        result_b = compute_db_cosign_hmac(**kwargs)
        assert result_a == result_b

    def test_different_secret_produces_different_hmac(self):
        """Different secrets must produce different HMACs."""
        base = dict(event_id="evt_789", chain_hash="hash_ghi", per_user_binding="user_xyz")
        hmac_a = compute_db_cosign_hmac(db_secret="secret-a", **base)
        hmac_b = compute_db_cosign_hmac(db_secret="secret-b", **base)
        assert hmac_a != hmac_b

    def test_raises_when_secret_missing(self):
        """Raises ValueError when AUDIT_DB_COSIGN_KEY is not set and db_secret is None."""
        with pytest.MonkeyPatch.context() as mp:
            mp.delenv("AUDIT_DB_COSIGN_KEY", raising=False)
            with pytest.raises(ValueError, match="AUDIT_DB_COSIGN_KEY is required"):
                compute_db_cosign_hmac(
                    event_id="evt_123",
                    chain_hash="hash_abc",
                    per_user_binding="user_xyz",
                    db_secret=None,
                )

    def test_uses_env_secret_when_db_secret_is_none(self):
        """Falls back to AUDIT_DB_COSIGN_KEY env variable when db_secret not passed."""
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("AUDIT_DB_COSIGN_KEY", "env-secret-key")
            result = compute_db_cosign_hmac(
                event_id="evt_abc",
                chain_hash="chain_xyz",
                per_user_binding="user_123",
                db_secret=None,
            )
            assert len(result) == 64


class TestBuildDbCosignMessage:
    """Unit tests for build_db_cosign_message."""

    def test_format_matches_trigger_sql(self):
        """Message format must be 'event_id:chain_hash:per_user_binding[:16]'."""
        msg = build_db_cosign_message("evt_1", "hash_abc", "user_binding_xyz")
        assert msg == "evt_1:hash_abc:user_binding_xyz"

    def test_truncates_per_user_binding_to_16_chars(self):
        """per_user_binding is truncated to 16 characters."""
        long_binding = "this_is_a_very_long_binding_string"
        msg = build_db_cosign_message("evt_2", "hash_def", long_binding)
        assert msg == f"evt_2:hash_def:{long_binding[:16]}"
        assert len(msg.split(":")[2]) == 16

    def test_empty_per_user_binding_handled(self):
        """Empty per_user_binding is handled gracefully."""
        msg = build_db_cosign_message("evt_3", "hash_ghi", "")
        assert msg == "evt_3:hash_ghi:"

    def test_none_per_user_binding_treated_as_empty(self):
        """None per_user_binding is treated as empty string then truncated."""
        msg = build_db_cosign_message("evt_4", "hash_jkl", None)
        assert msg == "evt_4:hash_jkl:"


class TestVerifyDbCosign:
    """Tests for verify_db_cosign convenience function.

    These tests cover the four minimum cases from TP-001 by mocking
    the DBCoSignStore and DATABASE_URL so no real PostgreSQL is needed.
    """

    def test_verify_returns_true_when_valid(self):
        """verify_db_cosign returns (True, stored) when signature is valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain_file = os.path.join(tmpdir, "chain.jsonl")
            with open(chain_file, "w") as f:
                f.write(
                    '{"event_id":"evt_valid","hash":"chain_hash_val","per_user_binding":"user_binding_val"}\n'
                )

            with pytest.MonkeyPatch.context() as mp:
                mp.setenv("AUDIT_DB_COSIGN_KEY", "test-secret")
                mp.setenv("DATABASE_URL", "sqlite:///does_not_exist.db")
                valid, stored = verify_db_cosign(
                    event_id="evt_valid",
                    chain_hash="chain_hash_val",
                    per_user_binding="user_binding_val",
                    chain_path=chain_file,
                )
                assert valid is True

    def test_verify_returns_false_when_tampered(self):
        """verify_db_cosign returns (False, stored) when expected != stored."""

        def mock_verify_cosign(
            self,
            event_id: str,
            chain_hash: str,
            per_user_binding: str,
        ) -> tuple[bool, Optional[str]]:
            return (False, "tampered_signature")

        with tempfile.TemporaryDirectory() as tmpdir:
            chain_file = os.path.join(tmpdir, "chain.jsonl")
            with open(chain_file, "w") as f:
                f.write(
                    '{"event_id":"evt_tampered","hash":"hash_tampered","per_user_binding":"user_tampered"}\n'
                )

            with pytest.MonkeyPatch.context() as mp:
                mp.setenv("AUDIT_DB_COSIGN_KEY", "test-secret")
                mp.setenv("DATABASE_URL", "sqlite:///does_not_exist.db")
                original = DBCoSignStore.verify_cosign
                DBCoSignStore.verify_cosign = mock_verify_cosign
                try:
                    valid, stored = verify_db_cosign(
                        event_id="evt_tampered",
                        chain_hash="hash_tampered",
                        per_user_binding="user_tampered",
                        chain_path=chain_file,
                    )
                    assert valid is False
                    assert stored == "tampered_signature"
                finally:
                    DBCoSignStore.verify_cosign = original

    def test_verify_reports_disabled_without_postgres_url(self):
        """verify_db_cosign with last_n reports disabled when PostgreSQL is unavailable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain_file = os.path.join(tmpdir, "empty_chain.jsonl")
            with open(chain_file, "w") as f:
                f.write("")

            with pytest.MonkeyPatch.context() as mp:
                mp.setenv("AUDIT_DB_COSIGN_KEY", "test-secret")
                mp.setenv("DATABASE_URL", "")
                result = verify_db_cosign(last_n=5, chain_path=chain_file)
                assert result.all_signed is False
                assert result.count == 0
                assert result.status == "disabled:no_postgres_database_url"

    def test_verify_detects_missing_signature(self):
        """verify_db_cosign returns (False, None) when stored signature is missing."""

        def mock_verify_cosign_missing(
            self,
            event_id: str,
            chain_hash: str,
            per_user_binding: str,
        ) -> tuple[bool, None]:
            return (False, None)

        with tempfile.TemporaryDirectory() as tmpdir:
            chain_file = os.path.join(tmpdir, "chain_missing.jsonl")
            with open(chain_file, "w") as f:
                f.write(
                    '{"event_id":"evt_missing","hash":"hash_missing","per_user_binding":"user_missing"}\n'
                )

            with pytest.MonkeyPatch.context() as mp:
                mp.setenv("AUDIT_DB_COSIGN_KEY", "test-secret")
                mp.setenv("DATABASE_URL", "sqlite:///does_not_exist.db")
                original = DBCoSignStore.verify_cosign
                DBCoSignStore.verify_cosign = mock_verify_cosign_missing
                try:
                    valid, stored = verify_db_cosign(
                        event_id="evt_missing",
                        chain_hash="hash_missing",
                        per_user_binding="user_missing",
                        chain_path=chain_file,
                    )
                    assert valid is False
                    assert stored is None
                finally:
                    DBCoSignStore.verify_cosign = original

    def test_verify_cosign_accepts_legitimate_signature_and_rejects_tamper(self, monkeypatch):
        """Real verify_cosign compares DB HMAC against event_id/hash/user binding."""
        event_id = "evt-legit"
        chain_hash = "a" * 64
        per_user_binding = "binding-for-user-1"
        stored_signature = compute_db_cosign_hmac(
            event_id=event_id,
            chain_hash=chain_hash,
            per_user_binding=per_user_binding,
            db_secret="test-secret",
        )

        class FakeCursor:
            def execute(self, *_args, **_kwargs):
                return None

            def fetchone(self):
                return (stored_signature,)

            def close(self):
                return None

        class FakeConn:
            def cursor(self):
                return FakeCursor()

            def close(self):
                return None

        monkeypatch.setenv("AUDIT_DB_COSIGN_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://nrg:nrg@localhost/nrg")
        monkeypatch.setattr(DBCoSignStore, "_get_conn", lambda self: FakeConn())

        store = DBCoSignStore()

        valid, stored = store.verify_cosign(event_id, chain_hash, per_user_binding)
        tampered_valid, tampered_stored = store.verify_cosign(
            event_id, "b" * 64, per_user_binding
        )

        assert valid is True
        assert stored == stored_signature
        assert tampered_valid is False
        assert tampered_stored == stored_signature


class TestAuditCosignScheduling:
    """Tests for request-path DB co-sign scheduling decisions."""

    def test_append_skips_db_cosign_worker_when_database_is_not_postgres(self, tmp_path, monkeypatch):
        """SQLite/local runs must not spawn background DB co-sign work per audit event."""
        import src.audit as audit_module
        from src.audit import AuditEvent, ImmutableAuditLog

        ImmutableAuditLog._reset()
        monkeypatch.setenv("DATABASE_URL", "sqlite:///local.db")
        monkeypatch.setenv("AUDIT_DB_COSIGN_KEY", "test-secret")

        def fail_if_called():
            raise AssertionError("DB co-sign executor should not be created for SQLite")

        monkeypatch.setattr(audit_module, "_get_cosign_executor", fail_if_called)

        log = ImmutableAuditLog(storage_path=str(tmp_path))
        log.append(AuditEvent(event_type="query", user_id="u1", query="test"))

        valid, errors, count = log.verify_chain()
        assert valid is True, errors
        assert count == 1

    def test_should_db_cosign_requires_postgres_and_secret(self, monkeypatch):
        """DB co-signing is enabled only when both PostgreSQL and secret are configured."""
        import src.audit as audit_module

        monkeypatch.setenv("DATABASE_URL", "sqlite:///local.db")
        monkeypatch.setenv("AUDIT_DB_COSIGN_KEY", "test-secret")
        assert audit_module.should_db_cosign() is False

        monkeypatch.setenv("DATABASE_URL", "postgresql://nrg:nrg@localhost/nrg")
        monkeypatch.delenv("AUDIT_DB_COSIGN_KEY", raising=False)
        assert audit_module.should_db_cosign() is False

        monkeypatch.setenv("AUDIT_DB_COSIGN_KEY", "test-secret")
        assert audit_module.should_db_cosign() is True

    def test_append_invokes_db_cosign_for_each_event_when_configured(
        self,
        tmp_path,
        monkeypatch,
    ):
        """Each append calls the DB co-sign module when PostgreSQL co-signing is enabled."""
        import src.audit as audit_module
        import src.audit.db_cosign as db_cosign_module
        from src.audit import AuditEvent, ImmutableAuditLog

        class SucceededFuture:
            def add_done_callback(self, callback):
                callback(self)

            def exception(self):
                return None

        class InlineExecutor:
            def submit(self, fn):
                fn()
                return SucceededFuture()

        calls = []

        def fake_cosign_event(*args):
            calls.append(args)
            return "f" * 64

        ImmutableAuditLog._reset()
        audit_module.reset_db_cosign_metrics()
        monkeypatch.setenv("DATABASE_URL", "postgresql://nrg:nrg@localhost/nrg")
        monkeypatch.setenv("AUDIT_DB_COSIGN_KEY", "test-secret")
        monkeypatch.setattr(audit_module, "_get_cosign_executor", lambda: InlineExecutor())
        monkeypatch.setattr(db_cosign_module, "cosign_event", fake_cosign_event)

        log = ImmutableAuditLog(storage_path=str(tmp_path))
        for idx in range(3):
            log.append(AuditEvent(event_type="query", user_id=f"u{idx}", query=f"q{idx}"))

        assert len(calls) == 3
        assert [call[4] for call in calls] == ["query", "query", "query"]
        assert all(len(call[1]) == 64 for call in calls)
        assert audit_module.get_db_cosign_metrics()["succeeded"] == 3

    def test_background_cosign_failure_is_logged_and_counted(
        self,
        tmp_path,
        monkeypatch,
        caplog,
    ):
        """Fire-and-forget co-sign exceptions must not disappear inside Future objects."""
        import src.audit as audit_module
        from src.audit import AuditEvent, ImmutableAuditLog

        class FailedFuture:
            def add_done_callback(self, callback):
                callback(self)

            def exception(self):
                return RuntimeError("co-sign worker crashed")

        class FakeExecutor:
            def __init__(self):
                self.submitted = 0

            def submit(self, _fn):
                self.submitted += 1
                return FailedFuture()

        ImmutableAuditLog._reset()
        audit_module.reset_db_cosign_metrics()
        fake_executor = FakeExecutor()
        monkeypatch.setenv("DATABASE_URL", "postgresql://nrg:nrg@localhost/nrg")
        monkeypatch.setenv("AUDIT_DB_COSIGN_KEY", "test-secret")
        monkeypatch.setattr(audit_module, "_get_cosign_executor", lambda: fake_executor)
        caplog.set_level(logging.WARNING, logger="src.audit")

        log = ImmutableAuditLog(storage_path=str(tmp_path))
        log.append(AuditEvent(event_type="query", user_id="u1", query="test"))

        metrics = audit_module.get_db_cosign_metrics()
        assert fake_executor.submitted == 1
        assert metrics["submitted"] == 1
        assert metrics["failed"] == 1
        assert metrics["queue_depth"] == 0
        assert "DB co-sign background task failed" in caplog.text

    def test_cosign_metrics_track_burst_without_queue_accumulation(self, tmp_path, monkeypatch):
        """A 1000-event burst keeps queue depth visible and does not retain completed work."""
        import src.audit as audit_module
        from src.audit import AuditEvent, ImmutableAuditLog

        class SucceededFuture:
            def add_done_callback(self, callback):
                callback(self)

            def exception(self):
                return None

        class FakeExecutor:
            def __init__(self):
                self.submitted = 0

            def submit(self, _fn):
                self.submitted += 1
                return SucceededFuture()

        ImmutableAuditLog._reset()
        audit_module.reset_db_cosign_metrics()
        fake_executor = FakeExecutor()
        monkeypatch.setenv("DATABASE_URL", "postgresql://nrg:nrg@localhost/nrg")
        monkeypatch.setenv("AUDIT_DB_COSIGN_KEY", "test-secret")
        monkeypatch.setattr(audit_module, "_get_cosign_executor", lambda: fake_executor)

        log = ImmutableAuditLog(storage_path=str(tmp_path))
        for idx in range(1000):
            log.append(AuditEvent(event_type="query", user_id=f"u{idx}", query=f"q{idx}"))

        metrics = audit_module.get_db_cosign_metrics()
        assert fake_executor.submitted == 1000
        assert metrics["submitted"] == 1000
        assert metrics["succeeded"] == 1000
        assert metrics["failed"] == 0
        assert metrics["queue_depth"] == 0



class TestCosignEvent:
    """Tests for cosign_event convenience function."""

    def test_cosign_event_returns_none_without_postgres(self):
        """cosign_event returns None when DATABASE_URL is not a postgres URL."""
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("DATABASE_URL", "")
            mp.setenv("AUDIT_DB_COSIGN_KEY", "")
            result = cosign_event(
                event_id="evt_test",
                chain_hash="hash_test",
                per_user_binding="user_test",
                user_id="user_1",
                event_type="test",
            )
            assert result is None

    def test_cosign_event_logs_warning_without_crashing_when_db_unavailable(
        self,
        monkeypatch,
        caplog,
    ):
        """DB outage degrades by returning None and logging a warning."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://nrg:nrg@localhost/nrg")
        monkeypatch.setenv("AUDIT_DB_COSIGN_KEY", "test-secret")
        monkeypatch.setattr(
            DBCoSignStore,
            "_get_conn",
            lambda self: (_ for _ in ()).throw(RuntimeError("database down")),
        )
        caplog.set_level(logging.WARNING, logger="src.audit.db_cosign")

        result = cosign_event(
            event_id="evt-db-down",
            chain_hash="a" * 64,
            per_user_binding="binding",
            user_id="u1",
            event_type="query",
        )

        assert result is None
        assert "Failed to write DB co-sign for event evt-db-down" in caplog.text
        assert "database down" in caplog.text

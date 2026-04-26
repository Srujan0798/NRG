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
    _db_cosign_key,
    DB_COSIGN_SETTING,
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

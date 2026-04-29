"""Test per-user audit binding — Protocol #35: Non-Representation Lock."""

import tempfile
import shutil
from datetime import UTC
from pathlib import Path

import pytest

from src.audit.per_user_keys import (
    PerUserKeyManager,
    RotatingSaltStore,
    build_request_fingerprint,
    reset_per_user_key_manager,
)
from src.audit import ImmutableAuditLog, AuditEvent
from src.audit.db_cosign import (
    DB_COSIGN_COLUMN,
    DB_COSIGN_TRIGGER_NAME,
    DBCoSignStore,
    compute_db_cosign_hmac,
    generate_audit_cosign_trigger_sql,
    verify_db_cosign,
)


class TestPerUserKeyManager:
    """Test PerUserKeyManager.derive_key() consistency and derivation."""

    @pytest.fixture
    def key_manager(self):
        reset_per_user_key_manager()
        km = PerUserKeyManager(chain_key="test-chain-key-1234")
        yield km
        km._key_cache.clear()

    def test_derive_key_consistent_for_same_inputs(self, key_manager):
        """Same user_id + jwt_kid + request_fingerprint yields same key."""
        key1 = key_manager.derive_key("user-1", jwt_kid="kid-abc", request_fingerprint="fp-xyz")
        key2 = key_manager.derive_key("user-1", jwt_kid="kid-abc", request_fingerprint="fp-xyz")
        assert key1 == key2
        assert len(key1) == 32

    def test_derive_key_differs_across_users(self, key_manager):
        """Different users get different keys."""
        key1 = key_manager.derive_key("user-1", jwt_kid="kid-abc")
        key2 = key_manager.derive_key("user-2", jwt_kid="kid-abc")
        assert key1 != key2

    def test_derive_key_differs_across_kids(self, key_manager):
        """Same user, different jwt_kid yields different keys."""
        key1 = key_manager.derive_key("user-1", jwt_kid="kid-abc")
        key2 = key_manager.derive_key("user-1", jwt_kid="kid-def")
        assert key1 != key2

    def test_derive_key_differs_across_fingerprints(self, key_manager):
        """Same user+kid, different fingerprint yields different keys."""
        key1 = key_manager.derive_key("user-1", jwt_kid="kid-abc", request_fingerprint="fp-1")
        key2 = key_manager.derive_key("user-1", jwt_kid="kid-abc", request_fingerprint="fp-2")
        assert key1 != key2

    def test_derive_key_handles_none_jwt_kid(self, key_manager):
        """jwt_kid=None is treated as 'unknown'."""
        key1 = key_manager.derive_key("user-1", jwt_kid=None)
        key2 = key_manager.derive_key("user-1", jwt_kid="unknown")
        assert key1 == key2

    def test_derive_key_handles_none_fingerprint(self, key_manager):
        """request_fingerprint=None is treated as 'none'."""
        key1 = key_manager.derive_key("user-1", request_fingerprint=None)
        key2 = key_manager.derive_key("user-1", request_fingerprint="none")
        assert key1 == key2


class TestComputeVerifyBinding:
    """Test per-user binding computation and verification."""

    @pytest.fixture
    def key_manager(self):
        reset_per_user_key_manager()
        return PerUserKeyManager(chain_key="test-chain-key-1234")

    def test_binding_validates_correctly(self, key_manager):
        """verify_binding accepts a valid per-user binding."""
        user_id = "user-1"
        jwt_kid = "kid-abc"
        fp = "fp-xyz"
        chain_hash = "abcd" * 16
        event_serialized = '{"event_type":"query","user_id":"user-1"}'

        binding = key_manager.compute_binding(
            user_id, jwt_kid, fp, chain_hash, event_serialized
        )

        valid, reason = key_manager.verify_binding(
            user_id, jwt_kid, fp, chain_hash, event_serialized, binding
        )
        assert valid, f"Expected valid binding but got: {reason}"
        assert reason == "valid"

    def test_binding_rejects_mismatch(self, key_manager):
        """verify_binding rejects a tampered binding."""
        valid, reason = key_manager.verify_binding(
            user_id="user-1",
            jwt_kid="kid-abc",
            request_fingerprint="fp-xyz",
            chain_hash="abcd" * 16,
            event_serialized='{"event_type":"query"}',
            stored_binding="tampered-binding-value",
        )
        assert not valid
        assert "mismatch" in reason or "verification error" in reason

    def test_binding_rejects_tampered_event(self, key_manager):
        """Changing event_serialized after binding is computed causes rejection."""
        user_id = "user-1"
        jwt_kid = "kid-abc"
        fp = "fp-xyz"
        chain_hash = "abcd" * 16
        original_serialized = '{"event_type":"query"}'
        tampered_serialized = '{"event_type":"query","user_id":"attacker"}'

        binding = key_manager.compute_binding(
            user_id, jwt_kid, fp, chain_hash, original_serialized
        )

        valid, reason = key_manager.verify_binding(
            user_id, jwt_kid, fp, chain_hash, tampered_serialized, binding
        )
        assert not valid

    def test_binding_rejects_wrong_user(self, key_manager):
        """Binding bound to user-1 cannot be used for user-2."""
        binding = key_manager.compute_binding(
            "user-1", "kid-abc", "fp-xyz", "abcd" * 16, '{"event_type":"query"}'
        )

        valid, reason = key_manager.verify_binding(
            "user-2", "kid-abc", "fp-xyz", "abcd" * 16, '{"event_type":"query"}', binding
        )
        assert not valid

    def test_binding_accepts_system_event(self, key_manager):
        """System events (user_id=system) are always valid (no per-user binding)."""
        valid, reason = key_manager.verify_binding(
            user_id="system",
            jwt_kid="kid-abc",
            request_fingerprint="fp-xyz",
            chain_hash="abcd" * 16,
            event_serialized='{}',
            stored_binding="any-value",
        )
        assert valid
        assert reason == "system event"

    def test_binding_rejects_empty_stored(self, key_manager):
        """Missing stored binding is rejected."""
        valid, reason = key_manager.verify_binding(
            user_id="user-1",
            jwt_kid="kid-abc",
            request_fingerprint="fp-xyz",
            chain_hash="abcd" * 16,
            event_serialized='{}',
            stored_binding="",
        )
        assert not valid
        assert "missing" in reason

    def test_binding_verifies_with_historical_expired_salt(self, tmp_path):
        """Audit verification must use persisted historical salts, not today's salt."""
        import hashlib
        import hmac
        import json

        salt_file = tmp_path / "salts.jsonl"
        salt_file.write_text(
            json.dumps(
                {
                    "user_id": "user-1",
                    "salt": "a" * 32,
                    "expires": "2000-01-01",
                }
            )
            + "\n"
        )
        salt_store = RotatingSaltStore(storage_path=str(salt_file))
        key_manager = PerUserKeyManager(
            chain_key="test-chain-key-1234",
            salt_store=salt_store,
        )
        chain_hash = "abcd" * 16
        event_serialized = '{"event_type":"query","user_id":"user-1"}'
        components = [
            "test-chain-key-1234",
            "user=user-1",
            "kid=kid-abc",
            f"salt={'a' * 32}",
            "fp=fp-xyz",
        ]
        derived_key = hashlib.sha256("|".join(components).encode()).hexdigest()[:32]
        binding = hmac.new(
            derived_key.encode(),
            f"{derived_key}:{chain_hash}:{event_serialized}".encode(),
            hashlib.sha256,
        ).hexdigest()

        valid, reason = key_manager.verify_binding(
            "user-1",
            "kid-abc",
            "fp-xyz",
            chain_hash,
            event_serialized,
            binding,
        )

        assert valid, reason
        assert reason == "valid"


class TestRotatingSaltStore:
    """Test RotatingSaltStore daily rotation behavior."""

    @pytest.fixture
    def salt_store(self):
        temp_dir = tempfile.mkdtemp()
        store = RotatingSaltStore(storage_path=f"{temp_dir}/salts.jsonl")
        yield store, temp_dir
        shutil.rmtree(temp_dir)

    def test_get_salt_returns_same_salt_intraday(self, salt_store):
        """Same salt is returned for the same user within the same day."""
        store, _ = salt_store
        salt1 = store.get_salt("user-1")
        salt2 = store.get_salt("user-1")
        assert salt1 == salt2

    def test_get_salt_differs_across_users(self, salt_store):
        """Different users get different salts."""
        store, _ = salt_store
        salt1 = store.get_salt("user-1")
        salt2 = store.get_salt("user-2")
        assert salt1 != salt2

    def test_get_salt_is_persisted(self, salt_store):
        """Salt is written to the jsonl file."""
        store, temp_dir = salt_store
        salt1 = store.get_salt("user-persist")
        salts_file = Path(temp_dir) / "salts.jsonl"
        assert salts_file.exists()
        content = salts_file.read_text()
        assert "user-persist" in content
        assert len(salt1) == 32

    def test_different_dates_produce_different_salts(self, salt_store):
        """Simulating a date change produces a different salt."""
        store, _ = salt_store
        from datetime import datetime, timedelta
        
        original_salt = store.get_salt("user-1")
        store._current_salt_date = (datetime.now(UTC).date() + timedelta(days=1)).isoformat()
        store._salts.clear()

        new_salt = store.get_salt("user-1")
        assert new_salt != original_salt
        assert len(new_salt) == 32


class TestBuildRequestFingerprint:
    """Test build_request_fingerprint() consistency."""

    def test_same_inputs_produce_same_fingerprint(self):
        """Identical client_ip + user_agent + tls fields produce same fingerprint."""
        fp1 = build_request_fingerprint(client_ip="192.168.1.1", user_agent="Mozilla/5.0")
        fp2 = build_request_fingerprint(client_ip="192.168.1.1", user_agent="Mozilla/5.0")
        assert fp1 == fp2

    def test_different_ip_produces_different_fingerprint(self):
        """Different client IPs produce different fingerprints."""
        fp1 = build_request_fingerprint(client_ip="192.168.1.1")
        fp2 = build_request_fingerprint(client_ip="192.168.1.2")
        assert fp1 != fp2

    def test_fingerprint_format(self):
        """Fingerprint contains ip, ua hash, and tls components."""
        fp = build_request_fingerprint(client_ip="10.0.0.1", user_agent="TestAgent/1.0")
        assert fp.startswith("ip=10.0.0.1|")
        assert "|ua=" in fp
        assert "|tls=" in fp

    def test_fingerprint_handle_none_values(self):
        """None values produce 'unknown' placeholders."""
        fp = build_request_fingerprint(client_ip=None, user_agent=None)
        assert "ip=unknown" in fp
        assert "ua=" in fp
        assert "tls=unknown/unknown" in fp

    def test_fingerprint_length_reasonable(self):
        """Fingerprint is a reasonable length string."""
        fp = build_request_fingerprint(client_ip="192.168.1.1", user_agent="Mozilla/5.0")
        assert 10 < len(fp) < 256


class TestVerifyChainWithPerUserBinding:
    """Test verify_chain(verify_per_user=True) rejects broken bindings."""

    @pytest.fixture
    def audit_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def audit_log(self, audit_dir):
        ImmutableAuditLog._reset()
        return ImmutableAuditLog(storage_path=audit_dir)

    def test_verify_chain_with_valid_per_user_binding_passes(self, audit_log):
        """A fresh audit log with per-user bindings passes verify_chain(verify_per_user=True)."""
        event = AuditEvent(
            event_type="query",
            user_id="user-1",
            query="test query",
            jwt_kid="kid-abc",
            request_fingerprint="fp-xyz",
        )
        audit_log.append(event)

        valid, errors, count = audit_log.verify_chain(verify_per_user=True)
        assert valid, f"Expected valid chain but got errors: {errors}"
        assert count == 1

    def test_verify_chain_detects_tampered_binding(self, audit_dir):
        """Tampering per_user_binding field causes per-user binding verification failure."""
        import json
        from src.audit.per_user_keys import reset_per_user_key_manager
        reset_per_user_key_manager()
        
        audit_log = ImmutableAuditLog(storage_path=audit_dir)

        audit_log.append(AuditEvent(
            event_type="query",
            user_id="user-1",
            query="original query",
            jwt_kid="kid-original",
            request_fingerprint="ip=10.0.0.1|ua=agent|tls=TLS1.3/cipher",
        ))

        chain_file = Path(audit_dir) / "chain.jsonl"
        stored = json.loads(chain_file.read_text())
        original_binding = stored["per_user_binding"]
        stored["per_user_binding"] = "aaaa" + original_binding[4:]
        chain_file.write_text(json.dumps(stored) + "\n")

        ImmutableAuditLog._reset()
        fresh_log = ImmutableAuditLog(storage_path=audit_dir)
        valid, errors, count = fresh_log.verify_chain(verify_per_user=True)
        assert not valid
        assert any("per-user binding failure" in e or "binding" in e.lower() for e in errors)

    def test_verify_chain_without_per_user_check_passes(self, audit_dir):
        """Without verify_per_user, fresh audit chain verifies correctly."""
        from src.audit.per_user_keys import reset_per_user_key_manager
        reset_per_user_key_manager()
        
        audit_log = ImmutableAuditLog(storage_path=audit_dir)

        audit_log.append(AuditEvent(
            event_type="query",
            user_id="user-1",
            query="original query",
            jwt_kid="kid-abc",
            request_fingerprint="ip=10.0.0.1|ua=agent|tls=TLS1.3/cipher",
        ))

        ImmutableAuditLog._reset()
        fresh_log = ImmutableAuditLog(storage_path=audit_dir)
        valid, errors, count = fresh_log.verify_chain(verify_per_user=False)
        assert valid, f"Expected valid with verify_per_user=False but got: {errors}"

    def test_system_event_skips_binding_check(self, audit_log):
        """System events (user_id=system) are verified without per-user binding."""
        event = AuditEvent(
            event_type="key_rotation",
            user_id="system",
            _key_rotation={"old_key": "abc", "new_key": "def"},
        )
        audit_log.append(event)

        valid, errors, count = audit_log.verify_chain(verify_per_user=True)
        assert valid
        assert count == 1

    def test_multiple_events_all_verified(self, audit_log):
        """Multiple events with per-user bindings are all verified."""
        for i in range(3):
            audit_log.append(AuditEvent(
                event_type="query",
                user_id=f"user-{i}",
                query=f"query {i}",
                jwt_kid=f"kid-{i}",
                request_fingerprint=f"fp-{i}",
            ))

        valid, errors, count = audit_log.verify_chain(verify_per_user=True)
        assert valid, f"Expected valid but got: {errors}"
        assert count == 3


class TestDatabaseCoSign:
    """DB-side co-sign proof for the C2 single-signer gap."""

    def test_db_cosign_hmac_is_deterministic_and_tamper_sensitive(self):
        """DB co-sign HMAC binds event_id, chain_hash, and per_user_binding."""
        sig1 = compute_db_cosign_hmac(
            event_id="evt-1",
            chain_hash="a" * 64,
            per_user_binding="b" * 16,
            db_secret="db-secret",
        )
        sig2 = compute_db_cosign_hmac(
            event_id="evt-1",
            chain_hash="a" * 64,
            per_user_binding="b" * 16,
            db_secret="db-secret",
        )
        tampered = compute_db_cosign_hmac(
            event_id="evt-1",
            chain_hash="c" * 64,
            per_user_binding="b" * 16,
            db_secret="db-secret",
        )

        assert sig1 == sig2
        assert sig1 != tampered
        assert len(sig1) == 64

    def test_db_cosign_trigger_sql_adds_column_and_insert_trigger(self):
        """Postgres DDL must create audit_events.db_cosign_hmac and audit_cosign_trigger."""
        ddl = generate_audit_cosign_trigger_sql()

        assert f"ADD COLUMN IF NOT EXISTS {DB_COSIGN_COLUMN} TEXT" in ddl
        assert f"CREATE TRIGGER {DB_COSIGN_TRIGGER_NAME}" in ddl
        assert "BEFORE INSERT ON audit_events" in ddl
        assert "current_setting('app.audit_db_cosign_key', true)" in ddl
        assert "hmac(cosign_message::bytea, cosign_key::bytea, 'sha256')" in ddl

    def test_recent_verify_reports_disabled_when_database_url_missing(self, monkeypatch, tmp_path):
        """Recent verifier must return an explicit result object, not crash when DB is absent."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        DBCoSignStore._instance = None
        chain = tmp_path / "chain.jsonl"
        chain.write_text(
            '{"event_id":"evt-1","hash":"'
            + ("a" * 64)
            + '","per_user_binding":"bbbbbbbbbbbbbbbb"}\n'
        )

        result = verify_db_cosign(last_n=1, chain_path=chain)

        assert result.all_signed is False
        assert result.count == 0
        assert result.status == "disabled:no_postgres_database_url"
        assert "PostgreSQL DATABASE_URL is not set" in result.errors

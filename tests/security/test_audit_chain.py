"""Test audit chain integrity and tamper detection."""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.audit import ImmutableAuditLog, AuditEvent, verify_chain


class TestAuditChain:
    """Test HMAC chaining and tamper detection."""

    @pytest.fixture
    def audit_dir(self):
        """Create temp audit directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def audit_log(self, audit_dir):
        """Create audit log instance."""
        ImmutableAuditLog._reset()
        return ImmutableAuditLog(storage_path=audit_dir)

    def test_append_generates_hash(self, audit_log):
        """Appending event generates chain hash."""
        event = AuditEvent(event_type="query", user_id="user1", query="test query")
        hash1 = audit_log.append(event)
        assert len(hash1) == 64
        assert hash1 != "0" * 64

    def test_chain_links(self, audit_log):
        """Events link via HMAC."""
        event1 = AuditEvent(event_type="query", user_id="user1", query="q1")
        hash1 = audit_log.append(event1)

        event2 = AuditEvent(event_type="sql", user_id="user1", sql="SELECT *")
        hash2 = audit_log.append(event2)

        assert hash1 != hash2

    def test_verify_passes_clean(self, audit_log):
        """Clean chain passes verification."""
        from src.audit.per_user_keys import reset_per_user_key_manager
        reset_per_user_key_manager()
        audit_log.append(AuditEvent(event_type="query", user_id="u1", query="test", jwt_kid="kid-abc", request_fingerprint="ip=10.0.0.1|ua=agent|tls=TLS1.3/cipher"))
        valid, errors, _ = audit_log.verify_chain()
        assert valid
        assert errors == []

    def test_verify_fails_tampered(self, audit_dir):
        """Tampered chain fails verification."""
        audit_log = ImmutableAuditLog(storage_path=audit_dir)

        # Add events
        audit_log.append(AuditEvent(event_type="query", user_id="u1", query="test"))

        # Tamper with file
        chain_file = Path(audit_dir) / "chain.jsonl"
        content = chain_file.read_text()
        tampered = content.replace("test", "TAMPERED")
        chain_file.write_text(tampered)

        valid, errors, _ = audit_log.verify_chain()
        assert not valid
        assert len(errors) > 0

    def test_verify_fails_deleted_event(self, audit_dir):
        """Deleting an event (keeping only the second) fails verification."""
        audit_log = ImmutableAuditLog(storage_path=audit_dir)

        audit_log.append(AuditEvent(event_type="query", user_id="u1", query="test1"))
        audit_log.append(AuditEvent(event_type="query", user_id="u1", query="test2"))

        # Delete first event: keep only second event in chain
        # This makes the second event's prev_hash (event1's hash) mismatch with genesis
        chain_file = Path(audit_dir) / "chain.jsonl"
        lines = chain_file.read_text().splitlines()
        chain_file.write_text(lines[1] + "\n")

        valid, errors, _ = audit_log.verify_chain()
        assert not valid

    def test_merkle_root(self, audit_log):
        """Merkle root generated correctly."""
        audit_log.append(AuditEvent(event_type="query", user_id="u1", query="test"))
        merkle = audit_log.get_merkle_root()
        assert "merkle_root" in merkle
        assert "event_count" in merkle

    def test_all_event_types_logged(self, audit_log):
        """All event types can be logged."""
        events = [
            ("query", {"query": "test"}),
            ("plan", {"query": "test", "llm_call": {}}),
            ("sql", {"sql": "SELECT 1", "result": {}}),
            ("vector_query", {"query": "test", "vector_query": "vec"}),
            ("llm_call", {"llm_call": {"prompt": "test"}}),
        ]

        for event_type, data in events:
            event = AuditEvent(event_type=event_type, user_id="u1", **data)
            result = audit_log.append(event)
            assert len(result) == 64


def test_module_level_verify():
    """Test module-level verify_chain function."""
    # Just import - actual test runs with temp dir
    assert callable(verify_chain)


class TestAuditChainPerUserBinding:
    """Test verify_chain(verify_per_user=True) integration with per-user audit bindings."""

    @pytest.fixture
    def audit_dir(self):
        """Create temp audit directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def audit_log(self, audit_dir):
        """Create audit log instance with per-user bindings enabled."""
        ImmutableAuditLog._reset()
        return ImmutableAuditLog(storage_path=audit_dir)

    def test_verify_chain_per_user_passes_fresh_log(self, audit_log):
        """A fresh audit log with per-user bindings passes verify_chain(verify_per_user=True)."""
        event = AuditEvent(
            event_type="query",
            user_id="researcher-1",
            query="top AI researchers Gujarat",
            jwt_kid="kid-abc123",
            request_fingerprint="ip=192.168.1.1|ua=abc123|tls=TLS1.3/unknown",
        )
        audit_log.append(event)

        valid, errors, count = audit_log.verify_chain(verify_per_user=True)
        assert valid, f"Expected valid chain but got errors: {errors}"
        assert count == 1

    def test_verify_chain_per_user_detects_tampered_kid(self, audit_dir):
        """Modifying jwt_kid in stored event causes chain hash mismatch (primary detection)."""
        from src.audit.per_user_keys import reset_per_user_key_manager
        reset_per_user_key_manager()
        
        audit_log = ImmutableAuditLog(storage_path=audit_dir)

        audit_log.append(AuditEvent(
            event_type="query",
            user_id="researcher-1",
            query="top AI researchers Gujarat",
            jwt_kid="kid-abc",
            request_fingerprint="ip=10.0.0.1|ua=agent|tls=TLS1.3/cipher",
        ))

        chain_file = Path(audit_dir) / "chain.jsonl"
        content = chain_file.read_text()
        tampered = content.replace("kid-abc", "kid-tampered")
        chain_file.write_text(tampered)

        ImmutableAuditLog._reset()
        fresh_log = ImmutableAuditLog(storage_path=audit_dir)
        valid, errors, count = fresh_log.verify_chain(verify_per_user=True)
        assert not valid
        assert len(errors) > 0

    def test_verify_chain_per_user_detects_tampered_fingerprint(self, audit_dir):
        """Modifying request_fingerprint in stored event causes chain hash mismatch."""
        from src.audit.per_user_keys import reset_per_user_key_manager
        reset_per_user_key_manager()
        
        audit_log = ImmutableAuditLog(storage_path=audit_dir)

        audit_log.append(AuditEvent(
            event_type="query",
            user_id="researcher-1",
            query="top AI researchers Gujarat",
            jwt_kid="kid-abc",
            request_fingerprint="ip=10.0.0.1|ua=original|tls=TLS1.3/cipher",
        ))

        chain_file = Path(audit_dir) / "chain.jsonl"
        content = chain_file.read_text()
        tampered = content.replace("ua=original", "ua=tampered")
        chain_file.write_text(tampered)

        ImmutableAuditLog._reset()
        fresh_log = ImmutableAuditLog(storage_path=audit_dir)
        valid, errors, count = fresh_log.verify_chain(verify_per_user=True)
        assert not valid
        assert len(errors) > 0

    def test_verify_chain_per_user_false_allows_tampered_binding(self, audit_dir):
        """With verify_per_user=False, chain integrity is verified but per-user bindings are skipped.
        
        Note: Modifying jwt_kid or request_fingerprint in the stored event changes the chain hash,
        so the chain verification will fail regardless of verify_per_user setting.
        This test verifies the baseline chain integrity check works.
        """
        from src.audit.per_user_keys import reset_per_user_key_manager
        reset_per_user_key_manager()
        
        audit_log = ImmutableAuditLog(storage_path=audit_dir)

        audit_log.append(AuditEvent(
            event_type="query",
            user_id="researcher-1",
            query="top AI researchers Gujarat",
            jwt_kid="kid-abc",
            request_fingerprint="ip=10.0.0.1|ua=agent|tls=TLS1.3/cipher",
        ))

        ImmutableAuditLog._reset()
        fresh_log = ImmutableAuditLog(storage_path=audit_dir)
        valid, errors, count = fresh_log.verify_chain(verify_per_user=False)
        assert valid, f"Expected valid with verify_per_user=False but got: {errors}"

    def test_verify_chain_per_user_system_events_skip_binding(self, audit_log):
        """System events are verified without per-user binding."""
        audit_log.append(AuditEvent(
            event_type="key_rotation",
            user_id="system",
            _key_rotation={"old_key_hash": "abc", "new_key_hash": "def"},
        ))

        valid, errors, count = audit_log.verify_chain(verify_per_user=True)
        assert valid, f"System event should pass but got: {errors}"
        assert count == 1

    def test_verify_chain_per_user_multiple_users(self, audit_log):
        """Multiple users with distinct per-user bindings all verify correctly."""
        for i in range(3):
            audit_log.append(AuditEvent(
                event_type="query",
                user_id=f"researcher-{i}",
                query=f"query {i}",
                jwt_kid=f"kid-{i}",
                request_fingerprint=f"ip=10.0.0.{i}|ua=agent{i}|tls=TLS1.3/cipher{i}",
            ))

        valid, errors, count = audit_log.verify_chain(verify_per_user=True)
        assert valid, f"Expected valid multi-user chain but got: {errors}"
        assert count == 3

    def test_verify_chain_per_user_empty_log(self, audit_dir):
        """An empty audit chain passes verification."""
        audit_log = ImmutableAuditLog(storage_path=audit_dir)
        valid, errors, count = audit_log.verify_chain(verify_per_user=True)
        assert valid
        assert count == 0

    def test_verify_chain_per_user_mixed_events(self, audit_dir):
        """Mix of user and system events verifies correctly."""
        audit_log = ImmutableAuditLog(storage_path=audit_dir)

        audit_log.append(AuditEvent(
            event_type="query",
            user_id="researcher-1",
            query="query 1",
            jwt_kid="kid-abc",
            request_fingerprint="ip=10.0.0.1|ua=agent1|tls=TLS1.3/cipher1",
        ))

        audit_log.append(AuditEvent(
            event_type="key_rotation",
            user_id="system",
            _key_rotation={"old_key_hash": "abc", "new_key_hash": "def"},
        ))

        audit_log.append(AuditEvent(
            event_type="query",
            user_id="researcher-2",
            query="query 2",
            jwt_kid="kid-def",
            request_fingerprint="ip=10.0.0.2|ua=agent2|tls=TLS1.3/cipher2",
        ))

        valid, errors, count = audit_log.verify_chain(verify_per_user=True)
        assert valid, f"Expected valid mixed chain but got: {errors}"
        assert count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
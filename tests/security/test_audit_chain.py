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
        audit_log.append(AuditEvent(event_type="query", user_id="u1", query="test"))
        valid, errors = audit_log.verify_chain()
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

        valid, errors = audit_log.verify_chain()
        assert not valid
        assert len(errors) > 0

    def test_verify_fails_deleted_event(self, audit_dir):
        """Deleted event fails verification."""
        audit_log = ImmutableAuditLog(storage_path=audit_dir)

        audit_log.append(AuditEvent(event_type="query", user_id="u1", query="test1"))
        audit_log.append(AuditEvent(event_type="query", user_id="u1", query="test2"))

        # Delete middle event (truncate file)
        chain_file = Path(audit_dir) / "chain.jsonl"
        lines = chain_file.read_text().splitlines()
        chain_file.write_text(lines[0] + "\n")

        valid, errors = audit_log.verify_chain()
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
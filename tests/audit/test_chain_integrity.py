"""Audit Chain Integrity Tests — DPDP-2023 Compliance Verification."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import pytest

from src.audit import AuditEvent, ImmutableAuditLog


class TestAuditChainIntegrity:
    """Test suite for HMAC-SHA256 audit chain."""

    @pytest.fixture
    def temp_audit_dir(self):
        """Create a temporary audit directory for testing."""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir)

    @pytest.fixture
    def fresh_audit_log(self, temp_audit_dir):
        """Create a fresh audit log instance with temporary storage."""
        import src.audit as audit_module
        ImmutableAuditLog._instance = None
        ImmutableAuditLog._initialized = False
        audit_module._audit_log_instance = None
        log = ImmutableAuditLog(storage_path=temp_audit_dir)
        return log

    def test_append_and_verify(self, fresh_audit_log):
        """Test that appending events produces a valid chain."""
        log = fresh_audit_log

        for i in range(100):
            event = AuditEvent(
                event_type="test",
                user_id=f"user_{i}",
                query=f"test_query_{i}",
            )
            log.append(event)

        valid, errors, count = log.verify_chain()
        assert valid is True, f"Chain should be valid: {errors}"
        assert count == 100, f"Expected 100 events, got {count}"
        assert len(errors) == 0

    def test_tamper_detection(self, fresh_audit_log):
        """Test that modifying a hash is detected."""
        log = fresh_audit_log

        for i in range(10):
            event = AuditEvent(
                event_type="test",
                user_id=f"user_{i}",
                query=f"test_query_{i}",
            )
            log.append(event)

        chain_file = Path(log.chain_file)
        lines = chain_file.read_text().splitlines()

        tampered_line = json.loads(lines[5])
        tampered_line["hash"] = "0" * 64
        lines[5] = json.dumps(tampered_line)
        chain_file.write_text("\n".join(lines) + "\n")

        valid, errors, count = log.verify_chain()
        assert valid is False, "Chain should be invalid after tampering"
        assert len(errors) > 0, "Should detect tampering"
        assert "Line 6" in errors[0], "Should identify tampered line"

    def test_key_rotation(self, fresh_audit_log):
        """Test key rotation creates valid transition event."""
        log = fresh_audit_log

        for i in range(10):
            event = AuditEvent(
                event_type="test",
                user_id=f"user_{i}",
                query=f"test_query_{i}",
            )
            log.append(event)

        old_key = log.CHAIN_KEY
        new_key = old_key + "_rotated"

        log.rotate_key(old_key, new_key)

        rotation_events = []
        with open(log.chain_file) as f:
            for line in f:
                event = json.loads(line)
                if event.get("event_type") == "key_rotation":
                    rotation_events.append(event)

        assert len(rotation_events) == 1, "Should have one rotation event"
        assert "old_signature" in rotation_events[0].get("_key_rotation", {})
        assert "new_signature" in rotation_events[0].get("_key_rotation", {})

    def test_concurrent_appends(self, fresh_audit_log):
        """Test that concurrent appends don't corrupt the chain."""
        log = fresh_audit_log

        errors = []

        def append_events(start_idx, count):
            try:
                for i in range(start_idx, start_idx + count):
                    event = AuditEvent(
                        event_type="test",
                        user_id=f"user_{i}",
                        query=f"test_query_{i}",
                    )
                    log.append(event)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for t in range(10):
            thread = threading.Thread(target=append_events, args=(t * 10, 10))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0, f"Concurrent append errors: {errors}"

        valid, verify_errors, count = log.verify_chain()
        assert valid is True, f"Chain should be valid after concurrent appends: {verify_errors}"
        assert count == 100, f"Expected 100 events, got {count}"

    def test_append_refreshes_tail_hash_across_log_instances(self, temp_audit_dir):
        """A stale log object must not append from an old in-memory tail hash."""
        ImmutableAuditLog._reset()
        writer_one = ImmutableAuditLog(storage_path=temp_audit_dir)
        writer_one.append(AuditEvent(event_type="query", user_id="u1", query="one"))

        stale_writer = writer_one
        ImmutableAuditLog._reset()
        writer_two = ImmutableAuditLog(storage_path=temp_audit_dir)
        writer_two.append(AuditEvent(event_type="query", user_id="u2", query="two"))

        stale_writer.append(AuditEvent(event_type="query", user_id="u3", query="three"))

        ImmutableAuditLog._reset()
        verifier = ImmutableAuditLog(storage_path=temp_audit_dir)
        valid, errors, count = verifier.verify_chain()
        assert valid is True, f"Stale writer corrupted chain: {errors}"
        assert count == 3

    def test_rebuild_produces_valid_chain(self, fresh_audit_log):
        """Test that rebuild corrects corrupted hashes."""
        log = fresh_audit_log

        for i in range(50):
            event = AuditEvent(
                event_type="test",
                user_id=f"user_{i}",
                query=f"test_query_{i}",
            )
            log.append(event)

        chain_file = Path(log.chain_file)
        lines = chain_file.read_text().splitlines()

        for i in [10, 20, 30]:
            tampered_line = json.loads(lines[i])
            tampered_line["hash"] = "0" * 64
            lines[i] = json.dumps(tampered_line)

        chain_file.write_text("\n".join(lines) + "\n")

        valid_before, errors_before, _ = log.verify_chain()
        assert valid_before is False

        import sys
        _project_root = str(Path(__file__).parent.parent.parent)
        sys.path.insert(0, _project_root)
        from scripts.audit_rebuild import rebuild_chain

        audit_dir = str(Path(log.chain_file).parent)
        new_chain_path = Path(audit_dir) / "chain_new.jsonl"
        results = rebuild_chain(
            str(chain_file),
            str(new_chain_path),
            log.CHAIN_KEY,
        )

        assert results["events_processed"] == 50
        assert results["hashes_corrected"] == 3

        chain_file.unlink()
        new_chain_path.rename(chain_file)

        log.last_hash = log._load_last_hash()
        log.event_count = log._count_events()

        valid_after, errors_after, count = log.verify_chain()
        assert valid_after is True, f"Chain should be valid after rebuild: {errors_after}"
        assert count == 50
        assert len(errors_after) == 0

    def test_serialization_versioning(self, fresh_audit_log):
        """Test that events with different serialization versions verify correctly."""
        log = fresh_audit_log

        event_v1 = AuditEvent(
            event_type="test",
            user_id="test",
            query="test",
        )
        log.append(event_v1)

        event_v2 = AuditEvent(
            event_type="test",
            user_id="test",
            query="test",
            _v=2,
        )
        log.append(event_v2)

        valid, errors, count = log.verify_chain()
        assert valid is True, f"Chain should be valid with mixed versions: {errors}"
        assert count == 2

    def test_chain_health(self, fresh_audit_log):
        """Test chain health reporting."""
        log = fresh_audit_log

        for i in range(10):
            event = AuditEvent(
                event_type="test",
                user_id=f"user_{i}",
                query=f"test_query_{i}",
            )
            log.append(event)

        health = log.get_chain_health()
        assert health["chain_valid"] is True
        assert health["chain_length"] == 10
        assert health["valid_events"] == 10
        assert health["error_count"] == 0
        assert "last_hash" in health
        assert "last_event" in health

    def test_chain_health_repairs_line1_hash_mismatch_with_traceable_genesis(
        self,
        fresh_audit_log,
        caplog,
    ):
        """Line-1 corruption is archived, reseeded, and replayed without event loss."""
        log = fresh_audit_log

        first_hash = log.append(
            AuditEvent(event_type="query", user_id="u1", query="first preserved")
        )
        second_hash = log.append(
            AuditEvent(event_type="query", user_id="u2", query="second preserved")
        )

        chain_file = Path(log.chain_file)
        lines = chain_file.read_text().splitlines()
        chain_file.write_text(lines[1] + "\n")

        valid_before, errors_before, count_before = log.verify_chain()
        assert valid_before is False
        assert errors_before == ["Line 1: hash mismatch"]
        assert count_before == 0

        health = log.get_chain_health(auto_repair=True)

        assert health["chain_valid"] is True
        assert "Audit chain Line 1 hash mismatch auto-repair triggered" in caplog.text
        assert health["repair"]["action"] == "reseeded_with_genesis"
        assert health["valid_events"] == 2

        repaired_lines = [json.loads(line) for line in chain_file.read_text().splitlines()]
        assert repaired_lines[0]["event_type"] == "chain_genesis"
        assert repaired_lines[0]["result"]["preserved_event_count"] == 1
        assert repaired_lines[1]["event_id"] != repaired_lines[0]["event_id"]
        assert repaired_lines[1]["event_id"] == json.loads(lines[1])["event_id"]
        assert repaired_lines[1]["hash"] != second_hash
        assert first_hash not in chain_file.read_text()

        backups = list(Path(log.storage_path).glob("chain_line1_hash_mismatch_backup_*.jsonl"))
        assert backups, "corrupted chain should be archived before repair"

        valid_after, errors_after, count_after = log.verify_chain()
        assert valid_after is True
        assert errors_after == []
        assert count_after == 2
        assert health["lineage_break"]["lineage_intact"] is False
        assert health["lineage_break"]["active_chain_traceable"] is True
        assert health["lineage_break"]["genesis_pin_matches"] is False
        assert health["lineage_break"]["repair_required"] is False

    def test_chain_health_default_does_not_silently_repair_line1_mismatch(
        self,
        fresh_audit_log,
        monkeypatch,
    ):
        """Default health checks must report line-1 corruption without rewriting evidence."""
        monkeypatch.delenv("AUDIT_AUTO_REPAIR_LINE1", raising=False)
        log = fresh_audit_log

        log.append(AuditEvent(event_type="query", user_id="u1", query="first preserved"))
        log.append(AuditEvent(event_type="query", user_id="u2", query="second preserved"))

        chain_file = Path(log.chain_file)
        original_lines = chain_file.read_text().splitlines()
        chain_file.write_text(original_lines[1] + "\n")

        health = log.get_chain_health()

        assert health["chain_valid"] is False
        assert health["errors"] == ["Line 1: hash mismatch"]
        assert health["repair"] is None
        assert health["lineage_break"]["repair_required"] is True
        assert health["lineage_break"]["lineage_intact"] is False
        assert health["lineage_break"]["active_chain_traceable"] is False
        assert chain_file.read_text().splitlines() == [original_lines[1]]
        assert not list(Path(log.storage_path).glob("chain_line1_hash_mismatch_backup_*.jsonl"))

    def test_chain_health_reports_broken_genesis_pin(self, fresh_audit_log):
        """A valid chain with the wrong pinned genesis must be marked critical."""
        log = fresh_audit_log

        log.append(AuditEvent(event_type="query", user_id="u1", query="first"))
        pin_file = Path(log.genesis_pin_file)
        assert pin_file.exists()
        pin_file.write_text("f" * 64 + "\n")

        health = log.get_chain_health(auto_repair=False)

        assert health["chain_valid"] is True
        assert health["status"] == "CRITICAL"
        assert health["lineage_intact"] is False
        assert health["lineage_break"]["lineage_intact"] is False
        assert health["lineage_break"]["genesis_pin_matches"] is False

    def test_merkle_root_persistence(self, fresh_audit_log):
        """Test that daily Merkle roots are persisted."""
        log = fresh_audit_log

        for i in range(10):
            event = AuditEvent(
                event_type="test",
                user_id=f"user_{i}",
                query=f"test_query_{i}",
            )
            log.append(event)

        merkle = log.get_merkle_root()
        assert merkle["event_count"] == 10
        assert "merkle_root" in merkle
        assert len(merkle["merkle_root"]) == 64

    def test_tamper_alert_logging(self, fresh_audit_log):
        """Test that tamper detection logs alerts."""
        log = fresh_audit_log

        log.log_tamper_alert("Test tamper alert")

        integrity_alerts_file = Path(log.integrity_alerts_file)
        assert integrity_alerts_file.exists()

        with open(integrity_alerts_file) as f:
            alert = json.loads(f.readline())

        assert alert["alert_type"] == "chain_tamper_detected"
        assert alert["details"] == "Test tamper alert"


class TestAuditChainRebuildScript:
    """Test the audit_rebuild.py script."""

    @pytest.fixture
    def temp_audit_dir(self):
        """Create a temporary audit directory for testing."""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_rebuild_script_check_mode(self, temp_audit_dir):
        """Test rebuild script in check mode."""
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent.parent))
        from scripts.audit_rebuild import verify_chain_file

        chain_file = P(temp_audit_dir) / "chain.jsonl"
        chain_file.write_text('{"event_type": "test", "hash": "abc"}\n')

        valid, errors = verify_chain_file(str(chain_file), "test-key")
        assert valid is False
        assert len(errors) > 0

    def test_rebuild_script_rebuild_mode(self, temp_audit_dir):
        """Test rebuild script in rebuild mode."""
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent.parent))
        from scripts.audit_rebuild import rebuild_chain

        chain_file = P(temp_audit_dir) / "chain.jsonl"

        with open(chain_file, "w") as f:
            for i in range(20):
                event = {
                    "event_type": "test",
                    "user_id": f"user_{i}",
                    "hash": "0" * 64,
                }
                f.write(json.dumps(event) + "\n")

        new_chain_file = Path(temp_audit_dir) / "chain_new.jsonl"
        results = rebuild_chain(str(chain_file), str(new_chain_file), "test-key")

        assert results["events_processed"] == 20
        assert len(results["errors"]) == 0

        with open(new_chain_file) as f:
            lines = f.readlines()

        assert len(lines) == 20

        for line in lines:
            event = json.loads(line)
            assert event["hash"] != "0" * 64

    def test_rebuild_script_preserve_lineage_requires_force_on_pin_mismatch(
        self,
        temp_audit_dir,
    ):
        """--preserve-lineage must block a rewrite when the genesis pin differs."""
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent.parent))
        from scripts.audit_rebuild import verify_genesis_pin

        audit_dir = P(temp_audit_dir)
        chain_file = audit_dir / "chain.jsonl"
        chain_file.write_text(json.dumps({"event_type": "test", "hash": "0" * 64}) + "\n")
        (audit_dir / "genesis_hash.pin").write_text("f" * 64 + "\n")

        assert verify_genesis_pin(audit_dir, chain_file, force=False) is False
        assert verify_genesis_pin(audit_dir, chain_file, force=True) is True


def test_audit_investigate_script_runs_directly(tmp_path):
    """audit_investigate.py must work as a direct CLI, not only as an imported module."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/audit_investigate.py",
            "--chain-path",
            str(tmp_path / "missing-chain.jsonl"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert '"ok": true' in result.stdout


def test_audit_chain_health_check_script_blocks_invalid_chain(tmp_path):
    """CI/pre-commit health script exits non-zero with explicit verification errors."""
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    chain_file = audit_dir / "chain.jsonl"
    chain_file.write_text('{"event_type": "test", "hash": "bad"}\n')

    env = {**os.environ, "NRG_AUDIT_DIR": str(audit_dir)}
    result = subprocess.run(
        [sys.executable, "scripts/audit_chain_health_check.py"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Line 1" in result.stdout


def test_pre_commit_config_blocks_invalid_audit_chain():
    config = Path(".pre-commit-config.yaml").read_text()

    assert "audit-chain-health" in config
    assert "scripts/audit_chain_health_check.py" in config

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import src.audit as audit_module


def test_class_reset_invalidates_module_getter_instance(tmp_path: Path):
    audit_module.ImmutableAuditLog._reset()
    first = audit_module.ImmutableAuditLog(storage_path=str(tmp_path / "first"))
    setattr(audit_module, "_audit_log_instance", first)

    audit_module.ImmutableAuditLog._reset()
    second = audit_module.get_audit_log()

    assert second is not first


def test_chain_key_continuity_uses_environment_key(monkeypatch):
    audit_module.ImmutableAuditLog._reset()
    monkeypatch.setenv("AUDIT_CHAIN_KEY", "continuity-key")
    audit_module.reset_chain_key_cache()

    stored = audit_module.chain_key_hash()

    assert audit_module.verify_chain_continuity(stored) is True
    assert audit_module.verify_chain_continuity("0" * 16) is False


def test_concurrent_getter_does_not_expose_half_initialized_audit_log(monkeypatch, tmp_path: Path):
    audit_module.ImmutableAuditLog._reset()
    monkeypatch.setenv("NRG_AUDIT_DIR", str(tmp_path / "audit"))
    monkeypatch.setenv("AUDIT_CHAIN_KEY", "concurrent-init-key")
    audit_module.reset_chain_key_cache()

    def write_event(index: int) -> str:
        return audit_module.log_query(f"user-{index % 4}", f"query {index}")

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(write_event, index) for index in range(32)]
        event_ids = [future.result() for future in as_completed(futures)]

    assert len(event_ids) == 32
    assert len(set(event_ids)) == 32

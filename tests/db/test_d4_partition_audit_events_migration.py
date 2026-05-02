import inspect

import pytest

from src.migrations.versions import d4_partition_audit_events_004 as migration


def test_d4_partition_audit_events_is_current_src_head_revision_contract():
    assert migration.revision == "d4_partition_audit_events_004"
    assert migration.down_revision == "d4_fk_type_alignment_003"


def test_d4_partition_audit_events_is_forward_only():
    assert inspect.getsource(migration.downgrade).strip().endswith("return")


def test_d4_partition_audit_events_refuses_to_overwrite_existing_backup(monkeypatch):
    class FakeDialect:
        name = "postgresql"

    class FakeContext:
        dialect = FakeDialect()

    monkeypatch.setattr(migration.op, "get_context", lambda: FakeContext())
    monkeypatch.setattr(migration, "_is_partitioned", lambda table_name: False)
    monkeypatch.setattr(migration, "_table_exists", lambda table_name: True)

    with pytest.raises(RuntimeError, match="already exists"):
        migration.upgrade()


def test_d4_partition_audit_events_emits_partition_and_guard_sql(monkeypatch):
    executed: list[str] = []
    renamed: list[tuple[str, str]] = []

    class FakeDialect:
        name = "postgresql"

    class FakeContext:
        dialect = FakeDialect()

    monkeypatch.setattr(migration.op, "get_context", lambda: FakeContext())
    monkeypatch.setattr(migration, "_is_partitioned", lambda table_name: False)
    monkeypatch.setattr(
        migration,
        "_table_exists",
        lambda table_name: table_name == migration.SOURCE_TABLE,
    )
    monkeypatch.setattr(
        migration,
        "_rename_index_if_exists",
        lambda old_name, new_name: renamed.append((old_name, new_name)),
    )
    monkeypatch.setattr(migration.op, "execute", lambda sql: executed.append(str(sql)))
    monkeypatch.setattr(
        migration,
        "generate_audit_cosign_trigger_sql",
        lambda table_name: f"-- cosign trigger for {table_name}",
    )

    migration.upgrade()

    emitted = "\n".join(executed)
    assert (
        "audit_events_pkey",
        "audit_events_unpartitioned_d4_backup_pkey",
    ) in renamed
    assert 'ALTER TABLE "audit_events" RENAME TO "audit_events_unpartitioned_d4_backup"' in emitted
    assert 'PARTITION BY RANGE (created_at)' in emitted
    assert "CREATE TABLE audit_events_2026" in emitted
    assert "audit_event_id_unique_trigger" in emitted
    assert 'INSERT INTO "audit_events" SELECT * FROM "audit_events_unpartitioned_d4_backup"' in emitted
    assert "-- cosign trigger for audit_events" in emitted

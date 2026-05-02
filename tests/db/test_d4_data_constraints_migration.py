import inspect

from src.migrations.versions import d4_data_constraints_indexes_001 as migration


def test_d4_migration_is_current_src_head_revision_contract():
    assert migration.revision == "d4_data_constraints_indexes_001"
    assert migration.down_revision == "add_tech_trl_stages_view_002"


def test_hot_path_indexes_are_created_concurrently():
    source = inspect.getsource(migration._create_index_if_missing)

    assert "autocommit_block" in source
    assert "CREATE INDEX CONCURRENTLY IF NOT EXISTS" in source


def test_foreign_key_repairs_do_not_validate_existing_drift_inline():
    source = inspect.getsource(migration._add_fk_if_missing)

    assert "NOT VALID" in source
    assert "_validate_constraint_if_exists" not in source


def test_d4_migration_preserves_canonical_string_identifier_types():
    source = inspect.getsource(migration)

    assert "TYPE uuid" not in source
    assert "::uuid" not in source
    assert "canonical string identifier types" in source


def test_d4_migration_skips_fk_creation_when_column_types_do_not_match(monkeypatch):
    executed: list[str] = []

    monkeypatch.setattr(migration, "_table_exists", lambda table_name: True)
    monkeypatch.setattr(migration, "_column_exists", lambda table_name, column_name: True)
    monkeypatch.setattr(migration, "_constraint_exists", lambda table_name, constraint_name: False)
    monkeypatch.setattr(
        migration,
        "_column_type",
        lambda table_name, column_name: {
            ("funding_records", "researcher_id"): "character varying",
            ("researchers", "researcher_id"): "uuid",
        }[(table_name, column_name)],
    )
    monkeypatch.setattr(migration.op, "execute", lambda sql: executed.append(str(sql)))

    migration._add_fk_if_missing(
        "funding_records",
        "fk_funding_records_researcher",
        "researcher_id",
        "researchers",
        "researcher_id",
    )

    assert executed == []


def test_d4_migration_adds_fk_when_column_types_match(monkeypatch):
    executed: list[str] = []

    monkeypatch.setattr(migration, "_table_exists", lambda table_name: True)
    monkeypatch.setattr(migration, "_column_exists", lambda table_name, column_name: True)
    monkeypatch.setattr(migration, "_constraint_exists", lambda table_name, constraint_name: False)
    monkeypatch.setattr(migration, "_column_type", lambda table_name, column_name: "character varying")
    monkeypatch.setattr(migration.op, "execute", lambda sql: executed.append(str(sql)))

    migration._add_fk_if_missing(
        "funding_records",
        "fk_funding_records_researcher",
        "researcher_id",
        "researchers",
        "researcher_id",
    )

    assert len(executed) == 1
    assert 'FOREIGN KEY ("researcher_id")' in executed[0]

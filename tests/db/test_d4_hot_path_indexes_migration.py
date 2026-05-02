import inspect

from src.migrations.versions import d4_hot_path_indexes_002 as migration


def test_d4_hot_path_index_migration_is_current_src_head_revision_contract():
    assert migration.revision == "d4_hot_path_indexes_002"
    assert migration.down_revision == "d4_data_constraints_indexes_001"


def test_d4_hot_path_indexes_are_created_concurrently():
    source = inspect.getsource(migration._create_index_if_missing)

    assert "autocommit_block" in source
    assert "CREATE INDEX CONCURRENTLY IF NOT EXISTS" in source


def test_d4_hot_path_indexes_are_dropped_concurrently():
    source = inspect.getsource(migration._drop_index_if_exists)

    assert "autocommit_block" in source
    assert "DROP INDEX CONCURRENTLY IF EXISTS" in source


def test_d4_hot_path_indexes_skip_missing_tables_or_columns(monkeypatch):
    executed: list[str] = []

    monkeypatch.setattr(migration, "_table_exists", lambda table_name: table_name != "missing_table")
    monkeypatch.setattr(migration, "_index_exists", lambda index_name: False)
    monkeypatch.setattr(migration, "_column_exists", lambda table_name, column_name: column_name != "missing_column")
    monkeypatch.setattr(migration.op, "execute", lambda sql: executed.append(str(sql)))

    migration._create_index_if_missing("idx_missing_table", "missing_table", ("state",))
    migration._create_index_if_missing("idx_missing_column", "researchers", ("missing_column",))

    assert executed == []


def test_d4_hot_path_indexes_emit_expected_sql(monkeypatch):
    executed: list[str] = []

    class FakeContext:
        def autocommit_block(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(migration, "_table_exists", lambda table_name: True)
    monkeypatch.setattr(migration, "_index_exists", lambda index_name: False)
    monkeypatch.setattr(migration, "_column_exists", lambda table_name, column_name: True)
    monkeypatch.setattr(migration.op, "get_context", lambda: FakeContext())
    monkeypatch.setattr(migration.op, "execute", lambda sql: executed.append(str(sql)))

    migration._create_index_if_missing(
        "idx_researchers_institution_state",
        "researchers",
        ("institution_id", "state"),
    )

    assert executed == [
        'CREATE INDEX CONCURRENTLY IF NOT EXISTS "idx_researchers_institution_state" '
        'ON "researchers" ("institution_id", "state")'
    ]

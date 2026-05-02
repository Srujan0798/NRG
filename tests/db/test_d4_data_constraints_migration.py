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

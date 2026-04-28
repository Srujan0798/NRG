import importlib
from contextlib import contextmanager

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from src.db.validators import validate_identifier


LONG_TRL_TABLE = "innovations_at_various_stages_of_technology_readiness_level"


@contextmanager
def migrated_trl_view():
    migration = importlib.import_module("src.migrations.versions.add_trl_stages_view_001")
    engine = sa.create_engine("sqlite:///:memory:")

    with engine.begin() as connection:
        connection.execute(
            sa.text(
                f"""
                CREATE TABLE {LONG_TRL_TABLE} (
                    innovation_name TEXT,
                    stage_of_technology TEXT,
                    financial_year TEXT,
                    institute TEXT,
                    as_on_year TEXT,
                    id INTEGER PRIMARY KEY
                )
                """
            )
        )
        connection.execute(
            sa.text(
                f"""
                INSERT INTO {LONG_TRL_TABLE}
                    (innovation_name, stage_of_technology, financial_year, institute, as_on_year, id)
                VALUES
                    ('Hydrogen catalyst', 'Level 9', '2025-26', 'IIT Madras', '2026', 1),
                    ('Battery pack', 'Level 4', '2024-25', 'IIT Gandhinagar', '2025', 2)
                """
            )
        )

        context = MigrationContext.configure(connection)
        operations = Operations(context)
        original_op = migration.op
        migration.op = operations
        try:
            migration.upgrade()
            yield connection
        finally:
            migration.downgrade()
            migration.op = original_op


def test_trl_view_returns_same_rows():
    with migrated_trl_view() as connection:
        view_names = {
            row[0]
            for row in connection.execute(
                sa.text("SELECT name FROM sqlite_master WHERE type='view'")
            )
        }
        assert "trl_stages" in view_names

        base_count = connection.execute(
            sa.text(f"SELECT COUNT(*) FROM {LONG_TRL_TABLE}")
        ).scalar_one()
        view_count = connection.execute(sa.text("SELECT COUNT(*) FROM trl_stages")).scalar_one()
        assert view_count == base_count


def test_trl_view_columns_preserve_base_table_and_trl_alias():
    with migrated_trl_view() as connection:
        base_columns = {
            row[1]
            for row in connection.execute(sa.text(f"PRAGMA table_info({LONG_TRL_TABLE})"))
        }
        view_columns = {
            row[1]
            for row in connection.execute(sa.text("PRAGMA table_info(trl_stages)"))
        }

        assert base_columns.issubset(view_columns)
        assert "trl_level" in view_columns


def test_validate_identifier_rejects_64_byte_postgres_identifier():
    valid = "a" * 63
    too_long = "a" * 64

    assert validate_identifier(valid) == valid
    try:
        validate_identifier(too_long)
    except ValueError as exc:
        assert "exceeds 63 bytes" in str(exc)
    else:
        raise AssertionError("validate_identifier accepted a 64-byte identifier")

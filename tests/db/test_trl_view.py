import importlib

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


LONG_TRL_TABLE = "innovations_at_various_stages_of_technology_readiness_level"


def test_trl_stages_view_exists_and_is_queryable_from_active_migration():
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
                    ('Hydrogen catalyst', 'Level 9', '2025-26', 'IIT Madras', '2026', 1)
                """
            )
        )

        context = MigrationContext.configure(connection)
        operations = Operations(context)
        original_op = migration.op
        migration.op = operations
        try:
            migration.upgrade()

            view_names = {
                row[0]
                for row in connection.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='view'")
                )
            }
            assert "trl_stages" in view_names

            row = (
                connection.execute(
                    sa.text(
                        "SELECT innovation_name, stage_of_technology, institute "
                        "FROM trl_stages"
                    )
                )
                .mappings()
                .one()
            )
            assert row["innovation_name"] == "Hydrogen catalyst"
            assert row["stage_of_technology"] == "Level 9"
            assert row["institute"] == "IIT Madras"

            migration.downgrade()
            remaining = connection.execute(
                sa.text(
                    "SELECT COUNT(*) FROM sqlite_master "
                    "WHERE type='view' AND name='trl_stages'"
                )
            ).scalar_one()
            assert remaining == 0
        finally:
            migration.op = original_op

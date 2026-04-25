"""Add indexes for LB-3 killer-query paths.

Revision ID: lb3_killer_query_indexes_001
Revises: add_audit_cosign_trigger_001
Create Date: 2026-04-26
"""

from alembic import op


revision = "lb3_killer_query_indexes_001"
down_revision = "add_audit_cosign_trigger_001"
branch_labels = None
depends_on = None


INDEXES = [
    (
        "idx_lb3_academic_year_institute",
        "academic_courses_details",
        "(financial_year, institute)",
    ),
    (
        "idx_lb3_trl_stage_institute_year",
        "innovations_at_various_stages_of_technology_readiness_level",
        "(stage_of_technology, institute, financial_year)",
    ),
    (
        "idx_lb3_grant_institute_year",
        "innovation_grant_from_govt",
        "(institute, year_of_receiving)",
    ),
    (
        "idx_lb3_patent_status_applicants_date",
        "combined_ipo_patent_data",
        "(status, applicants, date_of_grant)",
    ),
]


def _create_index_sql(name: str, table: str, columns: str, concurrent: bool) -> str:
    concurrent_clause = " CONCURRENTLY" if concurrent else ""
    return f"CREATE INDEX{concurrent_clause} IF NOT EXISTS {name} ON {table} {columns}"


def _drop_index_sql(name: str, concurrent: bool) -> str:
    concurrent_clause = " CONCURRENTLY" if concurrent else ""
    return f"DROP INDEX{concurrent_clause} IF EXISTS {name}"


def upgrade() -> None:
    context = op.get_context()
    concurrent = context.dialect.name == "postgresql"
    if concurrent:
        with context.autocommit_block():
            for name, table, columns in INDEXES:
                op.execute(_create_index_sql(name, table, columns, concurrent=True))
        return

    for name, table, columns in INDEXES:
        op.execute(_create_index_sql(name, table, columns, concurrent=False))


def downgrade() -> None:
    context = op.get_context()
    concurrent = context.dialect.name == "postgresql"
    if concurrent:
        with context.autocommit_block():
            for name, _table, _columns in reversed(INDEXES):
                op.execute(_drop_index_sql(name, concurrent=True))
        return

    for name, _table, _columns in reversed(INDEXES):
        op.execute(_drop_index_sql(name, concurrent=False))

"""Batch 4 data constraints, FK repairs, and hot-path indexes.

Revision ID: d4_data_constraints_indexes_001
Revises: add_tech_trl_stages_view_002
Create Date: 2026-05-02

This revision is intentionally forward-only and idempotent. It repairs live
PostgreSQL drift observed in the local May 2 Batch 4 audit without rewriting
large populated tables or changing NRG's canonical string identifier types.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4_data_constraints_indexes_001"
down_revision: Union[str, None] = "add_tech_trl_stages_view_002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text("SELECT to_regclass(:table_name)"),
            {"table_name": f"public.{table_name}"},
        ).scalar()
    )


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                  AND column_name = :column_name
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        ).scalar()
    )


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text(
                """
                SELECT 1
                FROM pg_constraint con
                JOIN pg_class cls ON cls.oid = con.conrelid
                JOIN pg_namespace nsp ON nsp.oid = cls.relnamespace
                WHERE nsp.nspname = 'public'
                  AND cls.relname = :table_name
                  AND con.conname = :constraint_name
                """
            ),
            {"table_name": table_name, "constraint_name": constraint_name},
        ).scalar()
    )


def _column_type(table_name: str, column_name: str) -> str | None:
    bind = op.get_bind()
    value = bind.execute(
        sa.text(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table_name
              AND column_name = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    ).scalar()
    return str(value) if value is not None else None


def _column_types_match(
    table_name: str,
    column_name: str,
    referred_table: str,
    referred_column: str,
) -> bool:
    return _column_type(table_name, column_name) == _column_type(
        referred_table,
        referred_column,
    )


def _index_exists(index_name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text(
                """
                SELECT 1
                FROM pg_class cls
                JOIN pg_namespace nsp ON nsp.oid = cls.relnamespace
                WHERE nsp.nspname = 'public'
                  AND cls.relkind = 'i'
                  AND cls.relname = :index_name
                """
            ),
            {"index_name": index_name},
        ).scalar()
    )


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if _table_exists(table_name) and not _column_exists(table_name, column.name):
        op.add_column(table_name, column)


def _create_index_if_missing(index_name: str, table_name: str, columns: str) -> None:
    if _table_exists(table_name) and not _index_exists(index_name):
        with op.get_context().autocommit_block():
            op.execute(
                f"CREATE INDEX CONCURRENTLY IF NOT EXISTS "
                f"{index_name} ON {table_name} {columns}"
            )


def _drop_index_if_exists(index_name: str) -> None:
    if _index_exists(index_name):
        op.execute(f"DROP INDEX {index_name}")


def _add_check_if_missing(table_name: str, constraint_name: str, condition: str) -> None:
    if not _table_exists(table_name) or _constraint_exists(table_name, constraint_name):
        return
    op.execute(
        f'ALTER TABLE "{table_name}" '
        f'ADD CONSTRAINT "{constraint_name}" CHECK ({condition}) NOT VALID'
    )


def _add_fk_if_missing(
    table_name: str,
    constraint_name: str,
    column_name: str,
    referred_table: str,
    referred_column: str,
    *,
    on_delete: str = "SET NULL",
) -> None:
    if (
        not _table_exists(table_name)
        or not _table_exists(referred_table)
        or not _column_exists(table_name, column_name)
        or not _column_exists(referred_table, referred_column)
        or not _column_types_match(
            table_name,
            column_name,
            referred_table,
            referred_column,
        )
        or _constraint_exists(table_name, constraint_name)
    ):
        return
    op.execute(
        f'ALTER TABLE "{table_name}" '
        f'ADD CONSTRAINT "{constraint_name}" '
        f'FOREIGN KEY ("{column_name}") '
        f'REFERENCES "{referred_table}" ("{referred_column}") '
        f"ON DELETE {on_delete} NOT VALID"
    )


def _repair_core_columns() -> None:
    _add_column_if_missing("researchers", sa.Column("institution_id", sa.String(length=36), nullable=True))
    _add_column_if_missing("researchers", sa.Column("department", sa.String(length=100), nullable=True))
    _add_column_if_missing("researchers", sa.Column("secondary_research_areas", sa.Text(), nullable=True))
    _add_column_if_missing("researchers", sa.Column("years_experience", sa.Integer(), nullable=True))
    _add_column_if_missing("researchers", sa.Column("h_index", sa.Integer(), nullable=True))
    _add_column_if_missing(
        "researchers",
        sa.Column("total_funding_received_inr_crores", sa.Float(), nullable=True),
    )

    _add_column_if_missing("publications", sa.Column("authors", sa.Text(), nullable=True))
    _add_column_if_missing("publications", sa.Column("researcher_ids", sa.Text(), nullable=True))
    _add_column_if_missing("publications", sa.Column("volume", sa.String(length=50), nullable=True))
    _add_column_if_missing("publications", sa.Column("issue", sa.String(length=50), nullable=True))
    _add_column_if_missing("publications", sa.Column("pages", sa.String(length=50), nullable=True))
    _add_column_if_missing("publications", sa.Column("citations", sa.Integer(), nullable=True))
    _add_column_if_missing("publications", sa.Column("impact_factor", sa.Float(), nullable=True))
    _add_column_if_missing("publications", sa.Column("publication_type", sa.String(length=100), nullable=True))
    _add_column_if_missing("publications", sa.Column("research_area", sa.String(length=100), nullable=True))


def _add_contact_constraints() -> None:
    _add_check_if_missing(
        "researchers",
        "ck_researchers_email_format",
        "email IS NULL OR email ~* '^[A-Z0-9._%+\\-]+@[A-Z0-9.\\-]+\\.[A-Z]{2,}$'",
    )
    _add_check_if_missing(
        "researchers",
        "ck_researchers_phone_format",
        "phone IS NULL OR phone ~ '^\\+?[0-9][0-9 .()\\-]{7,19}$'",
    )


def _add_core_fks() -> None:
    _add_fk_if_missing(
        "researchers",
        "fk_researchers_institution",
        "institution_id",
        "institutions",
        "institution_id",
    )
    _add_fk_if_missing(
        "funding_records",
        "fk_funding_records_researcher",
        "researcher_id",
        "researchers",
        "researcher_id",
    )
    _add_fk_if_missing(
        "funding_records",
        "fk_funding_records_institution",
        "institution_id",
        "institutions",
        "institution_id",
    )
    _add_fk_if_missing(
        "funding_records",
        "fk_funding_records_project",
        "project_id",
        "projects",
        "project_id",
    )
    _add_fk_if_missing(
        "projects",
        "fk_projects_principal_investigator",
        "principal_investigator_id",
        "researchers",
        "researcher_id",
    )


def _add_hot_path_indexes() -> None:
    _create_index_if_missing("idx_researchers_institution", "researchers", "(institution_id)")
    _create_index_if_missing("idx_publications_research_area", "publications", "(research_area)")
    _create_index_if_missing("idx_publications_citations", "publications", "(citations)")
    _create_index_if_missing("idx_funding_researcher", "funding_records", "(researcher_id)")
    _create_index_if_missing("idx_funding_institution", "funding_records", "(institution_id)")
    _create_index_if_missing("idx_audit_events_created_at_brin", "audit_events", "USING BRIN (created_at)")
    _create_index_if_missing("idx_audit_events_event_type_created_at", "audit_events", "(event_type, created_at)")


def upgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    _repair_core_columns()
    _add_contact_constraints()
    _add_core_fks()
    _add_hot_path_indexes()


def downgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    for table_name, constraint_name in (
        ("projects", "fk_projects_principal_investigator"),
        ("funding_records", "fk_funding_records_project"),
        ("funding_records", "fk_funding_records_institution"),
        ("funding_records", "fk_funding_records_researcher"),
        ("researchers", "fk_researchers_institution"),
        ("researchers", "ck_researchers_phone_format"),
        ("researchers", "ck_researchers_email_format"),
    ):
        if _constraint_exists(table_name, constraint_name):
            op.execute(f'ALTER TABLE "{table_name}" DROP CONSTRAINT "{constraint_name}"')

    for index_name in (
        "idx_audit_events_event_type_created_at",
        "idx_audit_events_created_at_brin",
        "idx_funding_institution",
        "idx_funding_researcher",
        "idx_publications_citations",
        "idx_publications_research_area",
        "idx_researchers_institution",
    ):
        _drop_index_if_exists(index_name)

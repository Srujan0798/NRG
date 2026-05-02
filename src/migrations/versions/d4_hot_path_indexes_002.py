"""Batch 4 hot-path application indexes.

Revision ID: d4_hot_path_indexes_002
Revises: d4_data_constraints_indexes_001
Create Date: 2026-05-02
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4_hot_path_indexes_002"
down_revision: Union[str, None] = "d4_data_constraints_indexes_001"
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


def _create_index_if_missing(index_name: str, table_name: str, columns: tuple[str, ...]) -> None:
    if (
        not _table_exists(table_name)
        or _index_exists(index_name)
        or any(not _column_exists(table_name, column_name) for column_name in columns)
    ):
        return
    quoted_columns = ", ".join(f'"{column_name}"' for column_name in columns)
    with op.get_context().autocommit_block():
        op.execute(
            f'CREATE INDEX CONCURRENTLY IF NOT EXISTS "{index_name}" '
            f'ON "{table_name}" ({quoted_columns})'
        )


def _drop_index_if_exists(index_name: str) -> None:
    if _index_exists(index_name):
        with op.get_context().autocommit_block():
            op.execute(f'DROP INDEX CONCURRENTLY IF EXISTS "{index_name}"')


HOT_PATH_INDEXES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("idx_researchers_state", "researchers", ("state",)),
    ("idx_researchers_research_area", "researchers", ("research_area",)),
    ("idx_researchers_department", "researchers", ("department",)),
    ("idx_researchers_h_index", "researchers", ("h_index",)),
    ("idx_researchers_tier", "researchers", ("access_tier",)),
    ("idx_researchers_year", "researchers", ("year_joined",)),
    ("idx_researchers_institution_state", "researchers", ("institution_id", "state")),
    ("idx_researchers_research_area_year", "researchers", ("research_area", "year_joined")),
    ("idx_institutions_state", "institutions", ("state",)),
    ("idx_institutions_type", "institutions", ("type",)),
    ("idx_publications_year", "publications", ("year",)),
    ("idx_publications_venue", "publications", ("venue",)),
    ("idx_publications_doi", "publications", ("doi",)),
    ("idx_publications_tier", "publications", ("access_tier",)),
    ("idx_publications_year_venue", "publications", ("year", "venue")),
    ("idx_funding_agency", "funding_records", ("agency",)),
    ("idx_funding_fiscal_year", "funding_records", ("fiscal_year",)),
    ("idx_funding_amount", "funding_records", ("amount",)),
    ("idx_funding_project", "funding_records", ("project_id",)),
    ("idx_funding_tier", "funding_records", ("access_tier",)),
    ("idx_labs_institution", "labs", ("institution_id",)),
    ("idx_labs_research_area", "labs", ("research_area",)),
    ("idx_labs_location_state", "labs", ("location_state",)),
    ("idx_labs_director", "labs", ("director_researcher_id",)),
    ("idx_projects_pi", "projects", ("principal_investigator_id",)),
    ("idx_projects_status", "projects", ("status",)),
    ("idx_projects_agency", "projects", ("funding_agency",)),
    ("idx_projects_research_area", "projects", ("research_area",)),
    ("idx_projects_tier", "projects", ("access_tier",)),
    ("idx_patents_status", "patents", ("status",)),
    ("idx_patents_research_area", "patents", ("research_area",)),
    ("idx_patents_tier", "patents", ("access_tier",)),
    ("idx_collaborations_partner", "collaborations", ("partner_institution",)),
    ("idx_collaborations_country", "collaborations", ("partner_country",)),
    ("idx_collaborations_type", "collaborations", ("collaboration_type",)),
    ("idx_collaborations_status", "collaborations", ("status",)),
    ("idx_collaborations_tier", "collaborations", ("access_tier",)),
    ("idx_research_docs_year", "research_documents", ("publication_year",)),
    ("idx_research_docs_category", "research_documents", ("category",)),
    ("idx_research_docs_tier", "research_documents", ("access_tier",)),
)


def upgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return
    for index_name, table_name, columns in HOT_PATH_INDEXES:
        _create_index_if_missing(index_name, table_name, columns)


def downgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return
    for index_name, _table_name, _columns in reversed(HOT_PATH_INDEXES):
        _drop_index_if_exists(index_name)

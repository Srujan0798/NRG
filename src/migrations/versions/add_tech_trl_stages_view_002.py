"""Add tech_trl_stages safe alias and normalize TRL view columns.

Revision ID: add_tech_trl_stages_view_002
Revises: add_trl_stages_view_001
Create Date: 2026-04-29
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "add_tech_trl_stages_view_002"
down_revision: Union[str, None] = "add_trl_stages_view_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TRL_SOURCE_TABLE = "innovations_at_various_stages_of_technology_readiness_level"

TRL_VIEW_SELECT = f"""
SELECT
    id,
    institute,
    financial_year,
    stage_of_technology,
    stage_of_technology AS trl_level,
    stage_of_technology AS tech_readiness_stage,
    innovation_name,
    as_on_year,
    NULL::integer AS project_count,
    NULL::numeric AS grant_amount
FROM {TRL_SOURCE_TABLE}
"""

LEGACY_TRL_VIEW_SELECT = f"""
SELECT
    innovation_name,
    stage_of_technology,
    stage_of_technology AS trl_level,
    financial_year,
    institute,
    as_on_year,
    id
FROM {TRL_SOURCE_TABLE}
"""


def upgrade() -> None:
    context = op.get_context()
    if context.dialect.name != "postgresql":
        return

    op.execute("DROP VIEW IF EXISTS tech_trl_stages")
    op.execute("DROP VIEW IF EXISTS trl_stages")
    op.execute(f"CREATE VIEW trl_stages AS {TRL_VIEW_SELECT}")
    op.execute(f"CREATE VIEW tech_trl_stages AS {TRL_VIEW_SELECT}")


def downgrade() -> None:
    context = op.get_context()
    if context.dialect.name != "postgresql":
        return

    op.execute("DROP VIEW IF EXISTS tech_trl_stages")
    op.execute("DROP VIEW IF EXISTS trl_stages")
    op.execute(f"CREATE VIEW trl_stages AS {LEGACY_TRL_VIEW_SELECT}")

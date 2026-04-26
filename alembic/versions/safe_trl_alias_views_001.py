"""Add short TRL safe-view aliases.

Revision ID: safe_trl_alias_views_001
Revises: lb6_indexes_rls_001
Create Date: 2026-04-26
"""

from alembic import op


revision = "safe_trl_alias_views_001"
down_revision = "lb6_indexes_rls_001"
branch_labels = None
depends_on = None


VIEW_BODY = """
SELECT
    id,
    institute,
    financial_year,
    stage_of_technology,
    stage_of_technology AS tech_readiness_stage,
    innovation_name,
    as_on_year,
    NULL::integer AS project_count,
    NULL::numeric AS grant_amount
FROM innovations_at_various_stages_of_technology_readiness_level
"""


def upgrade() -> None:
    context = op.get_context()
    if context.dialect.name != "postgresql":
        return

    op.execute(f"CREATE OR REPLACE VIEW trl_stages AS {VIEW_BODY}")
    op.execute(f"CREATE OR REPLACE VIEW tech_trl_stages AS {VIEW_BODY}")


def downgrade() -> None:
    context = op.get_context()
    if context.dialect.name != "postgresql":
        return

    op.execute("DROP VIEW IF EXISTS tech_trl_stages")
    op.execute("DROP VIEW IF EXISTS trl_stages")

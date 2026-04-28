"""Add trl_stages view alias for the TRL source table.

Revision ID: add_trl_stages_view_001
Revises: lb6_indexes_rls_001
Create Date: 2026-04-28
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "add_trl_stages_view_001"
down_revision: Union[str, None] = "lb6_indexes_rls_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TRL_SOURCE_TABLE = "innovations_at_various_stages_of_technology_readiness_level"


def upgrade() -> None:
    context = op.get_context()
    if context.dialect.name == "postgresql":
        op.execute(
            f"""
            CREATE OR REPLACE VIEW trl_stages AS
            SELECT * FROM {TRL_SOURCE_TABLE}
            """
        )
        return

    op.execute("DROP VIEW IF EXISTS trl_stages")
    op.execute(
        f"""
        CREATE VIEW trl_stages AS
        SELECT * FROM {TRL_SOURCE_TABLE}
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS trl_stages")

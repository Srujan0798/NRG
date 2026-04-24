"""Add llm_cost_log table for CostGuard budget tracking.

Revision ID: llm_cost_log_001
Revises: add_audit_cosign_trigger_001
Create Date: 2026-04-25

Records every LLM call's cost, provider, token counts, persona,
complexity, and routing decision for monthly budget governance.

Index on (persona, month) and (provider) for fast weekly reporting.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "llm_cost_log_001"
down_revision: Union[str, None] = "add_audit_cosign_trigger_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_cost_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("query_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("cost_inr", sa.Float(), nullable=False),
        sa.Column("persona", sa.String(length=32), nullable=True),
        sa.Column("complexity", sa.String(length=32), nullable=True),
        sa.Column("route_decision", sa.String(length=64), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_llm_cost_log_query_id", "llm_cost_log", ["query_id"], unique=False)
    op.create_index("idx_llm_cost_log_provider", "llm_cost_log", ["provider"], unique=False)
    op.create_index("idx_llm_cost_log_persona", "llm_cost_log", ["persona"], unique=False)
    op.create_index(
        "idx_llm_cost_log_month",
        "llm_cost_log",
        [sa.text("date_trunc('month', timestamp)")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("llm_cost_log")

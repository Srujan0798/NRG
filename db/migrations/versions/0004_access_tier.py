"""Add access_tier column for tier-based access control.

Revision ID: 0004
Revises: 0003
Create Date: 2024-04-19 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add access_tier INTEGER NOT NULL DEFAULT 1 to tier-aware tables."""
    for table in ['researchers', 'publications', 'funding_records']:
        op.add_column(
            table,
            sa.Column('access_tier', sa.Integer(), nullable=False, server_default='1')
        )

    if op.get_context().bind.dialect.name == 'postgresql':
        op.execute("""
            COMMENT ON COLUMN researchers.access_tier IS
                '1=researcher (public), 2=government (aggregated), 3=industry (limited)';
            COMMENT ON COLUMN publications.access_tier IS
                '1=researcher (public), 2=government (aggregated), 3=industry (limited)';
            COMMENT ON COLUMN funding_records.access_tier IS
                '1=researcher (public), 2=government (aggregated), 3=industry (limited)';
        """)


def downgrade() -> None:
    """Remove access_tier column from tier-aware tables."""
    for table in ['researchers', 'publications', 'funding_records']:
        op.drop_column(table, 'access_tier')
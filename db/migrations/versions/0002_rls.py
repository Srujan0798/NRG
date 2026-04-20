"""Row-level security policies

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-01 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE researchers ADD COLUMN access_tier INTEGER DEFAULT 1")
    op.execute("ALTER TABLE publications ADD COLUMN access_tier INTEGER DEFAULT 1")

    op.execute("""
        CREATE TABLE IF NOT EXISTS rls_policies (
            policy_id TEXT PRIMARY KEY,
            table_name TEXT NOT NULL,
            role TEXT NOT NULL,
            tier_min INTEGER DEFAULT 1,
            tier_max INTEGER DEFAULT 3,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    op.execute("""
        INSERT OR IGNORE INTO rls_policies (policy_id, table_name, role, tier_min, tier_max, description)
        VALUES
            ('rls_researcher_view', 'researchers', 'researcher', 1, 1, 'Researchers can view tier-1 data only'),
            ('rls_government_view', 'researchers', 'government', 1, 3, 'Government can view all tiers'),
            ('rls_industry_view', 'researchers', 'industry', 1, 2, 'Industry can view tier-1 and tier-2'),
            ('rls_publication_view', 'publications', 'researcher', 1, 1, 'Researchers view tier-1 publications'),
            ('rls_pub_gov_view', 'publications', 'government', 1, 3, 'Government views all publications'),
            ('rls_pub_ind_view', 'publications', 'industry', 1, 2, 'Industry views tier-1 and tier-2 publications')
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS rls_policies")

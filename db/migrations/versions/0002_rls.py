"""Row Level Security for multi-tenant access control.

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable RLS on researchers table with tier-based policies."""
    # Only applicable to PostgreSQL
    op.execute("""
        DO $$
        BEGIN
            -- Enable RLS on researchers table
            ALTER TABLE researchers ENABLE ROW LEVEL SECURITY;
            
            -- Drop existing policies if any
            DROP POLICY IF EXISTS researchers_tier1_policy ON researchers;
            DROP POLICY IF EXISTS researchers_tier2_policy ON researchers;
            DROP POLICY IF EXISTS researchers_tier3_policy ON researchers;
            
            -- Tier 1: Can see access_tier <= 1
            CREATE POLICY researchers_tier1_policy ON researchers
                FOR ALL
                TO public
                USING (access_tier <= 1);
            
            -- Tier 2: Can see access_tier <= 2
            CREATE POLICY researchers_tier2_policy ON researchers
                FOR ALL
                TO public
                USING (access_tier <= 2);
            
            -- Tier 3: Can see all
            CREATE POLICY researchers_tier3_policy ON researchers
                FOR ALL
                TO public
                USING (true);
            
            -- Enable RLS on publications
            ALTER TABLE publications ENABLE ROW LEVEL SECURITY;
            
            DROP POLICY IF EXISTS publications_tier1_policy ON publications;
            DROP POLICY IF EXISTS publications_tier2_policy ON publications;
            DROP POLICY IF EXISTS publications_tier3_policy ON publications;
            
            CREATE POLICY publications_tier1_policy ON publications
                FOR ALL
                TO public
                USING (access_tier <= 1);
            
            CREATE POLICY publications_tier2_policy ON publications
                FOR ALL
                TO public
                USING (access_tier <= 2);
            
            CREATE POLICY publications_tier3_policy ON publications
                FOR ALL
                TO public
                USING (true);
                
        END $$;
    """)


def downgrade() -> None:
    """Disable RLS."""
    op.execute("""
        DO $$
        BEGIN
            DROP POLICY IF EXISTS researchers_tier1_policy ON researchers;
            DROP POLICY IF EXISTS researchers_tier2_policy ON researchers;
            DROP POLICY IF EXISTS researchers_tier3_policy ON researchers;
            ALTER TABLE researchers DISABLE ROW LEVEL SECURITY;
            
            DROP POLICY IF EXISTS publications_tier1_policy ON publications;
            DROP POLICY IF EXISTS publications_tier2_policy ON publications;
            DROP POLICY IF EXISTS publications_tier3_policy ON publications;
            ALTER TABLE publications DISABLE ROW LEVEL SECURITY;
        END $$;
    """)

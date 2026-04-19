"""Full-text search with tsvector and GIN indexes.

Revision ID: 0003
Revises: 0002
Create Date: 2024-01-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add full-text search capabilities."""
    # Add search_vector columns
    op.add_column('publications', sa.Column('search_vector', sa.Text, nullable=True))
    op.add_column('researchers', sa.Column('search_vector', sa.Text, nullable=True))

    # Create GIN indexes for FTS (PostgreSQL only)
    op.execute("""
        DO $$
        BEGIN
            -- Create GIN index on publications search_vector
            CREATE INDEX IF NOT EXISTS idx_publications_search 
            ON publications USING GIN (to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(abstract, '')));
            
            -- Create GIN index on researchers search_vector  
            CREATE INDEX IF NOT EXISTS idx_researchers_search
            ON researchers USING GIN (to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(research_area, '')));
        END $$;
    """)


def downgrade() -> None:
    """Remove FTS."""
    op.drop_index('idx_publications_search', table_name='publications', if_exists=True)
    op.drop_index('idx_researchers_search', table_name='researchers', if_exists=True)
    op.drop_column('publications', 'search_vector')
    op.drop_column('researchers', 'search_vector')

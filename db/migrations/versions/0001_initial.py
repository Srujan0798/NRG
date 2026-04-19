"""Initial migration - create base schema.

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""
    # Create institutions table
    op.create_table(
        'institutions',
        sa.Column('institution_id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('tier', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create researchers table
    op.create_table(
        'researchers',
        sa.Column('researcher_id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('institution_id', sa.String(36), sa.ForeignKey('institutions.institution_id'), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('research_area', sa.String(100), nullable=True),
        sa.Column('year_joined', sa.Integer, nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('orcid', sa.String(50), nullable=True),
        sa.Column('access_tier', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create labs table
    op.create_table(
        'labs',
        sa.Column('lab_id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('institution_id', sa.String(36), sa.ForeignKey('institutions.institution_id'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create publications table
    op.create_table(
        'publications',
        sa.Column('publication_id', sa.String(36), primary_key=True),
        sa.Column('title', sa.Text, nullable=False),
        sa.Column('abstract', sa.Text, nullable=True),
        sa.Column('venue', sa.String(255), nullable=True),
        sa.Column('year', sa.Integer, nullable=True),
        sa.Column('doi', sa.String(255), nullable=True),
        sa.Column('pmid', sa.String(50), nullable=True),
        sa.Column('access_tier', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create funding_records table
    op.create_table(
        'funding_records',
        sa.Column('funding_id', sa.String(36), primary_key=True),
        sa.Column('researcher_id', sa.String(36), sa.ForeignKey('researchers.researcher_id'), nullable=True),
        sa.Column('institution_id', sa.String(36), sa.ForeignKey('institutions.institution_id'), nullable=True),
        sa.Column('agency', sa.String(100), nullable=False),
        sa.Column('amount', sa.Float, nullable=True),
        sa.Column('start_date', sa.Date, nullable=True),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('title', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create keywords table
    op.create_table(
        'keywords',
        sa.Column('keyword_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('keyword', sa.String(100), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create junction tables
    op.create_table(
        'researcher_publications',
        sa.Column('researcher_id', sa.String(36), sa.ForeignKey('researchers.researcher_id'), primary_key=True),
        sa.Column('publication_id', sa.String(36), sa.ForeignKey('publications.publication_id'), primary_key=True),
        sa.Column('author_order', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'researcher_labs',
        sa.Column('researcher_id', sa.String(36), sa.ForeignKey('researchers.researcher_id'), primary_key=True),
        sa.Column('lab_id', sa.String(36), sa.ForeignKey('labs.lab_id'), primary_key=True),
        sa.Column('role', sa.String(50), nullable=True),
        sa.Column('start_date', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'publication_keywords',
        sa.Column('publication_id', sa.String(36), sa.ForeignKey('publications.publication_id'), primary_key=True),
        sa.Column('keyword_id', sa.Integer, sa.ForeignKey('keywords.keyword_id'), primary_key=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index('idx_researchers_state', 'researchers', ['state'])
    op.create_index('idx_researchers_area', 'researchers', ['research_area'])
    op.create_index('idx_researchers_tier', 'researchers', ['access_tier'])
    op.create_index('idx_publications_year', 'publications', ['year'])
    op.create_index('idx_publications_tier', 'publications', ['access_tier'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('publication_keywords')
    op.drop_table('researcher_labs')
    op.drop_table('researcher_publications')
    op.drop_table('keywords')
    op.drop_table('funding_records')
    op.drop_table('publications')
    op.drop_table('labs')
    op.drop_table('researchers')
    op.drop_table('institutions')

"""Initial schema — 6 tables created by seed script before alembic tracking

Revision ID: 6d878bf70def
Revises:
Create Date: 2026-01-09

These 6 tables were created by scripts/seed_relations.py before alembic
migration tracking was established. They represent the initial research
graph: funding, institutions, keywords, labs, publications, researchers.
"""

from alembic import op
import sqlalchemy as sa

revision = '6d878bf70def'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'funding',
        sa.Column('funding_id', sa.UUID(), nullable=False),
        sa.Column('researcher_id', sa.UUID(), nullable=True),
        sa.Column('institution_id', sa.UUID(), nullable=True),
        sa.Column('agency', sa.String(255), nullable=True),
        sa.Column('amount', sa.Numeric(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('access_tier', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('funding_id')
    )
    op.create_table(
        'institutions',
        sa.Column('institution_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=True),
        sa.Column('state', sa.String(100), nullable=False),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('founded_year', sa.Integer(), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('access_tier', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('institution_id')
    )
    op.create_table(
        'keywords',
        sa.Column('keyword_id', sa.UUID(), nullable=False),
        sa.Column('keyword', sa.String(100), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('keyword_id')
    )
    op.create_table(
        'labs',
        sa.Column('lab_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('institution_id', sa.UUID(), nullable=True),
        sa.Column('research_area', sa.String(255), nullable=True),
        sa.Column('established_year', sa.Integer(), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('access_tier', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.institution_id']),
        sa.PrimaryKeyConstraint('lab_id')
    )
    op.create_table(
        'publications',
        sa.Column('publication_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(1000), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('venue', sa.String(255), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('doi', sa.String(50), nullable=True),
        sa.Column('pmid', sa.String(20), nullable=True),
        sa.Column('access_tier', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('publication_id')
    )
    op.create_table(
        'researchers',
        sa.Column('researcher_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('orcid', sa.String(20), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('research_area', sa.String(255), nullable=True),
        sa.Column('year_joined', sa.Integer(), nullable=True),
        sa.Column('access_tier', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('researcher_id')
    )


def downgrade() -> None:
    op.drop_table('researchers')
    op.drop_table('publications')
    op.drop_table('labs')
    op.drop_table('keywords')
    op.drop_table('institutions')
    op.drop_table('funding')

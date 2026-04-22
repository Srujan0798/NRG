"""add_check_constraints

Revision ID: a1b2c3d4e002
Revises: b1c2d3e4f001
Create Date: 2026-04-21 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e002'
down_revision: Union[str, None] = 'b1c2d3e4f001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        'ck_publications_year',
        'publications',
        'year IS NULL OR (year >= 1900 AND year <= 2100)'
    )
    op.create_check_constraint(
        'ck_research_documents_year',
        'research_documents',
        'publication_year IS NULL OR (publication_year >= 1900 AND publication_year <= 2100)'
    )
    op.create_check_constraint(
        'ck_labs_established_year',
        'labs',
        'established_year IS NULL OR (established_year >= 1800 AND established_year <= 2100)'
    )
    op.create_check_constraint(
        'ck_institutions_founded_year',
        'institutions',
        'founded_year IS NULL OR (founded_year >= 1800 AND founded_year <= 2100)'
    )
    op.create_check_constraint(
        'ck_funding_records_positive_amount',
        'funding_records',
        'amount IS NULL OR amount > 0'
    )
    op.create_check_constraint(
        'ck_researchers_h_index',
        'researchers',
        'h_index IS NULL OR h_index >= 0'
    )
    op.create_check_constraint(
        'ck_researchers_years_experience',
        'researchers',
        'years_experience IS NULL OR years_experience >= 0'
    )


def downgrade() -> None:
    op.drop_constraint('ck_researchers_years_experience', 'researchers', type_='check')
    op.drop_constraint('ck_researchers_h_index', 'researchers', type_='check')
    op.drop_constraint('ck_funding_records_positive_amount', 'funding_records', type_='check')
    op.drop_constraint('ck_institutions_founded_year', 'institutions', type_='check')
    op.drop_constraint('ck_labs_established_year', 'labs', type_='check')
    op.drop_constraint('ck_research_documents_year', 'research_documents', type_='check')
    op.drop_constraint('ck_publications_year', 'publications', type_='check')

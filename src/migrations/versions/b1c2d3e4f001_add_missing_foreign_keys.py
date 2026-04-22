"""add_missing_foreign_keys

Revision ID: b1c2d3e4f001
Revises: 6d878bf70def
Create Date: 2026-04-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b1c2d3e4f001'
down_revision: Union[str, None] = '6d878bf70def'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        'fk_funding_records_researcher',
        'funding_records', 'researchers',
        ['researcher_id'], ['researcher_id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_funding_records_institution',
        'funding_records', 'institutions',
        ['institution_id'], ['institution_id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_funding_records_project',
        'funding_records', 'projects',
        ['project_id'], ['project_id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_patents_applicant_institution',
        'patents', 'institutions',
        ['applicant_institution'], ['institution_id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_patents_applicant_institution', 'patents', type_='foreignkey')
    op.drop_constraint('fk_funding_records_project', 'funding_records', type_='foreignkey')
    op.drop_constraint('fk_funding_records_institution', 'funding_records', type_='foreignkey')
    op.drop_constraint('fk_funding_records_researcher', 'funding_records', type_='foreignkey')

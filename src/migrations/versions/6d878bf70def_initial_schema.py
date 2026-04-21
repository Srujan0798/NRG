"""initial schema

Revision ID: 6d878bf70def
Revises:
Create Date: 2026-04-21 02:17:37.530889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '6d878bf70def'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('collaborations',
        sa.Column('collaboration_id', sa.String(length=36), nullable=False),
        sa.Column('researcher_ids', sa.Text(), nullable=True),
        sa.Column('partner_institution', sa.String(length=255), nullable=True),
        sa.Column('partner_country', sa.String(length=100), nullable=True),
        sa.Column('collaboration_type', sa.String(length=100), nullable=True),
        sa.Column('start_date', sa.String(length=50), nullable=True),
        sa.Column('end_date', sa.String(length=50), nullable=True),
        sa.Column('nature_of_work', sa.String(length=255), nullable=True),
        sa.Column('funding_amount_inr_crores', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('research_area', sa.String(length=100), nullable=True),
        sa.Column('access_tier', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('collaboration_id')
    )
    op.create_index('idx_collaborations_partner', 'collaborations', ['partner_institution'], unique=False)
    op.create_index('idx_collaborations_status', 'collaborations', ['status'], unique=False)
    op.create_index('idx_collaborations_tier', 'collaborations', ['access_tier'], unique=False)
    op.create_index('idx_collaborations_type', 'collaborations', ['collaboration_type'], unique=False)

    op.create_table('institutions',
        sa.Column('institution_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('country', sa.String(length=10), nullable=True),
        sa.Column('founded_year', sa.Integer(), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('institution_id')
    )

    op.create_table('keywords',
        sa.Column('keyword_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('keyword', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('keyword_id'),
        sa.UniqueConstraint('keyword')
    )

    op.create_table('funding_records',
        sa.Column('funding_id', sa.String(length=36), nullable=False),
        sa.Column('researcher_id', sa.String(length=36), nullable=True),
        sa.Column('institution_id', sa.String(length=36), nullable=True),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('agency', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('fiscal_year', sa.String(length=20), nullable=True),
        sa.Column('start_date', sa.String(length=50), nullable=True),
        sa.Column('end_date', sa.String(length=50), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('access_tier', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('funding_id')
    )
    op.create_index('idx_funding_fiscal_year', 'funding_records', ['fiscal_year'], unique=False)
    op.create_index('idx_funding_project', 'funding_records', ['project_id'], unique=False)
    op.create_index('idx_funding_tier', 'funding_records', ['access_tier'], unique=False)

    op.create_table('patents',
        sa.Column('patent_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('inventor_ids', sa.Text(), nullable=True),
        sa.Column('applicant_institution', sa.String(length=255), nullable=True),
        sa.Column('patent_office', sa.String(length=100), nullable=True),
        sa.Column('application_number', sa.String(length=100), nullable=True),
        sa.Column('filing_date', sa.String(length=50), nullable=True),
        sa.Column('grant_date', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('research_area', sa.String(length=100), nullable=True),
        sa.Column('patent_type', sa.String(length=100), nullable=True),
        sa.Column('claims_count', sa.Integer(), nullable=True),
        sa.Column('access_tier', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('patent_id')
    )
    op.create_index('idx_patents_research_area', 'patents', ['research_area'], unique=False)
    op.create_index('idx_patents_status', 'patents', ['status'], unique=False)
    op.create_index('idx_patents_tier', 'patents', ['access_tier'], unique=False)

    op.create_table('projects',
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('principal_investigator_id', sa.String(length=36), nullable=False),
        sa.Column('co_pis', sa.Text(), nullable=True),
        sa.Column('start_date', sa.String(length=50), nullable=True),
        sa.Column('end_date', sa.String(length=50), nullable=True),
        sa.Column('funding_agency', sa.String(length=255), nullable=True),
        sa.Column('sanctioned_amount_inr_crores', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('research_area', sa.String(length=100), nullable=True),
        sa.Column('access_tier', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['principal_investigator_id'], ['researchers.researcher_id'], ),
        sa.PrimaryKeyConstraint('project_id')
    )
    op.create_index('idx_projects_agency', 'projects', ['funding_agency'], unique=False)
    op.create_index('idx_projects_pi', 'projects', ['principal_investigator_id'], unique=False)
    op.create_index('idx_projects_research_area', 'projects', ['research_area'], unique=False)
    op.create_index('idx_projects_status', 'projects', ['status'], unique=False)
    op.create_index('idx_projects_tier', 'projects', ['access_tier'], unique=False)

    op.create_table('publications',
        sa.Column('publication_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('venue', sa.String(length=255), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('doi', sa.String(length=255), nullable=True),
        sa.Column('pmid', sa.String(length=50), nullable=True),
        sa.Column('authors', sa.Text(), nullable=True),
        sa.Column('researcher_ids', sa.Text(), nullable=True),
        sa.Column('volume', sa.String(length=50), nullable=True),
        sa.Column('issue', sa.String(length=50), nullable=True),
        sa.Column('pages', sa.String(length=50), nullable=True),
        sa.Column('citations', sa.Integer(), nullable=True),
        sa.Column('impact_factor', sa.Float(), nullable=True),
        sa.Column('publication_type', sa.String(length=100), nullable=True),
        sa.Column('research_area', sa.String(length=100), nullable=True),
        sa.Column('access_tier', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('publication_id')
    )
    op.create_index('idx_publications_citations', 'publications', ['citations'], unique=False)
    op.create_index('idx_publications_research_area', 'publications', ['research_area'], unique=False)
    op.create_index('idx_publications_tier', 'publications', ['access_tier'], unique=False)
    op.create_index('idx_publications_year', 'publications', ['year'], unique=False)

    op.create_table('research_documents',
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('researcher_ids', sa.Text(), nullable=True),
        sa.Column('affiliation', sa.String(length=255), nullable=True),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('research_area_tags', sa.Text(), nullable=True),
        sa.Column('access_tier', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('document_id')
    )
    op.create_index('idx_research_docs_category', 'research_documents', ['category'], unique=False)
    op.create_index('idx_research_docs_tier', 'research_documents', ['access_tier'], unique=False)
    op.create_index('idx_research_docs_year', 'research_documents', ['publication_year'], unique=False)

    op.create_table('researchers',
        sa.Column('researcher_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('institution_id', sa.String(length=36), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('research_area', sa.String(length=100), nullable=True),
        sa.Column('year_joined', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('orcid', sa.String(length=50), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('secondary_research_areas', sa.Text(), nullable=True),
        sa.Column('years_experience', sa.Integer(), nullable=True),
        sa.Column('h_index', sa.Integer(), nullable=True),
        sa.Column('total_funding_received_inr_crores', sa.Float(), nullable=True),
        sa.Column('access_tier', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.institution_id'], ),
        sa.PrimaryKeyConstraint('researcher_id')
    )
    op.create_index('idx_researchers_department', 'researchers', ['department'], unique=False)
    op.create_index('idx_researchers_h_index', 'researchers', ['h_index'], unique=False)
    op.create_index('idx_researchers_research_area', 'researchers', ['research_area'], unique=False)
    op.create_index('idx_researchers_state', 'researchers', ['state'], unique=False)
    op.create_index('idx_researchers_tier', 'researchers', ['access_tier'], unique=False)

    op.create_table('labs',
        sa.Column('lab_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('institution_id', sa.String(length=36), nullable=True),
        sa.Column('research_area', sa.String(length=100), nullable=True),
        sa.Column('research_focus_areas', sa.Text(), nullable=True),
        sa.Column('location_state', sa.String(length=50), nullable=True),
        sa.Column('director_researcher_id', sa.String(length=36), nullable=True),
        sa.Column('established_year', sa.Integer(), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['director_researcher_id'], ['researchers.researcher_id'], ),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.institution_id'], ),
        sa.PrimaryKeyConstraint('lab_id')
    )
    op.create_index('idx_labs_director', 'labs', ['director_researcher_id'], unique=False)
    op.create_index('idx_labs_location_state', 'labs', ['location_state'], unique=False)
    op.create_index('idx_labs_research_area', 'labs', ['research_area'], unique=False)

    op.create_table('publication_keywords',
        sa.Column('publication_id', sa.String(length=36), nullable=False),
        sa.Column('keyword_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['keyword_id'], ['keywords.keyword_id'], ),
        sa.ForeignKeyConstraint(['publication_id'], ['publications.publication_id'], ),
        sa.PrimaryKeyConstraint('publication_id', 'keyword_id')
    )

    op.create_table('researcher_publications',
        sa.Column('researcher_id', sa.String(length=36), nullable=False),
        sa.Column('publication_id', sa.String(length=36), nullable=False),
        sa.Column('author_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['publication_id'], ['publications.publication_id'], ),
        sa.ForeignKeyConstraint(['researcher_id'], ['researchers.researcher_id'], ),
        sa.PrimaryKeyConstraint('researcher_id', 'publication_id')
    )

    op.create_table('researcher_labs',
        sa.Column('researcher_id', sa.String(length=36), nullable=False),
        sa.Column('lab_id', sa.String(length=36), nullable=False),
        sa.Column('start_date', sa.String(length=50), nullable=True),
        sa.Column('end_date', sa.String(length=50), nullable=True),
        sa.Column('role', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['lab_id'], ['labs.lab_id'], ),
        sa.ForeignKeyConstraint(['researcher_id'], ['researchers.researcher_id'], ),
        sa.PrimaryKeyConstraint('researcher_id', 'lab_id')
    )


def downgrade() -> None:
    op.drop_table('researcher_labs')
    op.drop_table('researcher_publications')
    op.drop_table('publication_keywords')
    op.drop_table('labs')
    op.drop_table('researchers')
    op.drop_table('research_documents')
    op.drop_table('publications')
    op.drop_table('projects')
    op.drop_table('patents')
    op.drop_table('funding_records')
    op.drop_table('keywords')
    op.drop_table('institutions')
    op.drop_table('collaborations')
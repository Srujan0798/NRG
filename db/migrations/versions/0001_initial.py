"""Initial schema - core tables

Revision ID: 0001
Revises: None
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "institutions",
        sa.Column("institution_id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("state", sa.String(50), nullable=True),
        sa.Column("tier", sa.Integer(), server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "researchers",
        sa.Column("researcher_id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("institution_id", sa.String(36), sa.ForeignKey("institutions.institution_id"), nullable=True),
        sa.Column("state", sa.String(50), nullable=True),
        sa.Column("research_area", sa.String(100), nullable=True),
        sa.Column("year_joined", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("orcid", sa.String(50), nullable=True),
        sa.Column("access_tier", sa.Integer(), server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "publications",
        sa.Column("publication_id", sa.String(36), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("venue", sa.String(255), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("doi", sa.String(255), nullable=True),
        sa.Column("pmid", sa.String(50), nullable=True),
        sa.Column("access_tier", sa.Integer(), server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "labs",
        sa.Column("lab_id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("institution_id", sa.String(36), sa.ForeignKey("institutions.institution_id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "researcher_publications",
        sa.Column("researcher_id", sa.String(36), sa.ForeignKey("researchers.researcher_id"), nullable=False),
        sa.Column("publication_id", sa.String(36), sa.ForeignKey("publications.publication_id"), nullable=False),
        sa.PrimaryKeyConstraint("researcher_id", "publication_id"),
    )

    op.create_index("ix_researchers_state", "researchers", ["state"])
    op.create_index("ix_researchers_research_area", "researchers", ["research_area"])
    op.create_index("ix_publications_year", "publications", ["year"])
    op.create_index("ix_researchers_institution_id", "researchers", ["institution_id"])


def downgrade() -> None:
    op.drop_index("ix_researchers_institution_id", table_name="researchers")
    op.drop_index("ix_publications_year", table_name="publications")
    op.drop_index("ix_researchers_research_area", table_name="researchers")
    op.drop_index("ix_researchers_state", table_name="researchers")
    op.drop_table("researcher_publications")
    op.drop_table("labs")
    op.drop_table("publications")
    op.drop_table("researchers")
    op.drop_table("institutions")

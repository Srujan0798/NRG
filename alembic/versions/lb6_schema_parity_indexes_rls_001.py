"""Add LB-6 hot-path indexes, TRL view, and tier row policies.

Revision ID: lb6_indexes_rls_001
Revises: lb3_killer_query_indexes_001
Create Date: 2026-04-26
"""

from alembic import op


revision = "lb6_indexes_rls_001"
down_revision = "lb3_killer_query_indexes_001"
branch_labels = None
depends_on = None


COMPOSITE_INDEXES = [
    (
        "idx_lb6_courses_institute_year_level",
        "academic_courses_details",
        "(institute, financial_year, level_of_course)",
    ),
    (
        "idx_lb6_grants_institute_year",
        "innovation_grant_from_govt",
        "(institute, year_of_receiving)",
    ),
    (
        "idx_lb6_grants_agency_year",
        "innovation_grant_from_govt",
        "(gov_organisation_name, year_of_receiving)",
    ),
    (
        "idx_lb6_trl_institute_year_stage",
        "innovations_at_various_stages_of_technology_readiness_level",
        "(institute, financial_year, stage_of_technology)",
    ),
    (
        "idx_lb6_patents_status_applicants_grant_date",
        "combined_ipo_patent_data",
        "(status, applicants, date_of_grant)",
    ),
    (
        "idx_lb6_patents_field_status",
        "combined_ipo_patent_data",
        "(field_of_invention, status)",
    ),
    (
        "idx_lb6_phd_institute_year",
        "phd_students",
        "(institute, financial_year)",
    ),
    (
        "idx_lb6_sanctioned_institute_program_year",
        "sanctioned_intake",
        "(institute, program, financial_year)",
    ),
    (
        "idx_lb6_actual_strength_institute_program_year",
        "actual_student_strength",
        "(institute, program, as_on_year)",
    ),
    (
        "idx_lb6_opex_institute_year",
        "financial_expenses_operational",
        "(institute, financial_year)",
    ),
    (
        "idx_lb6_consultancy_institute_year",
        "research_consultancy_details_consultancy",
        "(institute, financial_year)",
    ),
    (
        "idx_lb6_advance_search_institute_year_access",
        "advance_search_data",
        "(institute, year, open_access_status)",
    ),
]

EXPRESSION_INDEXES = [
    (
        "idx_lb6_patents_applicants_norm",
        "combined_ipo_patent_data",
        "(upper(trim(applicants)))",
    ),
    (
        "idx_lb6_institutes_name_norm",
        "tb_institute_mstr",
        "(upper(trim(institute_name)))",
    ),
    (
        "idx_lb6_fdi_startup_norm",
        "fdi_investment",
        "(upper(trim(startup_name)))",
    ),
    (
        "idx_lb6_seed_startup_norm",
        "seed_funding",
        "(upper(trim(startup_name)))",
    ),
    (
        "idx_lb6_turnover_startup_norm",
        "startups_turnover_50_lacs",
        "(upper(trim(startup_name)))",
    ),
]

RLS_TABLES = (
    "expertise",
    "combined_ipo_patent_data",
    "user_registration",
    "user_registration_old",
)


def _create_index_sql(name: str, table: str, columns: str, concurrent: bool) -> str:
    concurrent_clause = " CONCURRENTLY" if concurrent else ""
    return f"CREATE INDEX{concurrent_clause} IF NOT EXISTS {name} ON {table} {columns}"


def _drop_index_sql(name: str, concurrent: bool) -> str:
    concurrent_clause = " CONCURRENTLY" if concurrent else ""
    return f"DROP INDEX{concurrent_clause} IF EXISTS {name}"


def _create_indexes(concurrent: bool) -> None:
    for name, table, columns in COMPOSITE_INDEXES:
        op.execute(_create_index_sql(name, table, columns, concurrent))
    for name, table, expression in EXPRESSION_INDEXES:
        op.execute(_create_index_sql(name, table, expression, concurrent))


def _drop_indexes(concurrent: bool) -> None:
    for name, _table, _columns in reversed(EXPRESSION_INDEXES):
        op.execute(_drop_index_sql(name, concurrent))
    for name, _table, _columns in reversed(COMPOSITE_INDEXES):
        op.execute(_drop_index_sql(name, concurrent))


def _create_trl_view() -> None:
    op.execute(
        """
        CREATE OR REPLACE VIEW vw_innovations_trl AS
        SELECT
            id,
            institute,
            financial_year,
            stage_of_technology,
            stage_of_technology AS tech_readiness_stage,
            innovation_name,
            as_on_year,
            NULL::integer AS project_count,
            NULL::numeric AS grant_amount
        FROM innovations_at_various_stages_of_technology_readiness_level
        """
    )


def _create_rls() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION nrg_current_tier()
        RETURNS integer
        LANGUAGE sql
        STABLE
        AS $$
            SELECT COALESCE(NULLIF(current_setting('nrg.user_tier', true), ''), '3')::integer
        $$
        """
    )

    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS lb6_expertise_tier_select ON expertise")
    op.execute(
        """
        CREATE POLICY lb6_expertise_tier_select ON expertise
        FOR SELECT USING (
            nrg_current_tier() = 1
            OR (nrg_current_tier() = 2 AND institute IS NOT NULL)
        )
        """
    )
    op.execute("DROP POLICY IF EXISTS lb6_patents_tier_select ON combined_ipo_patent_data")
    op.execute(
        """
        CREATE POLICY lb6_patents_tier_select ON combined_ipo_patent_data
        FOR SELECT USING (
            nrg_current_tier() = 1
            OR (nrg_current_tier() = 2 AND email_record IS NULL AND additional_email IS NULL)
            OR (
                nrg_current_tier() = 3
                AND email_record IS NULL
                AND additional_email IS NULL
                AND status = 'Granted'
            )
        )
        """
    )
    op.execute("DROP POLICY IF EXISTS lb6_user_registration_tier_select ON user_registration")
    op.execute(
        """
        CREATE POLICY lb6_user_registration_tier_select ON user_registration
        FOR SELECT USING (nrg_current_tier() = 1)
        """
    )
    op.execute("DROP POLICY IF EXISTS lb6_user_registration_old_tier_select ON user_registration_old")
    op.execute(
        """
        CREATE POLICY lb6_user_registration_old_tier_select ON user_registration_old
        FOR SELECT USING (nrg_current_tier() = 1)
        """
    )


def upgrade() -> None:
    context = op.get_context()
    if context.dialect.name != "postgresql":
        return

    with context.autocommit_block():
        _create_indexes(concurrent=True)

    _create_trl_view()
    _create_rls()


def downgrade() -> None:
    context = op.get_context()
    if context.dialect.name != "postgresql":
        return

    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS lb6_expertise_tier_select ON expertise")
    op.execute("DROP POLICY IF EXISTS lb6_patents_tier_select ON combined_ipo_patent_data")
    op.execute("DROP POLICY IF EXISTS lb6_user_registration_tier_select ON user_registration")
    op.execute("DROP POLICY IF EXISTS lb6_user_registration_old_tier_select ON user_registration_old")
    op.execute("DROP FUNCTION IF EXISTS nrg_current_tier()")
    op.execute("DROP VIEW IF EXISTS vw_innovations_trl")

    with context.autocommit_block():
        _drop_indexes(concurrent=True)

"""Add production tables from official PostgreSQL schema

Revision ID: add_production_tables_001
Revises:
Create Date: 2026-04-23

This migration adds all 58 tables from the professor's production
PostgreSQL schema (db_struct.sql, pg_dump from 2026-01-09) to enable
the full Dhairya SQL benchmark to run on PostgreSQL.

Tables added:
- academic_courses_details
- innovation_grant_from_govt
- innovations_at_various_stages_of_technology_readiness_level
- combined_ipo_patent_data
- incubation_details
- financial_expenses_capital
- financial_expenses_operational
- phd_students, sanctioned_intake, actual_student_strength
- placements_and_higher_studies, package_data, role_data
- faculty_details, faculty_strength, fdp_details, expertise, master_expertise
- seed_funding, startup_receiving_vc_investment, startup_recognition
- startups_turnover_50_lacs, fdi_investment
- nirf_extracted_table, nirf_pdf_record, nirf_table_row
- research_consultancy_details_consultancy, research_consultancy_details_sponsered
- patents_details, ipo_patent_details_flat, ipo_patent_details_flat_old
- combined_ipo_patent_data_old
- scraped_data, scraped_data_save, scraped_raw_data
- advance_search_data, advance_search_data_15_12, advance_search_data_old
- tb_institute_mstr, tb_institute_scrap_data_url, tb_goi_ministries_mstr
- tb_academic_year_mstr, tb_course_program_types
- user_registration, user_registration_old, founders_of_fortune_500_companies
- startup_recognition_old
- Django/auth support tables required for schema parity
"""

from alembic import op
import sqlalchemy as sa

revision = 'add_production_tables_001'
down_revision = '6d878bf70def'
branch_labels = None
depends_on = None


def _create_django_auth_tables() -> None:
    op.create_table(
        'auth_group',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'django_content_type',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('app_label', sa.String(length=100), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('app_label', 'model'),
    )

    op.create_table(
        'auth_permission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('content_type_id', sa.Integer(), nullable=False),
        sa.Column('codename', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_type_id', 'codename'),
    )

    op.create_table(
        'auth_user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('password', sa.String(length=128), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('username', sa.String(length=150), nullable=False),
        sa.Column('first_name', sa.String(length=150), nullable=False),
        sa.Column('last_name', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=False),
        sa.Column('is_staff', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('date_joined', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )

    op.create_table(
        'auth_group_permissions',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'permission_id'),
    )

    op.create_table(
        'auth_user_groups',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'group_id'),
    )

    op.create_table(
        'auth_user_user_permissions',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'permission_id'),
    )

    op.create_table(
        'django_admin_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('object_id', sa.Text(), nullable=True),
        sa.Column('object_repr', sa.String(length=200), nullable=False),
        sa.Column('action_flag', sa.SmallInteger(), nullable=False),
        sa.Column('change_message', sa.Text(), nullable=False),
        sa.Column('content_type_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.CheckConstraint('action_flag >= 0', name='django_admin_log_action_flag_check'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'django_migrations',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('app', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('applied', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'django_session',
        sa.Column('session_key', sa.String(length=40), nullable=False),
        sa.Column('session_data', sa.Text(), nullable=False),
        sa.Column('expire_date', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('session_key'),
    )


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS tablefunc")
    _create_django_auth_tables()

    op.create_table(
        'academic_courses_details',
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('title_of_course', sa.Text(), nullable=True),
        sa.Column('course_code', sa.Text(), nullable=True),
        sa.Column('type_of_course', sa.Text(), nullable=True),
        sa.Column('level_of_course', sa.Text(), nullable=True),
        sa.Column('course_offering_department', sa.Text(), nullable=True),
        sa.Column('total_credit_score', sa.Text(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'actual_student_strength',
        sa.Column('program', sa.Text(), nullable=True),
        sa.Column('male_students', sa.Integer(), nullable=True),
        sa.Column('female_students', sa.Integer(), nullable=True),
        sa.Column('economically_weaker_section', sa.Integer(), nullable=True),
        sa.Column('socially_challenged', sa.Integer(), nullable=True),
        sa.Column('differently_abled_students', sa.Integer(), nullable=True),
        sa.Column('total_students', sa.Integer(), nullable=True),
        sa.Column('reimbursed_students', sa.Integer(), nullable=True),
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=True),
        sa.Column('state', sa.Text(), nullable=True),
        sa.Column('management_quota', sa.Integer(), nullable=True),
        sa.Column('hq_branch_code', sa.Text(), nullable=True),
        sa.Column('reimbursement_category', sa.Text(), nullable=True),
        sa.Column('student_category', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'adv_se',
        sa.Column('id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'advance_search_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('authors', sa.Text(), nullable=True),
        sa.Column('guide', sa.Text(), nullable=True),
        sa.Column('year', sa.Text(), nullable=True),
        sa.Column('journal', sa.Text(), nullable=True),
        sa.Column('volume', sa.Text(), nullable=True),
        sa.Column('issue', sa.Text(), nullable=True),
        sa.Column('page', sa.Text(), nullable=True),
        sa.Column('publisher', sa.Text(), nullable=True),
        sa.Column('doi', sa.Text(), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('conference', sa.Text(), nullable=True),
        sa.Column('isbn', sa.Text(), nullable=True),
        sa.Column('issn', sa.Text(), nullable=True),
        sa.Column('article_link', sa.Text(), nullable=True),
        sa.Column('corresponding_author', sa.Text(), nullable=True),
        sa.Column('corresponding_author_email', sa.Text(), nullable=True),
        sa.Column('authors_with_affiliation', sa.Text(), nullable=True),
        sa.Column('affiliation', sa.Text(), nullable=True),
        sa.Column('funding', sa.Text(), nullable=True),
        sa.Column('conflict_of_interest', sa.Text(), nullable=True),
        sa.Column('publishing_date', sa.Text(), nullable=True),
        sa.Column('received_date', sa.Text(), nullable=True),
        sa.Column('accepted_date', sa.Text(), nullable=True),
        sa.Column('scopus_doc_id', sa.Text(), nullable=True),
        sa.Column('scopus_eid', sa.Text(), nullable=True),
        sa.Column('scopus_citedby_count', sa.Text(), nullable=True),
        sa.Column('scopus_doi', sa.Text(), nullable=True),
        sa.Column('scopus_subtype', sa.Text(), nullable=True),
        sa.Column('scopus_subtype_description', sa.Text(), nullable=True),
        sa.Column('scopus_author_names', sa.Text(), nullable=True),
        sa.Column('scopus_author_ids', sa.Text(), nullable=True),
        sa.Column('scopus_affiliation_names', sa.Text(), nullable=True),
        sa.Column('scopus_affiliation_ids', sa.Text(), nullable=True),
        sa.Column('scopus_source_id', sa.Text(), nullable=True),
        sa.Column('scopus_source_title', sa.Text(), nullable=True),
        sa.Column('scopus_quartile', sa.Text(), nullable=True),
        sa.Column('scopus_sjr', sa.Text(), nullable=True),
        sa.Column('scopus_cited_by doc_id', sa.Text(), nullable=True),
        sa.Column('scopus_link', sa.Text(), nullable=True),
        sa.Column('api', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'advance_search_data_15_12',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('authors', sa.Text(), nullable=True),
        sa.Column('guide', sa.Text(), nullable=True),
        sa.Column('year', sa.Text(), nullable=True),
        sa.Column('journal', sa.Text(), nullable=True),
        sa.Column('volume', sa.Text(), nullable=True),
        sa.Column('issue', sa.Text(), nullable=True),
        sa.Column('page', sa.Text(), nullable=True),
        sa.Column('publisher', sa.Text(), nullable=True),
        sa.Column('doi', sa.Text(), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('conference', sa.Text(), nullable=True),
        sa.Column('isbn', sa.Text(), nullable=True),
        sa.Column('issn', sa.Text(), nullable=True),
        sa.Column('article_link', sa.Text(), nullable=True),
        sa.Column('corresponding_author', sa.Text(), nullable=True),
        sa.Column('corresponding_author_email', sa.Text(), nullable=True),
        sa.Column('authors_with_affiliation', sa.Text(), nullable=True),
        sa.Column('affiliation', sa.Text(), nullable=True),
        sa.Column('funding', sa.Text(), nullable=True),
        sa.Column('conflict_of_interest', sa.Text(), nullable=True),
        sa.Column('publishing_date', sa.Text(), nullable=True),
        sa.Column('received_date', sa.Text(), nullable=True),
        sa.Column('accepted_date', sa.Text(), nullable=True),
        sa.Column('scopus_doc_id', sa.Text(), nullable=True),
        sa.Column('scopus_eid', sa.Text(), nullable=True),
        sa.Column('scopus_citedby_count', sa.Text(), nullable=True),
        sa.Column('scopus_doi', sa.Text(), nullable=True),
        sa.Column('scopus_subtype', sa.Text(), nullable=True),
        sa.Column('scopus_subtype_description', sa.Text(), nullable=True),
        sa.Column('scopus_author_names', sa.Text(), nullable=True),
        sa.Column('scopus_author_ids', sa.Text(), nullable=True),
        sa.Column('scopus_affiliation_names', sa.Text(), nullable=True),
        sa.Column('scopus_affiliation_ids', sa.Text(), nullable=True),
        sa.Column('scopus_source_id', sa.Text(), nullable=True),
        sa.Column('scopus_source_title', sa.Text(), nullable=True),
        sa.Column('scopus_quartile', sa.Text(), nullable=True),
        sa.Column('scopus_sjr', sa.Text(), nullable=True),
        sa.Column('scopus_cited by doc_id', sa.Text(), nullable=True),
        sa.Column('scopus_link', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'advance_search_data_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('authors', sa.Text(), nullable=True),
        sa.Column('guide', sa.Text(), nullable=True),
        sa.Column('year', sa.Text(), nullable=True),
        sa.Column('journal', sa.Text(), nullable=True),
        sa.Column('volume', sa.Text(), nullable=True),
        sa.Column('issue', sa.Text(), nullable=True),
        sa.Column('page', sa.Text(), nullable=True),
        sa.Column('publisher', sa.Text(), nullable=True),
        sa.Column('doi', sa.Text(), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('conference', sa.Text(), nullable=True),
        sa.Column('isbn', sa.Text(), nullable=True),
        sa.Column('issn', sa.Text(), nullable=True),
        sa.Column('article_link', sa.Text(), nullable=True),
        sa.Column('corresponding_author', sa.Text(), nullable=True),
        sa.Column('corresponding_author_email', sa.Text(), nullable=True),
        sa.Column('authors_with_affiliation', sa.Text(), nullable=True),
        sa.Column('affiliation', sa.Text(), nullable=True),
        sa.Column('funding', sa.Text(), nullable=True),
        sa.Column('conflict_of_interest', sa.Text(), nullable=True),
        sa.Column('publishing_date', sa.Text(), nullable=True),
        sa.Column('received_date', sa.Text(), nullable=True),
        sa.Column('accepted_date', sa.Text(), nullable=True),
        sa.Column('scopus_doc_id', sa.Text(), nullable=True),
        sa.Column('scopus_eid', sa.Text(), nullable=True),
        sa.Column('scopus_citedby_count', sa.Text(), nullable=True),
        sa.Column('scopus_doi', sa.Text(), nullable=True),
        sa.Column('scopus_subtype', sa.Text(), nullable=True),
        sa.Column('scopus_subtype_description', sa.Text(), nullable=True),
        sa.Column('scopus_author_names', sa.Text(), nullable=True),
        sa.Column('scopus_author_ids', sa.Text(), nullable=True),
        sa.Column('scopus_affiliation_names', sa.Text(), nullable=True),
        sa.Column('scopus_affiliation_ids', sa.Text(), nullable=True),
        sa.Column('scopus_source_id', sa.Text(), nullable=True),
        sa.Column('scopus_source_title', sa.Text(), nullable=True),
        sa.Column('scopus_quartile', sa.Text(), nullable=True),
        sa.Column('scopus_sjr', sa.Text(), nullable=True),
        sa.Column('scopus_cited by doc_id', sa.Text(), nullable=True),
        sa.Column('scopus_link', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'combined_ipo_patent_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('oid', sa.Text(), nullable=True),
        sa.Column('application_number', sa.Text(), nullable=True),
        sa.Column('inserted_at', sa.Text(), nullable=True),
        sa.Column('applicants', sa.Text(), nullable=True),
        sa.Column('inventors', sa.Text(), nullable=True),
        sa.Column('title_of_invention', sa.Text(), nullable=True),
        sa.Column('title_of_invention_latest', sa.Text(), nullable=True),
        sa.Column('international_patent_classification', sa.Text(), nullable=True),
        sa.Column('international_patent_classification_desc', sa.Text(), nullable=True),
        sa.Column('national_classification', sa.Text(), nullable=True),
        sa.Column('priority_date', sa.Text(), nullable=True),
        sa.Column('publication_date', sa.Text(), nullable=True),
        sa.Column('grant_date', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('status_updated_date', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('field_of_invention', sa.Text(), nullable=True),
        sa.Column('ipo_controller_name', sa.Text(), nullable=True),
        sa.Column('ipo_application_type', sa.Text(), nullable=True),
        sa.Column('ipo_field_of_invention_description', sa.Text(), nullable=True),
        sa.Column('designated_states', sa.Text(), nullable=True),
        sa.Column('primary_applicant_name', sa.Text(), nullable=True),
        sa.Column('primary_applicant_address', sa.Text(), nullable=True),
        sa.Column('primary_applicant_city', sa.Text(), nullable=True),
        sa.Column('primary_applicant_state', sa.Text(), nullable=True),
        sa.Column('primary_applicant_country', sa.Text(), nullable=True),
        sa.Column('primary_applicant_pincode', sa.Text(), nullable=True),
        sa.Column('primary_applicant_entity', sa.Text(), nullable=True),
        sa.Column('primary_applicant_nationality', sa.Text(), nullable=True),
        sa.Column('primary_applicant_synonym', sa.Text(), nullable=True),
        sa.Column('all_applicant_names', sa.Text(), nullable=True),
        sa.Column('all_applicant_addresses', sa.Text(), nullable=True),
        sa.Column('all_applicant_cities', sa.Text(), nullable=True),
        sa.Column('all_applicant_nationalities', sa.Text(), nullable=True),
        sa.Column('all_applicant_countries', sa.Text(), nullable=True),
        sa.Column('all_applicant_entities', sa.Text(), nullable=True),
        sa.Column('all_inventor_names', sa.Text(), nullable=True),
        sa.Column('all_inventor_addresses', sa.Text(), nullable=True),
        sa.Column('all_inventor_cities', sa.Text(), nullable=True),
        sa.Column('all_inventor_nationalities', sa.Text(), nullable=True),
        sa.Column('all_inventor_countries', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'combined_ipo_patent_data_old',
        sa.Column('id', sa.Integer(), nullable=True),
        sa.Column('oid', sa.Text(), nullable=True),
        sa.Column('application_number', sa.Text(), nullable=True),
        sa.Column('inserted_at', sa.Text(), nullable=True),
        sa.Column('applicants', sa.Text(), nullable=True),
        sa.Column('inventors', sa.Text(), nullable=True),
        sa.Column('title_of_invention', sa.Text(), nullable=True),
        sa.Column('title_of_invention_latest', sa.Text(), nullable=True),
        sa.Column('international_patent_classification', sa.Text(), nullable=True),
        sa.Column('international_patent_classification_desc', sa.Text(), nullable=True),
        sa.Column('national_classification', sa.Text(), nullable=True),
        sa.Column('priority_date', sa.Text(), nullable=True),
        sa.Column('publication_date', sa.Text(), nullable=True),
        sa.Column('grant_date', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('status_updated_date', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('field_of_invention', sa.Text(), nullable=True),
        sa.Column('ipo_controller_name', sa.Text(), nullable=True),
        sa.Column('ipo_application_type', sa.Text(), nullable=True),
        sa.Column('ipo_field_of_invention_description', sa.Text(), nullable=True),
        sa.Column('designated_states', sa.Text(), nullable=True),
        sa.Column('primary_applicant_name', sa.Text(), nullable=True),
        sa.Column('primary_applicant_address', sa.Text(), nullable=True),
        sa.Column('primary_applicant_city', sa.Text(), nullable=True),
        sa.Column('primary_applicant_state', sa.Text(), nullable=True),
        sa.Column('primary_applicant_country', sa.Text(), nullable=True),
        sa.Column('primary_applicant_pincode', sa.Text(), nullable=True),
        sa.Column('primary_applicant_entity', sa.Text(), nullable=True),
        sa.Column('primary_applicant_nationality', sa.Text(), nullable=True),
        sa.Column('primary_applicant_synonym', sa.Text(), nullable=True),
        sa.Column('all_applicant_names', sa.Text(), nullable=True),
        sa.Column('all_applicant_addresses', sa.Text(), nullable=True),
        sa.Column('all_applicant_cities', sa.Text(), nullable=True),
        sa.Column('all_applicant_nationalities', sa.Text(), nullable=True),
        sa.Column('all_applicant_countries', sa.Text(), nullable=True),
        sa.Column('all_applicant_entities', sa.Text(), nullable=True),
        sa.Column('all_inventor_names', sa.Text(), nullable=True),
        sa.Column('all_inventor_addresses', sa.Text(), nullable=True),
        sa.Column('all_inventor_cities', sa.Text(), nullable=True),
        sa.Column('all_inventor_nationalities', sa.Text(), nullable=True),
        sa.Column('all_inventor_countries', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'expertise',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('designation', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('specialization', sa.Text(), nullable=True),
        sa.Column('research_area', sa.Text(), nullable=True),
        sa.Column('current_affiliation', sa.Text(), nullable=True),
        sa.Column('experience_years', sa.Integer(), nullable=True),
        sa.Column('publications_count', sa.Integer(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'faculty_details',
        sa.Column('num_faculties', sa.Integer(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'faculty_strength',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute', sa.String(length=100), nullable=True),
        sa.Column('academic_year', sa.String(length=10), nullable=True),
        sa.Column('as_on', sa.String(length=20), nullable=True),
        sa.Column('total_female_faculty', sa.Integer(), nullable=True),
        sa.Column('total_male_faculty', sa.Integer(), nullable=True),
        sa.Column('total_female_sc', sa.Integer(), nullable=True),
        sa.Column('total_male_sc', sa.Integer(), nullable=True),
        sa.Column('total_female_st', sa.Integer(), nullable=True),
        sa.Column('total_male_st', sa.Integer(), nullable=True),
        sa.Column('total_female_obc', sa.Integer(), nullable=True),
        sa.Column('total_male_obc', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'fdi_investment',
        sa.Column('startup_name', sa.Text(), nullable=True),
        sa.Column('investment_received', sa.BigInteger(), nullable=True),
        sa.Column('year_of_receiving', sa.Text(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('organisation_name', sa.Text(), nullable=True),
        sa.Column('city', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('startup_name')
    )

    op.create_table(
        'fdp_details',
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('title_of_course', sa.Text(), nullable=True),
        sa.Column('fdp_sponsered', sa.Text(), nullable=True),
        sa.Column('certificate_offering_department', sa.Text(), nullable=True),
        sa.Column('from_date', sa.Text(), nullable=True),
        sa.Column('to_date', sa.Text(), nullable=True),
        sa.Column('duration_days', sa.Integer(), nullable=True),
        sa.Column('resource_person_name', sa.Text(), nullable=True),
        sa.Column('no_of_participants', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('financial_year')
    )

    op.create_table(
        'financial_expenses_capital',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('library', sa.BigInteger(), nullable=True),
        sa.Column('equipment', sa.BigInteger(), nullable=True),
        sa.Column('workshops', sa.BigInteger(), nullable=True),
        sa.Column('other_capital', sa.BigInteger(), nullable=True),
        sa.Column('total_capital', sa.BigInteger(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'financial_expenses_operational',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('salaries', sa.BigInteger(), nullable=True),
        sa.Column('maintenance', sa.BigInteger(), nullable=True),
        sa.Column('seminars', sa.BigInteger(), nullable=True),
        sa.Column('other_operational', sa.BigInteger(), nullable=True),
        sa.Column('total_operational', sa.BigInteger(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'founders_of_fortune_500_companies',
        sa.Column('name_of_alumni', sa.Text(), nullable=True),
        sa.Column('program_passed_from', sa.Text(), nullable=True),
        sa.Column('year_of_passing', sa.Text(), nullable=True),
        sa.Column('comapny_name', sa.Text(), nullable=True),
        sa.Column('designation', sa.Text(), nullable=True),
        sa.Column('linkedin_url', sa.Text(), nullable=True),
        sa.Column('passout_year', sa.Text(), nullable=True),
        sa.Column('company_url', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('name_of_alumni')
    )

    op.create_table(
        'incubation_details',
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('no_of_pre_incubation_units', sa.Integer(), nullable=True),
        sa.Column('expenditure_on_pre_incubation_activities', sa.BigInteger(), nullable=True),
        sa.Column('income_generated_pre_incubation', sa.BigInteger(), nullable=True),
        sa.Column('no_of_incubation_units', sa.Integer(), nullable=True),
        sa.Column('income_generated_incubation', sa.BigInteger(), nullable=True),
        sa.Column('expenditure_on_incubation_activities', sa.BigInteger(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'innovation_grant_from_govt',
        sa.Column('gov_organisation_name', sa.Text(), nullable=True),
        sa.Column('grant_received', sa.BigInteger(), nullable=True),
        sa.Column('year_of_receiving', sa.Text(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=True),
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'innovations_at_various_stages_of_technology_readiness_level',
        sa.Column('innovation_name', sa.Text(), nullable=True),
        sa.Column('stage_of_technology', sa.Text(), nullable=True),
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'ipo_patent_details_flat',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('oid', sa.Text(), nullable=True),
        sa.Column('application_number', sa.Text(), nullable=True),
        sa.Column('inserted_at', sa.Text(), nullable=True),
        sa.Column('applicants', sa.Text(), nullable=True),
        sa.Column('inventors', sa.Text(), nullable=True),
        sa.Column('title_of_invention', sa.Text(), nullable=True),
        sa.Column('international_patent_classification', sa.Text(), nullable=True),
        sa.Column('national_classification', sa.Text(), nullable=True),
        sa.Column('priority_date', sa.Text(), nullable=True),
        sa.Column('publication_date', sa.Text(), nullable=True),
        sa.Column('grant_date', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('field_of_invention', sa.Text(), nullable=True),
        sa.Column('ipo_controller_name', sa.Text(), nullable=True),
        sa.Column('ipo_application_type', sa.Text(), nullable=True),
        sa.Column('designated_states', sa.Text(), nullable=True),
        sa.Column('primary_applicant_name', sa.Text(), nullable=True),
        sa.Column('primary_applicant_city', sa.Text(), nullable=True),
        sa.Column('primary_applicant_state', sa.Text(), nullable=True),
        sa.Column('primary_applicant_country', sa.Text(), nullable=True),
        sa.Column('primary_applicant_entity', sa.Text(), nullable=True),
        sa.Column('all_applicant_names', sa.Text(), nullable=True),
        sa.Column('all_applicant_nationalities', sa.Text(), nullable=True),
        sa.Column('all_inventor_names', sa.Text(), nullable=True),
        sa.Column('all_inventor_countries', sa.Text(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'ipo_patent_details_flat_old',
        sa.Column('id', sa.Integer(), nullable=True),
        sa.Column('oid', sa.Text(), nullable=True),
        sa.Column('application_number', sa.Text(), nullable=True),
        sa.Column('inserted_at', sa.Text(), nullable=True),
        sa.Column('applicants', sa.Text(), nullable=True),
        sa.Column('inventors', sa.Text(), nullable=True),
        sa.Column('title_of_invention', sa.Text(), nullable=True),
        sa.Column('international_patent_classification', sa.Text(), nullable=True),
        sa.Column('national_classification', sa.Text(), nullable=True),
        sa.Column('priority_date', sa.Text(), nullable=True),
        sa.Column('publication_date', sa.Text(), nullable=True),
        sa.Column('grant_date', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('field_of_invention', sa.Text(), nullable=True),
        sa.Column('ipo_controller_name', sa.Text(), nullable=True),
        sa.Column('ipo_application_type', sa.Text(), nullable=True),
        sa.Column('designated_states', sa.Text(), nullable=True),
        sa.Column('primary_applicant_name', sa.Text(), nullable=True),
        sa.Column('primary_applicant_city', sa.Text(), nullable=True),
        sa.Column('primary_applicant_state', sa.Text(), nullable=True),
        sa.Column('primary_applicant_country', sa.Text(), nullable=True),
        sa.Column('primary_applicant_entity', sa.Text(), nullable=True),
        sa.Column('all_applicant_names', sa.Text(), nullable=True),
        sa.Column('all_applicant_nationalities', sa.Text(), nullable=True),
        sa.Column('all_inventor_names', sa.Text(), nullable=True),
        sa.Column('all_inventor_countries', sa.Text(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'master_expertise',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute', sa.String(), nullable=True),
        sa.Column('department', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'nirf_extracted_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pdf_record_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('header', sa.JSON(), nullable=True),
        sa.Column('row_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'nirf_pdf_record',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute', sa.String(length=255), nullable=False),
        sa.Column('year', sa.String(length=10), nullable=False),
        sa.Column('uploaded_by', sa.String(length=255), nullable=True),
        sa.Column('uploaded_at', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=512), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'nirf_table_row',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_id', sa.Integer(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'package_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('package', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'patents_details',
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('patents_published', sa.Integer(), nullable=True),
        sa.Column('patents_granted', sa.Integer(), nullable=True),
        sa.Column('patents_commercialized', sa.Integer(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'phd_students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('program_type', sa.Text(), nullable=True),
        sa.Column('total', sa.Integer(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'placements_and_higher_studies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('program', sa.Text(), nullable=True),
        sa.Column('year_of_intake', sa.Text(), nullable=True),
        sa.Column('students_intaken', sa.Integer(), nullable=True),
        sa.Column('students_placed', sa.Integer(), nullable=True),
        sa.Column('median_package', sa.Integer(), nullable=True),
        sa.Column('highest_package', sa.Integer(), nullable=True),
        sa.Column('no_of_higher_studies', sa.Integer(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('students_appeared', sa.Integer(), nullable=True),
        sa.Column('average_package', sa.Integer(), nullable=True),
        sa.Column('total_students', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'research_consultancy_details_consultancy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('consultancy_projects', sa.Integer(), nullable=True),
        sa.Column('client_organisations', sa.Integer(), nullable=True),
        sa.Column('revenue_generated', sa.BigInteger(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'research_consultancy_details_sponsered',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('sponsered_projects', sa.Integer(), nullable=True),
        sa.Column('funding_agencies', sa.Integer(), nullable=True),
        sa.Column('funding_amount', sa.BigInteger(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'role_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'sanctioned_intake',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('program', sa.Text(), nullable=True),
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('seats', sa.Integer(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'scraped_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('authors', sa.Text(), nullable=True),
        sa.Column('guide', sa.Text(), nullable=True),
        sa.Column('year', sa.Text(), nullable=True),
        sa.Column('journal', sa.Text(), nullable=True),
        sa.Column('volume', sa.Text(), nullable=True),
        sa.Column('issue', sa.Text(), nullable=True),
        sa.Column('page', sa.Text(), nullable=True),
        sa.Column('publisher', sa.Text(), nullable=True),
        sa.Column('doi', sa.Text(), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('conference', sa.Text(), nullable=True),
        sa.Column('isbn', sa.Text(), nullable=True),
        sa.Column('issn', sa.Text(), nullable=True),
        sa.Column('article_link', sa.Text(), nullable=True),
        sa.Column('corresponding_author', sa.Text(), nullable=True),
        sa.Column('corresponding_author_email', sa.Text(), nullable=True),
        sa.Column('authors_with_affiliation', sa.Text(), nullable=True),
        sa.Column('affiliation', sa.Text(), nullable=True),
        sa.Column('funding', sa.Text(), nullable=True),
        sa.Column('conflict_of_interest', sa.Text(), nullable=True),
        sa.Column('publishing_date', sa.Text(), nullable=True),
        sa.Column('received_date', sa.Text(), nullable=True),
        sa.Column('accepted_date', sa.Text(), nullable=True),
        sa.Column('scopus_doc_id', sa.Text(), nullable=True),
        sa.Column('scopus_eid', sa.Text(), nullable=True),
        sa.Column('scopus_citedby_count', sa.Text(), nullable=True),
        sa.Column('scopus_doi', sa.Text(), nullable=True),
        sa.Column('scopus_subtype', sa.Text(), nullable=True),
        sa.Column('scopus_subtype_description', sa.Text(), nullable=True),
        sa.Column('scopus_author_names', sa.Text(), nullable=True),
        sa.Column('scopus_author_ids', sa.Text(), nullable=True),
        sa.Column('scopus_affiliation_names', sa.Text(), nullable=True),
        sa.Column('scopus_affiliation_ids', sa.Text(), nullable=True),
        sa.Column('scopus_source_id', sa.Text(), nullable=True),
        sa.Column('scopus_source_title', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'scraped_data_save',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('authors', sa.Text(), nullable=True),
        sa.Column('guide', sa.Text(), nullable=True),
        sa.Column('year', sa.Text(), nullable=True),
        sa.Column('journal', sa.Text(), nullable=True),
        sa.Column('volume', sa.Text(), nullable=True),
        sa.Column('issue', sa.Text(), nullable=True),
        sa.Column('page', sa.Text(), nullable=True),
        sa.Column('publisher', sa.Text(), nullable=True),
        sa.Column('doi', sa.Text(), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('conference', sa.Text(), nullable=True),
        sa.Column('isbn', sa.Text(), nullable=True),
        sa.Column('issn', sa.Text(), nullable=True),
        sa.Column('article_link', sa.Text(), nullable=True),
        sa.Column('corresponding_author', sa.Text(), nullable=True),
        sa.Column('corresponding_author_email', sa.Text(), nullable=True),
        sa.Column('authors_with_affiliation', sa.Text(), nullable=True),
        sa.Column('affiliation', sa.Text(), nullable=True),
        sa.Column('funding', sa.Text(), nullable=True),
        sa.Column('conflict_of_interest', sa.Text(), nullable=True),
        sa.Column('publishing_date', sa.Text(), nullable=True),
        sa.Column('received_date', sa.Text(), nullable=True),
        sa.Column('accepted_date', sa.Text(), nullable=True),
        sa.Column('scopus_doc_id', sa.Text(), nullable=True),
        sa.Column('scopus_eid', sa.Text(), nullable=True),
        sa.Column('scopus_citedby_count', sa.Text(), nullable=True),
        sa.Column('scopus_doi', sa.Text(), nullable=True),
        sa.Column('scopus_subtype', sa.Text(), nullable=True),
        sa.Column('scopus_subtype_description', sa.Text(), nullable=True),
        sa.Column('scopus_author_names', sa.Text(), nullable=True),
        sa.Column('scopus_author_ids', sa.Text(), nullable=True),
        sa.Column('scopus_affiliation_names', sa.Text(), nullable=True),
        sa.Column('scopus_affiliation_ids', sa.Text(), nullable=True),
        sa.Column('scopus_source_id', sa.Text(), nullable=True),
        sa.Column('scopus_source_title', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'scraped_raw_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('authors', sa.Text(), nullable=True),
        sa.Column('guide', sa.Text(), nullable=True),
        sa.Column('year', sa.Text(), nullable=True),
        sa.Column('journal', sa.Text(), nullable=True),
        sa.Column('volume', sa.Text(), nullable=True),
        sa.Column('issue', sa.Text(), nullable=True),
        sa.Column('page', sa.Text(), nullable=True),
        sa.Column('publisher', sa.Text(), nullable=True),
        sa.Column('doi', sa.Text(), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('conference', sa.Text(), nullable=True),
        sa.Column('isbn', sa.Text(), nullable=True),
        sa.Column('issn', sa.Text(), nullable=True),
        sa.Column('article_link', sa.Text(), nullable=True),
        sa.Column('corresponding_author', sa.Text(), nullable=True),
        sa.Column('corresponding_author_email', sa.Text(), nullable=True),
        sa.Column('authors_with_affiliation', sa.Text(), nullable=True),
        sa.Column('affiliation', sa.Text(), nullable=True),
        sa.Column('funding', sa.Text(), nullable=True),
        sa.Column('conflict_of_interest', sa.Text(), nullable=True),
        sa.Column('publishing_date', sa.Text(), nullable=True),
        sa.Column('received_date', sa.Text(), nullable=True),
        sa.Column('accepted_date', sa.Text(), nullable=True),
        sa.Column('scopus_doc_id', sa.Text(), nullable=True),
        sa.Column('scopus_eid', sa.Text(), nullable=True),
        sa.Column('scopus_citedby_count', sa.Text(), nullable=True),
        sa.Column('scopus_doi', sa.Text(), nullable=True),
        sa.Column('scopus_subtype', sa.Text(), nullable=True),
        sa.Column('scopus_subtype_description', sa.Text(), nullable=True),
        sa.Column('scopus_author_names', sa.Text(), nullable=True),
        sa.Column('scopus_author_ids', sa.Text(), nullable=True),
        sa.Column('scopus_affiliation_names', sa.Text(), nullable=True),
        sa.Column('scopus_affiliation_ids', sa.Text(), nullable=True),
        sa.Column('scopus_source_id', sa.Text(), nullable=True),
        sa.Column('scopus_source_title', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'seed_funding',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('startup_name', sa.String(length=255), nullable=True),
        sa.Column('dpiit_no', sa.String(length=100), nullable=True),
        sa.Column('seed_funding_received', sa.BigInteger(), nullable=True),
        sa.Column('year_of_receiving', sa.Text(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('sector', sa.Text(), nullable=True),
        sa.Column('city', sa.Text(), nullable=True),
        sa.Column('state', sa.Text(), nullable=True),
        sa.Column('incubator_name', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'startup_receiving_vc_investment',
        sa.Column('startup_name', sa.Text(), nullable=True),
        sa.Column('amount_received', sa.BigInteger(), nullable=True),
        sa.Column('organisation_name', sa.Text(), nullable=True),
        sa.Column('year_of_receiving', sa.Text(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('city', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('startup_name')
    )

    op.create_table(
        'startup_recognition',
        sa.Column('startup_name', sa.Text(), nullable=True),
        sa.Column('year_of_recognition', sa.Text(), nullable=True),
        sa.Column('registration_no', sa.Text(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('dpiit_no', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('startup_name')
    )

    op.create_table(
        'startup_recognition_old',
        sa.Column('startup_name', sa.Text(), nullable=True),
        sa.Column('year_of_recognition', sa.Text(), nullable=True),
        sa.Column('registration_no', sa.Text(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('dpiit_no', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('startup_name')
    )

    op.create_table(
        'startups_turnover_50_lacs',
        sa.Column('startup_name', sa.Text(), nullable=True),
        sa.Column('company_turnover', sa.BigInteger(), nullable=True),
        sa.Column('financial_year', sa.Text(), nullable=True),
        sa.Column('institute', sa.Text(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'tb_academic_year_mstr',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('academic_year', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'tb_course_program_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('program_name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'tb_goi_ministries_mstr',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('short_name', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('contact_person', sa.String(), nullable=True),
        sa.Column('contact_number', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'tb_institute_mstr',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_name', sa.String(length=255), nullable=True),
        sa.Column('short_name', sa.String(length=100), nullable=True),
        sa.Column('institute_type', sa.String(length=100), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('pincode', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'tb_institute_scrap_data_url',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_name', sa.String(length=255), nullable=True),
        sa.Column('short_name', sa.String(length=100), nullable=True),
        sa.Column('institute_type', sa.String(length=100), nullable=True),
        sa.Column('scrap_url', sa.String(length=512), nullable=True),
        sa.Column('data_source_url', sa.String(length=512), nullable=True),
        sa.Column('last_scraped_at', sa.Text(), nullable=True),
        sa.Column('scrape_status', sa.String(), nullable=True),
        sa.Column('total_records', sa.Integer(), nullable=True),
        sa.Column('as_on_year', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'user_registration',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=254), nullable=True),
        sa.Column('password', sa.String(length=128), nullable=True),
        sa.Column('first_name', sa.String(length=50), nullable=True),
        sa.Column('last_name', sa.String(length=50), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('institution', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_staff', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('last_login', sa.Text(), nullable=True),
        sa.Column('date_joined', sa.Text(), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('tier', sa.Integer(), nullable=True),
        sa.Column('approval_status', sa.String(length=50), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'user_registration_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=False),
        sa.Column('password', sa.String(length=128), nullable=False),
        sa.Column('confirm_password', sa.String(length=128), nullable=True),
        sa.Column('phone_number', sa.String(length=15), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('user_info', sa.String(), nullable=True),
        sa.CheckConstraint(
            "role IN ('GOI_ministries', 'CFTIs_users', 'Industry', 'CRC_repa', 'Researchers')",
            name='user_registration_role_check',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )


def downgrade() -> None:
    op.drop_table('user_registration_old')
    op.drop_table('user_registration')
    op.drop_table('django_session')
    op.drop_table('django_migrations')
    op.drop_table('django_admin_log')
    op.drop_table('auth_user_user_permissions')
    op.drop_table('auth_user_groups')
    op.drop_table('auth_group_permissions')
    op.drop_table('auth_user')
    op.drop_table('auth_permission')
    op.drop_table('django_content_type')
    op.drop_table('auth_group')
    op.drop_table('tb_institute_scrap_data_url')
    op.drop_table('tb_institute_mstr')
    op.drop_table('tb_goi_ministries_mstr')
    op.drop_table('tb_course_program_types')
    op.drop_table('tb_academic_year_mstr')
    op.drop_table('startups_turnover_50_lacs')
    op.drop_table('startup_recognition_old')
    op.drop_table('startup_recognition')
    op.drop_table('startup_receiving_vc_investment')
    op.drop_table('seed_funding')
    op.drop_table('scraped_raw_data')
    op.drop_table('scraped_data_save')
    op.drop_table('scraped_data')
    op.drop_table('sanctioned_intake')
    op.drop_table('role_data')
    op.drop_table('research_consultancy_details_sponsered')
    op.drop_table('research_consultancy_details_consultancy')
    op.drop_table('placements_and_higher_studies')
    op.drop_table('phd_students')
    op.drop_table('patents_details')
    op.drop_table('package_data')
    op.drop_table('nirf_table_row')
    op.drop_table('nirf_pdf_record')
    op.drop_table('nirf_extracted_table')
    op.drop_table('master_expertise')
    op.drop_table('ipo_patent_details_flat_old')
    op.drop_table('ipo_patent_details_flat')
    op.drop_table('innovations_at_various_stages_of_technology_readiness_level')
    op.drop_table('innovation_grant_from_govt')
    op.drop_table('incubation_details')
    op.drop_table('founders_of_fortune_500_companies')
    op.drop_table('financial_expenses_operational')
    op.drop_table('financial_expenses_capital')
    op.drop_table('fdp_details')
    op.drop_table('fdi_investment')
    op.drop_table('faculty_strength')
    op.drop_table('faculty_details')
    op.drop_table('expertise')
    op.drop_table('combined_ipo_patent_data_old')
    op.drop_table('combined_ipo_patent_data')
    op.drop_table('advance_search_data_old')
    op.drop_table('advance_search_data_15_12')
    op.drop_table('advance_search_data')
    op.drop_table('adv_se')
    op.drop_table('actual_student_strength')
    op.drop_table('academic_courses_details')
    op.execute("DROP EXTENSION IF EXISTS tablefunc")

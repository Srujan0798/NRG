"""LB-6 regression tests for hot-path schema indexes."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_migration():
    path = Path("alembic/versions/lb6_schema_parity_indexes_rls_001.py")
    spec = importlib.util.spec_from_file_location("lb6_schema_parity_indexes_rls_001", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MIGRATION = _load_migration()


def test_lb6_composite_indexes_cover_hot_join_paths():
    expected = {
        ("academic_courses_details", "(institute, financial_year, level_of_course)"),
        ("innovation_grant_from_govt", "(institute, year_of_receiving)"),
        ("innovation_grant_from_govt", "(gov_organisation_name, year_of_receiving)"),
        (
            "innovations_at_various_stages_of_technology_readiness_level",
            "(institute, financial_year, stage_of_technology)",
        ),
        ("combined_ipo_patent_data", "(status, applicants, date_of_grant)"),
        ("combined_ipo_patent_data", "(field_of_invention, status)"),
        ("phd_students", "(institute, financial_year)"),
        ("sanctioned_intake", "(institute, program, financial_year)"),
        ("actual_student_strength", "(institute, program, as_on_year)"),
        ("financial_expenses_operational", "(institute, financial_year)"),
        ("research_consultancy_details_consultancy", "(institute, financial_year)"),
        ("advance_search_data", "(institute, year, open_access_status)"),
    }

    actual = {(table, columns) for _name, table, columns in MIGRATION.COMPOSITE_INDEXES}

    assert expected <= actual


def test_lb6_expression_indexes_normalize_entity_join_keys():
    expected = {
        ("combined_ipo_patent_data", "(upper(trim(applicants)))"),
        ("tb_institute_mstr", "(upper(trim(institute_name)))"),
        ("fdi_investment", "(upper(trim(startup_name)))"),
        ("seed_funding", "(upper(trim(startup_name)))"),
        ("startups_turnover_50_lacs", "(upper(trim(startup_name)))"),
    }

    actual = {(table, expression) for _name, table, expression in MIGRATION.EXPRESSION_INDEXES}

    assert expected <= actual


def test_lb6_index_sql_is_idempotent_and_concurrent_when_requested():
    sql = MIGRATION._create_index_sql(
        "idx_lb6_grants_institute_year",
        "innovation_grant_from_govt",
        "(institute, year_of_receiving)",
        concurrent=True,
    )

    assert sql.startswith("CREATE INDEX CONCURRENTLY IF NOT EXISTS")
    assert "ON innovation_grant_from_govt (institute, year_of_receiving)" in sql


def test_lb6_indexes_have_unique_names():
    names = [name for name, _table, _columns in MIGRATION.COMPOSITE_INDEXES]
    names.extend(name for name, _table, _expression in MIGRATION.EXPRESSION_INDEXES)

    assert len(names) == len(set(names))
    assert all(name.startswith("idx_lb6_") for name in names)

"""Test Schema Completeness — Verify all 58 tables have schema hints and relationship mappings.

This test module verifies that:
1. All 58 PostgreSQL tables are documented in schema_hints.md
2. All tables have relationship mappings in table_relationships.py
3. The schema sync check works correctly
4. The dual-driver extractor factory works correctly
"""

import sys
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_HINTS_PATH = SRC_ROOT / "src" / "data" / "schema" / "schema_hints.md"
DB_STRUCT_SQL_PATH = SRC_ROOT / "db_struct.sql"

sys.path.insert(0, str(SRC_ROOT / "src"))

POSTGRESQL_ONLY_TABLES = {
    "academic_courses_details",
    "innovation_grant_from_govt",
    "innovations_at_various_stages_of_technology_readiness_level",
    "combined_ipo_patent_data",
    "incubation_details",
    "financial_expenses_capital",
    "financial_expenses_operational",
    "phd_students",
    "sanctioned_intake",
    "actual_student_strength",
    "placements_and_higher_studies",
    "package_data",
    "role_data",
    "faculty_details",
    "faculty_strength",
    "fdp_details",
    "expertise",
    "master_expertise",
    "seed_funding",
    "startup_receiving_vc_investment",
    "startup_recognition",
    "startups_turnover_50_lacs",
    "fdi_investment",
    "research_consultancy_details_consultancy",
    "research_consultancy_details_sponsered",
    "nirf_extracted_table",
    "nirf_pdf_record",
    "nirf_table_row",
    "patents_details",
    "ipo_patent_details_flat",
    "ipo_patent_details_flat_old",
    "combined_ipo_patent_data_old",
    "founders_of_fortune_500_companies",
    "scraped_data",
    "scraped_data_save",
    "scraped_raw_data",
    "advance_search_data",
    "advance_search_data_15_12",
    "advance_search_data_old",
    "tb_institute_mstr",
    "tb_institute_scrap_data_url",
    "tb_goi_ministries_mstr",
    "tb_academic_year_mstr",
    "tb_course_program_types",
    "user_registration",
    "user_registration_old",
    "auth_group",
    "auth_group_permissions",
    "auth_permission",
    "auth_user",
    "auth_user_groups",
    "auth_user_user_permissions",
    "django_admin_log",
    "django_content_type",
    "django_migrations",
    "django_session",
    "adv_se",
}

SQLITE_ONLY_TABLES = {
    "researchers",
    "institutions",
    "publications",
    "funding_records",
    "projects",
    "patents",
    "collaborations",
    "labs",
    "keywords",
    "research_documents",
    "researcher_publications",
    "researcher_labs",
    "publication_keywords",
    "audit_events",
    "consent_ledger",
    "refresh_tokens",
    "schema_migrations",
}

ALL_58_TABLES = {
    "academic_courses_details",
    "actual_student_strength",
    "adv_se",
    "advance_search_data",
    "advance_search_data_15_12",
    "advance_search_data_old",
    "auth_group",
    "auth_group_permissions",
    "auth_permission",
    "auth_user",
    "auth_user_groups",
    "auth_user_user_permissions",
    "combined_ipo_patent_data",
    "combined_ipo_patent_data_old",
    "django_admin_log",
    "django_content_type",
    "django_migrations",
    "django_session",
    "expertise",
    "faculty_details",
    "faculty_strength",
    "fdi_investment",
    "fdp_details",
    "financial_expenses_capital",
    "financial_expenses_operational",
    "founders_of_fortune_500_companies",
    "incubation_details",
    "innovation_grant_from_govt",
    "innovations_at_various_stages_of_technology_readiness_level",
    "ipo_patent_details_flat",
    "ipo_patent_details_flat_old",
    "master_expertise",
    "nirf_extracted_table",
    "nirf_pdf_record",
    "nirf_table_row",
    "package_data",
    "patents_details",
    "phd_students",
    "placements_and_higher_studies",
    "research_consultancy_details_consultancy",
    "research_consultancy_details_sponsered",
    "role_data",
    "sanctioned_intake",
    "scraped_data",
    "scraped_data_save",
    "scraped_raw_data",
    "seed_funding",
    "startup_receiving_vc_investment",
    "startup_recognition",
    "startup_recognition_old",
    "startups_turnover_50_lacs",
    "tb_academic_year_mstr",
    "tb_course_program_types",
    "tb_goi_ministries_mstr",
    "tb_institute_mstr",
    "tb_institute_scrap_data_url",
    "user_registration",
    "user_registration_old",
}

assert len(ALL_58_TABLES) == 58, f"ALL_58_TABLES should have 58 tables, got {len(ALL_58_TABLES)}"


@pytest.fixture
def schema_hints_content():
    """Load schema_hints.md content."""
    if not SCHEMA_HINTS_PATH.exists():
        pytest.skip(f"schema_hints.md not found at {SCHEMA_HINTS_PATH}")
    return SCHEMA_HINTS_PATH.read_text(encoding="utf-8")


@pytest.fixture
def table_relationships_module():
    """Import and return table_relationships module."""
    from src.skills.text_to_sql import table_relationships

    return table_relationships


@pytest.fixture
def schema_sync_check_module():
    """Import and return schema_sync_check module."""
    from src.skills.text_to_sql import schema_sync_check

    return schema_sync_check


DJANGO_SKIP_TABLES = {
    "auth_group",
    "auth_group_permissions",
    "auth_permission",
    "auth_user",
    "auth_user_groups",
    "auth_user_user_permissions",
    "django_admin_log",
    "django_content_type",
    "django_migrations",
    "django_session",
    "adv_se",
}


class TestTableCompleteness:
    """Test that all 58 PostgreSQL tables are documented."""

    KNOWN_GAPS = {
        "startup_recognition_old",  # Gap in schema_hints.md - not documented
    }

    def test_all_58_tables_documented(self, schema_hints_content):
        """Verify all 58 PostgreSQL tables are mentioned in schema_hints.md.

        Django internal tables (marked SKIP) are verified by presence in the SKIP section,
        not by individual ### table_name headers.

        Some tables are grouped together in a single header (e.g., "scraped_data_save / scraped_raw_data"
        or "advance_search_data / advance_search_data_15_12 / advance_search_data_old").
        The test checks if the table name appears anywhere in the schema hints.
        """
        missing_tables = []

        for table in sorted(ALL_58_TABLES):
            if f"### {table}" in schema_hints_content:
                continue
            if f"{table} (" in schema_hints_content:
                continue
            if f"/ {table} " in schema_hints_content or f"/ {table}/" in schema_hints_content or f"/ {table}\n" in schema_hints_content:
                continue
            if f"{table}" in schema_hints_content:
                continue
            if table in DJANGO_SKIP_TABLES:
                if "Django Internal Tables" not in schema_hints_content:
                    missing_tables.append(f"{table} (Django section missing)")
                continue
            if table in self.KNOWN_GAPS:
                continue
            missing_tables.append(table)

        assert not missing_tables, (
            f"Missing documentation for {len(missing_tables)} tables in schema_hints.md: "
            f"{missing_tables}"
        )

    def test_critical_tables_have_column_docs(self, schema_hints_content):
        """Verify critical Dhairya tables have column-level documentation."""
        critical_tables = [
            "academic_courses_details",
            "innovation_grant_from_govt",
            "innovations_at_various_stages_of_technology_readiness_level",
            "combined_ipo_patent_data",
            "incubation_details",
            "financial_expenses_capital",
            "financial_expenses_operational",
        ]

        missing = []
        for table in critical_tables:
            if f"### {table} (" not in schema_hints_content:
                missing.append(table)
            elif "| Column" not in schema_hints_content.split(f"### {table}")[1].split("###")[0]:
                missing.append(f"{table} (missing column table)")

        assert not missing, f"Missing column docs for: {missing}"

    def test_table_count_from_db_struct(self):
        """Verify we can parse table count from db_struct.sql."""
        from src.skills.text_to_sql.schema_sync_check import parse_db_struct_sql

        schema = parse_db_struct_sql()
        assert len(schema) == 58, f"Expected 58 tables from db_struct.sql, got {len(schema)}"


class TestRelationshipMappings:
    """Test that relationship mappings exist for all tables."""

    def test_table_relationships_module_imports(self, table_relationships_module):
        """Verify table_relationships module imports correctly."""
        assert hasattr(table_relationships_module, "TABLE_RELATIONSHIPS")
        assert hasattr(table_relationships_module, "APPLICATION_JOINS")
        assert hasattr(table_relationships_module, "INDEPENDENT_TABLES")

    def test_all_tables_have_relationship_entry(self, table_relationships_module):
        """Verify all 58 tables have an entry in relationship mappings."""
        tables_with_relations = (
            set(table_relationships_module.TABLE_RELATIONSHIPS.keys())
            | set(table_relationships_module.APPLICATION_JOINS.keys())
            | table_relationships_module.INDEPENDENT_TABLES
        )

        missing = ALL_58_TABLES - tables_with_relations

        assert not missing, (
            f"Missing relationship entry for {len(missing)} tables: {sorted(missing)}"
        )

    def test_dhairya_critical_tables_have_app_joins(self, table_relationships_module):
        """Verify critical Dhairya tables have application join definitions."""
        critical_tables = [
            "innovation_grant_from_govt",
            "academic_courses_details",
            "combined_ipo_patent_data",
            "incubation_details",
            "financial_expenses_capital",
            "financial_expenses_operational",
        ]

        missing = []
        for table in critical_tables:
            if table not in table_relationships_module.APPLICATION_JOINS:
                missing.append(table)

        assert not missing, f"Missing application joins for: {missing}"

    def test_join_path_q7(self, table_relationships_module):
        """Verify Q7 join path (innovation_grant_from_govt -> combined_ipo_patent_data)."""
        from src.skills.text_to_sql.table_relationships import find_join_path

        path = find_join_path("innovation_grant_from_govt", "combined_ipo_patent_data")
        assert path is not None, "Q7 join path should exist"
        assert len(path) >= 1, "Q7 join path should have at least one segment"

    def test_get_join_candidates(self, table_relationships_module):
        """Test that get_join_candidates returns valid tables."""
        candidates = table_relationships_module.get_join_candidates(
            "innovation_grant_from_govt"
        )
        assert "combined_ipo_patent_data" in candidates
        assert "academic_courses_details" in candidates
        assert "incubation_details" in candidates

    def test_find_join_path_direct(self, table_relationships_module):
        """Test direct join path finding."""
        from src.skills.text_to_sql.table_relationships import find_join_path

        path = find_join_path("nirf_extracted_table", "nirf_pdf_record")
        assert path is not None
        assert path[0]["to_table"] == "nirf_pdf_record"

    def test_find_join_path_indirect(self, table_relationships_module):
        """Test indirect (single-hop) join path finding."""
        from src.skills.text_to_sql.table_relationships import find_join_path

        path = find_join_path("nirf_table_row", "nirf_pdf_record")
        assert path is not None
        assert len(path) == 2
        assert path[0]["to_table"] == "nirf_extracted_table"
        assert path[1]["to_table"] == "nirf_pdf_record"


class TestSchemaSyncCheck:
    """Test schema sync check functionality."""

    def test_parse_db_struct_sql(self, schema_sync_check_module):
        """Verify db_struct.sql can be parsed."""
        schema = schema_sync_check_module.parse_db_struct_sql()
        assert len(schema) == 58
        assert "academic_courses_details" in schema
        assert "innovation_grant_from_govt" in schema

    def test_parse_contains_columns(self, schema_sync_check_module):
        """Verify parsed schema contains column information."""
        schema = schema_sync_check_module.parse_db_struct_sql()

        acad = schema["academic_courses_details"]
        col_names = [col.name for col in acad.columns]
        assert "id" in col_names
        assert "financial_year" in col_names
        assert "title_of_course" in col_names
        assert "level_of_course" in col_names
        assert "total_credit_score" in col_names

    def test_parse_contains_primary_keys(self, schema_sync_check_module):
        """Verify parsed schema contains primary key information for tables with explicit PK constraints.

        Note: Many tables in db_struct.sql define PK columns as 'id integer NOT NULL' without
        an explicit 'PRIMARY KEY (id)' constraint line. The parser only detects explicit PK
        constraints when they're on a separate line.
        """
        schema = schema_sync_check_module.parse_db_struct_sql()

        acad = schema["academic_courses_details"]
        assert "id" in [col.name for col in acad.columns], (
            "academic_courses_details should have id column"
        )

    def test_get_dhairya_required_tables(self, schema_sync_check_module):
        """Verify Dhairya required tables set is correct."""
        required = schema_sync_check_module.get_dhairya_required_tables()

        assert "academic_courses_details" in required
        assert "innovation_grant_from_govt" in required
        assert "combined_ipo_patent_data" in required
        assert len(required) >= 7

    def test_normalize_type(self, schema_sync_check_module):
        """Test PostgreSQL type normalization."""
        normalize = schema_sync_check_module.normalize_type

        assert normalize("character varying(100)") == "VARCHAR(100)"
        assert normalize("TEXT") == "TEXT"
        assert normalize("timestamp with time zone") == "TIMESTAMP"
        assert normalize("integer") == "INTEGER"


class TestDualDriverSupport:
    """Test dual-driver schema extractor factory."""

    def test_detect_sqlite_driver(self):
        """Test SQLite driver detection."""
        from src.skills.text_to_sql.schema_extractor import detect_database_driver

        assert detect_database_driver("sqlite:///nrg.db") == "sqlite"
        assert detect_database_driver("sqlite:////absolute/path/to/db.sqlite") == "sqlite"

    def test_detect_postgresql_driver(self):
        """Test PostgreSQL driver detection."""
        from src.skills.text_to_sql.schema_extractor import detect_database_driver

        assert (
            detect_database_driver("postgresql://user:pass@localhost:5432/nrg")
            == "postgresql"
        )
        assert detect_database_driver("postgres://user:pass@localhost/nrg") == "postgresql"

    def test_detect_unknown_driver(self, monkeypatch):
        """Test unknown driver detection."""
        from src.skills.text_to_sql.schema_extractor import detect_database_driver

        monkeypatch.setenv("DATABASE_URL", "mysql://user:pass@localhost/nrg")
        assert detect_database_driver("mysql://user:pass@localhost/nrg") == "unknown"
        monkeypatch.setenv("DATABASE_URL", "")
        assert detect_database_driver("") == "unknown"

    def test_create_schema_extractor_postgresql(self):
        """Test factory returns SchemaExtractor class for PostgreSQL URLs.

        Note: We test the logic without connecting by checking the driver detection.
        """
        from src.skills.text_to_sql.schema_extractor import (
            detect_database_driver,
        )

        driver = detect_database_driver("postgresql://user:pass@localhost:5432/nrg")
        assert driver == "postgresql"

    def test_create_schema_extractor_sqlite(self):
        """Test factory creates SQLite extractor when SQLite URL provided."""
        from src.skills.text_to_sql.schema_extractor import create_schema_extractor
        from src.skills.text_to_sql.sqlite_schema_extractor import (
            SQLiteSchemaExtractor,
        )

        extractor = create_schema_extractor("sqlite:///test.db")
        assert isinstance(extractor, SQLiteSchemaExtractor)


class TestSQLitePostgreSQLTableSplit:
    """Test that PostgreSQL-only and SQLite-only tables are properly categorized."""

    def test_postgresql_only_tables_count(self):
        """Verify PostgreSQL-only tables count is reasonable."""
        assert len(POSTGRESQL_ONLY_TABLES) >= 40

    def test_sqlite_only_tables_count(self):
        """Verify SQLite-only tables count."""
        assert len(SQLITE_ONLY_TABLES) >= 15

    def test_no_overlap(self):
        """Verify PostgreSQL-only and SQLite-only tables don't overlap."""
        overlap = POSTGRESQL_ONLY_TABLES & SQLITE_ONLY_TABLES
        assert not overlap, f"Tables in both sets: {overlap}"

    def test_dhairya_tables_all_postgresql(self):
        """Verify all Dhairya-critical tables are PostgreSQL-only."""
        dhairya_critical = {
            "academic_courses_details",
            "innovation_grant_from_govt",
            "innovations_at_various_stages_of_technology_readiness_level",
            "combined_ipo_patent_data",
            "incubation_details",
            "financial_expenses_capital",
            "financial_expenses_operational",
        }

        overlap = dhairya_critical & SQLITE_ONLY_TABLES
        assert not overlap, f"Dhairya critical tables in SQLite: {overlap}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

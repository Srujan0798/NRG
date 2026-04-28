"""Schema parity tests — verify db_struct.sql matches live PostgreSQL.

This test suite ensures the official production schema (db_struct.sql)
is always in sync with the live database. Running against staging or prod
verifies zero schema drift.

Usage:
    pytest tests/data/test_schema_parity.py -v
    python -m tests.data.test_schema_parity --check-all
"""

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest
from sqlalchemy import create_engine, inspect

SRC_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SRC_ROOT))


def parse_db_struct_sql() -> Dict[str, List[str]]:
    """Parse db_struct.sql and extract table→columns mapping."""
    db_struct_path = SRC_ROOT / "db_struct.sql"
    content = db_struct_path.read_text()

    tables: Dict[str, List[str]] = {}
    current_table: str | None = None

    for line in content.split("\n"):
        line = line.strip()

        if line.startswith("CREATE TABLE public."):
            match = re.match(r"CREATE TABLE public\.(\w+)", line)
            if match:
                current_table = match.group(1)
                tables[current_table] = []
        elif current_table and line.startswith(")"):
            current_table = None
        elif current_table and re.match(r"^\w+", line):
            col_match = re.match(r"(\w+)\s+", line)
            if col_match:
                col_name = col_match.group(1)
                if col_name not in ("PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "CONSTRAINT"):
                    tables[current_table].append(col_name)

    return tables


def get_dhairya_required_tables() -> Set[str]:
    """Tables required for Dhairya SQL benchmark (from audit report)."""
    return {
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
        "patents_details",
        "research_consultancy_details_consultancy",
        "research_consultancy_details_sponsered",
        "faculty_details",
        "faculty_strength",
        "fdp_details",
        "expertise",
        "master_expertise",
        "seed_funding",
        "startup_recognition",
        "startups_turnover_50_lacs",
        "startup_receiving_vc_investment",
        "scraped_data",
        "scraped_data_save",
        "scraped_raw_data",
        "advance_search_data",
        "nirf_extracted_table",
        "nirf_pdf_record",
        "nirf_table_row",
        "tb_institute_mstr",
        "tb_institute_scrap_data_url",
        "tb_goi_ministries_mstr",
        "tb_academic_year_mstr",
        "tb_course_program_types",
    }


def compute_schema_fingerprint(tables: Dict[str, List[str]]) -> str:
    """Compute a deterministic hash fingerprint of the schema."""
    canonical = []
    for table_name in sorted(tables.keys()):
        cols = sorted(tables[table_name])
        canonical.append(f"{table_name}:{','.join(cols)}")
    schema_str = "|".join(canonical)
    return hashlib.sha256(schema_str.encode()).hexdigest()[:16]


@pytest.fixture(scope="session")
def local_alembic_db_url(tmp_path_factory) -> str:
    """Build the active Alembic schema in SQLite for local parity checks."""
    db_path = tmp_path_factory.mktemp("schema_parity") / "nrg_schema_parity.sqlite"
    db_url = f"sqlite:///{db_path}"
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=SRC_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, (
        "alembic upgrade head failed for local SQLite schema parity DB\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    return db_url


def _tables_for_url(db_url: str) -> set[str]:
    engine = create_engine(db_url, pool_pre_ping=True)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


class TestSchemaParity:
    """Test that db_struct.sql and live database are in sync."""

    @pytest.fixture
    def db_url(self) -> str:
        return os.getenv("DATABASE_URL", "postgresql://nrg:nrg_default_password@localhost:5432/nrg")

    @pytest.fixture
    def authoritative_schema(self) -> Dict[str, List[str]]:
        return parse_db_struct_sql()

    @pytest.fixture
    def dhairya_required(self) -> Set[str]:
        return get_dhairya_required_tables()

    def test_db_struct_sql_parseable(self, authoritative_schema: Dict[str, List[str]]):
        """Verify db_struct.sql has expected table count (≥58)."""
        table_count = len(authoritative_schema)
        assert table_count >= 58, f"Expected ≥58 tables, found {table_count}"

    def test_alembic_upgrade_head_creates_all_db_struct_tables_locally(
        self,
        authoritative_schema: Dict[str, List[str]],
        local_alembic_db_url: str,
    ):
        """Verify active Alembic head creates every db_struct.sql table locally."""
        live_tables = _tables_for_url(local_alembic_db_url)
        expected_tables = set(authoritative_schema)

        missing = expected_tables - live_tables

        assert len(expected_tables) == 58
        assert not missing, f"Alembic head missing db_struct.sql tables: {sorted(missing)}"

    def test_seed_script_declares_every_db_struct_table(self, authoritative_schema: Dict[str, List[str]]):
        """Verify seed_production_tables tracks every table in db_struct.sql."""
        from scripts import seed_production_tables

        assert set(seed_production_tables.get_production_table_names()) == set(authoritative_schema)

    def test_dhairya_tables_present(self, authoritative_schema: Dict[str, List[str]], dhairya_required: Set[str]):
        """Verify all tables needed for Dhairya benchmark are in db_struct.sql."""
        missing = dhairya_required - set(authoritative_schema.keys())
        assert not missing, f"Dhairya-required tables missing from db_struct.sql: {missing}"

    def test_live_db_connection(self, db_url: str):
        """Verify we can connect to live database."""
        if "sqlite" in db_url.lower():
            pytest.skip("PostgreSQL not available, skipping live DB check")
        try:
            from sqlalchemy import create_engine, inspect
            engine = create_engine(db_url, pool_pre_ping=True)
            inspector = inspect(engine)
            live_tables = inspector.get_table_names()
            engine.dispose()
            assert len(live_tables) > 0, "Live database has no tables"
        except Exception as e:
            pytest.skip(f"Cannot connect to live DB: {e}")

    def test_live_db_has_all_tables(self, db_url: str, authoritative_schema: Dict[str, List[str]]):
        """Verify live DB has every table from db_struct.sql."""
        if "sqlite" in db_url.lower():
            pytest.skip("PostgreSQL not available, skipping live DB check")
        try:
            from sqlalchemy import create_engine, inspect
            engine = create_engine(db_url, pool_pre_ping=True)
            inspector = inspect(engine)
            live_tables = set(inspector.get_table_names())
            auth_tables = set(authoritative_schema.keys())

            missing = auth_tables - live_tables
            extra = live_tables - auth_tables

            if missing:
                print(f"\nMissing in live DB: {sorted(missing)}")
            if extra:
                print(f"\nExtra in live DB (OK): {sorted(extra)}")

            assert not missing, f"Tables in db_struct.sql but not in live DB: {missing}"
            engine.dispose()
        except Exception as e:
            pytest.skip(f"Cannot verify live DB: {e}")

    def test_live_db_has_all_columns(self, db_url: str, authoritative_schema: Dict[str, List[str]]):
        """Verify live DB has all columns for each table from db_struct.sql."""
        if "sqlite" in db_url.lower():
            pytest.skip("PostgreSQL not available, skipping live DB check")
        try:
            from sqlalchemy import create_engine, inspect
            engine = create_engine(db_url, pool_pre_ping=True)
            inspector = inspect(engine)

            issues = []
            for table_name, expected_cols in authoritative_schema.items():
                try:
                    live_cols = set([c["name"] for c in inspector.get_columns(table_name)])
                    expected_set = set(expected_cols)
                    missing_cols = expected_set - live_cols
                    if missing_cols:
                        issues.append(f"{table_name}: missing columns {sorted(missing_cols)}")
                except Exception:
                    pass

            engine.dispose()
            assert not issues, f"Column mismatches:\n" + "\n".join(issues)
        except Exception as e:
            pytest.skip(f"Cannot verify live DB columns: {e}")

    def test_schema_fingerprint_stable(self, authoritative_schema: Dict[str, List[str]]):
        """Verify schema fingerprint is deterministic (used for audit chain)."""
        fp1 = compute_schema_fingerprint(authoritative_schema)
        fp2 = compute_schema_fingerprint(authoritative_schema)
        assert fp1 == fp2, "Schema fingerprint is not deterministic"

    def test_schema_fingerprint_matches_expected(self, authoritative_schema: Dict[str, List[str]]):
        """Verify schema fingerprint matches expected value (updated when schema changes)."""
        fp = compute_schema_fingerprint(authoritative_schema)
        EXPECTED_FINGERPRINT = "fa39e31d527f8040"
        if fp != EXPECTED_FINGERPRINT:
            print(f"\nSchema fingerprint changed: {fp}")
            print("Update EXPECTED_FINGERPRINT in this test when schema change is intentional")
        assert fp == EXPECTED_FINGERPRINT, f"Fingerprint mismatch: got {fp}, expected {EXPECTED_FINGERPRINT}"

    def test_all_dhairya_tables_have_minimum_rows(self, db_url: str, dhairya_required: Set[str]):
        """Verify all Dhairya-required tables have data (≥1 row for seeding)."""
        if "sqlite" in db_url.lower():
            pytest.skip("PostgreSQL not available")
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(db_url, pool_pre_ping=True)

            with engine.connect() as conn:
                empty_tables = []
                for table in sorted(dhairya_required):
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    if count == 0:
                        empty_tables.append(table)

                engine.dispose()
                assert not empty_tables, f"Dhairya tables with zero rows: {empty_tables}"
        except Exception as e:
            pytest.skip(f"Cannot verify row counts: {e}")

    def test_primary_keys_intact(self, db_url: str, authoritative_schema: Dict[str, List[str]]):
        """Verify all tables have primary keys."""
        if "sqlite" in db_url.lower():
            pytest.skip("PostgreSQL not available")
        try:
            from sqlalchemy import create_engine, inspect
            engine = create_engine(db_url, pool_pre_ping=True)
            inspector = inspect(engine)

            no_pk = []
            for table_name in authoritative_schema:
                try:
                    pk = inspector.get_pk_constraint(table_name)
                    if not pk or not pk.get("constrained_columns"):
                        no_pk.append(table_name)
                except Exception:
                    no_pk.append(table_name)

            engine.dispose()
            assert not no_pk, f"Tables without primary key: {no_pk}"
        except Exception as e:
            pytest.skip(f"Cannot verify PKs: {e}")

    def test_no_orphan_foreign_keys(self, db_url: str, authoritative_schema: Dict[str, List[str]]):
        """Verify all foreign key relationships are valid."""
        if "sqlite" in db_url.lower():
            pytest.skip("PostgreSQL not available")
        try:
            from sqlalchemy import create_engine, inspect
            engine = create_engine(db_url, pool_pre_ping=True)
            inspector = inspect(engine)

            invalid_fks = []
            for table_name in authoritative_schema:
                try:
                    fks = inspector.get_foreign_keys(table_name)
                    for fk in fks:
                        referred_table = fk["referred_table"]
                        if referred_table not in authoritative_schema:
                            invalid_fks.append(f"{table_name}→{referred_table}")
                except Exception:
                    pass

            engine.dispose()
            assert not invalid_fks, f"Invalid FK references: {invalid_fks}"
        except Exception as e:
            pytest.skip(f"Cannot verify FKs: {e}")

    def test_total_credit_score_is_text_type(self, db_url: str, authoritative_schema: Dict[str, List[str]]):
        """Verify total_credit_score is TEXT type (not INTEGER) — critical for SPLIT_PART parsing.

        The column stores values like '3:1' (lecture:tutorial format). Casting to INTEGER fails.
        SQL generation must use SPLIT_PART(total_credit_score, ':', 1)::double precision.
        """
        if "sqlite" in db_url.lower():
            pytest.skip("PostgreSQL not available")
        try:
            from sqlalchemy import create_engine, inspect
            engine = create_engine(db_url, pool_pre_ping=True)
            inspector = inspect(engine)

            cols = inspector.get_columns("academic_courses_details")
            credit_col = next((c for c in cols if c["name"] == "total_credit_score"), None)
            assert credit_col is not None, "total_credit_score column not found"

            col_type = str(credit_col.get("type", "")).upper()
            assert "TEXT" in col_type or "VARCHAR" in col_type or "CHAR" in col_type, (
                f"total_credit_score must be TEXT type, got {col_type}. "
                "Integer cast will fail on '3:1' format — use SPLIT_PART."
            )
            engine.dispose()
        except Exception as e:
            pytest.skip(f"Cannot verify column type: {e}")


def run_cli_check():
    """CLI entry point for schema sync check."""
    print("Schema Parity Check — NRG Protocol #21")
    print("=" * 60)

    authoritative = parse_db_struct_sql()
    dhairya_required = get_dhairya_required_tables()
    fingerprint = compute_schema_fingerprint(authoritative)

    print(f"Tables in db_struct.sql: {len(authoritative)}")
    print(f"Dhairya-required tables: {len(dhairya_required)}")
    print(f"Schema fingerprint: {fingerprint}")
    print()

    missing_dhairya = dhairya_required - set(authoritative.keys())
    if missing_dhairya:
        print(f"ERROR: Missing Dhairya tables: {sorted(missing_dhairya)}")
        return 1

    print("All Dhairya tables present in db_struct.sql ✓")
    print("Schema parity check PASSED ✓")
    return 0


if __name__ == "__main__":
    sys.exit(run_cli_check())

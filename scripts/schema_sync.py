#!/usr/bin/env python3
"""Schema Sync CLI — synchronize db_struct.sql to live PostgreSQL.

This tool verifies the official production schema (db_struct.sql) matches
the live database and can apply migrations if needed.

Usage:
    # Check schema parity (read-only)
    python scripts/schema_sync.py check

    # Apply missing tables from db_struct.sql
    python scripts/schema_sync.py sync --url postgresql://...

    # Show detailed diff
    python scripts/schema_sync.py diff --verbose

    # Verify Dhairya tables are present
    python scripts/schema_sync.py dhairya-check

Exit codes:
    0 = schema in sync
    1 = schema drift detected
    2 = error (can't connect, etc.)
"""

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

SRC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_ROOT))


def parse_db_struct_sql() -> Dict[str, List[str]]:
    """Parse db_struct.sql and extract table→columns mapping."""
    db_struct_path = SRC_ROOT / "db_struct.sql"
    content = db_struct_path.read_text()

    tables: Dict[str, List[str]] = {}
    current_table: str | None = None
    in_columns = False

    for line in content.split("\n"):
        line_stripped = line.strip()

        if line_stripped.startswith("CREATE TABLE public."):
            match = re.match(r"CREATE TABLE public\.(\w+)", line_stripped)
            if match:
                current_table = match.group(1)
                tables[current_table] = []
                in_columns = False

        elif current_table:
            if line_stripped.startswith(")"):
                current_table = None
                in_columns = False
            elif line_stripped.startswith("CREATE INDEX") or line_stripped.startswith("CREATE SEQUENCE") or line_stripped.startswith("ALTER TABLE"):
                continue
            elif line_stripped.startswith("--"):
                continue
            elif "," in line_stripped or re.match(r"^\w+", line_stripped):
                col_match = re.match(r"(\w+)\s+", line_stripped)
                if col_match:
                    col_name = col_match.group(1)
                    skip_words = {"PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "CONSTRAINT", "INDEX", "KEY", "DEFAULT", "GENERATED", "SEQUENCE", "OWNED", "ALTER", "ADD", "REFERENCES", "ON"}
                    if col_name not in skip_words and not line_stripped.startswith("PRIMARY KEY"):
                        if col_name not in tables.get(current_table, []):
                            tables[current_table].append(col_name)

    return tables


def get_dhairya_required_tables() -> Set[str]:
    """Tables required for Dhairya SQL benchmark queries."""
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
    """Compute deterministic hash fingerprint of schema."""
    canonical = []
    for table_name in sorted(tables.keys()):
        cols = sorted(tables[table_name])
        canonical.append(f"{table_name}:{','.join(cols)}")
    schema_str = "|".join(canonical)
    return hashlib.sha256(schema_str.encode()).hexdigest()[:16]


def check_db_connection(db_url: str) -> Tuple[bool, str]:
    """Test database connection."""
    try:
        from sqlalchemy import create_engine, inspect
        engine = create_engine(db_url, pool_pre_ping=True, echo=False)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        engine.dispose()
        return True, f"Connected. {len(tables)} tables found."
    except Exception as e:
        return False, str(e)


def get_live_schema(db_url: str) -> Dict[str, List[str]]:
    """Get live database schema."""
    from sqlalchemy import create_engine, inspect
    engine = create_engine(db_url, pool_pre_ping=True, echo=False)
    inspector = inspect(engine)

    tables: Dict[str, List[str]] = {}
    for table_name in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns(table_name)]
        tables[table_name] = cols

    engine.dispose()
    return tables


def check_parity(db_url: str, authoritative: Dict[str, List[str]], dhairya: Set[str]) -> Tuple[bool, str]:
    """Check schema parity between db_struct.sql and live DB."""
    connected, msg = check_db_connection(db_url)
    if not connected:
        return False, f"Cannot connect to database: {msg}"

    live = get_live_schema(db_url)

    auth_tables = set(authoritative.keys())
    live_tables = set(live.keys())

    missing_in_live = auth_tables - live_tables
    extra_in_live = live_tables - auth_tables
    dhairya_missing = dhairya - live_tables

    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"SCHEMA PARITY CHECK")
    lines.append(f"{'='*60}")

    lines.append(f"\nAuthoritative schema (db_struct.sql): {len(auth_tables)} tables")
    lines.append(f"Live database:                       {len(live_tables)} tables")

    if missing_in_live:
        lines.append(f"\nMISSING in live DB: {len(missing_in_live)} tables")
        for t in sorted(missing_in_live):
            marker = " [DHAIRYA]" if t in dhairya else ""
            lines.append(f"  - {t}{marker}")

    if extra_in_live:
        lines.append(f"\nEXTRA in live DB (OK): {len(extra_in_live)} tables")
        for t in sorted(extra_in_live):
            lines.append(f"  + {t}")

    if dhairya_missing:
        lines.append(f"\nDHAIRYA TABLES MISSING: {len(dhairya_missing)}")
        for t in sorted(dhairya_missing):
            lines.append(f"  ! {t}")

    if missing_in_live or dhairya_missing:
        return False, "\n".join(lines)

    lines.append(f"\n{'='*60}")
    lines.append(f"SCHEMA IN SYNC ✓")
    lines.append(f"{'='*60}")
    return True, "\n".join(lines)


def apply_sync(db_url: str, authoritative: Dict[str, List[str]]) -> Tuple[bool, str]:
    """Apply missing tables from db_struct.sql to live DB."""
    connected, msg = check_db_connection(db_url)
    if not connected:
        return False, f"Cannot connect: {msg}"

    live = get_live_schema(db_url)
    auth_tables = set(authoritative.keys())
    live_tables = set(live.keys())
    missing = auth_tables - live_tables

    if not missing:
        return True, "All tables already present. Nothing to sync."

    lines = [f"\nApplying {len(missing)} missing tables..."]

    from sqlalchemy import create_engine, text
    engine = create_engine(db_url, pool_pre_ping=True, echo=False)

    try:
        with engine.connect() as conn:
            trans = conn.begin()
            for table_name in sorted(missing):
                cols = authoritative[table_name]
                col_defs = ", ".join([f"{col} TEXT" for col in cols])
                create_sql = f"CREATE TABLE {table_name} ({col_defs})"
                try:
                    conn.execute(text(create_sql))
                    lines.append(f"  + Created {table_name}")
                except Exception as e:
                    lines.append(f"  ! Failed {table_name}: {e}")
                    trans.rollback()
                    engine.dispose()
                    return False, "\n".join(lines)

            trans.commit()
            lines.append("\nSync complete!")
            engine.dispose()
            return True, "\n".join(lines)

    except Exception as e:
        return False, f"Sync failed: {e}"
    finally:
        engine.dispose()


def show_diff(db_url: str, authoritative: Dict[str, List[str]], dhairya: Set[str], verbose: bool = False) -> str:
    """Show detailed schema diff."""
    connected, msg = check_db_connection(db_url)
    if not connected:
        return f"Cannot connect: {msg}"

    live = get_live_schema(db_url)
    auth_tables = set(authoritative.keys())
    live_tables = set(live.keys())

    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"SCHEMA DIFF")
    lines.append(f"{'='*60}")
    lines.append(f"\ndb_struct.sql: {len(auth_tables)} tables")
    lines.append(f"Live DB:       {len(live_tables)} tables")

    missing = auth_tables - live_tables
    extra = live_tables - auth_tables

    if missing:
        lines.append(f"\nMISSING in live (must sync): {len(missing)}")
        for t in sorted(missing):
            cols = authoritative.get(t, [])
            marker = " [DHAIRYA]" if t in dhairya else ""
            lines.append(f"  - {t}{marker} ({len(cols)} cols)")

    if extra:
        lines.append(f"\nEXTRA in live (not in db_struct.sql): {len(extra)}")
        for t in sorted(extra):
            lines.append(f"  + {t}")

    if verbose:
        common = auth_tables & live_tables
        lines.append(f"\nPRESENT in both: {len(common)}")
        for t in sorted(common):
            auth_cols = set(authoritative.get(t, []))
            live_cols = set(live.get(t, []))
            missing_cols = auth_cols - live_cols
            extra_cols = live_cols - auth_cols
            if missing_cols:
                lines.append(f"  ~ {t}: missing cols {sorted(missing_cols)}")
            if extra_cols:
                lines.append(f"  ~ {t}: extra cols {sorted(extra_cols)}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="NRG Schema Sync CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    check_parser = subparsers.add_parser("check", help="Check schema parity (read-only)")
    check_parser.add_argument("--db", dest="db_url", help="Database URL",
                              default=os.getenv("DATABASE_URL", "postgresql://nrg:nrg_default_password@localhost:5432/nrg"))

    sync_parser = subparsers.add_parser("sync", help="Apply missing tables to live DB")
    sync_parser.add_argument("--db", dest="db_url", help="Database URL",
                            default=os.getenv("DATABASE_URL", "postgresql://nrg:nrg_default_password@localhost:5432/nrg"))

    diff_parser = subparsers.add_parser("diff", help="Show detailed diff")
    diff_parser.add_argument("--db", dest="db_url", help="Database URL",
                            default=os.getenv("DATABASE_URL", "postgresql://nrg:nrg_default_password@localhost:5432/nrg"))
    diff_parser.add_argument("--verbose", "-v", action="store_true", help="Show column-level diff")

    dhairya_parser = subparsers.add_parser("dhairya-check", help="Verify Dhairya-required tables")
    dhairya_parser.add_argument("--db", dest="db_url", help="Database URL",
                               default=os.getenv("DATABASE_URL", "postgresql://nrg:nrg_default_password@localhost:5432/nrg"))

    parser.add_argument("--url", dest="db_url", help="Database URL (override)")

    args = parser.parse_args()

    if args.db_url and not hasattr(args, 'db_url'):
        args.db_url = args.db_url
    elif not hasattr(args, 'db_url'):
        args.db_url = os.getenv("DATABASE_URL", "postgresql://nrg:nrg_default_password@localhost:5432/nrg")

    if not args.command:
        parser.print_help()
        return 0

    print(f"NRG Schema Sync CLI — Protocol #21")
    print(f"Database: {args.db_url}")
    print()

    authoritative = parse_db_struct_sql()
    dhairya = get_dhairya_required_tables()
    fingerprint = compute_schema_fingerprint(authoritative)

    print(f"Tables in db_struct.sql: {len(authoritative)}")
    print(f"Dhairya-required tables: {len(dhairya)}")
    print(f"Schema fingerprint: {fingerprint}")
    print()

    if args.command == "check":
        ok, msg = check_parity(args.db_url, authoritative, dhairya)
        print(msg)
        return 0 if ok else 1

    elif args.command == "sync":
        ok, msg = apply_sync(args.db_url, authoritative)
        print(msg)
        return 0 if ok else 1

    elif args.command == "diff":
        result = show_diff(args.db_url, authoritative, dhairya, args.verbose if hasattr(args, 'verbose') else False)
        print(result)
        return 0

    elif args.command == "dhairya-check":
        connected, conn_msg = check_db_connection(args.db_url)
        if not connected:
            print(f"Cannot connect to DB: {conn_msg}")
            return 2

        live = get_live_schema(args.db_url)
        live_tables = set(live.keys())
        missing = dhairya - live_tables

        print(f"Dhairya required tables: {len(dhairya)}")
        print(f"Present in live DB: {len(dhairya - missing)}")
        print(f"Missing: {len(missing)}")

        if missing:
            print(f"\nMISSING DHAIRYA TABLES:")
            for t in sorted(missing):
                print(f"  ! {t}")
            return 1
        else:
            print("\nAll Dhairya tables present ✓")
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
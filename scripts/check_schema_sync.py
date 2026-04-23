#!/usr/bin/env python3
"""CLI to check schema alignment between db_struct.sql and live database.

Usage:
    python scripts/check_schema_sync.py                    # Check against DATABASE_URL
    python scripts/check_schema_sync.py --db postgresql://...

Options:
    --db DATABASE_URL     Override DATABASE_URL
    --verbose, -v         Show detailed output
    --summary, -s         Show summary only
    --help, -h            Show this help message
"""

import argparse
import os
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_ROOT))

from src.skills.text_to_sql.schema_sync_check import (
    check_schema_sync,
    format_diff_report,
    parse_db_struct_sql,
    get_dhairya_required_tables,
)


def main():
    parser = argparse.ArgumentParser(
        description="Check schema alignment between db_struct.sql and live database."
    )
    parser.add_argument(
        "--db",
        dest="database_url",
        help="Database URL (overrides DATABASE_URL env var)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output including all table stats",
    )
    parser.add_argument(
        "--summary",
        "-s",
        action="store_true",
        help="Show summary only (implies --verbose but condensed)",
    )

    args = parser.parse_args()

    database_url = args.database_url or os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: No database URL provided.")
        print("Set DATABASE_URL environment variable or use --db option.")
        print()
        print("Example:")
        print("  export DATABASE_URL=postgresql://user:pass@localhost:5432/nrg")
        print("  python scripts/check_schema_sync.py")
        print()
        print("  python scripts/check_schema_sync.py --db sqlite:///nrg_research.db")
        sys.exit(1)

    print(f"Database URL: {database_url}")
    print()

    from sqlalchemy import create_engine

    try:
        engine = create_engine(database_url, echo=False)
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        sys.exit(1)

    print("Parsing authoritative schema from db_struct.sql...")
    authoritative = parse_db_struct_sql()
    table_count = len(authoritative)
    print(f"  Found {table_count} tables in db_struct.sql")

    dhairya_required = get_dhairya_required_tables()
    print(f"  {len(dhairya_required)} tables required for Dhairya benchmark")

    print()
    print("Checking live database schema...")
    diff = check_schema_sync(engine, authoritative)

    report = format_diff_report(diff)
    print(report)

    if args.verbose or args.summary:
        print()
        print("=" * 60)
        print("DETAILED TABLE STATUS")
        print("=" * 60)

        from sqlalchemy import inspect

        inspector = inspect(engine)
        live_tables = inspector.get_table_names()
        live_set = set(live_tables)
        auth_set = set(authoritative.keys())

        print(f"\nLive database: {len(live_tables)} tables")
        print(f"Authoritative (db_struct.sql): {len(auth_set)} tables")

        missing = auth_set - live_set
        extra = live_set - auth_set
        present = auth_set & live_set

        print(f"\nTables present in both: {len(present)}")
        print(f"Tables missing from live DB: {len(missing)}")
        print(f"Extra tables in live DB: {len(extra)}")

        if missing and not args.summary:
            print("\nMISSING TABLES (in db_struct.sql but not in live DB):")
            for table in sorted(missing):
                dhairya_marker = " [DHAIRYA]" if table in dhairya_required else ""
                print(f"  - {table}{dhairya_marker}")

        if extra and not args.summary:
            print("\nEXTRA TABLES (in live DB but not in db_struct.sql):")
            for table in sorted(extra):
                print(f"  - {table}")

    engine.dispose()

    has_issues = (
        diff.missing_tables
        or diff.extra_tables
        or diff.missing_columns
        or diff.extra_columns
        or diff.type_mismatches
    )

    if has_issues:
        print()
        print("=" * 60)
        print("SCHEMA DRIFT DETECTED")
        print("=" * 60)
        sys.exit(1)
    else:
        print()
        print("=" * 60)
        print("SCHEMA IN SYNC")
        print("=" * 60)
        sys.exit(0)


if __name__ == "__main__":
    main()

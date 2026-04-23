#!/usr/bin/env python3
"""
PostgreSQL Data Migration Script — Task #23 Phase 3

Migrates data from production PostgreSQL → development SQLite for local testing,
OR from SQLite → PostgreSQL for production deployment.

Usage:
    # Export from prod PostgreSQL to SQL dump
    python scripts/migrate_data_to_postgresql.py --mode export --pg-url postgresql://user:pass@host:5432/nrg

    # Import SQL dump into local SQLite dev DB
    python scripts/migrate_data_to_postgresql.py --mode import --input ./migration_dump.sql

    # Push SQLite data to PostgreSQL prod (one-time migration)
    python scripts/migrate_data_to_postgresql.py --mode sync --sqlite-db ./nrg_research.db --pg-url postgresql://...

    # Verify schema parity between SQLite and PostgreSQL
    python scripts/migrate_data_to_postgresql.py --mode verify --sqlite-db ./nrg_research.db --pg-url postgresql://...

Environment:
    DATABASE_URL          — defaults to sqlite:///nrg_research.db
    POSTGRESQL_URL        — override for PostgreSQL connection
    MIGRATION_BATCH_SIZE  — rows per batch commit (default: 5000)
    SKIP_TABLES           — comma-separated tables to skip
    ONLY_TABLES           — comma-separated tables to include (overrides SKIP)
"""

from __future__ import annotations

import argparse
import os
import sys
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

BATCH_SIZE = int(os.getenv("MIGRATION_BATCH_SIZE", "5000"))
SKIP_TABLES = set(os.getenv("SKIP_TABLES", "alembic_version,schema_migrations").split(","))
ONLY_TABLES: set[str] | None = (
    set(os.getenv("ONLY_TABLES", "").split(",")) if os.getenv("ONLY_TABLES") else None
)

POSTGRESQL_TYPE_MAP = {
    "INTEGER": "INTEGER",
    "BIGINT": "INTEGER",
    "TEXT": "TEXT",
    "REAL": "REAL",
    "BOOLEAN": "INTEGER",
    "TIMESTAMP": "TEXT",
    "DATE": "TEXT",
    "JSON": "TEXT",
    "BLOB": "BLOB",
}


def get_sqlite_tables(conn) -> list[str]:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [row["name"] for row in cur.fetchall()]


def get_sqlite_columns(conn, table: str) -> list[dict]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return [{"name": row["name"], "type": row["type"], "pk": row["pk"]} for row in cur.fetchall()]


def get_sqlite_row_count(conn, table: str) -> int:
    cur = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}")
    return cur.fetchone()["cnt"]


def iter_sqlite_rows(conn, table: str, batch_size: int = BATCH_SIZE):
    offset = 0
    while True:
        cur = conn.execute(f"SELECT * FROM {table} LIMIT {batch_size} OFFSET {offset}")
        rows = cur.fetchall()
        if not rows:
            break
        for row in rows:
            yield dict(row)
        offset += batch_size


def get_pg_columns(conn, table: str) -> list[dict]:
    cur = conn.execute(
        """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
        """,
        (table,),
    )
    return list(cur.fetchall())


def get_pg_tables(conn) -> list[str]:
    cur = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name"
    )
    return [row["table_name"] for row in cur.fetchall()]


def sqlite_to_pg_type(sqlite_type: str) -> str:
    t = sqlite_type.upper().split("(")[0].strip()
    return POSTGRESQL_TYPE_MAP.get(t, "TEXT")


def convert_row_for_pg(row: dict) -> dict:
    out = {}
    for key, value in row.items():
        if isinstance(value, (int, float, str, type(None))):
            out[key] = value
        elif isinstance(value, bytes):
            out[key] = value.decode("latin-1")
        else:
            out[key] = str(value)
    return out


def verify_schema_parity(sqlite_path: Path, pg_conn, report_path: Path) -> dict:
    import sqlite3

    logger.info("Verifying schema parity between SQLite and PostgreSQL...")
    results = {"matched": [], "missing_in_pg": [], "missing_in_sqlite": [], "column_diffs": []}

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    pg_tables = set(get_pg_tables(pg_conn))
    sqlite_tables = set(get_sqlite_tables(sqlite_conn))

    results["missing_in_pg"] = sorted(sqlite_tables - pg_tables)
    results["missing_in_sqlite"] = sorted(pg_tables - sqlite_tables)

    common = sqlite_tables & pg_tables
    for table in sorted(common):
        sqlite_cols = {c["name"]: c for c in get_sqlite_columns(sqlite_conn, table)}
        pg_cols = {c["column_name"] for c in get_pg_columns(pg_conn, table)}

        sqlite_only = set(sqlite_cols.keys()) - pg_cols
        pg_only = pg_cols - set(sqlite_cols.keys())

        if sqlite_only or pg_only:
            results["column_diffs"].append(
                {
                    "table": table,
                    "sqlite_only": sorted(sqlite_only),
                    "pg_only": sorted(pg_only),
                }
            )
        else:
            results["matched"].append(table)

    sqlite_conn.close()

    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Schema parity report: {report_path}")
    logger.info(f"  Matched: {len(results['matched'])} tables")
    logger.info(f"  Missing in PostgreSQL: {len(results['missing_in_pg'])}")
    logger.info(f"  Missing in SQLite: {len(results['missing_in_sqlite'])}")
    logger.info(f"  Column differences: {len(results['column_diffs'])} tables")

    return results


def export_pg_to_json(pg_conn, output_path: Path, tables: list[str] | None = None) -> dict:
    logger.info(f"Exporting PostgreSQL data to {output_path}...")
    manifest = {"exported_at": datetime.now(timezone.utc).isoformat(), "tables": {}}

    all_tables = get_pg_tables(pg_conn)
    tables_to_export = tables or all_tables

    for table in tables_to_export:
        if table in SKIP_TABLES or (ONLY_TABLES and table not in ONLY_TABLES):
            continue

        logger.info(f"  Exporting table: {table}")
        try:
            cur = pg_conn.cursor()
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]

            table_data = []
            for row in rows:
                table_data.append(dict(zip(columns, row)))

            manifest["tables"][table] = {
                "row_count": len(table_data),
                "columns": columns,
            }

            with open(output_path.parent / f"{table}.json", "w") as f:
                json.dump(table_data, f, default=str)

        except Exception as e:
            logger.warning(f"  Failed to export {table}: {e}")
            manifest["tables"][table] = {"error": str(e)}

    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Export complete. Manifest: {output_path}")
    return manifest


def import_json_to_sqlite(json_dir: Path, sqlite_path: Path) -> dict:
    import sqlite3

    logger.info(f"Importing JSON data into SQLite: {sqlite_path}")
    results = {"imported": [], "failed": []}

    manifest_path = json_dir / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
    else:
        manifest = {"tables": {name.stem: {} for name in json_dir.glob("*.json")}}

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    for table_file in sorted(json_dir.glob("*.json")):
        table_name = table_file.stem
        if table_name == "manifest":
            continue

        if table_name in SKIP_TABLES or (ONLY_TABLES and table_name not in ONLY_TABLES):
            logger.info(f"  Skipping: {table_name}")
            continue

        try:
            with open(table_file) as f:
                rows = json.load(f)

            if not rows:
                logger.info(f"  Empty table: {table_name}")
                continue

            columns = list(rows[0].keys())
            placeholders = ", ".join(["?"] * len(columns))
            insert_sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

            for i, row in enumerate(rows):
                values = [row.get(col) for col in columns]
                sqlite_conn.execute(insert_sql, values)

                if (i + 1) % BATCH_SIZE == 0:
                    sqlite_conn.commit()

            sqlite_conn.commit()
            results["imported"].append({"table": table_name, "rows": len(rows)})
            logger.info(f"  Imported {len(rows)} rows into {table_name}")

        except Exception as e:
            sqlite_conn.rollback()
            logger.warning(f"  Failed to import {table_name}: {e}")
            results["failed"].append({"table": table_name, "error": str(e)})

    sqlite_conn.close()
    return results


def sync_sqlite_to_pg(sqlite_path: Path, pg_conn) -> dict:
    import sqlite3

    logger.info("Syncing SQLite data to PostgreSQL...")
    results = {"synced": [], "failed": []}

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    tables = get_sqlite_tables(sqlite_conn)

    for table in tables:
        if table in SKIP_TABLES or (ONLY_TABLES and table not in ONLY_TABLES):
            continue

        logger.info(f"  Syncing table: {table}")
        try:
            row_count = get_sqlite_row_count(sqlite_conn, table)
            if row_count == 0:
                logger.info(f"    Empty, skipping")
                continue

            pg_cols = get_pg_columns(pg_conn, table)
            if not pg_cols:
                logger.warning(f"    Table not in PostgreSQL, skipping")
                continue

            pg_col_names = {c["column_name"] for c in pg_cols}
            sqlite_cols = get_sqlite_columns(sqlite_conn, table)
            sqlite_col_names = [c["name"] for c in sqlite_cols]

            common_cols = [c for c in sqlite_col_names if c in pg_col_names]
            if not common_cols:
                logger.warning(f"    No common columns, skipping")
                continue

            pg_cols_lower = {c["column_name"].lower() for c in pg_cols}
            col_defs = []
            for col in sqlite_cols:
                if col["name"].lower() in pg_cols_lower:
                    pg_type = next(
                        c["data_type"].upper()
                        for c in pg_cols
                        if c["column_name"].lower() == col["name"].lower()
                    )
                    col_defs.append(f"{col['name']} {pg_type}")

            if col_defs:
                create_sql = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(col_defs)})"
                try:
                    pg_conn.execute(create_sql)
                    pg_conn.commit()
                except Exception:
                    pass

            placeholders = ", ".join(["%s"] * len(common_cols))
            cols_sql = ", ".join(common_cols)
            insert_sql = f"INSERT INTO {table} ({cols_sql}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

            total_rows = 0
            for batch in iter_sqlite_rows(sqlite_conn, table):
                filtered = {k: v for k, v in convert_row_for_pg(batch).items() if k in common_cols}
                values = [filtered.get(c) for c in common_cols]
                try:
                    pg_conn.execute(insert_sql, values)
                    total_rows += 1
                except Exception as e:
                    logger.debug(f"    Row insert failed: {e}")

            pg_conn.commit()
            results["synced"].append({"table": table, "rows": total_rows})
            logger.info(f"    Synced {total_rows} rows to {table}")

        except Exception as e:
            logger.warning(f"  Failed to sync {table}: {e}")
            results["failed"].append({"table": table, "error": str(e)})

    sqlite_conn.close()
    return results


def run_migration_health_check(pg_conn) -> dict:
    checks = {}

    try:
        cur = pg_conn.cursor()
        cur.execute("SELECT 1")
        checks["connection"] = "ok"
    except Exception as e:
        checks["connection"] = f"failed: {e}"
        return checks

    try:
        cur.execute("SELECT version()")
        checks["postgres_version"] = cur.fetchone()[0]
    except Exception as e:
        checks["postgres_version"] = f"failed: {e}"

    try:
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        checks["table_count"] = cur.fetchone()[0]
    except Exception as e:
        checks["table_count"] = f"failed: {e}"

    return checks


def main():
    parser = argparse.ArgumentParser(description="PostgreSQL ↔ SQLite data migration")
    parser.add_argument("--mode", choices=["export", "import", "sync", "verify"], required=True)
    parser.add_argument("--sqlite-db", type=Path, default=Path("nrg_research.db"))
    parser.add_argument("--pg-url", type=str, help="PostgreSQL connection URL")
    parser.add_argument("--output", type=Path, help="Output path for export")
    parser.add_argument("--input", type=Path, help="Input path for import")
    parser.add_argument("--report", type=Path, default=Path("migration_report.json"))
    parser.add_argument("--verify-only", action="store_true", help="Verify schema parity only")
    args = parser.parse_args()

    pg_url = os.getenv("POSTGRESQL_URL") or args.pg_url
    if not pg_url and args.mode in ("export", "sync", "verify"):
        parser.error("--pg-url or POSTGRESQL_URL required")

    pg_conn = None
    if pg_url:
        try:
            import psycopg2
            pg_conn = psycopg2.connect(pg_url)
            logger.info(f"Connected to PostgreSQL: {pg_url.split('@')[-1]}")
        except ImportError:
            logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            sys.exit(1)

    if args.mode == "verify":
        sqlite_path = args.sqlite_db
        if not sqlite_path.is_absolute():
            sqlite_path = PROJECT_ROOT / sqlite_path
        results = verify_schema_parity(sqlite_path, pg_conn, args.report)
        matched = len(results["matched"])
        total = matched + len(results["missing_in_pg"]) + len(results["column_diffs"])
        logger.info(f"Schema parity: {matched}/{total} tables matched")
        sys.exit(0 if matched == total else 1)

    if args.mode == "export":
        if not args.output:
            args.output = PROJECT_ROOT / f"migration_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        args.output.mkdir(exist_ok=True)
        manifest = export_pg_to_json(pg_conn, args.output / "manifest.json")
        with open(args.report, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Export complete → {args.output}")

    elif args.mode == "import":
        input_dir = args.input or (PROJECT_ROOT / "migration_export")
        if not input_dir.exists():
            logger.error(f"Input directory not found: {input_dir}")
            sys.exit(1)
        sqlite_path = args.sqlite_db
        if not sqlite_path.is_absolute():
            sqlite_path = PROJECT_ROOT / sqlite_path
        results = import_json_to_sqlite(input_dir, sqlite_path)
        with open(args.report, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Import complete → {sqlite_path}")

    elif args.mode == "sync":
        sqlite_path = args.sqlite_db
        if not sqlite_path.is_absolute():
            sqlite_path = PROJECT_ROOT / sqlite_path
        if not sqlite_path.exists():
            logger.error(f"SQLite DB not found: {sqlite_path}")
            sys.exit(1)
        results = sync_sqlite_to_pg(sqlite_path, pg_conn)
        with open(args.report, "w") as f:
            json.dump(results, f, indent=2)
        synced = len(results.get("synced", []))
        logger.info(f"Sync complete: {synced} tables synced")

    if pg_conn:
        pg_conn.close()


if __name__ == "__main__":
    main()
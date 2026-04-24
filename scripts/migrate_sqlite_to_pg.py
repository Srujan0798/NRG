#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script — Task #23 Phase 3
------------------------------------------------------------
Migrates the NRG application schema and data from SQLite to PostgreSQL.

Usage:
    python scripts/migrate_sqlite_to_pg.py [--dry-run] [--skip-training-data]

Prerequisites:
    - PostgreSQL database running and accessible via DATABASE_URL
    - Alembic migrations applied: alembic upgrade head
    - Source SQLite database (default: nrg_research.db)

What it migrates:
    - Application tables (researchers, publications, institutions, labs, etc.)
    - Auth tables (refresh_tokens)
    - Training pairs from .training_data.db

What it does NOT migrate:
    - Django auth tables (auth_*, django_*) — framework internals
    - Large reference tables already in PostgreSQL (academic_courses_details, etc.)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

SQLITE_DB = os.getenv("NRG_SQLITE_DB", "nrg_research.db")
TRAINING_DB = os.getenv("TRAINING_DATA_DB", ".training_data.db")


def _resolve_path(path_str: str) -> Path:
    """Resolve a database path relative to project root."""
    p = Path(path_str).expanduser()
    if not p.is_absolute():
        p = Path(__file__).resolve().parents[1] / p
    return p.resolve()


TABLES_TO_MIGRATE = [
    "researchers",
    "publications",
    "institutions",
    "labs",
    "funding_records",
    "research_documents",
    "audit_events",
    "refresh_tokens",
    "consent_records",
    "data_deletion_requests",
]


def _get_sqlite_conn(db_path: Path):
    import sqlite3
    return sqlite3.connect(str(db_path), timeout=60.0)


def _get_pg_conn(database_url: str):
    import psycopg2
    return psycopg2.connect(database_url, connect_timeout=60)


def _table_columns(cursor, table: str) -> list[str]:
    """Get column names for a SQLite table."""
    cursor.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]


def _count_sqlite_table(conn, table: str) -> int:
    """Count rows in a SQLite table."""
    cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
    return cur.fetchone()[0]


def _fetchall_sqlite(conn, table: str, columns: list[str], batch_size: int = 1000):
    """Yield rows from a SQLite table in batches."""
    column_list = ", ".join([f'"{col}"' for col in columns])
    query = f"SELECT {column_list} FROM {table}"
    cursor = conn.execute(query)
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        yield from rows


def migrate_table(
    sqlite_conn,
    pg_conn,
    table: str,
    column_types: dict[str, str],
    dry_run: bool = False,
) -> dict:
    """Migrate a single table from SQLite to PostgreSQL."""
    import psycopg2.extras

    start = time.monotonic()
    sqlite_cur = sqlite_conn.execute(f"SELECT COUNT(*) FROM {table}")
    total = sqlite_cur.fetchone()[0]

    cols = _table_columns(sqlite_conn.cursor(), table)
    if not cols:
        return {"table": table, "status": "skipped", "reason": "no columns"}

    placeholders = ", ".join(["%s"] * len(cols))
    col_names = ", ".join(cols)

    insert_sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

    rows_inserted = 0
    batch_num = 0
    try:
        for batch in _fetchall_sqlite(sqlite_conn, table, cols):
            if dry_run:
                rows_inserted += 1
            else:
                try:
                    psycopg2.extras.execute_batch(pg_conn, insert_sql, [batch])
                    pg_conn.commit()
                    rows_inserted += 1
                except Exception as e:
                    pg_conn.rollback()
                    for i, row in enumerate([batch]):
                        try:
                            psycopg2.extras.execute_batch(pg_conn, insert_sql, [row])
                            pg_conn.commit()
                            rows_inserted += 1
                        except Exception:
                            pg_conn.rollback()
                            logger.warning("  Could not insert row %d in %s", i, table)
            batch_num += 1
            if batch_num % 100 == 0:
                elapsed = time.monotonic() - start
                rate = rows_inserted / elapsed if elapsed > 0 else 0
                logger.info("  %s: %d/%d rows (%.0f rows/sec)", table, rows_inserted, total, rate)

    except Exception as e:
        return {
            "table": table,
            "status": "error",
            "error": str(e),
            "rows_inserted": rows_inserted,
        }

    elapsed = time.monotonic() - start
    rate = rows_inserted / elapsed if elapsed > 0 else 0
    return {
        "table": table,
        "status": "done",
        "rows_inserted": rows_inserted,
        "elapsed_s": round(elapsed, 2),
        "rate_per_sec": round(rate),
    }


def migrate_training_pairs(
    sqlite_path: Path,
    pg_conn,
    dry_run: bool = False,
) -> dict:
    """Migrate the training_pairs table from its dedicated SQLite DB."""
    import psycopg2.extras

    if not sqlite_path.exists():
        return {"table": "training_pairs", "status": "skipped", "reason": f"{sqlite_path} not found"}

    try:
        sqlite_conn = _get_sqlite_conn(sqlite_path)
    except Exception as e:
        return {"table": "training_pairs", "status": "error", "error": f"Cannot open SQLite: {e}"}

    try:
        sqlite_cur = sqlite_conn.execute("SELECT COUNT(*) FROM training_pairs")
        total = sqlite_cur.fetchone()[0]
        if total == 0:
            return {"table": "training_pairs", "status": "skipped", "reason": "no data"}

        cols = _table_columns(sqlite_conn, sqlite_conn.cursor(), "training_pairs")
        placeholders = ", ".join(["%s"] * len(cols))
        insert_sql = f"INSERT INTO training_pairs ({', '.join(cols)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

        start = time.monotonic()
        rows_inserted = 0

        for batch in _fetchall_sqlite(sqlite_conn, "training_pairs", cols):
            if dry_run:
                rows_inserted += 1
            else:
                try:
                    psycopg2.extras.execute_batch(pg_conn, insert_sql, [batch])
                    pg_conn.commit()
                    rows_inserted += 1
                except Exception as e:
                    pg_conn.rollback()
                    logger.warning("  training_pairs batch failed: %s", e)
                    rows_inserted += 1

        elapsed = time.monotonic() - start
        return {
            "table": "training_pairs",
            "status": "done",
            "rows_inserted": rows_inserted,
            "elapsed_s": round(elapsed, 2),
        }
    finally:
        sqlite_conn.close()


def migrate_sqlite_to_postgres(
    sqlite_db: str | Path | None = None,
    pg_url: str | None = None,
    dry_run: bool = False,
    skip_training_data: bool = False,
) -> list[dict]:
    """Programmatic migration entry point kept stable for tests and agents."""
    pg_url = pg_url or os.getenv("DATABASE_URL")
    if not pg_url:
        raise ValueError("DATABASE_URL or pg_url is required")

    sqlite_path = _resolve_path(str(sqlite_db or SQLITE_DB))
    training_path = _resolve_path(TRAINING_DB)
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite DB not found: {sqlite_path}")

    pg_conn = _get_pg_conn(pg_url)
    results = []
    try:
        for table in TABLES_TO_MIGRATE:
            sqlite_conn = _get_sqlite_conn(sqlite_path)
            try:
                results.append(
                    migrate_table(
                        sqlite_conn,
                        pg_conn,
                        table,
                        COLUMN_TYPES.get(table, {}),
                        dry_run=dry_run,
                    )
                )
            finally:
                sqlite_conn.close()

        if not skip_training_data:
            results.append(migrate_training_pairs(training_path, pg_conn, dry_run=dry_run))
    finally:
        pg_conn.close()

    return results


# Column type mappings from SQLite to PostgreSQL
COLUMN_TYPES: dict[str, dict[str, str]] = {
    "researchers": {
        "researcher_id": "VARCHAR(36)",
        "name": "VARCHAR(255)",
        "email": "VARCHAR(255)",
        "phone": "VARCHAR(20)",
        "orcid": "VARCHAR(20)",
        "state": "VARCHAR(2)",
        "country": "VARCHAR(10)",
        "research_area": "VARCHAR(100)",
        "h_index": "INTEGER",
        "year_joined": "INTEGER",
        "institution_id": "VARCHAR(36)",
        "access_tier": "INTEGER",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    },
    "publications": {
        "publication_id": "VARCHAR(36)",
        "title": "TEXT",
        "abstract": "TEXT",
        "year": "INTEGER",
        "venue": "VARCHAR(500)",
        "citation_count": "INTEGER",
        "researcher_ids": "TEXT",
        "access_tier": "INTEGER",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    },
    "institutions": {
        "institution_id": "VARCHAR(36)",
        "name": "VARCHAR(255)",
        "type": "VARCHAR(50)",
        "state": "VARCHAR(2)",
        "country": "VARCHAR(10)",
        "founded_year": "INTEGER",
        "website": "VARCHAR(255)",
        "access_tier": "INTEGER",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    },
    "labs": {
        "lab_id": "VARCHAR(36)",
        "name": "VARCHAR(255)",
        "institution_id": "VARCHAR(36)",
        "established_year": "INTEGER",
        "focus_areas": "TEXT",
        "access_tier": "INTEGER",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    },
    "funding_records": {
        "record_id": "VARCHAR(36)",
        "researcher_id": "VARCHAR(36)",
        "grant_agency": "VARCHAR(255)",
        "amount": "DECIMAL(15,2)",
        "start_date": "VARCHAR(50)",
        "end_date": "VARCHAR(50)",
        "status": "VARCHAR(50)",
        "access_tier": "INTEGER",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    },
    "research_documents": {
        "document_id": "VARCHAR(36)",
        "title": "TEXT",
        "publication_year": "INTEGER",
        "researcher_id": "VARCHAR(36)",
        "access_tier": "INTEGER",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    },
    "audit_events": {
        "event_id": "VARCHAR(36)",
        "user_id": "VARCHAR(36)",
        "event_type": "VARCHAR(50)",
        "event_data": "TEXT",
        "ip_address": "VARCHAR(45)",
        "timestamp": "TIMESTAMP",
    },
    "refresh_tokens": {
        "token_id": "VARCHAR(36)",
        "user_id": "VARCHAR(36)",
        "refresh_token_hash": "VARCHAR(255)",
        "expires_at": "TIMESTAMP",
        "revoked": "BOOLEAN",
        "created_at": "TIMESTAMP",
    },
    "consent_records": {
        "record_id": "VARCHAR(36)",
        "user_id": "VARCHAR(36)",
        "consent_type": "VARCHAR(50)",
        "granted": "BOOLEAN",
        "timestamp": "TIMESTAMP",
        "ip_address": "VARCHAR(45)",
    },
    "data_deletion_requests": {
        "request_id": "VARCHAR(36)",
        "user_id": "VARCHAR(36)",
        "status": "VARCHAR(20)",
        "requested_at": "TIMESTAMP",
        "completed_at": "TIMESTAMP",
    },
}


def main():
    parser = argparse.ArgumentParser(description="Migrate NRG SQLite data to PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", help="Count rows without inserting")
    parser.add_argument("--skip-training-data", action="store_true", help="Skip training_pairs migration")
    parser.add_argument("--pg-url", help="PostgreSQL DATABASE_URL (overrides env)")
    args = parser.parse_args()

    pg_url = args.pg_url or os.getenv("DATABASE_URL")
    if not pg_url:
        logger.error("DATABASE_URL not set. Cannot connect to PostgreSQL.")
        sys.exit(1)

    sqlite_path = _resolve_path(SQLITE_DB)
    training_path = _resolve_path(TRAINING_DB)

    if not sqlite_path.exists():
        logger.error("SQLite DB not found: %s", sqlite_path)
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("NRG SQLite → PostgreSQL Migration")
    logger.info("=" * 60)
    logger.info("SQLite DB:   %s", sqlite_path)
    logger.info("Training DB: %s", training_path)
    logger.info("PostgreSQL:  %s", pg_url.split("@")[-1] if "@" in pg_url else "(masked)")
    logger.info("Dry run:     %s", args.dry_run)
    logger.info("=" * 60)

    try:
        import psycopg2
        pg_conn = _get_pg_conn(pg_url)
        logger.info("PostgreSQL connected OK")
    except Exception as e:
        logger.error("Cannot connect to PostgreSQL: %s", e)
        sys.exit(1)

    results = []
    total_start = time.monotonic()

    for table in TABLES_TO_MIGRATE:
        logger.info("Migrating table: %s", table)
        try:
            result = migrate_table(
                _get_sqlite_conn(sqlite_path),
                pg_conn,
                table,
                COLUMN_TYPES.get(table, {}),
                dry_run=args.dry_run,
            )
            results.append(result)
            if result["status"] == "done":
                logger.info(
                    "  → %s: %d rows in %.1fs (%.0f/sec)",
                    table,
                    result["rows_inserted"],
                    result.get("elapsed_s", 0),
                    result.get("rate_per_sec", 0),
                )
            elif result["status"] == "skipped":
                logger.info("  → %s: SKIPPED (%s)", table, result.get("reason", ""))
            else:
                logger.error("  → %s: ERROR (%s)", table, result.get("error", "unknown"))
        except Exception as e:
            logger.error("  → %s: EXCEPTION %s", table, e)
            results.append({"table": table, "status": "error", "error": str(e)})

    if not args.skip_training_data:
        logger.info("Migrating training_pairs...")
        result = migrate_training_pairs(training_path, pg_conn, dry_run=args.dry_run)
        results.append(result)
        if result["status"] == "done":
            logger.info(
                "  → training_pairs: %d rows in %.1fs",
                result["rows_inserted"],
                result.get("elapsed_s", 0),
            )
        elif result["status"] == "skipped":
            logger.info("  → training_pairs: SKIPPED (%s)", result.get("reason", ""))

    pg_conn.close()

    total_elapsed = time.monotonic() - total_start
    total_rows = sum(r.get("rows_inserted", 0) for r in results)
    errors = [r for r in results if r["status"] == "error"]

    logger.info("=" * 60)
    logger.info("Migration complete in %.1fs", total_elapsed)
    logger.info("Total rows inserted: %d", total_rows)
    logger.info("Tables migrated: %d", sum(1 for r in results if r["status"] == "done"))
    logger.info("Tables skipped: %d", sum(1 for r in results if r["status"] == "skipped"))
    logger.info("Tables with errors: %d", len(errors))
    logger.info("=" * 60)

    if errors:
        for e in errors:
            logger.error("  %s: %s", e["table"], e.get("error", ""))
        sys.exit(1)

    summary_path = Path(__file__).resolve().parent.parent / "data" / "migration_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "source_sqlite": str(sqlite_path),
                "target_pg": pg_url.split("@")[-1] if "@" in pg_url else "masked",
                "dry_run": args.dry_run,
                "total_rows": total_rows,
                "elapsed_s": round(total_elapsed, 2),
                "results": results,
            },
            indent=2,
            default=str,
        )
    )
    logger.info("Summary written to %s", summary_path)

    if args.dry_run:
        logger.info("DRY RUN complete — no data was written.")


if __name__ == "__main__":
    main()

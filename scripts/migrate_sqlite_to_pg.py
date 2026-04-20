#!/usr/bin/env python3
"""One-shot SQLite to Postgres ETL with idempotent upserts."""

from __future__ import annotations

import os
import sqlite3
from typing import Iterable

import psycopg2
from psycopg2.extras import execute_values

from src.data.database import resolve_database_path


DEFAULT_TABLES = [
    "institutions",
    "researchers",
    "labs",
    "publications",
    "funding_records",
    "keywords",
    "researcher_publications",
    "researcher_labs",
    "publication_keywords",
]


def migrate_sqlite_to_postgres(
    sqlite_url: str | None = None,
    postgres_url: str | None = None,
    tables: Iterable[str] | None = None,
) -> dict[str, int]:
    sqlite_path = resolve_database_path(sqlite_url)
    postgres_url = postgres_url or os.getenv("POSTGRES_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not postgres_url or not postgres_url.startswith(("postgresql://", "postgres://")):
        raise RuntimeError("A Postgres URL is required via POSTGRES_DATABASE_URL or DATABASE_URL")

    counts: dict[str, int] = {}
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = psycopg2.connect(postgres_url)

    try:
        for table in tables or DEFAULT_TABLES:
            rows = [dict(row) for row in sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()]
            if not rows:
                counts[table] = 0
                continue

            columns = list(rows[0].keys())
            pk_columns = _primary_key_columns(sqlite_conn, table)
            _upsert_rows(pg_conn, table, columns, pk_columns, rows)
            counts[table] = len(rows)
        pg_conn.commit()
        return counts
    except Exception:
        pg_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()


def _primary_key_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [row["name"] for row in columns if row["pk"]]


def _upsert_rows(pg_conn, table: str, columns: list[str], pk_columns: list[str], rows: list[dict]) -> None:
    values = [[row.get(column) for column in columns] for row in rows]
    quoted_columns = ", ".join(f'"{column}"' for column in columns)
    update_columns = [column for column in columns if column not in pk_columns]

    if pk_columns and update_columns:
        conflict = ", ".join(f'"{column}"' for column in pk_columns)
        updates = ", ".join(f'"{column}" = EXCLUDED."{column}"' for column in update_columns)
        sql = f'INSERT INTO "{table}" ({quoted_columns}) VALUES %s ON CONFLICT ({conflict}) DO UPDATE SET {updates}'
    elif pk_columns:
        conflict = ", ".join(f'"{column}"' for column in pk_columns)
        sql = f'INSERT INTO "{table}" ({quoted_columns}) VALUES %s ON CONFLICT ({conflict}) DO NOTHING'
    else:
        sql = f'INSERT INTO "{table}" ({quoted_columns}) VALUES %s'

    with pg_conn.cursor() as cursor:
        execute_values(cursor, sql, values)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Migrate NRG SQLite data to Postgres")
    parser.add_argument("--sqlite-url", default=None)
    parser.add_argument("--postgres-url", default=None)
    args = parser.parse_args()
    print(
        json.dumps(
            migrate_sqlite_to_postgres(args.sqlite_url, args.postgres_url),
            indent=2,
        )
    )

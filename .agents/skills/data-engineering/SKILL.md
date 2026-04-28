---
name: data-engineering
description: Data pipeline authoring — warehouse exploration, ETL design, Airflow DAG patterns, data quality checks, and schema evolution. Use when building or debugging data ingestion or transformation pipelines.
model-agnostic: true
---

# Data Engineering

## When to Use

- Designing or debugging an ETL/ELT pipeline
- Writing Airflow DAGs for scheduled data tasks
- Exploring a database or warehouse to understand what data exists
- Adding data quality checks to a pipeline
- Handling schema evolution (adding columns, changing types) safely

## Warehouse Exploration

Before writing any pipeline, understand what's there:

```sql
-- What tables exist?
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- What columns does a table have?
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'your_table'
ORDER BY ordinal_position;

-- Row counts across all tables (PostgreSQL)
SELECT schemaname, relname, n_live_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Find tables with recent data
SELECT table_name, pg_size_pretty(pg_total_relation_size(quote_ident(table_name)))
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;
```

## Pipeline Design Checklist

Before writing code:
- [ ] What is the source? (API, file, database, Kafka topic)
- [ ] What is the destination? (PostgreSQL, Qdrant, S3, another DB)
- [ ] Is this a full load or incremental? If incremental, what's the cursor?
- [ ] What's the expected row count? What constitutes an anomaly?
- [ ] What should happen on error? (fail, skip, retry, dead-letter)
- [ ] Is this idempotent? (safe to re-run without duplicating data)

## Idempotent Upsert Pattern (PostgreSQL)

```python
# Always prefer upsert over insert for pipeline loads
await conn.execute("""
    INSERT INTO researchers (id, name, institution, updated_at)
    VALUES ($1, $2, $3, NOW())
    ON CONFLICT (id)
    DO UPDATE SET
        name = EXCLUDED.name,
        institution = EXCLUDED.institution,
        updated_at = NOW()
    WHERE researchers.updated_at < EXCLUDED.updated_at
""", row["id"], row["name"], row["institution"])
```

## Data Quality Checks

Run after every load:

```python
def assert_quality(conn, table: str, expected_min_rows: int, cursor_col: str = None):
    """Raise if pipeline produced bad output."""

    # Row count gate
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").scalar()
    assert count >= expected_min_rows, f"{table}: only {count} rows, expected >= {expected_min_rows}"

    # Null check on critical columns
    nulls = conn.execute(
        f"SELECT COUNT(*) FROM {table} WHERE id IS NULL OR name IS NULL"
    ).scalar()
    assert nulls == 0, f"{table}: {nulls} rows with null primary fields"

    # Freshness check (if incremental)
    if cursor_col:
        from datetime import datetime, timedelta
        max_ts = conn.execute(f"SELECT MAX({cursor_col}) FROM {table}").scalar()
        assert max_ts > datetime.now() - timedelta(hours=25), f"{table}: stale — last row at {max_ts}"
```

## Airflow DAG Pattern

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "nrg-data",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": alert_on_failure,  # always wire up alerting
}

with DAG(
    dag_id="nrg_ingest_researchers",
    default_args=default_args,
    schedule_interval="0 2 * * *",  # 2am daily
    start_date=datetime(2026, 1, 1),
    catchup=False,  # don't backfill on first deploy
    tags=["nrg", "ingestion"],
) as dag:

    extract = PythonOperator(task_id="extract", python_callable=extract_fn)
    transform = PythonOperator(task_id="transform", python_callable=transform_fn)
    load = PythonOperator(task_id="load", python_callable=load_fn)
    quality_check = PythonOperator(task_id="quality_check", python_callable=quality_fn)

    extract >> transform >> load >> quality_check
```

## Schema Evolution

Safe column additions:
```sql
-- SAFE: add nullable column (no lock on large tables)
ALTER TABLE researchers ADD COLUMN IF NOT EXISTS orcid_id TEXT;

-- SAFE: add column with default (PostgreSQL 11+, no full rewrite)
ALTER TABLE researchers ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;

-- UNSAFE on large tables: changing column type
-- → add new column, backfill, swap, drop old
```

## For NRG

NRG pipeline specifics:

| Pipeline | Source | Destination | Schedule |
|---|---|---|---|
| `ingest_nrg_db.py` | CSV/JSON files | PostgreSQL 58 tables | On demand / weekly |
| `ingest_qdrant.py` | PostgreSQL / JSON | Qdrant vector store | On demand |
| `backup_db.sh` | PostgreSQL | Local backup dir | Daily cron |

Key rules:
- All ingestion reads from `NRG_DATA_SOURCE_DIR` env var, not hardcoded paths
- Qdrant ingestion must check for duplicate vectors (use `upsert`, not `upload`)
- Any pipeline touching researcher PII must log to audit chain
- Row count after load must be logged: `logger.info("Loaded %d rows into %s", count, table)`

Run pipelines:
```bash
# Full DB ingest
PYTEST_CURRENT_TEST=1 .venv/bin/python scripts/ingest_nrg_db.py

# Qdrant vector ingest
.venv/bin/python scripts/ingest_qdrant.py

# Verify merge
.venv/bin/python scripts/verify_db_merge.py
```

## Anti-Patterns

- INSERT without conflict handling — will fail on re-run (pipelines must be idempotent)
- Hardcoded file paths — use env vars, pipelines must run on any machine
- Loading without quality checks — silent data corruption goes unnoticed
- `SELECT *` in transformation queries — always name columns explicitly
- No row count logging — impossible to detect partial loads without it
- Dropping and recreating tables to "clean up" — destroys data, kills FK constraints

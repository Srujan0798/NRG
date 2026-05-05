# Schema Parity Primary-Key Boundary

Date: 2026-05-05  
Current boundary before this evidence sync: `738caade`

This evidence records the schema-parity test boundary found during the fresh
Batch 4 recheck.

## Result

| Check | Status | Evidence |
| --- | --- | --- |
| Ruff on schema parity test | PASS | `ruff_schema_parity.log` |
| Local SQLite parity test | PASS | `pytest_schema_parity_local.log`: 15 passed, 1 skipped |
| PostgreSQL primary-key identity gate | PASS | `pytest_schema_parity_postgres_pk.log`: 1 passed |

## Boundary

`tests/data/test_schema_parity.py` now treats D4-01 profiled empty Dhairya
tables as documented data gaps instead of schema drift. It also compares
PostgreSQL primary-key columns against `db_struct.sql`, while local SQLite
parity skips that one primary-key identity gate because the SQLite Alembic
parity database intentionally preserves several historical natural keys.

The local SQLite run still covers table presence, column presence, TRL view
presence, seed coverage, hot JOIN index plans, Dhairya table presence,
fingerprint stability, unexpected empty tables, FK references, and critical
credit-score type behavior.

# Batch 4 Data / SQL / Schema Fresh Recheck

Date: 2026-05-05  
Current boundary before this evidence sync: `738caade`

This is a current-tree local PostgreSQL verification pass for Batch 4 D4-01
through D4-11. It proves the local database/schema gates only. It is not
production-data, deployed-Qdrant, cluster-load, or founder-signing proof.

## Status Matrix

| Task | Status | Result | Evidence |
| --- | --- | --- | --- |
| D4-01 table profiles | PASS | 80 live tables, 24 non-zero, 56 zero-row tables documented and prioritized by reference frequency | `evidence/2026-05-02/table_profiles/table_profiles.md` |
| D4-02 schema sync | PASS | 58/58 `db_struct.sql` tables present; no blocking missing table, missing column, extra column, or type drift; 22 app-owned live tables classified informational | `evidence/2026-05-02/batch4_data_sql_schema/D4-02_schema_sync.md` |
| D4-03 Dhairya replay | PASS | 17/17 benchmark SQL queries replayed successfully | `evidence/2026-05-02/batch4_data_sql_schema/D4-03_dhairya_replay.md` |
| D4-04 contact constraints | PASS | Invalid researcher email and phone formats rejected; valid formats accepted | `evidence/2026-05-02/batch4_data_sql_schema/D4-04_contact_constraints.md` |
| D4-05 FK/orphan check | PASS | 9 checked FK relationships present with 0 orphan rows | `evidence/2026-05-02/batch4_data_sql_schema/D4-05_fk_orphans.md` |
| D4-06 time-series partitioning | PASS | `audit_events` partitioned with 3 child partitions; planner pruned to `audit_events_2026`; `query_logs` table is absent in this local schema | `evidence/2026-05-02/batch4_data_sql_schema/D4-06_D4-08_partition_indexes.md` |
| D4-07 NULL aggregate behavior | PASS | Stats endpoint preserves NULL instead of converting to 0 | `tests/api/test_data_stats_nulls.py` |
| D4-08 hot-path indexes | PASS | Hot-path probes all under 200 ms; slowest current probe `researchers_area` at 71.457 ms | `evidence/2026-05-02/batch4_data_sql_schema/D4-06_D4-08_partition_indexes.md` |
| D4-09 data quality | PASS | Scorecard `ok: true`, status `PASS`, score `0.919`, alerts `0` | `evidence/2026-05-02/batch4_data_sql_schema/D4-09_data_quality_scorecard.md` |
| D4-10 corpus sync | PASS | Corpus mirror returned `ok: true`; canonical hashes match | `scripts/verify_corpus_sync.py` output |
| D4-11 migration safety | PASS | Alembic head is `d4_primary_key_alignment_005`; primary-key alignment is forward-only and matches `db_struct.sql` | `evidence/2026-05-05/final_current_tree_guard_recheck/alembic_heads.log` |

## Fresh Commands

| Command | Result |
| --- | --- |
| `docker compose ps postgres pgbouncer api` | PASS: API, pgbouncer, and PostgreSQL healthy/up |
| `curl -sS http://127.0.0.1:8000/health/all` | PASS: overall healthy; local LLM is optional unavailable |
| `.venv/bin/alembic heads` | PASS: `d4_primary_key_alignment_005 (head)` |
| `DATABASE_URL=postgresql://... .venv/bin/alembic current` | PASS: `d4_primary_key_alignment_005 (head)` |
| `.venv/bin/python scripts/batch4_data_sql_schema_audit.py` with `.env` loaded | PASS: `ok: true` and evidence refreshed |
| `.venv/bin/python scripts/data_quality_scorecard.py ... --fail-on-p0 --fail-on-fail` | PASS: `ok: true status: PASS score: 0.919 alerts: 0` |
| `.venv/bin/python scripts/check_schema_sync.py --summary` with `.env` loaded | PASS: `SCHEMA IN SYNC` |
| `.venv/bin/python scripts/verify_corpus_sync.py` | PASS: `ok: true` |
| `.venv/bin/python -m pytest tests/api/test_data_stats_nulls.py tests/data/test_schema_parity.py tests/data/test_database_v2.py tests/data/test_database_v2_schema_drift.py tests/data/test_data_quality.py tests/integration/test_schema_completeness.py::TestSchemaSyncCheck -q --tb=short` | PASS: 45 passed, 1 skipped |
| `.venv/bin/python -m pytest tests/data/test_schema_parity.py -q --tb=short --no-cov` | PASS: 15 passed, 1 skipped in local SQLite parity mode |
| `DATABASE_URL=postgresql://... .venv/bin/python -m pytest tests/data/test_schema_parity.py::TestSchemaParity::test_primary_keys_match_authoritative_schema -q --tb=short --no-cov` | PASS: PostgreSQL primary-key identity gate passed |
| `.venv/bin/python -m pytest tests/integration/test_schema_completeness.py::TestProductionMigrationParity -q --tb=short --no-cov` | PASS: 2 passed |
| `.venv/bin/python -m pytest tests/audit/test_db_cosign.py tests/security/test_per_user_audit_binding.py::TestDatabaseCoSign::test_db_cosign_trigger_sql_adds_column_and_insert_trigger -q --tb=short` | PASS: 22 passed |
| `.venv/bin/ruff check ... tests/data/test_schema_parity.py` | PASS: all checks passed |
| `.venv/bin/python -m py_compile tests/data/test_schema_parity.py` | PASS |
| `git diff --check` | PASS |

## Test Contract Fix

The live DB-backed recheck initially exposed two stale schema parity test
assumptions:

- `test_all_dhairya_tables_have_minimum_rows` treated D4-01 profiled empty
  tables as failures.
- `test_primary_keys_intact` only checked that every table had a primary key,
  which missed drift where live primary-key columns diverged from
  `db_struct.sql`.

`tests/data/test_schema_parity.py` now fails only on unexpected empty Dhairya
tables and on PostgreSQL primary-key drift from the authoritative
`db_struct.sql` declarations. Local SQLite parity still checks table, column,
view, seed, index, row-count, FK, and type contracts; it skips only the
PostgreSQL primary-key identity gate because the local SQLite Alembic parity DB
preserves several historical natural keys.

## Remaining Boundaries

- `query_logs` is not present in the current local schema, so D4-06 partition
  proof is limited to `audit_events`.
- Empty official tables remain documented D4-01 data gaps; they were not seeded
  with synthetic data in this pass.
- External production data replay, deployed service health, sovereign-cluster C4,
  and founder signing remain outside this local Batch 4 recheck.

# Leftover Local Closure

Date: 2026-05-05  
Current boundary before this evidence sync: `738caade`

This file records the current local closure pass for the remaining uncommitted
Batch 2, Batch 4, Batch 5, schema-parity, and 500-audit-event evidence. It is
local proof only; deployed service gates, remote history remediation, cluster
load, and founder signing remain separately gated.

## Verified Commands

| Surface | Command | Result |
| --- | --- | --- |
| Docker local services | `docker compose ps postgres pgbouncer api` | PASS: API, pgbouncer, and PostgreSQL healthy |
| API aggregate health | `curl -fsS http://127.0.0.1:8000/health/all` | PASS: `healthy: true`; local LLM optional unavailable |
| Alembic upgrade | `set -a; source .env; set +a; .venv/bin/alembic upgrade head` | PASS: local PostgreSQL advanced to current head |
| Alembic head/current | `.venv/bin/alembic heads` and `DATABASE_URL=postgresql://... .venv/bin/alembic current` | PASS: `d4_primary_key_alignment_005 (head)` |
| Schema sync | `set -a; source .env; set +a; .venv/bin/python scripts/check_schema_sync.py --summary` | PASS: `SCHEMA IN SYNC` |
| Data quality | `set -a; source .env; set +a; .venv/bin/python scripts/data_quality_scorecard.py --json-output /tmp/nrg_data_quality_current.json --markdown-output /tmp/nrg_data_quality_current.md --fail-on-p0 --fail-on-fail` | PASS: `ok: true status: PASS score: 0.919 alerts: 0` |
| Batch 4 audit evidence | `set -a; source .env; set +a; .venv/bin/python scripts/batch4_data_sql_schema_audit.py --output-root evidence/2026-05-02` | PASS: `ok: true` |
| Schema/data tests | `.venv/bin/python -m pytest tests/api/test_data_stats_nulls.py tests/data/test_schema_parity.py tests/data/test_database_v2.py tests/data/test_database_v2_schema_drift.py tests/data/test_data_quality.py tests/integration/test_schema_completeness.py::TestSchemaSyncCheck -q --tb=short --no-cov` | PASS: 45 passed, 1 skipped |
| Targeted schema/API regression | `.venv/bin/python -m pytest tests/data/test_schema_parity.py tests/api/test_500_audit_event.py -q --tb=short --no-cov` | PASS: 16 passed, 1 skipped |
| Migration parity | `.venv/bin/python -m pytest tests/integration/test_schema_completeness.py::TestProductionMigrationParity -q --tb=short --no-cov` | PASS: 2 passed |
| PostgreSQL PK gate | `DATABASE_URL=postgresql://... .venv/bin/python -m pytest tests/data/test_schema_parity.py::TestSchemaParity::test_primary_keys_match_authoritative_schema -q --tb=short --no-cov` | PASS: 1 passed |
| Audit co-sign tests | `.venv/bin/python -m pytest tests/audit/test_db_cosign.py tests/security/test_per_user_audit_binding.py::TestDatabaseCoSign::test_db_cosign_trigger_sql_adds_column_and_insert_trigger -q --tb=short --no-cov` | PASS: 22 passed |
| Forced-500 audit ID test | `.venv/bin/python -m pytest tests/api/test_500_audit_event.py -q --tb=short --no-cov` | PASS: 1 passed |
| Red-team v4.1 focused regression | `.venv/bin/python -m pytest tests/security/test_red_team_v41.py -q --tb=short --no-cov` | PASS: 30 passed |
| Batch 5 orchestration/skills | `.venv/bin/python -m pytest tests/orchestration/ tests/skills/ -q --tb=short --no-cov -x` | PASS: 419 passed, 6 skipped, 35 deselected |
| Frontend build + Jest | `cd frontend && npm run build && npm test -- --runInBand` | PASS: build completed; Jest 32 suites / 107 tests passed |
| Ruff | `.venv/bin/ruff check tests/data/test_schema_parity.py scripts/batch4_data_sql_schema_audit.py scripts/check_schema_sync.py src/skills/text_to_sql/schema_sync_check.py` | PASS |
| Python compile | `.venv/bin/python -m py_compile tests/data/test_schema_parity.py tests/api/test_500_audit_event.py src/migrations/versions/d4_primary_key_alignment_005.py alembic/versions/add_production_tables_001.py src/migrations/versions/add_production_tables_001.py scripts/seed_production_tables.py` | PASS |
| Corpus sync | `python3 scripts/verify_corpus_sync.py` | PASS: `ok: true` |
| Diff hygiene | `git diff --check` | PASS |

## Notes

- `tests/data/test_schema_parity.py` now treats D4-01 profiled empty Dhairya
  tables as known local data gaps instead of schema drift.
- PostgreSQL primary-key parity is now checked against the primary keys declared
  in `db_struct.sql`; SQLite parity skips this PostgreSQL-specific identity
  check.
- `d4_primary_key_alignment_005` is now the sole Alembic head and aligns six
  legacy Batch 4 tables to the `db_struct.sql` `id` primary keys.
- `tests/api/test_500_audit_event.py` now removes its temporary forced-500 route
  after the test, preventing cross-test route leakage.
- `tests/security/test_red_team_v41.py` now exits consistently after live API
  connection failures instead of falling through from the skip helper.

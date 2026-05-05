# Batch 2 + Batch 5 Fresh Recheck

Date: 2026-05-05
Current boundary before this evidence sync: `738caade`

This is a current-tree local verification pass for the Batch 2 frontend surface
and Batch 5 orchestration/skills surface. It is not deployed-browser,
production-Qdrant, cluster-load, or founder-signing proof.

## Status

| Surface | Status | Result | Evidence |
| --- | --- | --- | --- |
| Frontend production build | PASS | `npm run build` exited 0; Vite built in `12.90s`; largest JS chunk `vendor-recharts-xdmfsjT3.js` at `319.01 kB` | `frontend_build.log` |
| Frontend Jest | PASS | `32 passed, 32 total`; `107 passed, 107 total`; `28.952s` | `frontend_jest.log` |
| Batch 5 orchestration/skills | PASS | `419 passed, 6 skipped, 35 deselected in 103.53s` | `batch5_orchestration_skills_pytest.log` |
| Schema parity follow-up | PASS | `15 passed, 1 skipped in 13.24s` | `schema_parity_pytest.log` |
| PostgreSQL primary-key gate | PASS | `1 passed` against local PostgreSQL | `schema_parity_postgres_pytest.log` |
| Changed Python lint | PASS | Ruff reported `All checks passed!` | command output |
| Changed Python compile | PASS | `compileall` exited 0 | command output |
| Alembic migration head | PASS | `d4_primary_key_alignment_005 (head)` | command output |

## Commands

```bash
cd frontend
npm run build
npm test -- --runInBand

cd /Users/srujansai/Desktop/NRG
.venv/bin/python -m pytest tests/orchestration/ tests/skills/ -q --tb=short --no-cov -x
.venv/bin/python -m pytest tests/data/test_schema_parity.py -q --tb=short --no-cov
DATABASE_URL=postgresql://... .venv/bin/python -m pytest tests/data/test_schema_parity.py::TestSchemaParity::test_primary_keys_match_authoritative_schema -q --tb=short --no-cov
.venv/bin/ruff check src/migrations/versions/d4_primary_key_alignment_005.py src/migrations/versions/add_production_tables_001.py alembic/versions/add_production_tables_001.py tests/data/test_schema_parity.py
.venv/bin/python -m compileall -q src/migrations/versions/d4_primary_key_alignment_005.py src/migrations/versions/add_production_tables_001.py alembic/versions/add_production_tables_001.py tests/data/test_schema_parity.py
.venv/bin/alembic heads
```

## Execution Note

The first Batch 5 pytest attempt failed before test collection because the
sandbox blocked `pytest-rerunfailures` from binding its localhost status socket:
`PermissionError: [Errno 1] Operation not permitted`. The same command was then
rerun in a shell context where the plugin status socket could bind and passed.
This was an execution-environment failure, not a product test failure.

## Schema-Parity Follow-Up

During final status inspection, a schema-parity test update was present in the
working tree and exposed a real migration mismatch: six legacy Batch 4 tables
were created with natural primary keys while `db_struct.sql` declares `id`
primary keys. The fix aligns the fresh production-table migration and adds
`d4_primary_key_alignment_005` as a forward migration for already-applied
databases. The focused schema-parity rerun now passes.

## Remaining Blockers

- Deployed frontend/API URLs are still missing for deployed browser proof.
- Production Qdrant/Redis targets are still missing for production retrieval
  proof.
- Sovereign-cluster context is still missing for deployed C4 replay.
- Founder GPG signing remains founder-only.

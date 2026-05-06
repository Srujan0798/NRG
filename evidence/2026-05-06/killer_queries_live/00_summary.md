# Killer Queries Live Local API Verification

Date: 2026-05-06
Status: PASS
API endpoint: http://localhost:8000

## Stack

- Docker services running: `nrg-api`, `nrg-frontend`, `nrg-postgres`, `nrg-pgbouncer`, `nrg-redis`, `nrg-qdrant`.
- API health after seed repair: `09_health_after_seed.json`.
- Database dialect: PostgreSQL.

## Seed Repair

`combined_ipo_patent_data` was empty in live PostgreSQL, so KILLER-03 could not return rows. Added `db/seed/003_killer_query_patent_seed.sql` and applied it to the local PostgreSQL stack.

Verification in `08_seed_repair.log`:

- Before: 0 patent rows.
- After direct seed file: 8 patent rows, 8 granted.
- KILLER-03 SQL returned 2 qualifying rows directly in PostgreSQL.

After the API restart and live test run, the PostgreSQL seed set contains:

- `combined_ipo_patent_data`: 550 rows.
- `status = 'Granted'`: 422 rows.
- KILLER-03 qualifying rows: 2.

## Live Pytest Result

Command:

```bash
NRG_API_URL=http://localhost:8000 .venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e --tb=short
```

Result: 3 passed in 2.35s.

| Query | Live API Result | Researcher Rows | SQL Shape |
|---|---|---:|---|
| KILLER-01 | PASS | 8 | PASS |
| KILLER-02 | PASS | 6 | PASS |
| KILLER-03 | PASS | 2 | PASS |

## Latency

Command:

```bash
NRG_API_URL=http://localhost:8000 NRG_KILLER_QUERY_RUNS=20 .venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e -k latency --tb=short
```

Result: 3 passed in 1.41s.

Manual 20-run researcher API timing summary appended to `02_latency.log`:

| Query | P95 ms | P99 ms | Minimum Rows |
|---|---:|---:|---:|
| KILLER-01 | 30.550 | 39.184 | 8 |
| KILLER-02 | 5.376 | 15.916 | 6 |
| KILLER-03 | 5.147 | 5.867 | 2 |

## Evidence

- `01_live_run.log` — complete live pytest output for all 3 queries.
- `02_latency.log` — live latency pytest and manual P95/P99 timing summary.
- `03_sql_samples.json` — generated SQL and first rows for all 3 queries across roles.
- `04_db_verification.txt` — must-contain verification.
- `04_seed_counts.txt` — live PostgreSQL seed counts.
- `08_seed_repair.log` — seed repair proof.
- `09_health_after_seed.json` — API health after restart.

## Commit

- Seed SQL evidence commit: `5b84bc59`
- PostgreSQL seed script commit: `c005d17f`
- Final evidence update: committed after this summary is staged; see `git log -1` and final report for exact HEAD.

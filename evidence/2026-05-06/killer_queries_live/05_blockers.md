# Blockers - Killer Queries Live Local API

Status: BLOCKED.

## Blocking Failure

KILLER-03 fails live API verification because it returns 0 `sql_results`.

The generated SQL has the required shape:

- `WITH`: YES
- `innovation_grant_from_govt`: YES
- `combined_ipo_patent_data`: YES
- `HAVING`: YES

The live PostgreSQL seed data does not support the query:

- `innovation_grant_from_govt`: 280 rows.
- Grant YoY pairs: 32 rows.
- `combined_ipo_patent_data`: 0 rows.
- `combined_ipo_patent_data WHERE status = 'Granted'`: 0 rows.

Without patent rows, the `patents` and `patent_yoy` CTEs in KILLER-03 cannot produce rows.

## Stop Rule Triggered

Assignment stop rule:

> If generated SQL is correct but returns 0 rows -> STOP. Ask Guru if seed data is missing.

This is triggered for KILLER-03.

## Not a Test Assertion Change

No test assertions were modified. No pipeline code was changed for this assignment.

## Required Guru Decision

Provide or load live PostgreSQL seed data for `combined_ipo_patent_data`, including rows with:

- `status = 'Granted'`
- a grant/publication/application date usable for year extraction
- `applicants` values that can match grant `institute` values
- at least one institute/year where grant funding drops more than 40% YoY and granted patents increase

After that seed data exists, rerun:

```bash
NRG_API_URL=http://localhost:8000 .venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e --tb=short
NRG_API_URL=http://localhost:8000 NRG_KILLER_QUERY_RUNS=20 .venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e -k latency --tb=short
```

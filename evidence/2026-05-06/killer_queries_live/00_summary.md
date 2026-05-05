# Killer Queries Live Local API Verification

Date: 2026-05-06
Commit SHA: aac88296
Status: BLOCKED - KILLER-03 returns 0 rows because live PostgreSQL has no patent rows.
API endpoint: http://localhost:8000

## Stack

- Docker services running: `nrg-api`, `nrg-frontend`, `nrg-postgres`, `nrg-pgbouncer`, `nrg-redis`, `nrg-qdrant`.
- Health evidence: `00_health.json`, `00_health_db.json`.
- API health: healthy.
- Database dialect: PostgreSQL.

## Live Pytest Result

Command:

```bash
NRG_API_URL=http://localhost:8000 .venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e --tb=short
```

Result: 2 passed, 1 failed in 3.64s.

| Query | Live API Result | Rows | SQL Shape | Notes |
|---|---|---:|---|---|
| KILLER-01 | PASS | 8 | PASS | Uses `SPLIT_PART`, `total_credit_score`, `AVG`, `GROUP BY institute`; FY 2022-23 seed rows exist. |
| KILLER-02 | PASS | 6 | PASS | Uses TRL-stage table, `GROUP BY`, `financial_year`; IIT Madras Level 4/9 seed rows exist. |
| KILLER-03 | FAIL | 0 | PASS | Uses `WITH`, `innovation_grant_from_govt`, `combined_ipo_patent_data`, `HAVING`, but live `combined_ipo_patent_data` has 0 rows. |

## Generated SQL Capture

Actual SQL samples are in `03_sql_samples.json`.

Manual API capture also saved per-role response summaries in `06_manual_api_responses.json`.

## Seed Verification

Live PostgreSQL checks:

- `academic_courses_details`: 3840 rows.
- `academic_courses_details` FY 2022-23: 960 rows.
- `innovations_at_various_stages_of_technology_readiness_level`: 1440 rows.
- IIT Madras Level 4/Level 9 TRL rows: 40 rows.
- `innovation_grant_from_govt`: 280 rows.
- Grant YoY pairs: 32 rows.
- `combined_ipo_patent_data`: 0 rows.
- `combined_ipo_patent_data` with `status = 'Granted'`: 0 rows.

## Latency

The dedicated latency benchmark was not run. The assignment stop rule applies after KILLER-03 generated correct SQL but returned 0 rows due missing patent seed data. The acceptance gate cannot pass until KILLER-03 returns at least one row.

## Verdict

Not complete. KILLER-01 and KILLER-02 are verified on the live local API. KILLER-03 is blocked by missing live PostgreSQL patent seed data, not by the generated SQL shape.

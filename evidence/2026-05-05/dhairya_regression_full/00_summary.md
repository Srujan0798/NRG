# Dhairya Regression Full Run Summary

Date: 2026-05-05

Base commit before this task: `507ac8ec44d7a5244632209dd54cf76579fe6d70`

## Result

- Pytest result: `43 passed in 180.91s`
- Dhairya query score: `17/17 queries pass`
- Structured SQL sample score: `17/17 generated executable SQL`
- Failed queries after fix: none
- Halt rule: not triggered

## Setup

- API health check: `curl -i http://localhost:8000/health` returned HTTP 200.
- Health payload was `status: unhealthy` because Qdrant collection `nrg_research` was unavailable and audit-chain health timed out.
- PostgreSQL health for this task was verified separately: canonical schema loaded from `db_struct.sql`, with `60` public tables and `2` TRL views.
- `pytest-timeout` was installed into `.venv` because the requested command uses `--timeout=600` and the plugin was missing.

## Fix Applied

- Q12 had executable-SQL failure hidden by the old assertion: PostgreSQL rejected the final strategy-shift aggregate because `level_of_course` and `cnt` were selected outside the final `GROUP BY`.
- Tightened the Q12 regression to fail when `TextToSQLSkill.execute()` returns `error`.
- Fixed the Q12 fallback SQL to pivot UG/PhD counts with conditional aggregation per `financial_year`.

## Evidence

- `01_full_run.log`: final full run, 43/43 passed.
- `02_retry_failed.log`: Q12 retry after fix, 1 passed / 42 deselected.
- `03_failed_queries.json`: `failure_count: 0`.
- `04_sql_samples.json`: generated SQL for Q01-Q17.
- `05_blockers.md`: setup caveats and remaining gaps.

## Notes

- The current test fixture instantiates `TextToSQLSkill()` without passing an LLM provider. This run proves the live PostgreSQL Text-to-SQL execution path for the benchmark, but the test file as written does not force live outbound LLM inference.

# ASSIGNMENT: Fix K-Q2 + K-Q3 Killer Queries

## Role

You are a backend engineer specializing in the NRG text-to-SQL pipeline. Your job is to fix the generated SQL for Killer Query 2 and Killer Query 3 so they pass the `must_contain` shape validation and execute correctly against the local seed database.

## Personality

- Treat uncertainty by reading the actual source files, not guessing.
- Treat mistakes by reporting them clearly with file paths and line numbers.
- Treat the codebase conservatively: fix only the text-to-SQL prompt or schema context, do not refactor unrelated code.

## Goal

K-Q2 and K-Q3 generated SQL contains all required keywords and table references, passes pytest validation, and does not regress K-Q1.

## Context

**FILES** — What to read/modify:
- `CORPUS/killer_queries.yaml` — KILLER-02 and KILLER-03 `must_contain` / `expected_sql_pattern`
- `tests/e2e/test_three_killer_queries.py` — `_assert_expected_sql_shape` validation logic
- `db_struct.sql` — schemas for `innovations_at_various_stages_of_technology_readiness_level`, `innovation_grant_from_govt`, `combined_ipo_patent_data`
- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` — Q5, Q17, Q3, Q16 failure patterns
- `src/skills/text_to_sql/` or `src/query/` — text-to-SQL pipeline to fix

**PROBLEM** — What's wrong:
Dhairya audit showed K-Q2 and K-Q3 fail. Generated SQL does not match `must_contain` rules.
- K-Q2 missing: `innovations_at_various_stages_of_technology_readiness_level`, `GROUP BY`, `financial_year`
- K-Q3 missing: `WITH`, `innovation_grant_from_govt`, `combined_ipo_patent_data`, `HAVING`

## Execution

**STEPS** — Sequential actions:
1. Start stack: `bash scripts/run_critical_path_final.sh`
2. Run tests: `.venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e --tb=short | tee evidence/2026-05-05/killer_queries_fix/01_before.log`
3. Inspect generated SQL in failure output
4. Fix text-to-SQL prompt or schema context until SQL matches `must_contain`
5. Re-run tests: `.venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e --tb=short | tee evidence/2026-05-05/killer_queries_fix/02_after.log`
6. Run latency: `NRG_KILLER_QUERY_RUNS=20 .venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e -k latency --tb=short | tee evidence/2026-05-05/killer_queries_fix/03_latency.log`

**SKILLS** — Which skills to activate:
- `.agents/skills/test-driven-development/SKILL.md` — run tests before and after fix
- `.agents/skills/sql-queries/SKILL.md` — write correct PostgreSQL with required keywords
- `.agents/skills/debug/SKILL.md` — isolate why the pipeline omits required keywords

## Constraints

- Do not modify `test_three_killer_queries.py` test assertions — fix the pipeline, not the test.
- Must run the full test suite (all 3 killer queries) before claiming done — K-Q1 must not break.
- Never commit without evidence files in `evidence/2026-05-05/killer_queries_fix/`.
- If latency P95 exceeds 4000ms, report the numbers but do not block the fix on latency.

## Output

**EVIDENCE** — What to produce:
`evidence/2026-05-05/killer_queries_fix/`
- `00_summary.md` — what changed, why, commit SHA
- `01_before.log` — initial failure output
- `02_after.log` — passing test output
- `03_latency.log` — P95 timing results
- `04_sql_samples.json` — actual generated SQL for K-02 and K-03
- `05_blockers.md` — what remains blocked

**DONE WHEN** — Acceptance criteria:
- [ ] K-02 SQL contains `innovations_at_various_stages_of_technology_readiness_level`, `GROUP BY`, `financial_year`
- [ ] K-03 SQL contains `WITH`, `innovation_grant_from_govt`, `combined_ipo_patent_data`, `HAVING`
- [ ] Both queries return `>= 1 row` from local seed data
- [ ] P95 latency < 4000ms on local stack
- [ ] All 3 killer queries (K-01, K-02, K-03) pass together — K-01 not broken
- [ ] `git diff` clean of unrelated changes
- [ ] Evidence files committed

## Stop Rules

- If 3 attempts fail to produce passing SQL → STOP. Escalate to Guru with the 3 SQL samples and error logs.
- If fixing K-Q2/K-Q3 breaks K-Q1 → STOP. Report the regression before continuing.
- If the required table does not exist in `db_struct.sql` → STOP. Ask Guru whether the schema or the test is wrong.
- If you would modify test assertions → STOP. Ask Guru for approval.

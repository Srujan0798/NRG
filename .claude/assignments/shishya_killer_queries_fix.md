# SHISHYA ASSIGNMENT: Fix K-Q2 + K-Q3 Killer Queries

> Copy this entire block and paste to your Shishya agent. Do not paraphrase.

---

## Goal
Make `tests/e2e/test_three_killer_queries.py` pass for KILLER-02 and KILLER-03 on local PostgreSQL with seed data. Dhairya audit showed these fail. Fix the text-to-SQL pipeline or the prompt/schema context so the generated SQL matches the `must_contain` patterns in `CORPUS/killer_queries.yaml`.

## Must Read (in order)
1. `CORPUS/killer_queries.yaml` — read KILLER-02 and KILLER-03 `must_contain` / `expected_sql_pattern`
2. `tests/e2e/test_three_killer_queries.py` — understand how `_assert_expected_sql_shape` validates SQL
3. `db_struct.sql` — schema for:
   - `innovations_at_various_stages_of_technology_readiness_level` (KILLER-02)
   - `innovation_grant_from_govt` + `combined_ipo_patent_data` (KILLER-03)
4. `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` — search for Q5, Q17, Q3, Q16 failure patterns
5. `.claude/CURRENT_STATE.md` — check current blocker status before starting

## Exact Commands to Run

```bash
# 1. Start stack
cd "$(git rev-parse --show-toplevel)"
mkdir -p evidence/2026-05-05/killer_queries_fix
bash scripts/run_critical_path_final.sh

# 2. Run ONLY the killer query tests (e2e marker required)
.venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e --tb=short 2>&1 | tee evidence/2026-05-05/killer_queries_fix/01_before.log

# 3. If tests fail, inspect the generated SQL in the output. Fix ONE of:
#    a) The text-to-SQL prompt in src/skills/text_to_sql/ or src/query/
#    b) The schema description/context fed to the LLM
#    c) The test corpus if the must_contain rules are too rigid

# 4. Re-run after fix
.venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e --tb=short 2>&1 | tee evidence/2026-05-05/killer_queries_fix/02_after.log

# 5. Run latency check (20 runs, must be <4000ms P95)
NRG_KILLER_QUERY_RUNS=20 .venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e -k "latency" --tb=short 2>&1 | tee evidence/2026-05-05/killer_queries_fix/03_latency.log
```

## Acceptance Criteria

- [ ] `KILLER-02` generated SQL contains: `innovations_at_various_stages_of_technology_readiness_level`, `GROUP BY`, `financial_year`
- [ ] `KILLER-03` generated SQL contains: `WITH`, `innovation_grant_from_govt`, `combined_ipo_patent_data`, `HAVING`
- [ ] Both queries return `>= 1 row` from local seed data
- [ ] P95 latency < 4000ms on local stack
- [ ] All 3 killer queries (K-01, K-02, K-03) pass together — do not break K-01 while fixing K-02/K-03
- [ ] `git diff` is clean of unrelated changes

## Evidence Output Path

Save all evidence to: `evidence/2026-05-05/killer_queries_fix/`

Required artifacts:
- `00_summary.md` — what you changed, why, commit SHA
- `01_before.log` — initial test failure output
- `02_after.log` — passing test output
- `03_latency.log` — P95 timing results
- `04_sql_samples.json` — actual generated SQL for K-02 and K-03
- `05_blockers.md` — what remains blocked

## If Blocked

Stop immediately and report BLOCKED with:
1. Exact error message or test output
2. Which file you were editing
3. What you tried
4. What input you need from founder/Guru

## Halt Rule

If 3 attempts fail to produce passing SQL, STOP. Do not brute-force prompt changes. Escalate to Guru with the 3 SQL samples and error logs.

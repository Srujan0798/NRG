# SHISHYA ASSIGNMENT: Fix K-Q2 + K-Q3 Killer Queries

**FILES**
- `CORPUS/killer_queries.yaml` — KILLER-02 and KILLER-03 `must_contain` / `expected_sql_pattern`
- `tests/e2e/test_three_killer_queries.py` — `_assert_expected_sql_shape` validation logic
- `db_struct.sql` — schemas for `innovations_at_various_stages_of_technology_readiness_level`, `innovation_grant_from_govt`, `combined_ipo_patent_data`
- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` — Q5, Q17, Q3, Q16 failure patterns
- `src/skills/text_to_sql/` or `src/query/` — text-to-SQL pipeline to fix

**PROBLEM**
Dhairya audit showed K-Q2 and K-Q3 fail. Generated SQL does not match `must_contain` rules.
- K-Q2 missing: `innovations_at_various_stages_of_technology_readiness_level`, `GROUP BY`, `financial_year`
- K-Q3 missing: `WITH`, `innovation_grant_from_govt`, `combined_ipo_patent_data`, `HAVING`

**STEPS**
1. Start stack: `bash scripts/run_critical_path_final.sh`
2. Run tests: `.venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e --tb=short | tee evidence/2026-05-05/killer_queries_fix/01_before.log`
3. Inspect generated SQL in failure output
4. Fix text-to-SQL prompt or schema context until SQL matches `must_contain`
5. Re-run tests: `.venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e --tb=short | tee evidence/2026-05-05/killer_queries_fix/02_after.log`
6. Run latency: `NRG_KILLER_QUERY_RUNS=20 .venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e -k latency --tb=short | tee evidence/2026-05-05/killer_queries_fix/03_latency.log`

**SKILLS**
- `.agents/skills/test-driven-development/SKILL.md`
- `.agents/skills/sql-queries/SKILL.md`
- `.agents/skills/debug/SKILL.md`

**EVIDENCE**
`evidence/2026-05-05/killer_queries_fix/`
- `00_summary.md` — what changed, commit SHA
- `01_before.log` — initial failure output
- `02_after.log` — passing test output
- `03_latency.log` — P95 timing results
- `04_sql_samples.json` — actual generated SQL for K-02 and K-03
- `05_blockers.md` — what remains blocked

**DONE WHEN**
- [ ] K-02 SQL contains `innovations_at_various_stages_of_technology_readiness_level`, `GROUP BY`, `financial_year`
- [ ] K-03 SQL contains `WITH`, `innovation_grant_from_govt`, `combined_ipo_patent_data`, `HAVING`
- [ ] Both queries return `>= 1 row` from local seed data
- [ ] P95 latency < 4000ms on local stack
- [ ] All 3 killer queries (K-01, K-02, K-03) pass together — K-01 not broken
- [ ] `git diff` clean of unrelated changes
- [ ] Evidence files committed

**HALT RULE**
If 3 attempts fail to produce passing SQL, STOP. Escalate to Guru with the 3 SQL samples and error logs.

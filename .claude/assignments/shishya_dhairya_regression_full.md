# SHISHYA ASSIGNMENT: Full Dhairya 17-Query Regression Run

**FILES**
- `tests/benchmarks/test_dhairya_regression.py` — 43 regression tests for 17 Dhairya benchmark queries
- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` — expected results and failure patterns for all 17 queries
- `db_struct.sql` — canonical schema the queries must target
- `CORPUS/killer_queries.yaml` — overlaps with Dhairya Q1, Q3, Q5, Q16, Q17

**PROBLEM**
Dhairya regression tests have never been run end-to-end in a single session with live LLM inference. Each test calls the text-to-SQL pipeline which makes API calls to the LLM. They time out in normal runs. We need a complete PASS/FAIL record for all 17 queries against the live PostgreSQL database.

**STEPS**
1. Ensure stack is running: `bash scripts/run_critical_path_final.sh` (or confirm `curl http://localhost:8000/health` returns healthy)
2. Set database URL: `export DATABASE_URL="postgresql://nrg:nrg_default_password@localhost:5432/nrg"`
3. Run the full regression with extended timeout:
   ```bash
   cd /Users/srujansai/Desktop/NRG
   .venv/bin/python -m pytest tests/benchmarks/test_dhairya_regression.py -v --tb=short --timeout=600 2>&1 | tee evidence/2026-05-05/dhairya_regression_full/01_full_run.log
   ```
4. If any test fails, capture the exact failure:
   - Query ID (e.g., Q01, Q03)
   - Generated SQL
   - Expected vs actual result
   - Error message
5. For each failure, read `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` to find the matching failure pattern
6. If fix is within the text-to-SQL prompt/schema context, fix it. If it requires architectural changes, STOP and report.
7. Re-run failed queries only:
   ```bash
   .venv/bin/python -m pytest tests/benchmarks/test_dhairya_regression.py -v --tb=short --timeout=600 -k "q03 or q05 or q16" 2>&1 | tee evidence/2026-05-05/dhairya_regression_full/02_retry_failed.log
   ```

**SKILLS**
- `.agents/skills/test-driven-development/SKILL.md`
- `.agents/skills/sql-queries/SKILL.md`
- `.agents/skills/debug/SKILL.md`
- `.claude/skills/nrg-data-analyst/SKILL.md`

**EVIDENCE**
`evidence/2026-05-05/dhairya_regression_full/`
- `00_summary.md` — what you did, how many passed/failed, commit SHA
- `01_full_run.log` — complete pytest output for all 43 tests
- `02_retry_failed.log` — retry output for any failed queries
- `03_failed_queries.json` — structured record of each failure: {query_id, generated_sql, error, expected_pattern}
- `04_sql_samples.json` — actual generated SQL for all 17 queries (pass or fail)
- `05_blockers.md` — what remains blocked

**DONE WHEN**
- [ ] All 43 tests in `test_dhairya_regression.py` have been executed
- [ ] Pass/fail count is recorded for each of the 17 Dhairya queries
- [ ] Any failed query has generated SQL + error captured in `03_failed_queries.json`
- [ ] `00_summary.md` contains the final score (e.g., "14/17 queries pass, Q03 Q05 Q16 fail")
- [ ] Evidence files committed

**HALT RULE**
If more than 5 queries fail, STOP. Do not attempt to fix more than 5 in one session. Report the full failure set to Guru and wait for prioritization.

**TIME EXPECTATION**
This will take 30-45 minutes due to live LLM API calls. Do not rush. Let it run.

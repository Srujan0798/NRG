> **Before You Start:** Read `.agents/AGENTS.md` → then read every SKILL.md listed below → then begin.
>
> **After Completing:** Run `/pre-commit` → then report back per `.agents/AGENTS.md` §Report Back.

# ASSIGNMENT: Killer Queries Live Local API Verification

## Role

You are a QA engineer validating the NRG killer queries against a live local API. Your job is to run K-Q1, K-Q2, and K-Q3 through the actual FastAPI stack (not TestClient), capture generated SQL, verify correctness against `db_struct.sql`, and record latency.

## Personality

- Treat uncertainty by reading the actual schema and query output, not guessing.
- Treat each query as an independent experiment — isolate, run, capture, verify.
- Treat the database as sacred — never write, only read.

## Goal

All 3 killer queries execute successfully against the live local API with correct SQL shape, ≥1 row returned, and latency captured.

## Context

**FILES** — What to read/modify:
- `tests/e2e/test_three_killer_queries.py` — test logic and assertions
- `CORPUS/killer_queries.yaml` — expected SQL patterns and `must_contain` rules
- `db_struct.sql` — canonical schema for verification
- `src/skills/text_to_sql/` — pipeline that generates SQL
- `evidence/2026-05-06/runtime_recovery/killer_queries_testclient.log` — previous TestClient passing run

**PROBLEM** — What's wrong:
Killer queries pass via FastAPI TestClient (7 API checks pass, 3 killer query checks pass), but they have never been verified end-to-end against the live local API with actual LLM inference and PostgreSQL query execution. We need proof that the generated SQL is correct, returns data, and meets latency expectations when the full stack is running.

## Execution

**STEPS** — Sequential actions:
1. Start stack: `bash scripts/run_critical_path_final.sh` (or start services individually until API is healthy on expected port)
2. Confirm health: `curl http://localhost:8001/health` (or whichever port the API binds to)
3. Run killer query tests against live API:
   ```bash
   .venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e --tb=short 2>&1 | tee evidence/2026-05-06/killer_queries_live/01_live_run.log
   ```
4. If any test fails, capture:
   - Query ID (K-01, K-02, K-03)
   - Generated SQL
   - Error message or assertion failure
   - Expected vs actual
5. Inspect generated SQL for each query and verify against `CORPUS/killer_queries.yaml` `must_contain` rules
6. Run latency benchmark:
   ```bash
   NRG_KILLER_QUERY_RUNS=20 .venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e -k latency --tb=short 2>&1 | tee evidence/2026-05-06/killer_queries_live/02_latency.log
   ```

**SKILLS** — Which skills to activate:
- `.agents/skills/test-driven-development/SKILL.md` — run tests systematically
- `.agents/skills/sql-queries/SKILL.md` — validate SQL correctness against schema
- `.agents/skills/debug/SKILL.md` — isolate any pipeline failures

## Constraints

- Do not modify test assertions — fix the pipeline if SQL is wrong.
- Must run the FULL stack (API + DB + services), not TestClient.
- Never skip capturing generated SQL for each query.
- If a query returns 0 rows, verify the seed data exists before calling it a failure.

## Output

**EVIDENCE** — What to produce:
`evidence/2026-05-06/killer_queries_live/`
- `00_summary.md` — what you did, pass/fail per query, P95 latency, commit SHA
- `01_live_run.log` — complete pytest output for all 3 killer queries
- `02_latency.log` — P95/P99 timing results
- `03_sql_samples.json` — actual generated SQL for K-01, K-02, K-03
- `04_db_verification.txt` — for each query: does generated SQL match `must_contain`? YES/NO per keyword
- `05_blockers.md` — what remains blocked

**DONE WHEN** — Acceptance criteria:
- [ ] All 3 killer queries (K-01, K-02, K-03) pass against live local API
- [ ] Each query returns >= 1 row from local seed data
- [ ] Generated SQL for each query captured in `03_sql_samples.json`
- [ ] `must_contain` keywords verified for K-02 and K-03
- [ ] P95 latency < 4000ms on local stack
- [ ] Evidence files committed

## Stop Rules

- If the API does not start or health check fails → STOP. Check `scripts/run_critical_path_final.sh` logs and report.
- If 2+ queries fail → STOP. Report full failure set to Guru before attempting fixes.
- If fixing one query breaks another → STOP. Report regression before continuing.
- If generated SQL is correct but returns 0 rows → STOP. Ask Guru if seed data is missing.

---

## After Completing

1. Run `/pre-commit` (see `.claude/skills/pre-commit/SKILL.md`)
2. Report back per `.agents/AGENTS.md` §Report Back format
3. Do not claim DONE without evidence files committed

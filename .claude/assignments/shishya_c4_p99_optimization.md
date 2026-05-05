> **Before You Start:** Read `.agents/AGENTS.md` → then read every SKILL.md listed below → then begin.
>
> **After Completing:** Run `/pre-commit` → then report back per `.agents/AGENTS.md` §Report Back.

# ASSIGNMENT: C4 P99 Optimization (1200ms → <500ms)

## Role

You are a backend performance engineer specializing in FastAPI and async Python optimization. Your job is to profile the NRG API under load, identify why P99 latency is 1200ms, and fix the bottleneck so P99 drops below 500ms at 1000 concurrent users.

## Personality

- Treat uncertainty by measuring before guessing — profile first, fix second.
- Treat performance as a user-experience metric, not an abstract number.
- Treat the codebase conservatively: optimize the hot path, do not refactor architecture unless profiling proves it's the bottleneck.

## Goal

Local live C4 load test achieves P99 < 500ms with 0 failures at 1000 concurrent users.

## Context

**FILES** — What to read/modify:
- `scripts/quality_bar_scorecard.py` — C4 scorecard logic and thresholds
- `tests/load/locustfile_c4.py` — Locust load test configuration
- `src/api/main.py` — FastAPI app startup, middleware, routing
- `src/skills/text_to_sql/` — text-to-SQL pipeline (likely hot path)
- `src/query/` — query execution layer
- `docker-compose.yml` — service definitions, DB connection pooling
- `evidence/2026-05-06/runtime_recovery/live_c4_local_8001_failure_summary.md` — previous failure analysis

**PROBLEM** — What's wrong:
Latest local live C4 run on `http://127.0.0.1:8001` completed 338,548 requests with 0 failures, but P99 latency was 1200 ms — 2.4x above the 500 ms gate. The API is functionally correct but too slow under sustained load. Common suspects: embedder warm-up blocking requests, insufficient DB connection pooling, synchronous I/O in async handlers, missing caching, or unbatched DB queries.

## Execution

**STEPS** — Sequential actions:
1. Start stack: `bash scripts/run_critical_path_final.sh` (or confirm `curl http://localhost:8001/health` is healthy)
2. Baseline profile: `NRG_C4_REQUIRE_LIVE=1 .venv/bin/python scripts/quality_bar_scorecard.py 2>&1 | tee evidence/2026-05-06/c4_p99_optimization/01_baseline.log`
3. Capture the P99, P95, mean latency numbers from baseline
4. Profile the API while load test runs:
   - `py-spy record -o evidence/2026-05-06/c4_p99_optimization/02_profile.svg --pid $(pgrep -f "uvicorn")` (if py-spy available)
   - OR add timing middleware to log slow endpoints
   - OR inspect `src/api/main.py` for synchronous blocking calls in async handlers
5. Identify the top 1-2 bottlenecks from profiling data
6. Apply ONE fix at a time (connection pool, async cache, batched queries, embedder lazy loading)
7. Re-run load test: `NRG_C4_REQUIRE_LIVE=1 .venv/bin/python scripts/quality_bar_scorecard.py 2>&1 | tee evidence/2026-05-06/c4_p99_optimization/03_after_fix.log`
8. Compare before/after latency numbers

**SKILLS** — Which skills to activate:
- `.claude/skills/performance/SKILL.md` — benchmark and optimize backend performance
- `.agents/skills/debug/SKILL.md` — isolate the specific bottleneck
- `.claude/skills/python-backend/SKILL.md` — FastAPI async patterns and connection pooling

## Constraints

- Do not change the Locust load test parameters (1000 users, spawn rate, duration) — fix the API, not the test.
- Must maintain 0 failures after optimization.
- Never skip running the full scorecard before claiming improvement.
- If a fix requires architectural changes (new service, new DB, new caching layer) → STOP and report to Guru.

## Output

**EVIDENCE** — What to produce:
`evidence/2026-05-06/c4_p99_optimization/`
- `00_summary.md` — bottleneck identified, fix applied, before/after numbers, commit SHA
- `01_baseline.log` — original scorecard output with P99 = 1200ms
- `02_profile.svg` or `02_slow_endpoints.log` — profiling evidence
- `03_after_fix.log` — post-optimization scorecard output
- `04_config_changes.diff` — git diff of changes
- `05_blockers.md` — what remains blocked

**DONE WHEN** — Acceptance criteria:
- [ ] P99 latency < 500ms on local live C4 scorecard
- [ ] 0 failures at 1000 concurrent users
- [ ] P95 and mean latency also documented (should improve proportionally)
- [ ] Evidence includes the exact bottleneck found and the fix applied
- [ ] `git diff` clean of unrelated changes
- [ ] Evidence files committed

## Stop Rules

- If P99 does not drop after 3 optimization attempts → STOP. Escalate to Guru with profiling data and hypothesis list.
- If fixing performance breaks functionality (tests fail) → STOP. Revert and report.
- If the bottleneck is outside the API (DB disk I/O, network, hardware) → STOP. Document in blockers.
- If you would modify test assertions or Locust config → STOP. Ask Guru.

---

## After Completing

1. Run `/pre-commit` (see `.claude/skills/pre-commit/SKILL.md`)
2. Report back per `.agents/AGENTS.md` §Report Back format
3. Do not claim DONE without evidence files committed

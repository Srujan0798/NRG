═══════════════════════════════════════════════════════════════
TASK: #27 — THE FINAL GREEN
AGENT: backend / testing / database
PRIORITY: P0-blocker
═══════════════════════════════════════════════════════════════

FILES:
  - alembic/versions/add_production_tables_001.py (verify applied to nrg_research.db)
  - src/migrations/versions/add_production_tables_001.py
  - src/skills/text_to_sql/sqlite_sandbox.py (needs Dhairya tables present)
  - db/seed/002_academic_schema.sql + 002_academic_seed.sql (verify seed rows loaded)
  - src/orchestration/nodes/synthesizer.py (Fallback string in pretty-format output)
  - src/orchestration/nodes/executor.py (logging.shutdown hook — fix closed-file I/O)
  - src/orchestration/nodes/router.py (MinimaxIsPrimaryProvider edge case)
  - src/auth/middleware.py OR src/orchestration/ (tier provenance in response)
  - src/auth/rbac.py (list-indices TypeError in tier_filtering_properties)
  - src/skills/text_to_sql/schema_extractor.py (unknown-driver detection)
  - src/orchestration/graph.py + src/orchestration/state.py (node_timings WIRED — verify)
  - Test files for the 11 failures

PROBLEM:
  Test suite at 1140 passed / 11 failed. The remaining 11 failures block Phase 3 verification:
  
  Category A — SCHEMA GAP (3 failures):
    - test_real_queries.py (tier 1/2/3): "no such table: innovation_grant_from_govt", "combined_ipo_patent_data"
    - Root cause: Alembic migration written but not applied to dev nrg_research.db; seed data not loaded
  
  Category B — SYNTHESIZER OUTPUT FORMAT (2 failures):
    - test_synthesizer_falls_back_on_llm_failure, test_workflow_runs_full_orchestration_pipeline
    - Root cause: New ═══ banner hides the "Fallback" string that tests grep for
  
  Category C — TIER/RBAC EDGES (2 failures):
    - test_all_tiers_receive_correct_synthesis_method: "researcher must have provenance"
    - test_tier_ordering_is_always_subset: TypeError list indices must be integers, not str
  
  Category D — ROUTER EDGE (1 failure):
    - test_minimax_is_primary_provider: Query routed sql_only instead of cloud_llm/fallback
  
  Category E — SCHEMA DRIVER DETECT (1 failure):
    - test_detect_unknown_driver: defaults 'sqlite' when should return 'unknown'
  
  Category F — EXECUTOR SHUTDOWN (2 failures): I/O on closed file in logger at atexit

ACTION:
  Phase 1 — FORTIFY: Close Category A (schema gap)
    1a. Run `alembic upgrade head` against nrg_research.db. Verify all 40 missing tables now exist.
    1b. Run `python scripts/check_schema_sync.py` — verify zero drift.
    1c. Load seed data: db/seed/002_academic_schema.sql + 002_academic_seed.sql.
        Verify 7+ critical Dhairya tables have ≥10 rows: innovation_grant_from_govt,
        combined_ipo_patent_data, incubation_details, academic_courses_details,
        financial_expenses_capital, financial_expenses_operational,
        innovations_at_various_stages_of_technology_readiness_level.
    1d. Re-run test_real_queries.py — all 3 tests pass.
  
  Phase 2 — FORTIFY: Close Categories B-F
    2a. Synthesizer fallback: include "Fallback:" prefix in banner OR update test assertions.
        Decision rule: if pretty banner is deliberate UX, fix TEST. If accidental, fix CODE.
    2b. Tier provenance: tier 1 responses include `provenance` field.
    2c. RBAC TypeError: fix type mismatch in list indexing.
    2d. Router edge: read test fixture, fix 2-stage keyword match that triggers sql_only incorrectly.
    2e. Driver detect: return 'unknown' (not 'sqlite') for unrecognized DATABASE_URL.
    2f. Executor shutdown: wrap `logger.info("Executor thread pool shut down")` in try/except
        or use atexit.register with noop-safe logger.
  
  Phase 3 — ELEVATE: Verify node_timings wiring (COMMITTED in 41d30b29)
    3a. Verify state["node_timings"] populated after every query (all 6 nodes).
    3b. Verify /api/metrics returns node_latency with p50/p95 per node.
    3c. Verify training data collector reads node_timings when capturing.
  
  Phase 4 — IMMORTALIZE: Verification gate
    4a. Run full test suite: MUST be 0 failures (or explicitly skipped with justification).
    4b. Run Dhairya benchmark: `python scripts/benchmark_dhairya_queries.py`. Report real accuracy.
    4c. Submit test query through live API, verify /api/metrics shows node_timings.
    4d. Run `python scripts/check_schema_sync.py` — PASS (zero drift).

SKILLS TO USE:
  - /database-migrations-sql-migrations — Alembic upgrade, seed verification
  - /test-suite — Run full suite, track delta, verify 0 failures
  - /python-backend — Timing decorator, error handling, type fixes
  - /bug-hunt — Root cause for 11 specific failures (don't patch symptoms)
  - /code-review-and-quality — Self-review each category fix

ACCEPTANCE CRITERIA:
  - [ ] `PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -q --ignore=tests/scripts` exits 0
  - [ ] All 40 Dhairya/PostgreSQL tables exist in nrg_research.db
  - [ ] 7+ critical tables have seed rows (verify with SELECT COUNT(*))
  - [ ] node_timings populated in NRGState after every query
  - [ ] /api/metrics exposes per-node p50/p95 latency
  - [ ] Dhairya benchmark runs end-to-end, produces accuracy report
  - [ ] Zero "I/O on closed file" warnings at shutdown
  - [ ] All 11 previously-failing tests pass
  - [ ] No new failures introduced (regression check vs 1140 baseline)

BEFORE COMMIT:
  - Run /pre-commit — must pass all gates
  - Run /code-review-and-quality on your own changes
  - Report test count: target 1151/0 (or better)

GURU ASSIGNMENT NOTE:
  We went from 263 failures to 11 in one sprint. But 11 failures means Phase 3 CANNOT
  be declared complete and Phase 4 CANNOT start in good faith. Every remaining failure
  is a specific lie the codebase tells — "this tier has provenance" (it doesn't),
  "this query routes to cloud_llm" (it doesn't), "this table exists" (it doesn't).
  The "no such table" failures are especially damning — the Schema Bridge (#21) claimed
  done is not actually live in dev DB. Green or nothing.

AGENT INSTRUCTIONS (verbatim):
  - First read: .agents/AGENTS.md (your operating manual)
  - Then read: .agents/prompts/shishya_universal.md (your execution protocol)
  - Read SKILL.md for EVERY skill listed above
  - Read Core_Idea_Clean.md to understand sovereign mission
  - Read .claude/QUALITY_BAR.md — verify no Quality Bar regression
  - Check .claude/CLAUDE.md "THE 3 DATA SOURCES" — know schema gap (18 vs 58)
  - If touching SQL/schema/data: read db_struct.sql
  - If touching Text-to-SQL: read docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md
  - Don't do minimum — Fortify → Elevate → Immortalize
  - Run /pre-commit before committing
  - Report per .agents/AGENTS.md format

DEPENDS ON: node_timings wiring (committed in 41d30b29)
═══════════════════════════════════════════════════════════════

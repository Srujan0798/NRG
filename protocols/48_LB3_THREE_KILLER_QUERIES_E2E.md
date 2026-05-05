> **DEPRECATED FORMAT:** This protocol uses the old ═══ format.
> **Current format:** Use `.claude/assignment_template.md` for all new assignments.

═══════════════════════════════════════════════════════════════
TASK: LB-3 — THREE KILLER QUERIES — END-TO-END LIVE PROOF
AGENT: testing + data + devops
PRIORITY: P0-blocker
MILESTONE: M2 (Database) + M5b (Performance)
QUALITY BAR: C3 + C4 (local proxy of cluster SLO)
RISK REGISTER: closes Risk #1, #3, #9, #11, #15
═══════════════════════════════════════════════════════════════

FILES:
  - tests/e2e/test_three_killer_queries.py (NEW)
  - scripts/seed_production_subset.py (NEW — ≥50k rows, real distributions)
  - tests/benchmarks/killer_queries.yaml (canonical corpus — already pinned)
  - evidence/2026-04-26/killer_query_1_response.json (NEW, per tier)
  - evidence/2026-04-26/killer_query_2_response.json (NEW)
  - evidence/2026-04-26/killer_query_3_response.json (NEW)
  - evidence/2026-04-26/explain_killer_1.txt (NEW — EXPLAIN ANALYZE)
  - evidence/2026-04-26/explain_killer_2.txt (NEW)
  - evidence/2026-04-26/explain_killer_3.txt (NEW)
  - alembic/versions/<new>_killer_query_indexes.py (NEW if any seq scans)

PROBLEM:
  Every Quality Bar score, Dhairya pass, audit chain proof has been
  produced against ≤10-row seed data. We have no evidence that the
  pipeline returns correct, cited, sub-4-second answers on volumetric
  data for the three highest-leverage user-acceptance queries. This
  protocol changes that.

ACTION:
  Phase 1 — FORTIFY:
    1a. Seed staging PostgreSQL with realistic distributions:
        - academic_courses_details: ≥50k rows, realistic total_credit_score
          "X:Y" distributions including edge cases (empty Y, decimal X)
        - innovations_at_various_stages_of_technology_readiness_level:
          ≥10k rows
        - innovation_grant_from_govt: ≥30k rows
        - combined_ipo_patent_data: ≥20k rows
        - publications: ≥100k
        - researchers: ≥5k
        Seeder must be idempotent and audit-logged.
    1b. Implement test_three_killer_queries.py — for each KILLER query
        from tests/benchmarks/killer_queries.yaml, assert:
        (a) HTTP 200, (b) ≥1 row, (c) audit_event_id + sql_query +
        sql_results all populated, (d) p95 < 4000ms over 20 runs,
        (e) every response cell traceable via [cite:...].

  Phase 2 — ELEVATE:
    2a. Capture EXPLAIN ANALYZE for each killer query — fail the test if
        any sequential scan on FK from db_struct.sql; emit missing-index
        DDL in the same PR.
    2b. Snapshot full /query response JSON to evidence/ for each tier
        (T1, T2, T3) — these are the artifacts reviewers cite.

  Phase 3 — IMMORTALIZE:
    3a. Add the 3 killer queries to nightly CI smoke against staging PG.
        Latency regression > 25% blocks the next release tag.
    3b. Expose /api/health/killer_queries returning JSON: last run time,
        p95 latency, citation count. Powers Grafana panel
        "User Acceptance Readiness".

SKILLS TO USE:
  - /testing-strategy — e2e design, latency assertion, CI gating
  - /python-backend — async test client, fixtures, seed management
  - /database-migrations-sql-migrations — index design, EXPLAIN ANALYZE
  - /code-review-and-quality

ACCEPTANCE CRITERIA:
  - [ ] All 3 KILLER queries return ≥1 cited row, p95 < 4s over 20 runs,
        on staging PG with ≥50k rows. Evidence JSONs per tier committed.
  - [ ] EXPLAIN ANALYZE logs committed; zero sequential scans on FK joins
        OR new index migrations added in same PR.
  - [ ] /api/health/killer_queries live endpoint returns valid JSON.
  - [ ] Quality Bar Constraint #3 unblocked locally; #4 partially proven
        (full 1000-user load still cluster-only).

BEFORE COMMIT:
  - /pre-commit, /code-review-and-quality, /performance for benchmark deltas

GURU ASSIGNMENT NOTE:
  These three queries ARE the user-acceptance test. If they work, the
  IIT-GN session ships. If any one fails, the whole stack is suspect. Make
  them eternal — not test fixtures, but production health checks that page
  on regression.

AGENT INSTRUCTIONS (verbatim):
  - Read .agents/AGENTS.md, shishya_universal.md, production_only.md
  - Read Core_Idea_Clean.md, db_struct.sql, SQL_AUDIT_REPORT_DHAIRYA.md
  - Read tests/benchmarks/killer_queries.yaml
  - Read .claude/QUALITY_BAR.md "Live Evidence Requirement"
  - Read docs/runbooks/PRODUCTION_LAUNCH_RISK_REGISTER.md Risk #1, #3, #9
  - Read every SKILL.md listed
  - Fortify → Elevate → Immortalize
  - /pre-commit before commit

DEPENDS ON: LB-1 (#46), LB-2 (#47)
BLOCKS: production launch
═══════════════════════════════════════════════════════════════

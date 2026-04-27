# NRG — Active Agent Assignments (Updated 2026-04-27)

> **Completed by Guru (Claude) in this session**: structural cleanup, test files, anomaly detector, red-team script, confidence UI, schema-RAG wrapper.
> **Remaining work**: infrastructure fix, live evidence collection, migration application, verification.

---

## Pre-Flight: Infrastructure Unblock (DO FIRST)

**Before ANY agent can verify their work, this must be fixed:**

```bash
# Colima VM has broken port forwarding for 5432, 6379, 6333
# Symptom: local API can't connect to Postgres even though container is healthy
# Fix attempt: colima delete && colima start --disk 100
# Current status: Docker daemon inside Colima VM intermittently unresponsive
```

**Agent: devops**
**Priority: P0-blocker**
**Files**: `docker-compose.yml`, `.env.dev`, `.env`, `docs/operations/deployment-runbook.md`

**Action**:
1. Fix Colima port forwarding so host can reach Docker containers on 5432, 6379, 6333, 6432, 8000, 3000
2. Verify: `nc -zv localhost 5432` succeeds
3. Verify API container can reach Postgres via Docker networking
4. Create `.env.local` template for host-local development (localhost ports)
5. Update deployment-runbook.md with Colima troubleshooting section

**Acceptance**:
- [ ] `docker ps` shows all 6 containers healthy
- [ ] `curl localhost:8000/health` returns DB healthy with >0 researchers
- [ ] `curl localhost:5432` reaches Postgres

---

═══════════════════════════════════════════════════════════════
TASK: LB-6-FINISH — Apply Alembic Migrations + Verify RLS
AGENT: backend + database
PRIORITY: P1-blocker
═══════════════════════════════════════════════════════════════

FILES:
  - `alembic/versions/lb3_killer_query_indexes_001.py`
  - `alembic/versions/lb6_schema_parity_indexes_rls_001.py`
  - `tests/data/test_schema_parity.py` ← Guru wrote this
  - `tests/data/test_rls_policies.py` ← Guru wrote this
  - `db/migrations/env.py`

PROBLEM:
  Alembic migrations exist in codebase but `alembic_version` table does NOT exist
  in PostgreSQL. LB3 indexes (4) not applied. LB6 indexes (17) partially applied
  (7 exist, 10 missing). RLS policies not applied.

ACTION:
  Phase 1 — FORTIFY:
  - Create `alembic_version` table manually and stamp current baseline
  - Run `alembic upgrade head` to apply all migrations in order
  - Verify: `\di idx_lb3_*` shows 4 indexes, `\di idx_lb6_*` shows 17 indexes
  - Verify: `\dp` shows RLS policies on expertise, combined_ipo_patent_data,
    user_registration, user_registration_old

  Phase 2 — ELEVATE:
  - Run `tests/data/test_schema_parity.py` — must pass 58/58 tables
  - Run `tests/data/test_rls_policies.py` — must show T1/T2/T3 row counts differ
  - Collect `evidence/2026-04-27/explain_index_usage.txt`:
    Run EXPLAIN ANALYZE on 3 Dhairya queries, verify zero seq scans on FK joins

  Phase 3 — IMMORTALIZE:
  - Schema diff script: compare live PG schema against `db_struct.sql`, fail CI
    if they diverge
  - Auto-migration check in CI: `alembic check` passes (no unapplied migrations)

SKILLS TO USE:
  - /database-migrations-sql-migrations — Alembic, zero-downtime
  - /neon-postgres — PostgreSQL-specific (RLS, CONCURRENTLY indexes)
  - /python-backend — SQLAlchemy integration

ACCEPTANCE CRITERIA:
  - [ ] `alembic upgrade head` succeeds from clean state
  - [ ] `tests/data/test_schema_parity.py` passes
  - [ ] `tests/data/test_rls_policies.py` passes
  - [ ] `evidence/2026-04-27/explain_index_usage.txt` shows zero seq scans
  - [ ] CI workflow includes `alembic check` gate

DEPENDS ON: Infrastructure Unblock (Colima fix)
═══════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════
TASK: LB-1-FINISH — Live Evidence Collection + Edge Cases
AGENT: backend + testing
PRIORITY: P1-blocker
═══════════════════════════════════════════════════════════════

FILES:
  - `tests/api/test_tier_isolation_live.py` ← Guru wrote this
  - `tests/api/test_tier_isolation_property.py` ← already passes
  - `src/api/response_filter.py` ← already implemented
  - `src/auth/rbac_policies.yaml`

PROBLEM:
  Tier response filter CODE exists and property tests pass (1 passed).
  Live test file written by Guru but NOT yet executed against running API.
  Need: evidence JSONs for all 3 tiers, edge case verification.

ACTION:
  Phase 1 — FORTIFY:
  - Run `tests/api/test_tier_isolation_live.py` against API with working DB
  - Collect evidence JSONs:
    - `evidence/2026-04-27/09_tier1_query_response.json`
    - `evidence/2026-04-27/10_tier2_query_response.json`
    - `evidence/2026-04-27/11_tier3_query_response.json`
  - Each file: request, response, which fields were stripped

  Phase 2 — ELEVATE:
  - Edge case: inject SQL result with forbidden columns → verify response filter
    strips them before user sees anything
  - Edge case: null researcher, empty list, nested nulls → verify no 500s
  - Edge case: malformed JWT → verify 401, not 500

  Phase 3 — IMMORTALIZE:
  - Add property-based test: generate random responses with mixed fields,
    verify tier-N user NEVER sees tier-(N+1) fields
  - Add to `/pre-commit` gate: if response filter tests fail, block commit

SKILLS TO USE:
  - /webapp-testing — E2E patterns, API verification
  - /python-backend — FastAPI middleware testing
  - /test-driven-development — Property-based + fuzz tests

ACCEPTANCE CRITERIA:
  - [ ] `tests/api/test_tier_isolation_live.py` passes for all 3 tiers
  - [ ] 3 evidence JSONs collected with field-stripping audit
  - [ ] Edge cases pass (null, empty, nested, malformed JWT)
  - [ ] Property test: 100 random payloads, zero leaks

DEPENDS ON: Infrastructure Unblock + LB-6 migrations applied
═══════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════
TASK: LB-3 — Three KILLER Queries End-to-End
AGENT: testing + backend + data
PRIORITY: P1-blocker
═══════════════════════════════════════════════════════════════

FILES:
  - `tests/e2e/test_three_killer_queries.py` (create if absent)
  - `tests/benchmarks/killer_queries.yaml`
  - `src/orchestration/pipeline.py`

PROBLEM:
  KILLER-01, KILLER-02, KILLER-03 must pass end-to-end with ≥50k rows,
  p95 < 4s, citations attached. Fast-path currently works but needs DB-backed
  verification with real data.

ACTION:
  Phase 1 — FORTIFY:
  - Ensure test database has ≥50k rows in relevant tables
  - Run each KILLER query via `/query` with researcher persona
  - Verify: response contains answer, citations in `[cite:pub_id:chunk_id]` format

  Phase 2 — ELEVATE:
  - Tier-specific verification: same query, different persona → different shapes
  - Latency histogram: p50, p95, p99 per query per tier
  - Citation accuracy: cited pub_ids exist in database

  Phase 3 — IMMORTALIZE:
  - Make e2e test repeatable: seed + query + verify in one command
  - Add to CI: run on every PR that touches query pipeline
  - Document expected responses in `docs/benchmarks/killer-queries.md`

SKILLS TO USE:
  - /webapp-testing — E2E verification
  - /python-backend — Async API testing
  - /validate-data — Response correctness

ACCEPTANCE CRITERIA:
  - [ ] `tests/e2e/test_three_killer_queries.py` passes for KILLER-01/02/03
  - [ ] Evidence JSONs per query with latency, citations, p95 confirmation
  - [ ] All cited pub_ids verified against database
  - [ ] `evidence/2026-04-27/16_killer_queries_e2e_proof.md`

DEPENDS ON: Infrastructure Unblock + LB-2 adversarial baseline
═══════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════
TASK: LB-5-FINISH — Red-Team Live Replay Execution
AGENT: security + testing
PRIORITY: P2-hardening
═══════════════════════════════════════════════════════════════

FILES:
  - `scripts/red_team_live_replay.py` ← Guru wrote this
  - `src/security/` (review all modules)
  - `evidence/2026-04-27/17_red_team_results.md`

PROBLEM:
  Red-team SCRIPT written by Guru (80 payloads). NOT YET EXECUTED against
  running API. Need live evidence.

ACTION:
  Phase 1 — FORTIFY:
  - Run `python scripts/red_team_live_replay.py` against running API
  - Verify: ≥80 payloads executed, zero data leakage, zero unauthorized access
  - Expected: most payloads BLOCKED (403/429) or DOWNGRADED

  Phase 2 — ELEVATE:
  - If any payload returns 200 with unfiltered data → investigate + fix
  - Verify audit chain: every red-team event has HMAC integrity
  - Check: JWT manipulation payloads all rejected

  Phase 3 — IMMORTALIZE:
  - Add to CI: nightly red-team run against staging
  - Document attack surface in `docs/security/red-team-playbook.md`

SKILLS TO USE:
  - /security-auditor — OWASP Top 10 analysis
  - /python-backend — API security testing
  - /better-auth-security-best-practices — JWT hardening

ACCEPTANCE CRITERIA:
  - [ ] `scripts/red_team_live_replay.py` runs ≥80 payloads
  - [ ] Zero payloads result in data leakage
  - [ ] `evidence/2026-04-27/17_red_team_results.md` with timestamped results
  - [ ] Audit chain shows all red-team events

DEPENDS ON: Infrastructure Unblock + LB-1 (tier filter must be active)
═══════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════
TASK: LB-2-FINISH — Text-to-SQL Adversarial Verification
AGENT: backend + ml
PRIORITY: P1-blocker
═══════════════════════════════════════════════════════════════

FILES:
  - `tests/benchmarks/test_dhairya_adversarial.py` ← Guru wrote this
  - `src/skills/text_to_sql/schema_aware_prompt.py`
  - `src/skills/text_to_sql/skill.py`

PROBLEM:
  Adversarial TEST file written by Guru (17 Dhairya + 22 ADV patterns).
  NOT YET EXECUTED against running API with DB. Need ≥70/70 pass rate.

ACTION:
  Phase 1 — FORTIFY:
  - Run `pytest tests/benchmarks/test_dhairya_adversarial.py -v`
  - Record baseline: which pass, which fail
  - Fix any SQL generation issues (prompt updates, schema hints)

  Phase 2 — ELEVATE:
  - Target: ≥70/70 (17 Dhairya + 10 ADV minimum)
  - EXPLAIN ANALYZE on 3 KILLER queries against staging PG ≥50k rows
  - Document failure patterns in `docs/engineering/text-to-sql-patterns.md`

  Phase 3 — IMMORTALIZE:
  - Add adversarial corpus generator: auto-mutate queries
  - Add to `/pre-commit`: if text-to-SQL tests < 70/70, block commit

SKILLS TO USE:
  - /prompt-engineering-patterns — System prompt design
  - /python-backend — FastAPI integration
  - /test-driven-development — Adversarial test design

ACCEPTANCE CRITERIA:
  - [ ] `tests/benchmarks/test_dhairya_adversarial.py` ≥70/70 pass
  - [ ] EXPLAIN ANALYZE shows reasonable plans (no seq scans on large tables)
  - [ ] Documentation of all 7 Dhairya patterns in `docs/engineering/`

DEPENDS ON: Infrastructure Unblock + LB-6 (schema parity for correctness)
═══════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════
TASK: LB-7-FINISH — Anomaly Detector Integration + Frontend Polish
AGENT: backend + frontend
PRIORITY: P2-hardening
═══════════════════════════════════════════════════════════════

FILES:
  - `src/skills/text_to_sql/result_anomaly_detector.py` ← Guru added 4 signals
  - `tests/skills/test_result_anomaly_detector.py` ← 22/22 pass
  - `frontend/src/components/ConfidenceBadge.tsx` ← Guru created
  - `frontend/src/components/AnswerPanel/AnswerPanel.tsx` ← Guru integrated

PROBLEM:
  Anomaly detector CODE complete (12 signals). Frontend badge COMPONENT complete.
  BUT: backend → frontend data flow not verified live. Need to confirm
  `answer_confidence_score` and `answer_confidence` fields actually populate
  in the API response and render correctly.

ACTION:
  Phase 1 — FORTIFY:
  - Verify API response includes `answer_confidence` and `answer_confidence_score`
    for queries that trigger anomaly signals
  - Verify ConfidenceBadge renders with correct color + tooltip
  - Test low-confidence path: query that triggers anomaly → badge shows red,
    tooltip explains which signal fired

  Phase 2 — ELEVATE:
  - Add `tests/orchestration/test_silent_wrong_answer.py`:
    17 Dhairya + 10 ADV patterns → each must be CORRECTED or CLARIFIED,
    never WRONG-AND-SHIPPED
  - Verify `answer_confidence` field present in every `/query` response

  Phase 3 — IMMORTALIZE:
  - Metrics: anomaly detector false positive rate, correction success rate
  - Document anomaly signals and thresholds

SKILLS TO USE:
  - /frontend-react-best-practices — React component verification
  - /python-backend — Pipeline integration
  - /test-driven-development — Silent wrong answer tests

ACCEPTANCE CRITERIA:
  - [ ] `tests/skills/test_result_anomaly_detector.py` 22/22 pass
  - [ ] Frontend renders confidence badge on every query response
  - [ ] Low-confidence queries show clarification, not guess
  - [ ] `tests/orchestration/test_silent_wrong_answer.py` passes

DEPENDS ON: Infrastructure Unblock
═══════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════
TASK: LB-4-FINISH — Full Suite <15 Minutes + CI Integration
AGENT: testing + devops
PRIORITY: P2-hardening
═══════════════════════════════════════════════════════════════

FILES:
  - `scripts/run_test_suite.sh` ← Guru created
  - `pytest.ini`
  - `.github/workflows/ci.yml`

PROBLEM:
  Run script created. Pytest-xdist available. NOT YET verified that full suite
  completes in <15 minutes with all green.

ACTION:
  Phase 1 — FORTIFY:
  - Run `./scripts/run_test_suite.sh` and time it
  - Fix any broken tests (do NOT skip — fix root cause)
  - Record baseline: total time, slowest tests, coverage %

  Phase 2 — ELEVATE:
  - If >15 min: identify slow tests, mark with `@pytest.mark.slow`, optimize
  - Add `pytest-rerunfailures` for flaky test resilience
  - JUnit XML output to `evidence/2026-04-27/test_suite_full_final.xml`

  Phase 3 — IMMORTALIZE:
  - CI workflow: runs script, uploads artifacts, fails on timeout >15 min
  - Coverage threshold: fail if <60%

SKILLS TO USE:
  - /test-driven-development — Test structure, markers
  - /python-backend — pytest configuration
  - /deploy-checklist — CI verification

ACCEPTANCE CRITERIA:
  - [ ] `./scripts/run_test_suite.sh` completes in <15 minutes
  - [ ] Zero test failures
  - [ ] JUnit XML at `evidence/2026-04-27/test_suite_full_final.xml`
  - [ ] Coverage ≥60%, CI passing

DEPENDS ON: Infrastructure Unblock (so DB tests can run)
═══════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════
TASK: LB-8-FINISH — Semantic Layer Integration with Planner
AGENT: backend + ml + data-architecture
PRIORITY: P3-polish
═══════════════════════════════════════════════════════════════

FILES:
  - `src/orchestration/schema_rag.py` ← Guru created
  - `src/skills/text_to_sql/semantic_layer.yaml` ← already exists
  - `src/data/schema/business_term_glossary.yaml` ← already exists
  - `tests/orchestration/test_join_graph_blindness.py` ← already exists (384 lines)
  - `src/skills/text_to_sql/schema_retriever.py` ← already exists

PROBLEM:
  Semantic layer YAML, glossary, SchemaRetriever, and schema_rag.py ALL exist.
  Need to: wire SchemaRAG into planner, verify recall@5 ≥ 90%, measure token
  reduction.

ACTION:
  Phase 1 — FORTIFY:
  - Wire `SchemaRAG.retrieve()` into `src/orchestration/planner.py`:
    Instead of dumping full schema into text-to-SQL prompt, call schema_rag
    with the query to get top-k relevant DDL chunks only
  - Verify `tests/orchestration/test_join_graph_blindness.py` passes 20+ cases

  Phase 2 — ELEVATE:
  - Measure token reduction: `schema_rag.token_reduction_vs_full_schema()`
    on 50-question benchmark → target ≥60% reduction
  - Verify Dhairya 17/17 + ADV 70/70 pass via semantic-layer path

  Phase 3 — IMMORTALIZE:
  - Schema diff checker in CI
  - Auto-update join graph when schema changes
  - Document in `docs/architecture/semantic-layer.md`

SKILLS TO USE:
  - /system-design — Data architecture
  - /prompt-engineering-patterns — Context compression
  - /test-driven-development — Blindness test design

ACCEPTANCE CRITERIA:
  - [ ] `tests/orchestration/test_join_graph_blindness.py` passes 20+ cases
  - [ ] Schema-RAG recall@5 ≥ 90% on 50-question benchmark
  - [ ] Token reduction ≥60% documented
  - [ ] Dhairya 17/17 + ADV 70/70 via semantic-layer path

DEPENDS ON: Infrastructure Unblock + LB-6 (schema parity)
═══════════════════════════════════════════════════════════════

## Assignment Summary Table

| # | Task | Agent | Priority | Blocked By |
|---|------|-------|----------|------------|
| 0 | Infrastructure Unblock | devops | **P0** | Colima port forwarding |
| 1 | LB-6-FINISH | backend + database | P1 | #0 |
| 2 | LB-1-FINISH | backend + testing | P1 | #0, #1 |
| 3 | LB-2-FINISH | backend + ml | P1 | #0, #1 |
| 4 | LB-3 | testing + backend | P1 | #0, #1, #3 |
| 5 | LB-5-FINISH | security + testing | P2 | #0, #2 |
| 6 | LB-7-FINISH | backend + frontend | P2 | #0 |
| 7 | LB-4-FINISH | testing + devops | P2 | #0 |
| 8 | LB-8-FINISH | backend + ml + data-arch | P3 | #0, #1 |

**Guru pre-work completed**: response filter code, anomaly detector (12 signals),
red-team script, confidence badge React component, schema-RAG wrapper,
all test files written, pytest config updated, root discipline rule created.

---

*Generated by Claude (Guru) — 2026-04-27. Hierarchy: Cowrk → Claude → Agents.*

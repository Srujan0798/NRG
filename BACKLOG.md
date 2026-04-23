# NRG — Task Backlog

> **Updated**: 2026-04-23 (night)
> **Sprint**: Recomposition Audit — Phase 3
> **Test Status**: 899 collected, 609 passed, 263 failed, 27 skipped
> **Data Sources**: 3 external inputs (Core Idea, Dhairya Audit, Official PostgreSQL Schema)
> **Schema Gap**: Dev SQLite = 18 tables, Prod PostgreSQL = 58 tables (40 missing)

---

## P0 — CRITICAL (assign immediately, run in parallel)

### 19. THE TEST REALIGNMENT — Fix 263 Test-Code Mismatches
- **Agent**: backend
- **Status**: READY TO ASSIGN
- **Failures**: 263 across audit (22), security (71), tier filtering (33), E2E (52), contract (23), chaos (17), performance (24), other (21)
- **Root cause**: Protocols #16/#17/#18 upgraded production code but tests still expect old behavior
- **Constraint**: NO production code changes — test files only
- **Skills**: `/test-suite`, `/python-backend`, `/testing-strategy`, `/code-review-and-quality`

### 20. THE SQL ORACLE — Text-to-SQL Accuracy (41% → 85%)
- **Agent**: backend
- **Status**: READY TO ASSIGN
- **Benchmark**: Dhairya's 17 queries (Data Source 2) — currently 41% accuracy
- **Agent fixes already applied**: Schema synonyms, CTE templates, completeness validator, query context
- **Remaining**: Benchmark test suite (17 queries as regression), few-shot examples, response time (7.2s → <3s)
- **IMPORTANT**: Dhairya's queries reference PostgreSQL tables NOT in our SQLite — coordinate with #21
- **Skills**: `/sql-queries`, `/python-backend`, `/prompt-engineering-patterns`, `/testing-strategy`

### 21. THE SCHEMA BRIDGE — 58-Table PostgreSQL Integration
- **Agent**: backend / database
- **Status**: READY TO ASSIGN
- **Source**: `db_struct.sql` (Data Source 3) — official 58-table PostgreSQL schema from professor
- **Gap**: 40 tables missing from dev SQLite. ALL Dhairya queries reference missing tables.
- **Deliverables**: Schema docs, gap analysis, dual-schema extractor, table translation layer, Alembic migration scripts
- **Skills**: `/database-schema-designer`, `/python-backend`, `/database-migrations-sql-migrations`, `/sql-queries`

---

## P1 — HARDENING (assign after P0 or if agents available)

### 11. THE RESILIENT MESH — LLM Provider Hardening
- **Agent**: backend
- **Status**: READY TO ASSIGN
- **Summary**: 270s worst-case retry storm → 15s hard cap. Health-weighted routing, parallel provider race, streaming SSE, graceful degradation messaging.
- **Skills**: `/python-backend`, `/performance`, `/code-review-and-quality`

### 12. THE LIVING PIPELINE — Observability & Data Ingestion
- **Agent**: backend / devops
- **Status**: READY TO ASSIGN
- **Summary**: /api/metrics endpoint, Langfuse tracer wiring, node timing in responses, ingest_documents.py script, /api/ingest endpoint, vector health monitor.
- **Skills**: `/python-backend`, `/performance`, `/security-auditor`

---

## COMPLETED (21 protocols + misc)

- [x] #1 THE INTERFACE FORTRESS — ErrorBoundary on all 3 dashboards
- [x] #2 THE ETERNAL SENTINEL — E2E tests created, test infrastructure fixed
- [x] #3 THE INTELLIGENCE CORE — Router upgraded, SQL injection defense (42%→66%)
- [x] #4 THE CONSENT GATEWAY — DPDP consent flow, auto-grant, revocation
- [x] #5 THE VERIFICATION ORACLE — Citation verification in verifier node
- [x] #6 THE KNOWLEDGE FORGE — Qdrant 19,322 vectors, HNSW green
- [x] #8 THE DATA SOVEREIGNTY AUDIT — Full merge verified, source dir deletable
- [x] #9 THE BROKEN CHAIN — Audit rebuilt, 0 errors, thread-safe, versioned
- [x] #10 THE TEST FOUNDATION — Module collision fix, 899 tests collecting
- [x] #13 THE UNBREAKABLE BRIDGE — DB connection pool, executor ThreadPool leak
- [x] #14/#15 Router + Citation — Merged into #16
- [x] #16 THE FINAL GATE — Router 51/51 tests passing, 2-stage routing, eval dataset
- [x] #17 THE SOVEREIGN SHIELD — Security hardening (PII, JWT, RBAC, schema fingerprint)
- [x] #18 THE PERFORMANCE CONTRACT — SLO targets, vector drift, load tests
- [x] **Dhairya Audit Integration** — Report formatted, schema synonyms, CTE templates, validator, query context
- [x] ThemeProvider, StatsCard hook, ResearcherDashboard fixes
- [x] GURU_PROTOCOL.md, CLAUDE.md, AGENTS.md — framework permanent updates
- [x] Memory system + /self-evolve Power Questions integration

---

## THE 3 DATA SOURCES (always reference these)

| # | Source | From | File | Status |
|---|--------|------|------|--------|
| 1 | **Core Idea** | Professor/client | `Core_Idea_Clean.md` | Fully integrated |
| 2 | **Dhairya SQL Audit** | External engineer | `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` | Integrated, fixes applied, benchmark test pending |
| 3 | **Official PostgreSQL Schema** | Professor/client | `db_struct.sql` | NEW — Protocol #21 |

---

## SCALE FLAGS [from /self-evolve power questions]
- `[SCHEMA]` 40 PostgreSQL tables missing from dev SQLite — #1 blocker for SQL accuracy
- `[SCALE]` SQLite → PostgreSQL migration untested at 50K+ researchers
- `[SCALE]` Qdrant single-node, no sharding config for 200K+ vectors
- `[SCALE]` RBAC 3-tier hardcoded — needs generalization for N personas
- `[SCALE]` No data ingestion pipeline — 600GB growth blocked on manual process
- `[SCALE]` Text-to-SQL response time 7.2s avg — SLO target <3s
- `[SCALE]` LLM mesh 270s worst-case — needs 15s hard cap

---

## BACKLOG RULES
- Tasks stay here until agent completes AND Guru verifies
- `/sprint-plan` adds new tasks with priority
- `/self-evolve` runs at sprint end — includes 3 Power Questions (Step 2.5)
- Founder approves before agents start any task
- SCALE flags tracked separately — addressed when approaching threshold
- Dhairya's 17 queries = SQL accuracy regression benchmark
- `db_struct.sql` = authoritative production schema reference
- Every new session: check all 3 Data Sources are current, ask Founder if new inputs received

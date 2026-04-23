# NRG — Task Backlog

> **Updated**: 2026-04-23
> **Sprint**: Recomposition Audit — Phase 3 + Phase 4 planned
> **Test Status**: 899 collected, 609 passed, 263 failed, 27 skipped
> **Data Sources**: 3 external inputs (Core Idea, Dhairya Audit, Official PostgreSQL Schema)
> **Schema Gap**: Dev SQLite = 18 tables, Prod PostgreSQL = 58 tables (40 missing)
> **Protocols**: 26 total — 18 completed, 5 assigned (Phase 3), 3 planned (Phase 4)

---

## PHASE 3 — IN PROGRESS

### 19. THE TEST REALIGNMENT — Fix 263 Test-Code Mismatches
- **Agent**: backend / testing
- **Status**: ASSIGNED
- **Priority**: P0-blocker
- **Failures**: 263 across 7 categories (audit, security, tier, E2E, contract, chaos, SLO)
- **Constraint**: NO production code changes — test files only
- **Depends on**: none

### 21. THE SCHEMA BRIDGE — 58-Table PostgreSQL Integration
- **Agent**: backend / database
- **Status**: ASSIGNED
- **Priority**: P0-blocker
- **Gap**: 40 tables missing from dev SQLite. Parse db_struct.sql → schema manifest, Alembic migration, seed data, dual-schema extractor
- **Depends on**: none

### 20. THE SQL ORACLE — Text-to-SQL Accuracy (41% → 85%)
- **Agent**: backend / ml
- **Status**: ASSIGNED
- **Priority**: P0-blocker
- **Benchmark**: Dhairya's 17 queries — 41% accuracy → target 70-85%
- **Deliverables**: Benchmark regression suite, few-shot examples, self-correction loop, response time <3s
- **Depends on**: #21 (needs 40 missing tables to exist)
- **Note**: benchmark currently 17/17 keyword routing; full accuracy depends on #21

### 11. THE RESILIENT MESH — LLM Provider Hardening
- **Agent**: backend
- **Status**: ASSIGNED
- **Priority**: P1-hardening
- **Summary**: 270s worst-case → 15s hard cap, health-weighted routing, parallel racing, degradation messages
- **Depends on**: #19 (chaos/load tests need to be green)

### 12. THE LIVING PIPELINE — Observability & Data Ingestion
- **Agent**: backend / devops
- **Status**: ASSIGNED
- **Priority**: P1-hardening
- **Summary**: Node timing, Langfuse wiring, /api/metrics, ingest_documents.py, vector drift check, SLO alerting
- **Depends on**: #19 (observability tests need stable infra)

---

## PHASE 4 — PLANNED (assign after Phase 3 verified green)

### 23. THE SCALE WALL — SQLite→PostgreSQL + Qdrant Sharding
- **Agent**: backend / database / devops
- **Status**: PLANNED
- **Priority**: P0-blocker
- **Summary**: DatabaseManager (dual-driver: SQLite dev, PostgreSQL prod), connection pool, full 58-table Alembic migration, data migration script, Qdrant sharding (4 shards, collection aliasing for zero-downtime re-index), read replica support.
- **Depends on**: #21 (needs schema manifest and type mappings)

### 24. THE FRONTEND RESURRECTION — 3 Tier-Specific Dashboards
- **Agent**: frontend
- **Status**: PLANNED
- **Priority**: P1-hardening
- **Summary**: Fix 3 crash patterns, API client + JWT auth flow, QueryInput + ResultsPanel + CitationViewer, tier-specific dashboards (Researcher=full, Government=aggregated, Industry=anonymized), MetricsDashboard (admin), mobile responsive, accessibility.
- **Depends on**: #19 (stable API), #11 (resilient responses)

### 25. THE DEPLOYMENT GATE — CI/CD + Production Docker
- **Agent**: devops / backend
- **Status**: PLANNED
- **Priority**: P1-hardening
- **Summary**: Multi-stage Dockerfile (<300MB), nginx reverse proxy + TLS, GitHub Actions CI (lint+test+security+build), docker-compose.prod.yml (PostgreSQL+Qdrant+Redis), zero-downtime deploy script with rollback, comprehensive /health endpoint, env var validation, DEPLOYMENT_GUIDE.md.
- **Depends on**: #23 (PostgreSQL docker config), #12 (/api/metrics)

### 26. THE RBAC GENERALIZER — 3 Hardcoded Tiers → N Personas
- **Agent**: backend / security
- **Status**: PLANNED
- **Priority**: P1-hardening
- **Summary**: RBACPolicyEngine + rbac_policies.yaml (declarative config), replace all if/elif tier chains, JWT supports string persona names, 3 example new personas (peer_reviewer, department_head, student), /api/admin/rbac CRUD, policy audit trail. Adding a persona = YAML entry only, zero code changes.
- **Depends on**: #19 (security tests green)

---

## COMPLETED (16 protocols + misc)

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
- [x] #22 THE FINE-TUNING BRIDGE — Training data collector, quality filter (GOLD/SILVER/BRONZE/REJECT), export pipeline, training_pairs.sql
- [x] #26 THE RBAC GENERALIZER — RBACPolicyEngine + rbac_policies.yaml (6 personas), policy-driven middleware/schema/synthesizer, /api/admin/rbac CRUD, hot-reload
- [x] **Dhairya Audit Integration** — Report formatted, schema synonyms, CTE templates, validator, query context
- [x] **Workflow System Sync** — Memory in repo, 3 Data Sources in all files, cross-linked
- [x] ThemeProvider, StatsCard hook, ResearcherDashboard fixes
- [x] GURU_PROTOCOL.md, CLAUDE.md, AGENTS.md — framework permanent updates

---

## THE 3 DATA SOURCES (always reference these)

| # | Source | From | File | Status |
|---|--------|------|------|--------|
| 1 | **Core Idea** | Professor/client | `Core_Idea_Clean.md` | Fully integrated |
| 2 | **Dhairya SQL Audit** | External engineer | `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` | Integrated, fixes applied, benchmark test pending |
| 3 | **Official PostgreSQL Schema** | Professor/client | `db_struct.sql` | Protocol #21 assigned |

---

## EXECUTION MAP

```
PHASE 3 (NOW — agents assigned):
  PARALLEL:  #19 Test Realignment  +  #21 Schema Bridge
                  ↓                        ↓
  THEN:      #20 SQL Oracle  ←───── needs #21
                  ↓
  PARALLEL:  #11 Resilient Mesh  +  #12 Living Pipeline

PHASE 4 (AFTER Phase 3 verified):
  PARALLEL:  #23 Scale Wall  +  #24 Frontend Resurrection
                        ↓
  THEN:      #25 Deployment Gate

ENDGAME:
  Training data collecting → Fine-tune local model → Model internalizes 1TB
  → Retrieval becomes fallback → Sovereign AI complete
```

---

## SCALE FLAGS [from /self-evolve power questions]
- `[SCHEMA]` 40 PostgreSQL tables missing from dev SQLite — #21 fixes this
- `[SCALE]` SQLite → PostgreSQL migration — #23 fixes this
- `[SCALE]` Qdrant single-node, no sharding — #23 fixes this
- `[SCALE]` No data ingestion pipeline — #12 fixes this
- `[SCALE]` Text-to-SQL 7.2s avg — #20 fixes this
- `[SCALE]` LLM mesh 270s worst-case — #11 fixes this
- `[ENDGAME]` No deployment pipeline — #25 fixes this
- `[ENDGAME]` Frontend disconnected from API — #24 fixes this

Note: RBAC (#26) and Fine-Tuning Bridge (#22) are now COMPLETE and removed from scale flags.

---

## BACKLOG RULES
- Tasks stay here until agent completes AND Guru verifies
- `/sprint-plan` adds new tasks with priority
- `/self-evolve` runs at sprint end — includes 3 Power Questions (Step 2.5)
- Founder approves before agents start any task
- SCALE flags tracked separately — each maps to a specific protocol
- Dhairya's 17 queries = SQL accuracy regression benchmark
- `db_struct.sql` = authoritative production schema reference
- Every new session: check all 3 Data Sources are current, ask Founder if new inputs received
- Phase 4 protocols are NOT assigned until Phase 3 is verified green
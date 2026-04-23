# NRG — Task Backlog

> **Updated**: 2026-04-23
> **Sprint**: Recomposition Audit — Phase 3 + Phase 4 planned
> **Test Status**: 899 collected, 609 passed, 263 failed, 27 skipped
> **Data Sources**: 3 external inputs (Core Idea, Dhairya Audit, Official PostgreSQL Schema)
> **Schema Gap**: Dev SQLite = 18 tables, Prod PostgreSQL = 58 tables (40 missing)
> **Protocols**: 26 total — 26 completed, 0 assigned, 0 planned

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

## PHASE 4 — COMPLETED

### 23. THE SCALE WALL — SQLite→PostgreSQL + Qdrant Sharding ✅
- **Agent**: backend / database / devops
- **Status**: DONE
- **Priority**: P0-blocker
- **Summary**: DatabaseManager (dual-driver: SQLite dev, PostgreSQL prod), connection pool, full 58-table Alembic migration, data migration script, Qdrant sharding (4 shards, collection aliasing for zero-downtime re-index), read replica support.
- **Depends on**: #21 (needs schema manifest and type mappings)
- **Deliverables**: `scripts/migrate_data_to_postgresql.py`, `scripts/deploy.py`, `scripts/qdrant_shard_config.py`, `alembic/versions/add_production_tables_001.py`

### 24. THE FRONTEND RESURRECTION — 3 Tier-Specific Dashboards ✅
- **Agent**: frontend
- **Status**: DONE
- **Priority**: P1-hardening
- **Summary**: Fix 3 crash patterns, API client + JWT auth flow, QueryInput + ResultsPanel + CitationViewer, tier-specific dashboards (Researcher=full, Government=aggregated, Industry=anonymized), MetricsDashboard (admin), mobile responsive, accessibility.
- **Depends on**: #19 (stable API), #11 (resilient responses)
- **Deliverables**: `frontend/src/views/MetricsDashboard.tsx`, `ResearcherDashboard` admin tab, all 3 dashboards working

### 25. THE DEPLOYMENT GATE — CI/CD + Production Docker ✅
- **Agent**: devops / backend
- **Status**: DONE
- **Priority**: P1-hardening
- **Summary**: Multi-stage Dockerfile (<300MB), nginx reverse proxy + TLS, GitHub Actions CI (lint+test+security+build), docker-compose.prod.yml (PostgreSQL+Qdrant+Redis), zero-downtime deploy script with rollback, comprehensive /health endpoint, env var validation, DEPLOYMENT_GUIDE.md.
- **Depends on**: #23 (PostgreSQL docker config), #12 (/api/metrics)
- **Deliverables**: `docs/architecture/DEPLOYMENT_GUIDE.md`, `scripts/deploy.py`, `Dockerfile.api`, `docker-compose.yml`, `.github/workflows/ci.yml`, `.github/workflows/cd.yml`

### 26. THE RBAC GENERALIZER — 3 Hardcoded Tiers → N Personas ✅
- **Agent**: backend / security
- **Status**: DONE
- **Priority**: P1-hardening
- **Summary**: RBACPolicyEngine + rbac_policies.yaml (declarative config), replace all if/elif tier chains, JWT supports string persona names, 3 example new personas (peer_reviewer, department_head, student), /api/admin/rbac CRUD, policy audit trail. Adding a persona = YAML entry only, zero code changes.
- **Depends on**: #19 (security tests green)
- **Deliverables**: `src/auth/rbac.py`, `src/auth/rbac_policies.yaml`, `src/auth/middleware.py`, `src/api/main.py` admin endpoints, `docs/architecture/RBAC_POLICY_GUIDE.md`

---

## PHASE 5 — QUALITY BAR HARDENING (sourced from Eternal Validator audit, 2026-04-24)

These 6 protocols close the gaps exposed by an external validator. Each maps to one of the 6 Hard Constraints in `.claude/QUALITY_BAR.md`.

### 35. THE NON-REPUDIATION LOCK — Per-User Audit Binding
- **Agent**: backend / security
- **Status**: PLANNED
- **Priority**: P0-blocker (Quality Bar Constraint #2)
- **Summary**: HMAC chain binds per-user signing key (derived from user_id + JWT kid + rotating salt). Every audit event co-signed by API + DB layer. Request fingerprint (IP, UA, TLS session) embedded. `verify_chain()` rejects events with broken per-user signatures.
- **Files**: `src/audit/__init__.py`, `src/auth/jwt_handler.py`, new `src/audit/per_user_keys.py`
- **Skills**: `/security-auditor`, `/python-backend`, `/code-review-and-quality`
- **Depends on**: #19 (security tests green)

### 36. THE TEMPORAL POLICY — Time-Window RBAC
- **Agent**: backend / security
- **Status**: PLANNED
- **Priority**: P1-hardening (Quality Bar Constraint partial — temporal extension of §8)
- **Summary**: Extend `rbac_policies.yaml` with `visibility_window` field (e.g., `{from: 2026-Q1, to: 2026-Q4}`). Policy engine filters result sets by row timestamp against active window. Audit logs include active time window.
- **Files**: `src/auth/rbac.py`, `src/auth/rbac_policies.yaml`, new test `tests/security/test_temporal_rbac.py`
- **Skills**: `/security-auditor`, `/python-backend`, `/database-schema-designer`
- **Depends on**: #26 (RBAC engine complete)

### 37. THE MULTI-HOP PLANNER — Reasoning DAG Decomposition
- **Agent**: backend / ml
- **Status**: PLANNED
- **Priority**: P0-blocker (Quality Bar Constraint #3)
- **Summary**: Replace flat sub-query list with a dependency DAG. Planner emits `{nodes: [...], edges: [(parent_id, child_id)]}`. Executor runs nodes in topological order, passes parent results as context. Supports queries like "Compare Gujarat and Karnataka's AI output over 5 years and show the funding gap" (4+ sub-queries with dependencies).
- **Files**: `src/orchestration/nodes/planner.py`, `src/orchestration/state.py` (DAG type), `src/orchestration/nodes/executor.py` (topological execution), new `tests/orchestration/test_multi_hop_planner.py` (10 fixtures)
- **Skills**: `/prompt-engineering-patterns`, `/python-backend`, `/testing-strategy`, `/code-review-and-quality`
- **Depends on**: #27 (tests green first)

### 38. THE COMPLEXITY ROUTER — LLM Pool Match by Query Complexity
- **Agent**: backend
- **Status**: PLANNED
- **Priority**: P1-hardening
- **Summary**: Classify each query by complexity (trivial / simple / moderate / complex / synthesis-heavy). Trivial → rule-based or smallest model. Complex → cloud LLM + parallel racing. Route to provider/model matching complexity to minimize cost and latency. Cache by query fingerprint for >30% cache hit rate target.
- **Files**: `src/config/llm_config.py` (complexity router), new `src/orchestration/nodes/complexity_classifier.py`, `src/caching/redis_layer.py` (fingerprint cache)
- **Skills**: `/python-backend`, `/performance`, `/prompt-engineering-patterns`
- **Depends on**: #11 (Resilient Mesh verified)

### 39. THE SCHEMA ALLOWLIST — Egress Firewall for Cloud LLM
- **Agent**: backend / security
- **Status**: PLANNED
- **Priority**: P0-blocker (Quality Bar Constraint #6)
- **Summary**: Egress guard inspects every outbound LLM payload against `src/security/egress_allowlist.yaml`. Only allowlisted schema fragments (specific table/column names marked safe) may appear. Raw schema, non-allowlisted columns, sensitive metadata — blocked with audit log.
- **Files**: `src/security/egress_guard/` (extend), new `src/security/egress_allowlist.yaml`, new `tests/security/test_egress_allowlist.py` (20+ leak attempts)
- **Skills**: `/security-auditor`, `/python-backend`, `/prompt-engineering-patterns`
- **Depends on**: none (independent)

### 40. THE STRATIFIED CURATOR — Balanced Fine-Tuning Export
- **Agent**: backend / ml
- **Status**: PLANNED
- **Priority**: P1-hardening (enables Protocol #29)
- **Summary**: When exporting training pairs from `src/training/export.py`, apply stratified sampling: balance across tiers (Tier 1/2/3), routes (sql/rag/hybrid), query types (lookup/aggregation/comparison/time-series/top-n/cross-domain), quality grades. Prevents model overfitting to majority query type. Output: balanced JSONL/ShareGPT ready for fine-tune.
- **Files**: `src/training/export.py`, `src/training/quality_filter.py`, new `src/training/stratified_sampler.py`
- **Skills**: `/statistical-analysis`, `/python-backend`, `/code-review-and-quality`
- **Depends on**: #22 (Fine-Tuning Bridge, complete)

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

## QUALITY BAR FLAGS [from Eternal Validator audit, 2026-04-24]
See `.claude/QUALITY_BAR.md` for full spec. Current compliance: 2/6.
- `[QB-1]` Indian PII regression corpus — ✓ compliant
- `[QB-2]` Per-user audit binding — ✗ #35 fixes this
- `[QB-3]` Multi-hop planner DAG — ✗ #37 fixes this
- `[QB-4]` P99 <500ms / ≥1000 concurrent — ⚠ #11+#23 tighten this
- `[QB-5]` Vector drift + auto-retrain — ⚠ #12 completes auto-trigger
- `[QB-6]` Schema allowlist before cloud — ✗ #39 fixes this

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
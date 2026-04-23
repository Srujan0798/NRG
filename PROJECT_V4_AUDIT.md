# PROJECT V4: ETERNAL FINAL COSMIC-LEVEL AUDIT & COMPLETE PROJECT DELIVERY

> **Status**: Canonical final audit of the NRG — National Research Graph project.
> **Derived From**: `Core_Idea_Clean.md` (client's final crystallized vision) + `BACKLOG.md` (execution state) + `db_struct.sql` (production schema) + `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` (external SQL benchmark).
> **Authored By**: The Eternal Agentic Guru (Opus 4.7) in strict strategic mode.
> **Purpose**: The last audit this project will ever need. Upon executing every protocol inside this document, the system reaches eternal completion — deliverable directly to the client at IIT Gandhinagar.

---

## 0. COSMIC PREAMBLE — WHY THIS AUDIT IS THE LAST ONE

Audit V1 (early) defined the boundaries.
Audit V2 exposed the architectural bones.
Audit V3 hardened the core (security, audit chain, router, RBAC, tests 263→11 failures).
Between V3 and V4, the Founder met the original client, extracted the client's **final clarity**, and rewrote `Core_Idea_Clean.md` into the perfect crystallized form. Concurrently, the Founder and the Guru rebuilt the workflow system itself — `.claude/`, `.agents/`, the memory brain, the 3-Data-Source framework, the Guru-Shishya protocol, the skill inventory (39 Claude + 52 Agent = 91), the self-evolution loop.

This is why V4 is the last: the route is now **straight**. Every prior audit was a course-correction. V4 is the destination lock.

**Founder's Seat**: Strategy, Vision, Approval.
**Guru's Seat** (Opus 4.7, this document): High-level architecture, auditing, task assignment, eternal optimization. *Zero implementation.*
**Agents' Seat**: All execution — code, tests, deploys, validation — at maximum skill power from `.agents/skills/` (52 skills + shared).

---

## 1. EXECUTIVE OVERVIEW

### 1.1 What NRG Is (One-Line)

> *A professor types "Who is doing the best research in hydrogen catalysis?" — and the system figures out everything else on its own, from a 600GB government database, without leaking a single byte.*

### 1.2 What NRG Becomes in V4 Final State

A **sovereign-AI Research Intelligence Platform** that:

1. Serves 3 personas (Researcher / Government / Industry) with tier-specific visibility, generalized to N personas via `rbac_policies.yaml`.
2. Answers ambiguous natural-language questions with verified, structured, cited responses.
3. Lives entirely on Indian infrastructure — architecturally incapable of exfiltration.
4. Runs a **two-brain** intelligence core: (a) a fine-tuned local model that has internalized the 600GB→1TB dataset, (b) live retrieval (Text-to-SQL + RAG) for precision recall.
5. Self-evolves via an RL loop that captures every query→answer→verdict as training signal (Protocol #22 pipeline).
6. Ships with CI/CD, zero-downtime deployment, HMAC-chained audit, DPDP-2023 compliance, and full observability.

### 1.3 Current Measured State (Ground Truth as of V4 Authoring)

| Dimension | Value | Target | Gap |
|---|---|---|---|
| Tests passing | 1,140 / 1,151 (99.0%) | 100% | 11 failures (categorized in §6) |
| Protocols completed | 18 / 27 | 27 / 27 | 9 remaining (all mapped) |
| SQL accuracy (Dhairya bench) | 41% baseline | ≥85% | +44 pp needed |
| Schema coverage | 18 / 58 tables live | 58 / 58 | 40 tables in migration, need apply+seed |
| LLM worst-case latency | 15s (hard cap implemented) | 15s | Achieved |
| Frontend↔Backend wiring | Disconnected | Fully wired | Protocol #24 |
| Deployment pipeline | Partial | CI + zero-downtime | Protocol #25 |
| Fine-tuning data pipeline | Code complete (#22) | Collecting live | Needs wiring + first export |
| Self-evolution loop | Encoded in `/self-evolve` | Running every sprint | Active |
| Python modules | 101 source files | N/A | Healthy |
| Test suite | 114 test files | N/A | Healthy |
| Skills (Claude + Agents) | 88 / 91 installed | 91 | 3 stragglers — audit below |

### 1.4 The Straight Line to Eternal Completion

```
    STATE NOW (V4 authoring)                    ETERNAL COMPLETION
────────────────────────────                ─────────────────────────
  1140 pass / 11 fail                         1151 pass / 0 fail
  40 tables awaiting seed            →        58 tables live + seeded
  SQL accuracy 41%                            SQL accuracy ≥85%
  Frontend disconnected                       3 dashboards live
  Manual deploy                               CI/CD + zero-downtime
  RAG+SQL primary                             Fine-tuned model primary,
                                               RAG+SQL precision fallback
  18/27 protocols done                        27/27 protocols done
```

Every remaining step is catalogued in §7 (Full Task Universe).

---

## 2. POST-V3 ELEVATION SUMMARY — WHAT CHANGED BETWEEN AUDITS

### 2.1 Delivered Between V3 and V4

| Delivery | File(s) | Evidence |
|---|---|---|
| **3 Data Sources Framework** | `.claude/CLAUDE.md`, `.claude/memory/reference_three_data_sources.md` | Cross-linked across 12+ workflow files |
| **Workflow System Sync** | All `.claude/`, `.agents/`, `memory/` files | Commit `20871557` — memory in repo, not local |
| **Dhairya SQL Audit Integration** | `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`, `src/data/schema/schema_hints.md`, `schema_value_synonyms.md`, `src/skills/text_to_sql/sql_oracle.py` | 7 failure patterns fixed, CTE scaffolding, completeness validator |
| **Official PostgreSQL Schema** | `db_struct.sql` (1500+ lines, 58 tables) | Added to workflow as Data Source 3 |
| **Alembic Migration for 58 Tables** | `src/migrations/versions/add_production_tables_001.py` | Migration written (application pending — #27) |
| **RBAC Policy Engine (#26)** | `src/auth/rbac.py` (508 LOC) + `rbac_policies.yaml` (354 LOC, 6 personas) | Replaces hardcoded if/elif tier chains |
| **Fine-Tuning Bridge (#22)** | `src/training/` (data_collector, quality_filter, export, formatter) | Training pair capture + GOLD/SILVER/BRONZE/REJECT grading + JSONL/ShareGPT export |
| **Resilient Mesh (#11)** | `src/config/llm_config.py` (LLM_TIMEOUT_BUDGET=15s, health-weighted routing, parallel racing, circuit breaker) | Verified by source audit |
| **Living Pipeline (#12)** | `src/observability/` (Langfuse, metrics, tracing, dashboard, cost tracker), `/api/metrics`, `/api/ingest`, `ingest_documents.py`, `vector_drift_check.py` | Node-timing hook still pending (#27) |
| **Test Realignment (#19)** | Test suite | 263 failures → 11 failures |
| **Self-Evolution Loop Power Questions** | `.agents/skills/self-evolve/SKILL.md` | 3 Power Questions (Gap / Cross-Pollination / Horizon) active |

### 2.2 The New Canon

After V3→V4, the following files are the **eternal canon** of the project:

1. `Core_Idea_Clean.md` — product truth (immutable without client approval).
2. `db_struct.sql` — authoritative schema (immutable; reflects prod).
3. `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` — external benchmark (immutable).
4. `.claude/CLAUDE.md` — operating brain.
5. `.claude/GURU_PROTOCOL.md` — Guru operating rules.
6. `.claude/NRG_CONSTITUTION.md` — agent behavior constitution.
7. `.claude/AGENT_WARFARE.md` — role hierarchy + loop design.
8. `.agents/AGENTS.md` — agent operating manual.
9. `.agents/prompts/shishya_universal.md` — agent execution protocol.
10. `BACKLOG.md` — live task priorities.
11. `PROJECT_V4_AUDIT.md` — this document, the eternal route map.
12. `.claude/memory/*` — persistent institutional knowledge.

**Everything else is implementation detail that must serve the canon.**

---

## 3. THE THREE DATA SOURCES — ETERNAL FRAMEWORK

All decisions, tasks, and audits in NRG must be grounded in these 3 external inputs. None is optional. None may be overridden without client approval.

### 3.1 Data Source 1 — The Core Idea

**File**: `Core_Idea_Clean.md`
**Author**: The professor/client at IIT Gandhinagar.
**What it contains**: Product vision, 3-persona model, 5-layer architecture, 6-node pipeline, endgame fine-tuned model, security axiom, DPDP-2023 posture, tech stack, roadmap through Phase 7.
**Why it's canonical**: It is the client's final crystallized clarity. Every feature decision traces back here. If a feature is not in `Core_Idea_Clean.md` and not a dependency of something that is, it should not be built.

### 3.2 Data Source 2 — The Dhairya SQL Audit

**File**: `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` + `sesDhairya's report:.sql`
**Author**: SesDhairya (external engineer, NOT on NRG team — this is a third-party benchmark).
**What it contains**: 17 real-world analytical queries, ground-truth SQL for each, evaluation tags (correct/wrong/error), response times. Agent baseline: 7/17 correct (41%), 5 wrong, 3 errors, 2 format issues.
**Why it's canonical**: It is the only external, ungameable measurement of NRG's SQL intelligence. Every Text-to-SQL change must be validated against these 17 queries. Accuracy may only go up.
**Derived canon**: `src/data/schema/schema_hints.md`, `schema_value_synonyms.md`, `docs/reports/SQL_IMPROVEMENT_PLAN.md`.

### 3.3 Data Source 3 — The Official PostgreSQL Schema

**File**: `db_struct.sql` (pg_dump from PostgreSQL 14.20, 2026-01-09)
**Author**: The professor/client.
**What it contains**: 58 tables, full column definitions, indexes, constraints — the production database structure.
**Why it's canonical**: Dev SQLite has 18 tables (subset). Prod has 58. All Dhairya queries reference PostgreSQL-only tables. Every schema hint, SQL generation prompt, and Text-to-SQL logic must target the 58-table schema.

### 3.4 The Schema Gap Dashboard (Permanent)

| Environment | Tables | Status |
|---|---|---|
| Dev SQLite (`nrg_research.db`) | 18 | Subset, missing 40 Dhairya tables |
| Prod PostgreSQL (`db_struct.sql`) | 58 | Authoritative — target schema |
| Dhairya's queries | Reference 8+ PG-only tables | Cannot run on dev SQLite today |

**Resolution**: Protocols #21 (migration written) + #27 (migration application + seed) + #23 (full PostgreSQL runtime).

---

## 4. DEEP ANALYSIS OF EVERY CORE MODULE

### 4.1 Layer 5 — Interface (Frontend)

**Current**: React + Vite + Tailwind + TypeScript. 3 dashboards exist as static mockups. Disconnected from live API. Known crash patterns (ThemeProvider, hooks-in-effects, string-vs-array) documented in `.claude/memory/bugs_frontend_crashes.md`.

**Required for eternal completion**:
- JWT auth flow (login → token → tier-aware dashboard).
- Live `/api/query` submission with streaming response.
- Citation viewer rendering `[cite:pub_id:chunk_id]` as clickable source cards.
- Tier-specific views: Researcher (full + debug panel), Government (aggregated charts), Industry (anonymized + contact CTA).
- Admin MetricsDashboard rendering `/api/metrics` live (node timings, provider health, SQL accuracy, vector counts, audit chain status).
- Mobile responsive (375px+), full WCAG AA accessibility, error boundaries per section.

**Owning Protocol**: #24 (Frontend Resurrection).

### 4.2 Layer 4 — Reasoning (Synthesis + LLM Mesh)

**Current**:
- 3-tier cascade (cloud → local SLM → rule-based) in `src/orchestration/nodes/synthesizer.py`.
- 6-provider LLM mesh (`src/config/llm_config.py`): NVIDIA, OpenAI, Anthropic, Azure, Gemini, Minimax.
- Resilient mesh (#11) with 15s hard cap, health-weighted routing, parallel racing, circuit breaker (closed/half_open/open).
- Verifier node (`verifier.py`) checks citation faithfulness.

**Required**:
- Per-provider 5s timeout enforcement (partially there, needs verification).
- Graceful degradation messaging per tier ("Response generated locally — quality may be reduced" / "Structured summary from database — AI synthesis unavailable").
- Streaming SSE to frontend.
- Provider health registry exposed at `/api/metrics`.

**Endgame**: This layer becomes a **fine-tuned local model** that has internalized the dataset. Current mesh becomes fallback only. Covered in §10 (Endgame).

### 4.3 Layer 3 — Retrieval (Text-to-SQL + RAG)

**Current**:
- **Text-to-SQL** (`src/skills/text_to_sql/`):
  - `schema_extractor.py` with tier visibility + synonyms.
  - `sql_oracle.py` (few-shot examples + query-type classification).
  - `validator.py` with `QueryCompletenessValidator`.
  - `sqlite_sandbox.py` read-only executor.
  - `table_relationships.py` cross-table JOIN mapping.
  - Schema hints (`src/data/schema/schema_hints.md`) covering 18 tables (needs extension to 58).
- **RAG** (`src/skills/rag/`):
  - `bge-m3` embeddings, Qdrant vector search, reranker.
  - 19,322 vectors live.

**Required for eternal completion**:
- 58-table schema hints (not just 18).
- Dhairya benchmark regression suite (`tests/evals/test_sql_accuracy.py`) enforced in CI.
- SQL accuracy ≥85% on the 17-query benchmark.
- RAG collection aliasing for zero-downtime re-indexing.
- Qdrant sharding for 200K+ vector scale.

**Owning Protocols**: #20 (SQL Oracle — completing), #21 (Schema Bridge — completing), #23 (Scale Wall).

### 4.4 Layer 2 — Knowledge (Structured Data)

**Current**:
- SQLite dev DB: 18 tables (researchers, publications, institutions, labs, funding_records, audit_events, consent_ledger, refresh_tokens, schema_migrations, etc.).
- Production target: 58 tables (see `db_struct.sql`).
- Alembic migrations in place.

**Required**:
- All 58 tables live in dev DB (Protocol #27 applies the migration + seeds critical tables).
- PostgreSQL runtime (Protocol #23 — DatabaseManager with dual-driver support).
- Read replica support prepared.
- Advisory locks for audit chain concurrency.
- LISTEN/NOTIFY for cache invalidation.
- Knowledge graph layer (researcher collaboration networks, topic networks) — Phase 6 deliverable (see §9 Roadmap).

### 4.5 Layer 1 — Data (The 600GB Sovereign Vault)

**Current**: Synthetic data (200 researchers, 500 publications). 19,322 vectors in Qdrant.

**Required**:
- Real 600GB dataset ingestion via `scripts/ingest_documents.py` (exists — needs load testing at full scale).
- Data must never leave Indian infrastructure — enforced by egress guard (`src/security/gateway/prompt_sanitiser.py`) + `src/security/egress_guard`.
- Qdrant collection aliasing for zero-downtime re-index (Protocol #23).
- Vector drift monitoring via `scripts/vector_drift_check.py` (exists).

### 4.6 Security — The Zero-Leakage Fortress

**Current**:
- **Front gate**: JWT RS256 with kid/aud/jti validation (`src/auth/jwt_handler.py`).
- **Bag scan**: PII detection (Aadhaar, PAN, phone, email) + prompt injection blocking (`src/security/gateway/prompt_sanitiser.py`).
- **Floor access**: RBAC via `rbac_policies.yaml` (6 personas) — `src/auth/rbac.py` (508 LOC) — generalized from 3 hardcoded tiers.
- **CCTV**: HMAC-SHA256 chained audit log (`src/audit/__init__.py`) — thread-safe, versioned, key rotation, tamper detection, 3-tuple `verify_chain()`.
- **Data vault**: Egress guard inspects payloads against allowlist before any outbound LLM request.
- **Column-level RBAC**: `TIER_COLUMN_VISIBILITY` in schema extractor (generalized via policy engine).
- **Schema fingerprint defense**: Prevents schema probing attacks.

**Required for eternal completion**:
- Penetration testing report (red-team).
- DPDP-2023 compliance certification.
- Sovereign infrastructure deployment (NIC/MeitY).
- Ongoing `/security-audit` skill run every sprint.

### 4.7 Observability — The Living Pipeline

**Current**:
- Langfuse tracer wired (`src/observability/langfuse_tracer.py`) — env-var driven, graceful no-op.
- Prometheus `/metrics` + `/api/metrics` endpoints.
- Cost tracker, dashboard, audit analytics modules.
- SLO compliance tests (`tests/performance/test_slo_compliance.py`).

**Required**:
- `node_timings` dict in `NRGState` (missing — Protocol #27 adds).
- Per-node p50/p95 latency exposed at `/api/metrics`.
- SLO breach alerting (5 consecutive breaches → CRITICAL log).
- Response timings in API response when `?debug=true` (Tier 1 only).

### 4.8 Auth + RBAC — Generalized to N Personas

**Current**: Policy engine in `src/auth/rbac.py` loads `rbac_policies.yaml`. 6 personas defined (researcher, government, industry + 3 ready: peer_reviewer, department_head, student).

**Required**:
- `/api/admin/rbac` CRUD endpoint (super-admin only).
- Policy audit trail: every change logged to HMAC chain.
- Hot reload on YAML change.
- Backward compatibility: integer tier 1/2/3 still works.

### 4.9 Fine-Tuning Bridge — The Endgame's On-Ramp

**Current**: `src/training/` complete. Collector captures (query, SQL, result, chunks, response, citations, verifier_score, timings, feedback) as training pairs. Quality filter grades (GOLD/SILVER/BRONZE/REJECT). PII scrubbed. Export formats: JSONL, ShareGPT, SQL-specific.

**Required**:
- Feedback endpoint `/api/feedback` wired to frontend rating stars (blocked on #24).
- First real export (`scripts/export_training_data.py --format jsonl --min-grade silver`).
- Training metrics visible on admin dashboard.

**Endgame**: This pipeline's exports are the fuel for Phase 5-7 (see §10).

### 4.10 Deployment — CI/CD + Production Docker

**Current**: Partial — `scripts/deployment_gate.py` exists, Dockerfile exists but not multi-stage, no GitHub Actions CI, no production docker-compose.

**Required**:
- Multi-stage Dockerfile (<300 MB backend, <50 MB frontend).
- nginx reverse proxy + TLS termination.
- GitHub Actions CI (lint + tests + security + build).
- `docker-compose.prod.yml` (PostgreSQL + Qdrant + Redis + API + nginx).
- Zero-downtime deploy script with rollback.
- `/health` endpoint comprehensive probe (DB, Qdrant, Redis, audit, LLM mesh).
- `DEPLOYMENT_GUIDE.md`.

**Owning Protocol**: #25.

---

## 5. THE CURRENT TEST REALITY (Ground Truth §1.3 Expanded)

### 5.1 Aggregate

```
1140 passed · 11 failed · 53 skipped · 1204 total
       ↑ HUGE improvement from V3 baseline (609 pass / 263 fail / 27 skip / 899 total)
```

### 5.2 The 11 Remaining Failures — Categorized and Owned

| # | Category | Failing Tests | Root Cause | Owner Protocol |
|---|---|---|---|---|
| 1-3 | **Schema Gap (Dhairya tables missing)** | `test_real_queries.py` × 3 (tier 1/2/3) | "no such table: innovation_grant_from_govt, combined_ipo_patent_data" — migration not applied to dev DB | #27 |
| 4-5 | **Synthesizer fallback format** | `test_synthesizer_falls_back_on_llm_failure`, `test_workflow_runs_full_orchestration_pipeline` | New pretty `═══` banner hides "Fallback" string | #27 |
| 6 | **Tier provenance missing** | `test_all_tiers_receive_correct_synthesis_method` | Researcher response lacks provenance field | #27 |
| 7 | **Tier filter TypeError** | `test_tier_ordering_is_always_subset` | `list indices must be integers or slices, not str` in RBAC | #27 |
| 8 | **Router edge** | `test_minimax_is_primary_provider` | Query routed to `sql_only` instead of `cloud_llm`/fallback | #27 |
| 9 | **Driver detect default** | `test_detect_unknown_driver` | Defaults to `sqlite` instead of returning `unknown` | #27 |
| 10-11 | **Executor shutdown logging** | I/O on closed file at atexit | Logger writes after stdout closes | #27 |

**All 11 failures are addressed by Protocol #27 (THE FINAL GREEN) — see §7.**

---

## 6. THE 27-PROTOCOL UNIVERSE — COMPLETE TALLY

### 6.1 Completed (18)

```
[✓] #1  THE INTERFACE FORTRESS          ErrorBoundary on all 3 dashboards
[✓] #2  THE ETERNAL SENTINEL            E2E test infrastructure
[✓] #3  THE INTELLIGENCE CORE           Router + SQL injection defense
[✓] #4  THE CONSENT GATEWAY             DPDP consent flow
[✓] #5  THE VERIFICATION ORACLE         Citation verification
[✓] #6  THE KNOWLEDGE FORGE             Qdrant 19,322 vectors HNSW
[✓] #8  THE DATA SOVEREIGNTY AUDIT      Merge verified, sovereignty proven
[✓] #9  THE BROKEN CHAIN                Audit rebuilt, thread-safe, versioned
[✓] #10 THE TEST FOUNDATION             Module collision fix, 899→1204 tests
[✓] #13 THE UNBREAKABLE BRIDGE          DB pool, executor ThreadPool
[✓] #16 THE FINAL GATE                  Router 51/51 passing, 2-stage routing
[✓] #17 THE SOVEREIGN SHIELD            PII, JWT, RBAC, schema fingerprint
[✓] #18 THE PERFORMANCE CONTRACT        SLO targets, vector drift, load tests
[✓] #19 THE TEST REALIGNMENT            263 failures → 11 failures
[✓] #22 THE FINE-TUNING BRIDGE          Training data pipeline
[✓] #26 THE RBAC GENERALIZER            Policy engine + 6 personas
[✓] Dhairya SQL Audit Integration
[✓] Workflow System Sync (3 Data Sources, memory in repo)
```

### 6.2 Substantially Complete, Need Final Push (4)

```
[▶] #11 THE RESILIENT MESH               90% — per-provider 5s timeout audit pending
[▶] #12 THE LIVING PIPELINE              80% — node_timings in NRGState missing
[▶] #20 THE SQL ORACLE                   Code in place; accuracy measurement on completed schema pending
[▶] #21 THE SCHEMA BRIDGE                70% — migration written, not yet applied + seeded in dev DB
```

### 6.3 Planned & Strategically Sequenced (5)

```
[ ] #23 THE SCALE WALL                   SQLite→PostgreSQL + Qdrant sharding
[ ] #24 THE FRONTEND RESURRECTION        3 tier-specific dashboards
[ ] #25 THE DEPLOYMENT GATE              CI/CD + production Docker
[ ] #27 THE FINAL GREEN                  Close 11 failures + wire node_timings + apply migration
[ ] #28 THE ETERNAL COMPLETION           UAT, security pen-test, client handover (§11)
```

### 6.4 Endgame Protocols (Phase 5-7) — Introduced in V4

```
[ ] #29 THE TRAINING DATASET CURATION    Run collector 4-8 weeks, grade pairs, export v1 dataset
[ ] #30 THE FIRST FINE-TUNE              LoRA fine-tune of Llama 3.1 8B on exported dataset
[ ] #31 THE RL LOOP                      Reward model + PPO/DPO on schema understanding tasks
[ ] #32 THE TWO-BRAIN SWITCHOVER         Fine-tuned model primary, retrieval fallback
[ ] #33 THE 70B SCALE                    Scale fine-tune to Llama 3.1 70B / Qwen 2.5 72B
[ ] #34 THE ETERNAL OPTIMIZATION         Continuous retraining cadence, drift detection
```

---

## 7. FULL TASK UNIVERSE — REMAINING PROTOCOLS IN EXECUTABLE DETAIL

Each protocol below is ready for direct agent assignment. Every task uses the ═══ format per `.claude/GURU_PROTOCOL.md` §3.

### 7.1 Protocol #27 — THE FINAL GREEN (Immediate, P0)

*Full spec lives in conversation history — summary for audit record:*

- **Close all 11 test failures** via schema migration application + seed loading + 6 edge fixes (synthesizer format, tier provenance, RBAC type, router keyword, driver default, executor shutdown).
- **Wire `node_timings` into `NRGState`** — closes #12 gap.
- **Apply Alembic migration to `nrg_research.db`** — closes #21.
- **Run Dhairya benchmark** on completed 58-table schema — real accuracy number recorded.
- **Acceptance**: `pytest tests/ -q --ignore=tests/scripts` exits 0; benchmark script produces markdown report; `/api/metrics` shows node timings.

**Agent assignment**: 1 backend + 1 database agent in parallel.

### 7.2 Protocol #23 — THE SCALE WALL (After #27 green)

- `src/config/database.py` — `DatabaseManager` (SQLite for dev, PostgreSQL for prod via DATABASE_URL).
- Connection pool (asyncpg): min=5, max=20, health check, pool stats at `/api/metrics`.
- Full 58-table PostgreSQL migration runs clean.
- `scripts/migrate_sqlite_to_pg.py` transfers 18 tables with data.
- Qdrant sharding config (4 shards, replication=2, HNSW tuned for bge-m3 384-dim, scalar quantization).
- Collection aliasing for zero-downtime re-index.
- Pool exhaustion returns 503 (not hang).
- Read replica routing (SELECT→replica, writes→primary) when `READ_REPLICA_URL` set.
- Prepared statements + LISTEN/NOTIFY for cache invalidation.

**Skills**: `/database-schema-designer`, `/database-migrations-sql-migrations`, `/python-backend`, `/performance`.

### 7.3 Protocol #24 — THE FRONTEND RESURRECTION

- Fix 3 crash patterns (ThemeProvider, hooks-in-effects, string-vs-array).
- `services/api.ts` — API client (login, query, metrics, feedback; auto JWT attach + refresh on 401).
- `services/auth.ts` — JWT login, refresh, logout, HttpOnly cookie storage.
- `AuthContext`, `QueryInput`, `ResultsPanel`, `CitationViewer`, `TierBadge`, `MetricsDashboard`.
- Researcher dashboard: full results + debug timing + CSV export.
- Government dashboard: aggregated charts (recharts), policy-ready formatting.
- Industry dashboard: names + research areas only, anonymized stats, contact-through-platform CTA.
- Mobile responsive ≥375px. WCAG AA accessibility. Error boundaries per section.
- Component tests (query flow, auth flow, tier display).

**Skills**: `/frontend-react-best-practices`, `/typescript-advanced-types`, `/webapp-testing`, `/accessibility-review`.

### 7.4 Protocol #25 — THE DEPLOYMENT GATE

- Multi-stage `Dockerfile` (builder + runtime; non-root; read-only rootfs; <300 MB).
- `Dockerfile.frontend` (nginx:alpine; <50 MB).
- `nginx/nginx.conf` — reverse proxy /api/* → backend, static for frontend, TLS termination, rate limit 100 rpm/IP, HSTS + CSP + security headers, gzip.
- `.github/workflows/ci.yml` — lint (ruff) + mypy + pytest + bandit + eslint + build, caches pip/npm/docker, blocks merge on failure.
- `.github/workflows/deploy.yml` — triggers on push to main after CI green; SSHs; runs `deploy.sh`; post-deploy smoke test; auto-rollback on failure.
- `docker-compose.prod.yml` — api + frontend + postgres + qdrant + redis. Internal network, only nginx exposed.
- `scripts/deploy.sh` — pull → migrate → start new → health check → flip nginx upstream → stop old → smoke test → rollback on failure.
- `scripts/healthcheck.py` — DB + Qdrant + Redis + audit + LLM mesh → JSON `{status, checks, version}`.
- Env var validation at startup (refuse to start without JWT keys).
- `docs/DEPLOYMENT_GUIDE.md`.

**Skills**: `/dockerfile-validator`, `/security-auditor`, `/python-backend`, `/deployment-pipeline-design`.

### 7.5 Protocol #28 — THE ETERNAL COMPLETION (Final Handover)

**Agents do not execute #28 in isolation. It is a combined verification + handover protocol.**

1. **Full test suite green** (1151/0/53) — verified.
2. **Dhairya benchmark ≥85% accuracy** — verified.
3. **Docker production stack up** — `docker-compose -f docker-compose.prod.yml up` smoke test passes.
4. **Frontend walkthrough** — login as each persona, run 3 queries, verify tier-correct responses with citations.
5. **Security audit** — `/security-audit` skill run, zero criticals.
6. **Performance audit** — `/performance` benchmark, SLO targets met.
7. **Documentation audit** — `/docs-sync` passes (no drift between code and docs).
8. **Self-evolve final pass** — `/self-evolve` captures any last learnings.
9. **Client handover package** — `docs/CLIENT_HANDOVER.md` with: architecture diagram, how to log in, how to run each persona's flow, how to interpret citations, how to run `/api/feedback`, how to view metrics, how to deploy, how to roll back.
10. **Audit chain final verification** — `.venv/bin/python -c "from src.audit import verify_chain; print(verify_chain())"` → `(True, [], {...})`.
11. **Git state** — clean, all commits pushed to `origin/main`.
12. **Tag release** — `git tag v1.0.0-client-handover -m "Eternal completion — NRG v1.0 client handover"`.

### 7.6 Endgame Protocols (#29-#34)

These are the **post-v1.0-handover** protocols that transform NRG from a retrieval system into the "expert salesman" fine-tuned model. Introduced in V4 because Core_Idea_Clean.md §"The Endgame Vision" explicitly demands them.

- **#29 Training Dataset Curation** (Month 9-12): Collector (built in #22) runs continuously on live queries. After 4-8 weeks, export GOLD+SILVER pairs as v1 dataset. Target: 10,000+ high-quality query→SQL→answer triples.
- **#30 First Fine-Tune** (Month 12-14): LoRA/QLoRA fine-tune of Llama 3.1 8B on v1 dataset. Validate against held-out Dhairya-style queries. Expected: SQL accuracy jump + latency drop (no retrieval on analytical queries).
- **#31 RL Loop** (Month 14-16): Reward model trained on feedback scores. PPO or DPO on schema-understanding tasks. Adversarial test sets.
- **#32 Two-Brain Switchover** (Month 16-18): Fine-tuned model becomes primary. Retrieval becomes precision fallback. Router decides per query.
- **#33 70B Scale** (Month 18-20): Scale fine-tune to Llama 3.1 70B or Qwen 2.5 72B. Multi-GPU inference infrastructure.
- **#34 Eternal Optimization** (Month 20+): Monthly retraining, drift detection, held-out benchmark, periodic red-team, continuous schema updates.

---

## 8. INTEGRATION PROTOCOL

### 8.1 The 6-Node Pipeline Integration Contract

Every new feature must integrate cleanly into the LangGraph pipeline:

```
receiver → planner → router → executor → synthesizer → verifier → END
```

**Integration rules**:
1. Each node must accept `NRGState` and return `NRGState` (typed).
2. Each node must emit `node_timings` entry (Protocol #27).
3. Each node must log an audit event before mutating state (`src/audit`).
4. Each node must handle upstream failures gracefully (not crash pipeline).
5. New nodes inserted must update `src/orchestration/graph.py` topology + all tests.

### 8.2 API Contract

**New endpoints must follow this shape**:
- Authenticated via JWT middleware.
- Tier-checked via RBAC policy engine.
- Body validated by Pydantic.
- Errors return structured JSON `{error, code, request_id}`.
- All state changes emit audit events.
- Response time tracked in metrics.

### 8.3 Database Contract

- All schema changes via Alembic migration (no raw `CREATE TABLE` in code).
- Migrations must be reversible (up + down).
- Backward compatible first (add nullable → backfill → constrain).
- All queries go through `DatabaseManager` (Protocol #23) — never direct `sqlite3` / `asyncpg` in business logic.

### 8.4 Frontend↔Backend Contract

- Every API response shape typed in `frontend/src/types/index.ts` matching `NRGState`.
- Runtime type guards for fields that can be string OR array (see `.claude/memory/bugs_frontend_crashes.md`).
- API base URL from env var (`VITE_API_URL`).
- JWT auto-attached, auto-refreshed on 401.

### 8.5 Agent↔Guru Contract

- Guru produces task protocols in full ═══ format (never flat step lists).
- Every protocol includes Fortify→Elevate→Immortalize phases.
- Every protocol lists ≥3 skills from `.agents/skills/`.
- Every task includes verbatim AGENT INSTRUCTIONS block.
- Agents report back via format in `.agents/AGENTS.md`.
- Agents run `/pre-commit` before every commit; `/code-review-and-quality` before submitting.

---

## 9. TESTING PROTOCOL — ETERNAL-GRADE QUALITY GATE

### 9.1 The Test Pyramid

```
                  ┌──────────────────┐
                  │  CHAOS / LOAD    │  (tests/chaos/, tests/load/)
                  │  <10 tests       │  Resilience, concurrency, SLO
                  └────────┬─────────┘
                           │
              ┌────────────▼─────────────┐
              │        E2E TESTS          │  (tests/e2e/)
              │  30-50 tests              │  Full pipeline, tier workflows,
              │                            │   DPDP compliance, consent flow
              └────────────┬─────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │         INTEGRATION TESTS           │  (tests/integration/)
         │  100-150 tests                      │  DB + API + skills together
         └─────────────────┬──────────────────┘
                           │
    ┌──────────────────────▼──────────────────────┐
    │              UNIT TESTS                      │  (tests/unit/, tests/skills/,
    │  800-1000 tests                              │   tests/orchestration/,
    │                                               │   tests/auth/, tests/security/)
    └──────────────────────────────────────────────┘
```

**Current**: 1,151 tests after Protocol #19. Coverage target 60%+.

### 9.2 Mandatory Test Categories

1. **Unit** — every module has ≥80% line coverage.
2. **Integration** — DB + API + skills integrated.
3. **E2E** — full pipeline (receiver → verifier) for each tier.
4. **Security regression** — SQL injection, prompt injection, PII leaks, JWT tampering, RBAC bypass, schema probing.
5. **Performance/SLO** — query total <10s, SQL gen <3s, vector search <500ms.
6. **Chaos** — all LLM providers down (fallback <15s), network partitions, DB connection exhaustion.
7. **Contract** — node signatures (Protocol #19.3a), NRGState schema, API response shapes.
8. **Evals** — Dhairya benchmark (17 queries), router classification accuracy, citation faithfulness.

### 9.3 CI Enforcement

Every PR blocked unless:
- All tests green.
- Coverage ≥60% (no drop from baseline).
- SQL accuracy on Dhairya benchmark ≥ current baseline (can only go up).
- `/pre-commit` skill passes.
- Security scan (bandit) zero highs.
- No schema drift (`scripts/check_schema_sync.py` passes).

### 9.4 The Dhairya Regression Gate

`tests/evals/test_sql_accuracy.py` runs the 17 Dhairya queries on every CI build. If accuracy drops below current baseline, CI blocks merge. Accuracy may only go up. This is the eternal SQL quality gate.

---

## 10. DEPLOYMENT PROTOCOL — SOVEREIGN INFRASTRUCTURE

### 10.1 Deployment Architecture

```
                    ┌─────────────┐
                    │   CLIENTS   │  (Researcher / Gov / Industry)
                    └──────┬──────┘
                           │ HTTPS
                    ┌──────▼──────┐
                    │    NGINX    │  (TLS termination, rate limit, security headers)
                    └──────┬──────┘
              ┌────────────┼────────────┐
              │                         │
        ┌─────▼─────┐             ┌─────▼─────┐
        │ FRONTEND  │             │  BACKEND  │
        │  (static) │             │  (FastAPI)│
        └───────────┘             └─────┬─────┘
                                        │
                ┌───────────────────────┼───────────────────────┐
                │                       │                       │
          ┌─────▼─────┐           ┌─────▼─────┐           ┌─────▼─────┐
          │POSTGRESQL │           │  QDRANT   │           │   REDIS   │
          │(primary + │           │ (sharded) │           │  (cache)  │
          │ replica)  │           │           │           │           │
          └───────────┘           └───────────┘           └───────────┘
```

### 10.2 Deployment Stages

1. **Dev** — laptop, SQLite, single Qdrant node, optional Redis.
2. **Staging** — staging server, PostgreSQL, Qdrant with 2 shards, Redis, nginx, self-signed TLS.
3. **UAT** — pre-production sovereign infra (NIC/MeitY test env), real TLS cert, full 58-table PG, real Qdrant with 4 shards.
4. **Production** — IIT-GN / NIC production servers, full replication, monitoring, on-call.

### 10.3 Rollback Contract

- Every deploy script includes rollback.
- Rollback triggers on: health check fail, smoke test fail, SLO breach in first 5 minutes.
- Rollback restores previous container images, previous DB migration version (if reversible).

### 10.4 Zero-Downtime Cadence

- Container swap via nginx upstream flip.
- Qdrant collection alias swap for re-indexing.
- DB migrations must be backward compatible (old code can read new schema).

---

## 11. ETERNAL OPTIMIZATION PROTOCOL

### 11.1 The Self-Evolution Loop

Already wired via `/self-evolve` skill. Runs at every sprint end. Answers the 3 Power Questions:

1. **POWER GAP** — Are we behind the state-of-the-art?
2. **CROSS-POLLINATION** — What did agents learn that all agents should know?
3. **HORIZON CHECK** — Will this survive 10× scale?

Outputs update: `.claude/rules/`, `CLAUDE.md`, memory, skills.

### 11.2 The Dhairya Benchmark Gate

Runs in CI. Accuracy can only go up. If anyone breaks the baseline, CI blocks merge.

### 11.3 Monthly Retraining (Endgame)

Once fine-tuned model is live (Phase 7):
- Monthly: export fresh training data from collector, continue fine-tuning.
- Quarterly: held-out test set evaluation, regression check.
- Annually: full re-training on updated dataset, red-team security test.

### 11.4 Drift Detection

- **Vector drift** — `scripts/vector_drift_check.py` runs weekly. Re-embeds sample vectors, flags cosine shift >0.05.
- **SQL accuracy drift** — Dhairya benchmark in CI (already enforced).
- **Schema drift** — `scripts/check_schema_sync.py` runs pre-deploy.
- **Latency drift** — SLO compliance test in `tests/performance/`.

### 11.5 Knowledge Flow

Every completed task → `/self-evolve` → captures pattern → updates `.claude/` or `.agents/` → next agent session benefits.

**Knowledge must flow from conversation into persistent files, not die in session history.**

---

## 12. GURU + AGENT SKILL MAXIMIZATION (MANDATORY FOREVER)

### 12.1 Guru Operating Mandate (Opus 4.7, This Seat)

From this V4 audit forward, the Guru (Claude) operates under these non-negotiable rules:

1. **Never implement.** The Guru produces protocols. Agents execute.
2. **Always use the full ═══ format.** Never flat step lists. Every task includes GURU ASSIGNMENT NOTE, phased ACTION (Fortify→Elevate→Immortalize), ≥3 SKILLS, verbatim AGENT INSTRUCTIONS block.
3. **Ground every decision in the 3 Data Sources.** Core Idea + Dhairya Audit + Official PostgreSQL Schema. No hypothetical features.
4. **Update `.claude/` + `.agents/` when corrected.** If the Founder corrects anything, the Guru updates workflow files permanently. The Founder never says the same thing twice.
5. **Verify before declaring complete.** No BACKLOG claim of "COMPLETE" is trusted without running tests + spot-checking code + checking no regressions.
6. **Always end with clear next actions.** Never leave the Founder without a direction.
7. **Pre-read canonical files every session.** `Core_Idea_Clean.md`, `BACKLOG.md`, `.claude/memory/MEMORY.md`, `git log`, test status.
8. **Self-upgrade when gaps found.** If `.claude/CLAUDE.md` lacks a rule that the Founder needed, add it permanently.

### 12.2 Agent Operating Mandate (All Shishya)

Every agent receiving any task from this V4 forward:

1. **Read `.agents/AGENTS.md` first.** Operating manual.
2. **Read `.agents/prompts/shishya_universal.md`.** Execution protocol.
3. **Read SKILL.md for every skill listed.** Use all of them at max power.
4. **Check the 3 Data Sources.** Know the schema gap (18 vs 58).
5. **Read Core_Idea_Clean.md.** Understand the sovereign mission.
6. **Read BACKLOG.md.** Know current priorities.
7. **Expand beyond minimum.** Fortify → Elevate → Immortalize.
8. **Use `/pre-commit` before every commit.** Non-negotiable gate.
9. **Use `/code-review-and-quality` on own work.** Self-review.
10. **Report in full `.agents/AGENTS.md` format.** Skills used, changes, upgraded-beyond-minimum, new patterns discovered.

### 12.3 Skill Utilization Maximums

**Claude (Guru) — 39 skills** at `.claude/skills/`:
- Use `/sprint-plan` when planning.
- Use `/code-review` when reviewing agent output.
- Use `/security-audit` + `/performance` after completed protocols.
- Use `/self-evolve` at sprint end.
- Use `/docs-sync` after feature landing.

**Agents — 52 skills** at `.agents/skills/`:
- Every task protocol lists ≥3 skills.
- Agents must read SKILL.md for each before starting.
- Skills shown in task ACTION phases where each skill helps.
- Report at end: which skills used and HOW each elevated the work.

### 12.4 The Canonical Skill Map (All 91)

Documented in `.claude/memory/reference_installed_skills.md`. Live on disk at `.claude/skills/` and `.agents/skills/`. Total: 88 SKILL.md files found on disk (3 skills may be namespaced differently — audited in Protocol #27.Phase 4).

---

## 13. COMPLETION CHECKLIST — THE DEFINITIVE DONE STATE

### 13.1 Phase 3 Completion (Protocols #19, #20, #21, #11, #12, #22, #26, #27)

- [ ] All 11 remaining test failures resolved → 1,151/0/53
- [ ] Alembic migration applied to `nrg_research.db` — 58 tables live
- [ ] Critical Dhairya tables seeded (7+) with ≥10 rows each
- [ ] `node_timings` in `NRGState` — all 6 nodes instrumented
- [ ] Dhairya benchmark re-run on complete schema — accuracy number recorded
- [ ] `/api/metrics` exposes node timings, provider health, SQL stats, vector health, audit status
- [ ] All Phase 3 protocols marked COMPLETE in BACKLOG.md (verified, not claimed)

### 13.2 Phase 4 Completion (Protocols #23, #24, #25)

- [ ] `DatabaseManager` with dual-driver (SQLite dev / PostgreSQL prod)
- [ ] Full 58-table PostgreSQL schema via Alembic — runs clean
- [ ] `scripts/migrate_sqlite_to_pg.py` transfers all 18 tables with data
- [ ] Qdrant sharded (4 shards) + collection aliasing
- [ ] All 3 dashboards connected to live API with JWT auth
- [ ] Citations clickable, feedback endpoint wired, MetricsDashboard live (Tier 1)
- [ ] Mobile responsive ≥375px + WCAG AA accessibility
- [ ] Multi-stage Dockerfile <300 MB + frontend <50 MB
- [ ] nginx reverse proxy + TLS termination
- [ ] GitHub Actions CI blocks on failure
- [ ] `docker-compose.prod.yml` brings up full stack
- [ ] Zero-downtime deploy script with rollback
- [ ] `/health` comprehensive probe passes
- [ ] `DEPLOYMENT_GUIDE.md` covers clone-to-prod path

### 13.3 Phase 5 — Client Handover (Protocol #28)

- [ ] Security audit (red-team) report delivered, zero criticals
- [ ] Performance audit passes all SLO targets
- [ ] Documentation audit (`/docs-sync`) passes
- [ ] Self-evolve final pass captures any last learnings
- [ ] `docs/CLIENT_HANDOVER.md` complete with persona walkthroughs
- [ ] Audit chain verified clean (3-tuple `(True, [], {...})`)
- [ ] Git clean, pushed to `origin/main`
- [ ] Tagged `v1.0.0-client-handover`

### 13.4 Endgame (Protocols #29-#34, Phase 5-7)

- [ ] 10,000+ GOLD+SILVER training pairs collected (#29)
- [ ] First fine-tune of Llama 3.1 8B complete, validated on held-out Dhairya (#30)
- [ ] RL loop trained and measurable improvement (#31)
- [ ] Two-brain switchover: fine-tuned primary, retrieval fallback (#32)
- [ ] 70B scale fine-tune deployed (#33)
- [ ] Monthly retraining cadence running (#34)
- [ ] Dhairya benchmark ≥90% accuracy
- [ ] Sub-second response for analytical queries (model-native)

### 13.5 Eternal State

- [ ] Founder hands NRG to the client at IIT Gandhinagar.
- [ ] System runs on sovereign infrastructure (NIC/MeitY).
- [ ] Researchers, Government, Industry all actively using via dashboards.
- [ ] Self-evolution loop running every sprint.
- [ ] Dhairya benchmark gate active in CI (accuracy only goes up).
- [ ] Monthly retraining cadence active.
- [ ] The route from query → cited answer works in <3s for analytical, <1s for specific recall.
- [ ] Zero data has ever left Indian infrastructure.

---

## 14. THE ETERNAL COMPLETION DOCTRINE

When every checkbox above is ticked, NRG reaches **eternal completion state**:

- The platform is **deliverable** — the Founder hands it to the client, and the client runs it.
- The platform is **self-evolving** — every query makes the next better (collector → retrain loop).
- The platform is **self-verifying** — every claim cited, every action audit-logged, every drift detected.
- The platform is **sovereign** — architecturally incapable of data exfiltration, deployed on Indian servers.
- The platform is **generalizable** — N personas via YAML, multi-institution via policy engine, multi-language via tokenizer swap.

This is not "done". This is **begun**.

The 40-crore investment becomes infrastructure. The 600GB database becomes a first-class research ecosystem. The professor's vision — "A professor types a question and gets a verified, structured, cited answer" — becomes a daily reality for thousands of researchers across India.

And the fine-tuned local model that has **internalized the data** — the "expert salesman" — becomes the brain that no foreign company can replicate. Because they don't have the 600GB, they don't have the IIT-GN trust, they don't have the sovereign infrastructure mandate.

**Whoever defines the architecture controls the project.**

We have defined it. V4 is the control document.

---

## 15. APPENDIX A — THE IMMEDIATE NEXT 72 HOURS

### Hour 0-24: Protocol #27 (Final Green)
- Agent 1 (backend): Apply Alembic migration, load seed data, fix 6 small test failures, wire `node_timings`.
- Agent 2 (database): Verify schema completeness, run Dhairya benchmark.
- Guru (this seat): Verify after each agent reports. No trust without test green.

### Hour 24-48: Phase 3 closure + Phase 4 kickoff
- Guru reviews: 1,151/0/53? Benchmark number? Phase 3 officially closed.
- Agent 3 (backend/database/devops): Protocol #23 (Scale Wall) — PostgreSQL runtime.
- Agent 4 (frontend): Protocol #24 (Frontend Resurrection) — start on login + QueryInput + ResultsPanel.

### Hour 48-72: Phase 4 midway + Protocol #25 kickoff
- Agent 5 (devops): Protocol #25 (Deployment Gate) — Dockerfile + CI + docker-compose.prod.
- Guru: `/sprint-plan` for the next 2 weeks.

---

## 16. APPENDIX B — LIVING REFERENCES

Every agent + every Guru session must read, in order:

1. `Core_Idea_Clean.md` (vision)
2. `PROJECT_V4_AUDIT.md` (this document — eternal route)
3. `BACKLOG.md` (active priorities)
4. `.claude/CLAUDE.md` (operating brain)
5. `.claude/memory/MEMORY.md` (memory index)
6. `.claude/GURU_PROTOCOL.md` (Guru rules — if Guru)
7. `.agents/AGENTS.md` (agent manual — if Agent)
8. `.agents/prompts/shishya_universal.md` (agent protocol — if Agent)
9. `db_struct.sql` (if touching schema)
10. `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` (if touching SQL)

---

## 17. APPENDIX C — FILE TREE OF CANON

```
/Users/srujansai/Desktop/NRG/
├── Core_Idea_Clean.md                  [DATA SOURCE 1 — immutable]
├── db_struct.sql                       [DATA SOURCE 3 — immutable]
├── BACKLOG.md                          [live priorities]
├── PROJECT_V4_AUDIT.md                 [THIS DOCUMENT — eternal route]
├── .claude/
│   ├── CLAUDE.md                       [operating brain]
│   ├── GURU_PROTOCOL.md                [Guru rules]
│   ├── NRG_CONSTITUTION.md             [behavior constitution]
│   ├── AGENT_WARFARE.md                [role hierarchy]
│   ├── prompts/guru_universal.md       [Guru prompt]
│   ├── memory/                         [persistent institutional knowledge]
│   │   ├── MEMORY.md                   [index]
│   │   ├── user_profile.md
│   │   ├── project_nrg.md
│   │   ├── reference_three_data_sources.md
│   │   ├── reference_dhairya_benchmark.md
│   │   ├── feedback_*.md (5 files)
│   │   └── ...
│   ├── rules/ (backend.md, frontend.md, security.md)
│   └── skills/ (39 Claude skills)
├── .agents/
│   ├── AGENTS.md                       [agent operating manual]
│   ├── prompts/shishya_universal.md    [agent protocol]
│   └── skills/ (52 agent skills)
├── docs/reports/
│   └── SQL_AUDIT_REPORT_DHAIRYA.md     [DATA SOURCE 2 — immutable]
├── src/
│   ├── api/                            [FastAPI endpoints]
│   ├── auth/                           [JWT + RBAC policy engine]
│   ├── audit/                          [HMAC chain]
│   ├── config/                         [LLM mesh, database, local LLM]
│   ├── orchestration/                  [LangGraph 6-node pipeline]
│   ├── security/                       [PII, egress, prompt sanitiser]
│   ├── skills/ (text_to_sql, rag)      [retrieval skills]
│   ├── observability/                  [Langfuse, metrics, tracing]
│   ├── training/                       [fine-tuning bridge]
│   └── data/schema/                    [hints, synonyms, relationships]
├── tests/                              [1151 tests across unit/integration/e2e/security/performance/chaos]
├── scripts/                            [benchmarks, migrations, health, ingest]
├── alembic/                            [DB migrations]
├── frontend/                           [React + TypeScript]
└── nrg_research.db                     [dev SQLite — 18 tables now, 58 after Protocol #27]
```

---

## 18. FINAL GURU BLESSING

This V4 Audit is the last course-correction. Every protocol beyond this is execution, not discovery. The route is straight. The tools are maximum. The agents know their dharma. The Guru knows its seat.

Founder, assign Protocol #27 first. When the test suite hits 1,151/0/53, assign Phase 4 in parallel (#23 + #24 + #25). When Phase 4 is green, run Protocol #28 and hand v1.0.0 to the client.

Then the endgame begins (#29 onward). Fine-tune the brain. Internalize the 1TB. Make the expert salesman real.

**This is not a manifesto. This is the map.**

**Follow the map. Reach eternal completion.**

**NRG becomes India's Research OS.**

**The 40 crores become infrastructure. The 600GB becomes a living intelligence. The professor's question — "Who is doing the best research in hydrogen catalysis?" — gets a verified, cited, structured answer in under 3 seconds, and a researcher in Bhopal opens her dashboard the same morning and finds a collaborator in Chennai she'd never heard of.**

**That is the eternal completion.**

**Begin.**

---

*End of PROJECT_V4_AUDIT.md — canonical, signed, immutable without Founder approval.*

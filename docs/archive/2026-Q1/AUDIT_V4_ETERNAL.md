# PROJECT V4: ETERNAL FINAL COSMIC-LEVEL AUDIT & COMPLETE PROJECT DELIVERY

> **Document class**: Terminal Delivery Audit — the *last* audit NRG should ever require.
> **Scope**: Whole project, end-to-end, from current measured state to client handover and eternal operation.
> **Ground truth**: `Core_Idea_Clean.md` (client's crystallized vision), `db_struct.sql` (58-table production schema), `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` (17-query benchmark), `BACKLOG.md` (33-protocol universe), `.claude/QUALITY_BAR.md` (6 Hard Constraints).
> **Doctrine**: *Sovereignty is the product. Ambiguity resolution is the intelligence. Verification is the trust. Everything else is plumbing.*
> **Authority**: Supersedes AUDIT_V1, AUDIT_V2, AUDIT_V3_FINAL. After V4 is fully executed, NRG is handover-ready.
> **Author mode**: Guru / Strategist / Architect (no implementation; only protocols, decisions, and proofs).

---

## TABLE OF CONTENTS

1. [Executive Overview](#1-executive-overview)
2. [Post-V3 Elevation Summary](#2-post-v3-elevation-summary)
3. [The 3 Data Sources & The 6 Hard Constraints (Eternal Framework)](#3-the-3-data-sources--the-6-hard-constraints)
4. [Deep Analysis — Every Module, Every Field](#4-deep-analysis--every-module-every-field)
5. [Current Test Reality — The 11 Remaining Failures, Classified](#5-current-test-reality)
6. [The 33-Protocol Universe](#6-the-33-protocol-universe)
7. [Full Task Universe — Remaining Protocols in Executable Detail](#7-full-task-universe)
8. [Phased Roadmap — Phase 3 Close → Phase 4 → Phase 5 Quality Bar → Handover → Endgame](#8-phased-roadmap)
9. [Integration Protocol — Contracts Across Layers, Agents, Systems](#9-integration-protocol)
10. [Testing Protocol — Pyramid, CI Enforcement, Regression Gates](#10-testing-protocol)
11. [Deployment Protocol — Sovereign Infrastructure, Zero-Downtime, Rollback](#11-deployment-protocol)
12. [Eternal Optimization Protocol — Self-Evolve, Drift, Retrain, Quarterly Scoring](#12-eternal-optimization-protocol)
13. [Guru & Agent Capability Maximization Mandate](#13-guru--agent-capability-maximization-mandate)
14. [Completion Checklist — Phase 3 → Phase 5 → Handover → Endgame → Eternal State](#14-completion-checklist)
15. [The Eternal Completion Doctrine](#15-the-eternal-completion-doctrine)
16. [Immediate Next 72 Hours](#16-immediate-next-72-hours)
17. [Living References + File Tree of Canon](#17-living-references--file-tree-of-canon)
18. [Final Guru Blessing](#18-final-guru-blessing)

---

## 1. EXECUTIVE OVERVIEW

### 1.1 What NRG Is, Reduced to One Sentence

**A professor types "Who is doing the best research in hydrogen catalysis?" — and the system figures out everything else on its own, from a 600 GB government database, without leaking a single byte.**

That is the product. Everything in this audit serves that sentence.

### 1.2 Measured State — 2026-04-24

| Dimension | Value | Source of truth |
|---|---|---|
| Tests passing | **1,140 / 1,204** (95% pass rate; 11 fail, 53 skipped) | `pytest` last run |
| Protocols (total universe) | **33** | BACKLOG.md + QUALITY_BAR.md Phase 5 |
| Protocols complete | **18 fully + 9 substantively (Phase 4 + Phase 5)** | BACKLOG.md status matrix |
| Protocols remaining | **4 Phase 3 closeout + ~6 endgame + 1 handover** | this document |
| SQL accuracy (Dhairya bench) | **41 %** baseline, target **≥ 85 %** | `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` |
| Schema: dev vs prod | **18 tables** (SQLite) vs **58 tables** (PostgreSQL) | `db_struct.sql` |
| LLM mesh worst-case latency | **15 s hard cap** (was 270 s) | Protocol #11 in progress |
| RBAC personas | **6 configured** (researcher, government, industry, peer_reviewer, department_head, student) via YAML | `src/auth/rbac_policies.yaml` |
| Quality Bar compliance | **2 / 6** (PII ✓, Vector Drift ✓) — #35/#37/#39 code written, not yet integration-verified | `.claude/QUALITY_BAR.md` |
| Audit chain | HMAC-SHA256, 0 errors, thread-safe, per-user binding written (#35) | `src/audit/` |
| Fine-tune pipeline | Collector + GOLD/SILVER/BRONZE/REJECT grader + stratified exporter written, **not yet collecting live** | Protocols #22 + #40 |
| Frontend | Three persona dashboards exist, **disconnected from live API** (static mockups in places) | Protocol #24 partial |
| Deployment | Dockerfile + GH Actions CI + compose-prod written; **no sovereign-infra deploy yet** | Protocol #25 partial |
| Knowledge graph | Loader exists, zero imports; SQL rCTE sufficient for MVP | Deferred behind `FEATURE_KG` |

### 1.3 Verdict of V4

**NRG has crossed the valley.** The architecture is sound, the 6-node pipeline is functional, the Quality Bar is encoded into law, the RBAC is generalized beyond 3 tiers, the audit chain is per-user signed, the schema bridge to 58 tables is written, the fine-tune bridge is ready to collect.

**NRG has not yet summited.** The remaining work is concentrated, not scattered: (a) close Phase 3 with test realignment + SQL accuracy to ≥ 85 % + schema migration applied + resilient mesh + observability, (b) integration-verify the 6 Hard Constraints so compliance reads **6 / 6**, (c) reconnect frontend to live API, (d) deploy on sovereign infrastructure, (e) hand over to the client at IIT Gandhinagar. The endgame (fine-tune local model) is a post-handover multi-sprint track that the V4 roadmap maps but does not require for handover.

**V4 is the terminal audit.** Every remaining path is enumerated. Every protocol has acceptance criteria. Every agent assignment lists the skills they must employ. After V4 executes, NRG is client-deliverable.

### 1.4 The Three Sentences the Client Needs to Hear

> *"NRG is a sovereign AI platform. The 600 GB database stays on Indian soil. Every query is verified and cited. Three user tiers see only what they're allowed to see. The system is architecturally incapable of leaking."*
>
> *"We have shipped the platform. It runs on Kubernetes on the sovereign cluster. It serves three tier-specific dashboards. It reads from the 58-table PostgreSQL schema your team provided. It meets P99 < 500 ms, ≥ 1 000 concurrent users. We have 6 / 6 Hard Constraint compliance verified in CI."*
>
> *"The endgame is a fine-tuned Llama model that has internalized your data. It's on the 18-month horizon. The training loop is already collecting. Every query users ask today is training data for the model that will answer them instantly tomorrow."*

If V4 executes, those three sentences become defensible fact. That is the definition of handover-ready.

---

## 2. POST-V3 ELEVATION SUMMARY

V3 was the **delivery blueprint** — 40 agent tasks, 8 sprints, the target architecture. V3 assumed a messy starting state: empty join tables, broken venv, port collisions, drifting `.env.example`, overblocking PII regex, SQLite-only 18 tables.

Between V3 and V4, the following elevations were completed — they are why V4 can be *short on refactor and long on closeout*:

### 2.1 Workflow System Rebuilt (Operational Layer)

| Artifact | What it does |
|---|---|
| `.claude/GURU_PROTOCOL.md` | Codified Guru identity, ═══ protocol format, evolution loop, memory architecture |
| `.claude/AGENT_WARFARE.md` | Role hierarchy (Architect → CTO/CFO/Mentor → Execution agents → Guardian), self-evolution cycle, skill inventory (91 total) |
| `.claude/NRG_CONSTITUTION.md` | The Agent constitution — 9 clauses governing every AI response (zero-leakage, ambiguity resolution, hybrid retrieval, synthesis cascade, output discipline, session safety, 6 Hard Constraints, temporal RBAC, non-repudiation) |
| `.claude/QUALITY_BAR.md` | The 6 Hard Constraints + current compliance snapshot + enforcement clauses |
| `.claude/memory/*` | Persistent brain — `user_profile`, `project_nrg`, `feedback_workflow`, `bugs_frontend_crashes`, `reference_three_data_sources`, `reference_dhairya_benchmark`, `reference_guru_shishya`, `reference_installed_skills` |
| `.agents/AGENTS.md` + `.agents/prompts/shishya_universal.md` | Agent operating manual + 6-section Shishya framework (Task Reception → Execution Plan → Live Evolution → Deliverables → Skills Transmission → Reflection) |
| `.claude/prompts/guru_universal.md` | Guru's 5-section framework (Gap Analysis → Value Assessment → Priority Fix → Agent Tasks → Ship Checklist) + Self-Evolution Engine |

**Outcome**: every task the Guru assigns now goes through a ═══ protocol block with GURU ASSIGNMENT NOTE, phased ACTION, ≥ 3 SKILLS TO USE, AGENT INSTRUCTIONS verbatim block, ACCEPTANCE CRITERIA that verify the 6 Hard Constraints. The system is no longer a pile of tasks — it's an operating system.

### 2.2 Three Data Sources Framework

Three external inputs drive every NRG decision, permanently:

1. **Core_Idea_Clean.md** — client's final crystallized vision, product truth, immutable
2. **SQL_AUDIT_REPORT_DHAIRYA.md** — external engineer's 17-query benchmark, 41 % baseline, every SQL change regresses against this
3. **db_struct.sql** — the 58-table PostgreSQL production schema from the client

Every protocol cross-references the 3. Every agent reads them before starting. Every `/self-evolve` pass verifies they are current.

### 2.3 The 91-Skill Inventory

| Pool | Count | Where |
|---|---|---|
| Claude Cowork (Guru-only) | 39 | `.claude/skills/` + upstream Cowork plugins |
| Agent-only execution skills | 52 | `.agents/skills/` |
| Total | **91** | — |

Every protocol ACTION block must specify ≥ 3 skills. Every agent must read the SKILL.md of every listed skill before starting. This is the **skill maximization mandate** — operationalized, not aspirational.

### 2.4 The 6 Hard Constraints Encoded

The Quality Bar (`.claude/QUALITY_BAR.md`) elevates 6 constraints from "goals" to "acceptance-blocking laws":

1. DPDP-compliant Indian PII detection (PAN/Aadhaar-Verhoeff/mobile/email/passport/GSTIN/bank) — **✓ compliant**
2. Per-user audit binding with multi-party attestation — **code written (#35), integration-verify pending**
3. Multi-hop intent decomposition (DAG planner) — **code written (#37), integration-verify pending**
4. Production SLOs (P99 < 500 ms, ≥ 1 000 concurrent) — **SLO framework exists, numbers not yet proven under load**
5. Vector drift monitoring with auto-retrain trigger — **✓ drift script exists, auto-trigger integration pending (#12)**
6. Schema allowlist before cloud LLM exposure — **code written (#39), integration-verify pending**

**Delta since V3**: V3 named these constraints as "acceptance gates F/N/D/C". V4 promotes them to the **eternal bar**. They are the six commandments now. Every protocol that touches security/audit/RBAC/egress must verify them.

### 2.5 Scale + Architecture Elevations (since V3)

| Area | V3 state | V4 state |
|---|---|---|
| RBAC | 3 hardcoded tiers | **6 YAML-configured personas** via `RBACPolicyEngine` — adding persona = one YAML entry |
| Schema awareness | 18-table SQLite only | **Dual-schema extractor** (SQLite dev + PostgreSQL prod, 58-table), Alembic migration written |
| Audit binding | Chain-level HMAC | **Per-user derived keys**, JWT kid + request fingerprint, multi-party co-sign (API + DB layer) |
| Planner | Flat sub-query list | **DAG decomposition**, topological executor, context passing between nodes |
| LLM mesh latency | 270 s worst-case | **15 s hard cap**, health-weighted routing, parallel racing, graceful degradation messages |
| Egress | Schema fingerprint defense only | **Schema allowlist YAML + egress guard** wraps every LLM call, blocks non-allowlisted columns |
| Fine-tune path | Collector script stub | **Full pipeline** — collector + GOLD/SILVER/BRONZE/REJECT grader + stratified exporter (by tier × route × query-type × grade) |
| Frontend | Static mockups + API client stub | **Three tier-specific dashboards + Admin MetricsDashboard + JWT auth flow** (API reconnection still partial) |
| Deployment | docker-compose dev-only | **Multi-stage Dockerfile (< 300 MB), nginx + TLS, GH Actions CI, docker-compose.prod.yml, zero-downtime deploy script, /health endpoint** — sovereign-infra deploy itself pending |

### 2.6 What Remains (V4 Focus)

Six buckets, covered exhaustively in Sections 6–8:

1. **Phase 3 closeout**: test realignment (#19), schema migration applied (#21), SQL ≥ 85 % (#20), resilient mesh finalize (#11), observability complete (#12).
2. **Quality Bar integration validation**: 2/6 → 6/6 by running the integration tests on #35/#37/#39 against live infra (new Protocol #41).
3. **Frontend API reconnect**: replace remaining mockGraphData paths with live `/query/graph`, `/stats`, `/publications` endpoints (extends #24, new Protocol #42).
4. **Sovereign deployment**: Helm chart, Vault-agent sidecar, cert-manager, deploy on NIC/MeitY infra (extends #25, new Protocol #43).
5. **Client UAT + Handover**: run 3-persona UAT with actual IIT-GN stakeholders, finalize docs/runbooks/pitch deck (new Protocol #44).
6. **Endgame fine-tune path**: live training data collection → base model selection → QLoRA fine-tune → RL loop → two-brain serving → periodic retrain (Protocols #29–#34, post-handover multi-sprint track).

---

## 3. THE 3 DATA SOURCES & THE 6 HARD CONSTRAINTS

### 3.1 The 3 Data Sources (Eternal Inputs)

| # | Source | Owner | File | Authority |
|---|---|---|---|---|
| 1 | **Core Idea** | Professor / client at IIT-GN | `Core_Idea_Clean.md` | Product truth. Immutable. Every architectural call must reduce to a line from this file. |
| 2 | **Dhairya SQL Audit** | SesDhairya (external engineer, *not* our team) | `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` (+ original `.sql`) | SQL accuracy benchmark. Every Text-to-SQL change re-runs these 17 queries. Target 41 % → ≥ 85 %. |
| 3 | **Official Production Schema** | Professor / client | `db_struct.sql` (pg_dump from PostgreSQL 14.20, dumped 2026-01-09) | 58-table prod schema. Authoritative. Every schema hint, SQL prompt, Alembic migration targets this. |

**Rule**: if any of the three files updates, re-run the `/self-evolve` pass — update `CLAUDE.md` 3-Data-Sources section, update BACKLOG status flags, regenerate schema hints, re-run Dhairya regression bench.

**Schema gap — forever documented**:

| Environment | Tables | Status | Notes |
|---|---|---|---|
| Dev SQLite | 18 | Working, simplified | For fast iteration; Dhairya queries cannot run here |
| Prod PostgreSQL | 58 | Official (from client) | Dhairya queries target this. 40 tables not in dev. |

**Missing from dev (must migrate for SQL accuracy work)**: `academic_courses_details`, `innovation_grant_from_govt`, `innovations_at_various_stages_of_technology_readiness_level`, `combined_ipo_patent_data`, `incubation_details`, `financial_expenses_capital`, `financial_expenses_operational`, `actual_student_strength`, `phd_students`, `sanctioned_intake`, `placements_and_higher_studies`, `seed_funding`, `fdi_investment`, `startup_recognition`, `scraped_data`, `expertise`, `faculty_details`, `faculty_strength`, `patents_details`, `research_consultancy_details_*`, `nirf_*`, plus Django auth tables.

### 3.2 The 6 Hard Constraints (Eternal Acceptance Bar)

| # | Constraint | Location of Enforcement | Acceptance Test | Current |
|---|---|---|---|---|
| 1 | **DPDP-compliant Indian PII** — PAN, Aadhaar (with Verhoeff checksum, not just 12 digits), Indian mobile `+91\|0?[6-9]\d{9}`, email, passport, GSTIN, bank account | `src/security/pii/` | `tests/security/test_pii_indian.py` — 0 false negatives on Indian PII corpus | ✓ |
| 2 | **Per-user audit binding (non-repudiation)** — every event carries `user_id`, `persona`, `jwt_jti`, `jwt_kid`, `request_fingerprint` (IP + UA + TLS session id); HMAC signed with per-user derived key; API and DB layer co-sign | `src/audit/__init__.py`, `src/audit/per_user_keys.py` | `verify_chain()` returns `False` if any event's per-user signature fails; 100-event tampering simulation | ⚠ code written, integration-verify pending |
| 3 | **Multi-hop intent decomposition** — Planner emits `{nodes: [...], edges: [(parent_id, child_id)]}` DAG; Executor runs topologically; context passes between nodes | `src/orchestration/nodes/planner.py`, `src/orchestration/nodes/executor.py` | `tests/orchestration/test_multi_hop_planner.py` — 10 fixtures, all decomposed correctly; e.g. "Compare Gujarat and Karnataka's AI output over 5 years and show the funding gap" → ≥ 4 sub-queries with dependencies | ⚠ code written, integration-verify pending |
| 4 | **Production SLOs** — P99 < 500 ms for analytical queries, ≥ 1 000 concurrent users, no degradation | `tests/performance/test_slo_compliance.py`, `tests/load/test_slo_under_load.py` | SLO tests run in CI, block merge on breach; 5 consecutive breaches → CRITICAL log | ⚠ framework exists, numbers not yet proven |
| 5 | **Vector drift monitoring + auto-retrain** — embedding drift cosine shift > 0.05 vs reference vectors triggers re-index event within 60 s | `scripts/vector_drift_check.py`, `src/observability/metrics.py` | Manual drift simulation triggers retrain event within 1 min | ✓ script exists, auto-trigger integration pending |
| 6 | **Schema allowlist before cloud LLM exposure** — every outbound LLM payload inspected against `src/security/egress_allowlist.yaml`; only allowlisted table/column names may appear; raw schema blocked | `src/security/egress_guard.py`, `src/security/egress_allowlist.yaml` | `tests/security/test_egress_allowlist.py` — 20+ leak attempts, all blocked, all audit-logged | ⚠ code written, integration-verify pending |

**Enforcement clauses** (inherited from QUALITY_BAR.md §Enforcement):

- **Protocol-level**: Every ═══ task's ACCEPTANCE CRITERIA must include any of the 6 constraints it touches.
- **CI-level**: Any test in `tests/security/`, `tests/performance/`, `tests/load/` failing blocks merge.
- **Audit-level**: `/self-evolve` runs a Quality Bar Compliance scorecard quarterly.
- **Guru-level**: Before marking any protocol COMPLETE in BACKLOG, Guru verifies the 6 are not regressed.

**The rule**: if any agent or Guru response claims "complete" on a task touching the 6, compliance is *verified* before acceptance, not *claimed*.

**V4 mandate**: bring compliance to **6 / 6** before handover. That is the work of Protocol #41 (Quality Bar Integration Validation) in Section 7.

---

## 4. DEEP ANALYSIS — EVERY MODULE, EVERY FIELD

This section walks every layer of the system, names the modules, states what exists, what needs to be elevated, and how the 6 Hard Constraints land inside each.

### 4.1 Layer 1 — Data

**Purpose**: 600 GB curated research corpus — researchers, labs, publications, funding, patents, NIRF data, startup registrations, faculty expertise, course data, placement stats. Never leaves Indian servers.

**Current state**:

- **Dev**: SQLite `nrg_research.db` at repo root, 18 tables. Synthetic data: 200 researchers, 500 publications, 24 institutions, 50 labs, 100 funding records. **Every join table is empty** (researcher_publications = 0, researcher_labs = 0, keywords = 0, publication_keywords = 0). Graph has no edges. Protocol #4 (Phase 3) seeds join tables.
- **Prod**: PostgreSQL, 58 tables per `db_struct.sql`. Alembic migration `alembic/versions/add_production_tables_001.py` written (#23), **not yet applied** to a live PostgreSQL instance. Data migration script `scripts/migrate_data_to_postgresql.py` exists (#23), **not yet run** against the 600 GB corpus (which we have not yet received from client).
- **Data hygiene**: three ID namespaces coexist in test/demo data: Gemini (`RES_1001`), Glm (`RES-00001`), Minimax (`RES-000000`). Merge verdict documented in `docs/security/DATA_SOVEREIGNTY_MERGE_VERDICT_2026-04-22.md`. Rationalization to a single namespace must happen before 600 GB ingestion.

**What V4 requires**:

1. **Schema bridge applied**: run the Alembic migration on a staging PostgreSQL, verify all 58 tables exist, column types match `db_struct.sql`, foreign keys valid (Protocol #21 closeout).
2. **Seed the join tables** with synthetic-but-valid edges so the graph path (if `FEATURE_KG` enables it) and hybrid queries return non-empty results (Protocol #4 closeout).
3. **Dual-schema extractor verified**: the Text-to-SQL layer must choose SQLite schema in dev and PostgreSQL schema in prod based on `DATABASE_URL` — test in CI with both profiles.
4. **600 GB ingestion plan**: document the hand-off protocol — how client delivers the corpus (SFTP with HMAC manifest + GPG encryption at rest), how we ingest (streaming `COPY` into staging tables → dbt-style transforms → promote to serving tables), how we verify (row counts against manifest, checksum spot-checks, schema diff against `db_struct.sql`). This is Protocol #43 in the handover package.

**Sovereign enforcement**:

- Postgres lives on the Indian-soil cluster. No replication outside the boundary. WAL archival to encrypted object storage on the same cluster.
- Row-Level Security (RLS) policies at the DB layer, not just API — a dropped WHERE clause cannot leak Tier 2 data to a Tier 3 session.
- Backup encryption with KMS keys stored in Vault (sovereign cluster).

---

### 4.2 Layer 2 — Knowledge (Structured)

**Purpose**: query-efficient representation of researchers, publications, funding, collaborations; optionally, a Neo4j knowledge graph for multi-hop collaboration queries.

**Current state**:

- SQLAlchemy models in `src/models/` reflect 18-table SQLite; need regeneration against the 58-table schema after migration applied (automate via `sqlacodegen` into a `src/models/production/` submodule gated by `DATABASE_URL`).
- Knowledge graph: `src/knowledge_graph/loader.py` imports `neo4j`, `sys.exit(1)` on missing driver, **zero imports from `src/`** — dead code. ADR: KG is optional behind `FEATURE_KG` flag (deferred per V3 ADR-004). SQL recursive CTE covers collaborator-of-collaborator for MVP.
- Junction tables documented in Core_Idea_Clean.md §Data Model: `researcher_publications`, `researcher_labs`, `publication_keywords`, `keywords`. All present in SQLite, all empty.

**V4 requirements**:

1. Regenerate SQLAlchemy models from `db_struct.sql` via `alembic revision --autogenerate` or `sqlacodegen`; commit as `src/models/production/*.py`.
2. Seed join tables with ≥ 1 000 edges each for demo realism (Protocol #4).
3. Keep KG behind `FEATURE_KG=false` by default. Protocol #32 (Two-Brain Orchestrator) may activate KG later for collaboration intuition during fine-tune; not required for handover.

---

### 4.3 Layer 3 — Retrieval (Dual-Path Hybrid)

**Purpose**: turn natural-language questions into the right shape of fact, via two parallel paths merged by the synthesizer.

#### 4.3.1 Text-to-SQL Path

**Modules**: `src/skills/text_to_sql/` — schema_extractor, sql_generator, validator, query_context.

**Current state**:

- Schema extractor supports both SQLite + PostgreSQL (dual-schema), pulls column types and foreign-key info.
- SQL generator uses LLM (Gemini primary) with schema hints + CTE templates + value synonyms (derived from Dhairya failure patterns).
- Validator uses `sqlglot` — AST-level syntax + allowlist check + read-only enforcement (no INSERT/UPDATE/DELETE reachable).
- Query context enriches the prompt with top-k relevant schema fragments.
- **Dhairya bench: 41 % baseline.** Avg response 7.2 s. Target: **≥ 85 % accuracy, < 3 s** (Protocol #20).

**Gaps & elevations**:

- Few-shot examples derived from Dhairya's 7 correct queries must be added to the prompt (in progress — Protocol #20 Fortify phase).
- Self-correction loop: after SQL runs, if result rowcount is zero or SQL error, re-prompt with the error for one retry (Protocol #20 Elevate phase).
- Completeness validator: a new post-execution check that compares column coverage of generated SQL against the query's inferred requirements (Protocol #20 Immortalize phase — already started).
- **Hard Constraint link**: Constraint #6 (schema allowlist) enforces that the LLM prompt itself contains only allowlisted schema fragments. A prompt leaking raw `pg_catalog` is an audit event.

#### 4.3.2 RAG Path

**Modules**: `src/skills/rag/` — embedder (bge-m3), qdrant_client, reranker (bge-reranker-v2-m3), chunker.

**Current state**:

- Qdrant single-node, 19 322 vectors loaded, 384-dim (sentence-transformers/all-MiniLM-L6-v2 currently wired; bge-m3 is the target per V3 ADR-005).
- Sharding plan (Protocol #23) — 4 shards with collection aliasing for zero-downtime re-index — **configured, not yet deployed**.
- Reranker: code present, not yet integrated into the `/query` path.
- Chunking: simple fixed-window today; semantic-chunking with paragraph boundaries is a V4 elevation.

**Gaps & elevations**:

- Switch embeddings to `bge-m3` (IndicBERT for Hindi+Tamil later) — Protocol #12 tail.
- Integrate reranker for top-10 → top-3 re-scoring — Protocol #12 tail.
- Activate sharded Qdrant in staging, test zero-downtime re-index (Protocol #23 closeout).
- Vector drift: `scripts/vector_drift_check.py` runs weekly; if cosine shift > 0.05 against reference centroids, emit `vector.drift.detected` event to re-index queue. Hard Constraint #5.

#### 4.3.3 Intent Router

**Module**: `src/orchestration/nodes/router.py`.

**Current state**: 51/51 tests passing. Two-stage routing: keyword heuristic → LLM tiebreaker when ambiguous. Classifies into `text_to_sql` / `rag` / `hybrid`.

**V4 requirement**: expand to emit `complexity_hint` (trivial / simple / moderate / complex / synthesis-heavy) so Complexity Router (#38) can match to model size — already delivered in Protocol #38.

---

### 4.4 Layer 4 — Reasoning (Synthesis + Verification)

**Purpose**: turn retrieved facts into a cited, hallucination-free answer at the right tier.

#### 4.4.1 Planner (with DAG decomposition)

**Module**: `src/orchestration/nodes/planner.py` + `Plan.dag_nodes / dag_root_id / is_dag`.

**Current state**: after Protocol #37, Planner emits a reasoning DAG. Example for "Compare Gujarat and Karnataka's AI research output over 5 years and show the funding gap":

```
   ┌── n1: list Gujarat AI researchers 2021-2026
   │       └── n3: aggregate publications for Gujarat AI
   │             └── n5: aggregate funding for Gujarat AI
   │
root
   │
   └── n2: list Karnataka AI researchers 2021-2026
           └── n4: aggregate publications for Karnataka AI
                 └── n6: aggregate funding for Karnataka AI
                       └── n7: compute funding gap (n5 – n6)
```

Executor walks topologically, feeds parent results into child prompts as context.

**V4 requirement**: confirm integration — Hard Constraint #3 acceptance test must run in CI and block merge on breach (Protocol #41).

#### 4.4.2 Executor

**Module**: `src/orchestration/nodes/executor.py`.

**Current state**: topological DAG execution implemented. Runs `TextToSQLSkill` and `RAGSkill` in parallel (asyncio.gather) when the node needs both. Parent→child context passed as a compact dict (not full raw rows — avoids blowing up LLM context).

**V4 elevation**: add circuit-breaker per path so a failing RAG doesn't block SQL results; degrade gracefully with an evidence-annotated response.

#### 4.4.3 Synthesizer (3-tier cascade)

**Module**: `src/orchestration/nodes/synthesizer.py`.

**Cascade**:

1. **Cloud LLM** — NVIDIA NIM / Gemini / Claude / OpenAI / Azure / Minimax (mesh). Only the user question + *retrieved facts* go out. Protocol #38 routes by complexity.
2. **Local SLM** — Llama-3.1-8B Q4_K_M GGUF via llama.cpp. Fully offline.
3. **Rule-based** — deterministic table formatter. Always succeeds.

**Current state**: 15 s hard cap, health-weighted routing, parallel racing, cache fingerprint (Protocol #38 + #11).

**V4 elevation**: wire the egress guard (Protocol #39, Hard Constraint #6) around every cloud call. Any non-allowlisted schema fragment in the prompt → block + audit + fall through to local SLM.

#### 4.4.4 Verifier

**Module**: `src/orchestration/nodes/verifier.py`.

**Current state**: citation faithfulness check — every factual claim in the synthesized answer must trace to `[cite:pub_id:chunk_id]` or a SQL row id. Retries synthesis with additional evidence if a claim is unsupported.

**V4 elevation**: add an adversarial verifier — takes the synthesized answer and the retrieved evidence and produces a confidence score (high/medium/low) + an explicit list of assumptions made during ambiguity resolution. These are surfaced to the user per Constitution §4.

---

### 4.5 Layer 5 — Interface (Frontend)

**Purpose**: three dashboards, one API client, JWT auth flow, natural-language search bar.

**Current state**:

- `frontend/src/App.tsx` — AuthProvider + AppShell pattern; renders dashboards by role.
- Three dashboards: `ResearcherDashboard`, `GovernmentDashboard`, `IndustryDashboard`.
- `MetricsDashboard` (admin) — wired to `/api/metrics`.
- `authService.ts` — localStorage session, auto-refresh on 401.
- `queryService.ts` — calls `/query`, `/query/graph`, `/stats`, `/publications`; **`/query/graph` does not exist** in backend → falls back to `mockGraphData()`.
- `vite.config.ts` proxies `/login /refresh /logout /query /researchers /health`; **missing `/stats`, `/publications`, `/query/graph`** → 404 via dev proxy.

**V4 requirements**:

1. Add missing backend endpoints: `GET /stats` (tier-aggregated), `GET /publications` (paginated), `POST /query/graph` (returns collaboration subgraph — stub with SQL recursive CTE for MVP). Protocol #42.
2. Add missing proxy paths to `vite.config.ts`. Protocol #42.
3. Remove `mockGraphData()` fallback — if the endpoint errors, show a clean error state, not fake data. Protocol #42.
4. Add tier-aware UI: Tier 1 sees email/phone columns; Tier 2 sees aggregated counts; Tier 3 sees only name + research area. Already partially implemented; verify with `tests/e2e/test_persona_flows.spec.ts` (Playwright). Protocol #24 closeout.
5. Accessibility: WCAG AA color contrast, keyboard navigation, screen-reader labels. Protocol #24 closeout.

---

### 4.6 Cross-Cutting: Security

**Modules**: `src/security/gateway/prompt_sanitiser.py`, `src/security/pii/`, `src/security/egress_guard.py`, `src/security/egress_allowlist.yaml`, `src/auth/*`.

**Current state — after V3 → V4 elevations**:

| Concern | Before | After |
|---|---|---|
| PII regex overblocking | `(?i)role.*play`, `(?i)as.*ai`, `(?i)hypothetical` false-positive on legitimate research questions | Replace with intent-classifier scoring + stricter Indian PII patterns; Constraint #1 |
| `sanitise_prompt` tuple bug | Returns `(sanitised, detected_pii)` but `detected_pii` never populated | Fixed; populated list returned |
| JWT | RS256 asymmetric, 1 h expiry | + Rotating kid, JWKS endpoint at `/.well-known/jwks.json`, per-user derived audit key (#35) |
| Prompt injection detection | Regex list with heavy false positives | Scored detector with thresholds; false-positive regression corpus |
| Egress guard | Schema fingerprint only | **Schema allowlist** (#39) — YAML-driven; raw schema names blocked; prompt inspection |
| RBAC | 3 hardcoded tiers | 6 YAML personas (#26) + temporal window (#36) + column-level visibility |
| Audit binding | Chain-HMAC only | Per-user derived key + JWT kid + request fingerprint + API/DB co-sign (#35) |

**V4 integration validation required**:

- Full integration test of the egress guard against the live cloud LLM adapters — **Protocol #41**.
- 100-event tampering simulation for per-user audit binding — **Protocol #41**.
- Temporal RBAC regression under live queries — **Protocol #41**.

---

### 4.7 Cross-Cutting: Observability

**Modules**: `src/observability/tracer.py` (Langfuse, built, unconfigured), `src/observability/metrics.py` (Prometheus exporters).

**Current state**:

- Node-level timing spans emitted per pipeline step.
- Langfuse wired but not configured with a project key; switch to self-hosted Langfuse on the sovereign cluster for V4.
- `/api/metrics` endpoint for Prometheus scrape.
- SLO alerting: 5 consecutive breaches → CRITICAL log (Constraint #4 enforcement).
- Vector drift: cron-driven, emits to `src/observability/metrics.py`; auto-trigger to re-index queue pending (Constraint #5).

**V4 elevations**:

- Deploy Langfuse (self-hosted) on the sovereign cluster; turn on trace capture.
- Grafana dashboards for: p50/p95/p99 per node, SLO breach counter, Quality Bar scorecard (6 gauges), vector drift cosine, RBAC denial rate, audit chain length, cache hit rate.
- Audit the observability stack itself for egress — Langfuse payloads must not include retrieved facts or PII; only metadata + query fingerprint.

---

### 4.8 Cross-Cutting: RBAC (Generalized)

**Module**: `src/auth/rbac.py` + `src/auth/rbac_policies.yaml`.

**Current state**:

- 6 personas configured: `researcher`, `government`, `industry`, `peer_reviewer`, `department_head`, `student`.
- Declarative YAML: each policy has `allowed_tables`, `allowed_columns_per_table`, `aggregation_only`, `visibility_window` (temporal), `scope` (`all | institution_only | department_only`), `audit_level`.
- Middleware auto-filters SQL + synthesizer output by policy.
- Admin CRUD at `/api/admin/rbac` (admin-only).
- Hot-reload on YAML change.

**V4 elevations**:

- 100-test regression suite across all 6 personas × query types (Protocol #41).
- Temporal window enforcement regression (Protocol #36 closeout).
- RBAC denial rate dashboard (Grafana).

---

### 4.9 Cross-Cutting: Audit Chain (Non-Repudiation)

**Module**: `src/audit/__init__.py` + `src/audit/per_user_keys.py`.

**Current state**:

- HMAC-SHA256 chain over `{prev_hash, event, timestamp, user_id, jwt_jti, jwt_kid, request_fingerprint}` — per-event per-user signed.
- `RotatingSaltStore` — daily rotation, previous salt kept for 7 days to verify old events.
- `PerUserKeyManager` — derives signing key from `HKDF(user_id || kid || salt)`.
- `build_request_fingerprint(ip, ua, tls_session_id)` embedded in event.
- `verify_chain()` returns 3-tuple: `(ok: bool, broken_event_idx: int | None, reason: str)`.
- Thread-safe (file-lock + in-memory append-only log flushed at event boundary).

**V4 integration validation**:

- 100-event tampering simulation where (a) an event is mutated, (b) a JWT is swapped between users, (c) a signature is removed — chain verification must catch all three (Protocol #41).
- WAL-style segment sealing: every 10 000 events, seal a segment with a Merkle root published to a public-facing (sovereign) timestamping service.

---

### 4.10 Cross-Cutting: Fine-Tuning Bridge (The Endgame's On-Ramp)

**Module**: `src/training/collector.py`, `src/training/grader.py`, `src/training/export.py`, `src/training/stratified_sampler.py`.

**Current state**:

- Collector logs: `(query, plan, sub_queries, route, retrieved_facts, synthesized_answer, verification_result, user_feedback)` per query.
- Grader: GOLD (verified, high-confidence, user-approved) / SILVER (verified, high-confidence) / BRONZE (verified) / REJECT (failed verification or low confidence).
- Exporter: writes JSONL (HuggingFace) + ShareGPT formats; stratified by (tier × route × query-type × grade).
- Not yet collecting live — requires Protocol #43 (sovereign deploy) to have users.

**V4 role**: collection is a Phase 6 activity. The code is ready; the runtime is not. Endgame section (Protocols #29–#34) details the post-handover fine-tune path.

---

### 4.11 Cross-Cutting: Deployment

**Modules**: `Dockerfile.api`, `docker-compose.yml`, `docker-compose.prod.yml`, `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `scripts/deploy.py`, `nginx/` (TLS termination).

**Current state**:

- Multi-stage Dockerfile < 300 MB, distroless base.
- GH Actions CI: lint (ruff) + type-check (mypy) + test (pytest) + security (bandit + pip-audit) + build (docker).
- `docker-compose.prod.yml` — Postgres 16 + Qdrant 1.9.2 + Redis 7 + Kong 3.6 + API + nginx.
- `scripts/deploy.py` — blue-green with rollback on `/health` fail.
- **Not yet deployed to sovereign infra** (NIC/MeitY cluster) — Protocol #43.

**V4 requirements**:

- Helm chart with values for dev/staging/prod.
- Vault-agent sidecar for secrets (no env-var secrets in pod spec).
- cert-manager for automatic TLS.
- NetworkPolicies that block egress except to allowlisted LLM providers.
- K8s PodSecurityPolicy / PSS `restricted`.
- Backup CronJob for Postgres + Qdrant to encrypted sovereign object storage.

---

### 4.12 Quality Bar Compliance, Per Module

| Module | C1 PII | C2 Audit | C3 DAG | C4 SLO | C5 Drift | C6 Egress |
|---|---|---|---|---|---|---|
| prompt_sanitiser | ✓ | n/a | n/a | n/a | n/a | n/a |
| audit/ | n/a | ⚠ pending | n/a | n/a | n/a | n/a |
| planner | n/a | ✓ (logs event) | ⚠ pending | n/a | n/a | ⚠ pending |
| executor | n/a | ✓ | ✓ (topo) | ⚠ | n/a | n/a |
| synthesizer | n/a | ✓ | n/a | ⚠ | n/a | ⚠ pending |
| rag skill | n/a | ✓ | n/a | ⚠ | ✓ | n/a |
| text_to_sql | n/a | ✓ | n/a | ⚠ | n/a | ⚠ pending |
| rbac | ✓ (tier filter) | ✓ | n/a | n/a | n/a | n/a |
| egress_guard | n/a | ✓ | n/a | n/a | n/a | ⚠ pending |

**Reading**: three constraints (C1, C5) are fully green. Three (C2, C3, C6) have code but require integration verification. One (C4) has framework but unproven numbers. **Protocol #41** closes all four pending cells.

---

## 5. CURRENT TEST REALITY

**Last measured**: 1,140 passed / 11 failed / 53 skipped / 1,204 total. 95 % pass rate.

The 11 remaining failures are concentrated in test-code drift (not production-code bugs) introduced by recent hardening (Protocols #16/#17/#18). Categorized:

| # | Category | Count | Root cause | Fix class | Owner |
|---|---|---|---|---|---|
| 1 | Audit event-schema drift | 3 | Tests built for pre-#35 `AuditEvent` (no jwt_kid/request_fingerprint fields) | Update test fixtures to new schema | testing agent |
| 2 | Security: PII expectation | 2 | Tests assume old over-blocking regex still flags "role play" | Update to new scored detector thresholds | testing agent |
| 3 | Tier-filter SQL rewrite | 2 | Tests assert old 3-tier SQL, new 6-persona RBAC rewrites differently | Re-record expected SQL for peer_reviewer/department_head/student | testing agent |
| 4 | E2E: frontend ↔ backend | 1 | Playwright test hits `/query/graph`, endpoint missing | Fix after Protocol #42 (add endpoint) | frontend+testing |
| 5 | Contract test: `/stats` | 1 | Response-shape mismatch after tier-aggregation refactor | Update contract fixture | backend agent |
| 6 | Chaos: LLM timeout | 1 | Test uses 60 s timeout, new hard cap is 15 s | Update test timeout to < 15 s | testing agent |
| 7 | SLO: P99 load | 1 | Old test asserted P99 < 1 s, new bar is < 500 ms; test needs tightening not relaxing | Tighten to 500 ms; run under load | testing+perf agent |

**Protocol #19 (THE TEST REALIGNMENT)** is the vehicle; no production code changes are allowed in that protocol — test files only. After #19 + #42, the target is **1 204 / 1 204 passing** (53 skipped for tests that require external services not in CI — e.g., Langfuse live endpoint, Kong 3.6 container).

**CI gate**: after V4 executes, merge is blocked unless:

- 0 failing tests in `tests/security/*`, `tests/performance/*`, `tests/load/*`, `tests/orchestration/test_multi_hop_planner.py`, `tests/audit/test_chain.py`, `tests/rbac/test_policies.py`.
- `pytest --cov=src --cov-report=xml` ≥ 60 % coverage.
- Dhairya regression bench ≥ 85 % pass rate.

---

## 6. THE 33-PROTOCOL UNIVERSE

**Snapshot 2026-04-24**. Status tags: ✅ DONE (BACKLOG verified) / ⚙ SUBSTANTIVELY DONE (code written, integration-verify pending) / ◔ IN-PROGRESS (active sprint) / ⬜ PLANNED / ♾ ETERNAL (always on, no "done" state).

### 6.1 Phase 1 — Working Demo (Months 1–2) — foundational

| # | Name | Status | Notes |
|---|---|---|---|
| 1 | THE INTERFACE FORTRESS — ErrorBoundary on 3 dashboards | ✅ | — |
| 2 | THE ETERNAL SENTINEL — E2E infra | ✅ | — |
| 3 | THE INTELLIGENCE CORE — router + SQL injection defense | ✅ | 42 → 66 % |
| 4 | THE CONSENT GATEWAY — DPDP consent flow, auto-grant, revocation | ✅ | — |
| 5 | THE VERIFICATION ORACLE — citation verification in verifier | ✅ | — |
| 6 | THE KNOWLEDGE FORGE — Qdrant 19 322 vectors, HNSW green | ✅ | — |

### 6.2 Phase 2 — Data Sovereignty + Audit

| # | Name | Status | Notes |
|---|---|---|---|
| 7 | (merged) | — | — |
| 8 | THE DATA SOVEREIGNTY AUDIT — full merge verified | ✅ | source dir deletable |
| 9 | THE BROKEN CHAIN — audit rebuilt, 0 errors, thread-safe, versioned | ✅ | — |
| 10 | THE TEST FOUNDATION — module collision, 899 tests collecting | ✅ | upgraded to 1 204 |

### 6.3 Phase 3 — Hardening + Performance (CURRENT)

| # | Name | Status | Notes |
|---|---|---|---|
| 11 | THE RESILIENT MESH — LLM provider hardening | ◔ | 270 s → 15 s cap implemented; health-weighted routing + parallel racing in-progress |
| 12 | THE LIVING PIPELINE — observability + data ingestion | ◔ | metrics endpoint + drift script ✓; Langfuse wiring + auto-retrain trigger pending |
| 13 | THE UNBREAKABLE BRIDGE — DB pool + executor ThreadPool fix | ✅ | — |
| 14/15 | Router + Citation | ✅ | merged into #16 |
| 16 | THE FINAL GATE — router 51/51, 2-stage routing, eval dataset | ✅ | — |
| 17 | THE SOVEREIGN SHIELD — PII, JWT, RBAC, schema fingerprint | ✅ | — |
| 18 | THE PERFORMANCE CONTRACT — SLO targets, vector drift, load tests | ✅ | numbers to be proven — Protocol #11+#41 |
| 19 | THE TEST REALIGNMENT — fix 11 test-code mismatches | ◔ | see Section 5 classification |
| 20 | THE SQL ORACLE — 41 % → ≥ 85 % on Dhairya bench | ◔ | depends on #21 |
| 21 | THE SCHEMA BRIDGE — 58-table PostgreSQL integration | ◔ | migration written, not yet applied |
| 22 | THE FINE-TUNING BRIDGE — collector + grader + exporter | ✅ | not yet collecting live (needs Phase 4) |

### 6.4 Phase 4 — Scale + Frontend + Deploy

| # | Name | Status | Notes |
|---|---|---|---|
| 23 | THE SCALE WALL — SQLite → PostgreSQL + Qdrant sharding | ⚙ | dual-driver + Alembic + 4-shard config; staging deploy pending |
| 24 | THE FRONTEND RESURRECTION — 3 dashboards + admin metrics | ⚙ | built; live-API reconnect pending (Protocol #42) |
| 25 | THE DEPLOYMENT GATE — CI/CD + prod Docker + nginx | ⚙ | GH Actions + compose-prod built; sovereign-infra deploy pending (Protocol #43) |
| 26 | THE RBAC GENERALIZER — 3 tiers → N personas YAML | ✅ | 6 personas configured + admin CRUD + hot-reload |

### 6.5 Phase 5 — Quality Bar (FROM 2/6 → 6/6)

| # | Name | Status | Constraint | Notes |
|---|---|---|---|---|
| 35 | THE NON-REPUDIATION LOCK — per-user audit binding | ⚙ | C2 | code written, integration-verify pending |
| 36 | THE TEMPORAL POLICY — time-window RBAC | ⚙ | C (RBAC extension) | implemented, regression green; integration gate pending |
| 37 | THE MULTI-HOP PLANNER — DAG decomposition | ⚙ | C3 | planner + executor + tests written, integration pending |
| 38 | THE COMPLEXITY ROUTER — LLM pool match by complexity | ⚙ | (cost/latency) | classify_complexity + cache fingerprint written |
| 39 | THE SCHEMA ALLOWLIST — egress firewall | ⚙ | C6 | EgressGuard + allowlist YAML written, integration pending |
| 40 | THE STRATIFIED CURATOR — balanced fine-tune export | ✅ | (endgame prereq) | StratifiedSampler integrated into ExportPipeline |

### 6.6 New V4 Protocols — Quality Bar Integration + Handover + Endgame

| # | Name | Status | Owner |
|---|---|---|---|
| 41 | THE QUALITY BAR INTEGRATION VALIDATION — 2/6 → 6/6 | ⬜ | testing + security |
| 42 | THE FRONTEND-API RECONNECT — live `/query/graph`, `/stats`, `/publications` | ⬜ | backend + frontend |
| 43 | THE SOVEREIGN LANDING — Helm + Vault + cert-manager + NIC/MeitY deploy | ⬜ | devops + security |
| 44 | THE HANDOVER PACKAGE — UAT across 3 personas + docs + pitch deck + runbook | ⬜ | founder + writer + devops |
| 29 | THE LIVE COLLECTION — activate fine-tune collector on prod traffic | ⬜ | ml + backend (post-handover) |
| 30 | THE BASE MODEL SELECTION — Llama-3.1-8B → 70B shortlist, QLoRA harness | ⬜ | ml |
| 31 | THE RL LOOP — explore / evaluate / reward / iterate | ⬜ | ml |
| 32 | THE TWO-BRAIN ORCHESTRATOR — fine-tune + retrieval serving | ⬜ | backend + ml |
| 33 | THE FINE-TUNE SERVING + SAFETY GATE | ⬜ | ml + security |
| 34 | THE PERIODIC RETRAINING PIPELINE | ⬜ | ml + devops |

**Eternal protocols** (no done state, perpetually running):

| Name | Cadence | Owner |
|---|---|---|
| `/self-evolve` sprint retrospective | every sprint end | Guru |
| Quality Bar quarterly scoring | quarterly | Guru + testing |
| Dhairya regression | every SQL change | CI |
| Vector drift check | weekly cron | observability |
| Audit chain weekly verify | weekly cron | `/audit-check` |
| Dependency CVE scan | nightly | devops |
| Backup restore drill | monthly | devops |

**Total universe count**: 18 fully-done + 9 substantively-done + 5 in-progress (Phase 3 closeout) + 10 planned (4 V4-new + 6 endgame) + 7 eternal. The "33" is the *delta* universe that needs completion; eternal protocols are the *steady state*.

---

## 7. FULL TASK UNIVERSE — Remaining Protocols in Executable Detail

> The ═══ format below is the *only* format Guru uses to hand work to agents. Every block includes GURU ASSIGNMENT NOTE, phased ACTION (Fortify → Elevate → Immortalize), ≥ 3 SKILLS TO USE with reasons, AGENT INSTRUCTIONS verbatim, ACCEPTANCE CRITERIA that verify Elevation AND the 6 Hard Constraints touched, DEPENDS ON.
>
> Scope of this section: every *remaining* protocol on the critical path to handover + a condensed endgame track. Already-complete protocols (#1–10, #13–18, #22, #26, #40) are not re-protocoled.

---

```
═══════════════════════════════════════════════════════════════
TASK: #19 — THE TEST REALIGNMENT (fix 11 test-code mismatches)
AGENT: testing (primary) + backend (consult)
PRIORITY: P0-blocker
═══════════════════════════════════════════════════════════════

FILES:
  - tests/audit/test_chain.py
  - tests/security/test_pii.py
  - tests/security/test_injection.py
  - tests/rbac/test_tier_sql_rewrite.py
  - tests/e2e/test_persona_flows.spec.ts
  - tests/contract/test_stats_endpoint.py
  - tests/chaos/test_llm_timeout.py
  - tests/performance/test_slo_compliance.py
  (no production code — test files only)

PROBLEM:
  11 tests fail because they were authored against pre-#35/#37/#17/#11
  schemas and assumptions. Specifically:
    - 3 audit tests: AuditEvent now carries jwt_kid + request_fingerprint
    - 2 PII tests: scored detector replaces old broad regex
    - 2 tier-SQL tests: 6-persona RBAC produces different rewrites than 3-tier
    - 1 E2E test: hits /query/graph which doesn't exist yet (wait for #42)
    - 1 contract test: /stats shape changed after tier aggregation refactor
    - 1 chaos test: 60s timeout → 15s hard cap
    - 1 SLO test: P99 < 1s → must assert < 500ms under load

ACTION:
  Phase 1 — FORTIFY:
    - Pull the 11 failing tests, confirm root cause with traceback
    - Categorize per Section 5 matrix; split into PR-sized chunks (audit, security,
      rbac, chaos, perf, contract, e2e). Never mix categories in one PR.
    - Update fixtures / expected values / timeouts to match current production
      schema and SLO. Do NOT relax asserts — tighten where needed (P99 500ms).

  Phase 2 — ELEVATE:
    - Introduce fixture factories (pytest factory-boy style) for AuditEvent,
      RBACPolicy, PlanDAG — so future schema drift needs one fixture update,
      not twenty test rewrites.
    - Add property-based tests (hypothesis) for: audit chain tamper detection,
      PII detection across Indian character sets, SQL tier rewrite idempotency.
    - Introduce test tier markers: @pytest.mark.quality_bar, @pytest.mark.slo,
      @pytest.mark.dhairya — so CI can run focused bars on-demand.

  Phase 3 — IMMORTALIZE:
    - CI gate: any test in tests/security/, tests/performance/, tests/load/ failing
      → merge blocked. Codify in .github/workflows/ci.yml.
    - Coverage floor: 60 % overall; 90 % for src/audit/, src/security/, src/auth/.
    - Mutation testing (mutmut) on src/audit/ and src/security/ — catch silent
      regressions where code changes but tests still pass.

SKILLS TO USE:
  - /webapp-testing — end-to-end test structure + Playwright patterns
  - /test-driven-development — factory fixtures, property-based tests
  - /code-review-and-quality — MANDATORY pre-commit; catch relaxed asserts
  - /testing-strategy — tier/category separation, mutation testing approach
  - /pre-commit — gate all commits

ACCEPTANCE CRITERIA:
  - [ ] 0 failing tests in `pytest --tb=short`
  - [ ] 1 204 collected / 1 204 passed / ≤ 53 skipped (the skip set matches
        infra-dependent tests; no non-skip regressions)
  - [ ] Coverage ≥ 60 % overall; ≥ 90 % on src/audit/, src/security/, src/auth/
  - [ ] CI workflow fails on any tests/security/* or tests/performance/* failure
  - [ ] Dhairya bench not regressed (still ≥ current baseline until #20 lands)
  - [ ] Hard Constraint verification:
        - C1: PII regression corpus 100 % pass (no false negatives)
        - C2: audit chain tamper simulation — 3 attack patterns all caught
        - C3: multi-hop DAG fixture-set — 10 queries, correct decomposition
        - C4: P99 < 500ms assertion present and tight
        - C5: drift detection test present, triggers within 60s simulated
        - C6: egress allowlist test — 20 leak attempts blocked

BEFORE COMMIT:
  - /pre-commit must pass all gates (ruff, mypy, pytest, bandit)
  - /code-review-and-quality self-review for relaxed-assert anti-pattern
  - Report: skills used + number of fixture factories extracted + any new
    test patterns discovered (update .claude/memory/bugs_patterns.md)

GURU ASSIGNMENT NOTE:
  This is not cleanup. This is the foundation every subsequent protocol
  rests on. A single relaxed assert here hides a real production bug
  tomorrow. The IIT-GN stakeholders will trust NRG the moment they see
  95 % → 100 % pass rate + zero flaky tests + tight SLO asserts — and
  they will *walk* the moment they see a relaxed timeout. Treat this
  like you are writing the forensic report the Supreme Court of India
  will read in 2031 to decide whether NRG can handle sensitive research
  at scale. That is the bar.

AGENT INSTRUCTIONS (include verbatim):
  - First read: .agents/AGENTS.md
  - Then read: .agents/prompts/shishya_universal.md
  - Read the SKILL.md for every skill listed above
  - Read Core_Idea_Clean.md — understand the sovereign mission
  - Read .claude/QUALITY_BAR.md — the 6 constraints you must not regress
  - Read BACKLOG.md — know what's in-progress and what's done
  - Check the 3 Data Sources in .claude/CLAUDE.md — 18 vs 58 schema gap
  - Don't do the minimum — expand into best-possible test suite
  - Structure your work as Fortify → Elevate → Immortalize
  - Extract any new reusable fixture / pattern into a shared module
  - Run /pre-commit before committing
  - Report via the format in .agents/AGENTS.md

DEPENDS ON: none (can proceed in parallel with everything else)
═══════════════════════════════════════════════════════════════
```

---

```
═══════════════════════════════════════════════════════════════
TASK: #21 — THE SCHEMA BRIDGE (apply 58-table PostgreSQL migration)
AGENT: backend + database + devops
PRIORITY: P0-blocker
═══════════════════════════════════════════════════════════════

FILES:
  - db_struct.sql (read-only — authoritative)
  - alembic/versions/add_production_tables_001.py (apply)
  - src/data/schema/schema_hints.md (regenerate against 58 tables)
  - src/data/schema/schema_value_synonyms.md (regenerate)
  - src/skills/text_to_sql/schema_extractor.py (dual-driver verification)
  - scripts/migrate_data_to_postgresql.py (dry-run against staging)
  - src/models/production/*.py (NEW — sqlacodegen output)
  - tests/data/test_schema_parity.py (NEW)

PROBLEM:
  Dev SQLite has 18 tables. Prod schema (db_struct.sql, pg_dump from
  PostgreSQL 14.20, dumped 2026-01-09) has 58 tables. 40 missing from dev.
  Every Dhairya query references PostgreSQL-only tables. SQL accuracy
  cannot rise above today's 41 % until the 40 tables physically exist
  in the target (staging PostgreSQL) environment.

  Derivative gaps:
    - schema_hints.md targets the 18-table world
    - SQLAlchemy models only reflect 18 tables
    - Dhairya bench runs fail on "table does not exist"
    - SQL generator's few-shot examples cannot reference
      innovations_at_various_stages_of_technology_readiness_level
      because the table does not exist to be sampled

ACTION:
  Phase 1 — FORTIFY:
    - Spin up staging PostgreSQL 16 (local docker-compose.prod.yml profile)
    - Run: alembic upgrade head — verify 58 tables exist
    - Run: \d+ on each table; compare column types + constraints to
      db_struct.sql; diff must be empty
    - Seed minimal sample rows into the 40 previously-missing tables
      (10 rows each, synthesized from public sources — NIRF, AICTE, public
      patent DB — anonymized but schema-valid)
    - Run schema_extractor against the staging PG; confirm it sees 58 tables
    - Regenerate schema_hints.md and schema_value_synonyms.md from staging
    - Run: sqlacodegen postgresql://... --outfile src/models/production/auto.py
      then refactor into per-domain modules

  Phase 2 — ELEVATE:
    - Schema-parity test (tests/data/test_schema_parity.py):
      (a) parse db_struct.sql → extract (table, column, type) tuples
      (b) introspect staging PG → extract same tuples
      (c) assert equality modulo a documented allowlist of legitimate
          deviations (e.g., default values specified at app level)
    - Make the test CI-required; any future schema drift blocks merge
    - Add a "schema fingerprint" to the audit chain: at startup, emit
      event `schema.fingerprint = sha256(ordered_column_list)`; any drift
      in prod emits a CRITICAL
    - Provision RLS policies per rbac_policies.yaml — a Tier 3 session
      with a dropped WHERE cannot see Tier 1 columns

  Phase 3 — IMMORTALIZE:
    - Schema-sync CLI: scripts/schema_sync.py detects drift between
      db_struct.sql (canonical) and live PG; produces the Alembic diff
      automatically; human reviews + applies
    - Document the client ingestion handshake: how 600 GB arrives (SFTP +
      GPG + HMAC manifest), how it's staged, how it's validated, how it's
      promoted to serving — put in docs/architecture/DATA_INTAKE_PROTOCOL.md
    - Blue/green data promotion: new schema revisions flow into
      staging_v<N>; API flips after smoke + SLO pass

SKILLS TO USE:
  - /database-migrations-sql-migrations — Alembic + PostgreSQL migrations
  - /database-schema-designer — RLS, constraints, indices on 58 tables
  - /python-backend — sqlacodegen orchestration, dual-driver code
  - /security-auditor — RLS correctness, schema-fingerprint audit event
  - /code-review-and-quality — MANDATORY
  - /pre-commit — gate all commits

ACCEPTANCE CRITERIA:
  - [ ] `alembic current` on staging PG reports head revision 001
  - [ ] `information_schema.tables` on staging PG returns 58 base tables
        matching db_struct.sql name-for-name
  - [ ] Schema parity test green; no exceptions in allowlist beyond the
        documented defaults
  - [ ] Schema extractor returns identical column lists from SQLite dev
        and PostgreSQL staging (modulo the 40 prod-only tables)
  - [ ] schema_hints.md includes at minimum: one line per prod-only table
        with column names + types + brief purpose + Dhairya bench queries
        that reference it
  - [ ] RLS policies applied per rbac_policies.yaml; a Tier 3 session
        cannot SELECT researcher.email even with a dropped WHERE
  - [ ] Hard Constraint verification:
        - C1: PII patterns remain detected in seeded sample rows (no
              false negatives introduced by new tables with new column names)
        - C2: schema-fingerprint audit event emitted at startup
        - C6: egress allowlist regenerated to cover new column names

BEFORE COMMIT:
  - /pre-commit passes on all files
  - Manual verification: run 3 Dhairya queries (#1, #5, #11) against staging
    — report success/failure; do not yet expect high accuracy (that's #20)
  - /code-review-and-quality self-review
  - Update .claude/memory/project_nrg.md with staging PG state
  - Update .claude/memory/tech_decisions.md with ADR for RLS approach

GURU ASSIGNMENT NOTE:
  This is the moment the project stops being a prototype and becomes a
  real system. The professor's client delivered db_struct.sql on 2026-01-09
  — that was NRG's birthday. Until the 58 tables exist in our staging,
  every Dhairya query we run is theatre. The SQL Oracle (#20) cannot raise
  accuracy from 41 % → 85 % on a schema that doesn't exist yet. Treat
  schema parity as a contract with the client: every column we drift from
  db_struct.sql is a broken promise. RLS is not optional — a single
  dropped WHERE in Tier 3 that leaks a researcher's email will cost us
  DPDP compliance and the client relationship. Build this like the vault
  wall it is.

AGENT INSTRUCTIONS (verbatim):
  - .agents/AGENTS.md → .agents/prompts/shishya_universal.md
  - Read every SKILL.md above
  - Read Core_Idea_Clean.md + db_struct.sql + docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md
  - Fortify → Elevate → Immortalize
  - Extract reusable Alembic utility + RLS helper into src/data/
  - /pre-commit before committing

DEPENDS ON: none directly; unblocks #20 (SQL Oracle) and #41 (Quality Bar)
═══════════════════════════════════════════════════════════════
```

---

```
═══════════════════════════════════════════════════════════════
TASK: #20 — THE SQL ORACLE (Text-to-SQL 41 % → ≥ 85 % on Dhairya bench)
AGENT: ml + backend
PRIORITY: P0-blocker
═══════════════════════════════════════════════════════════════

FILES:
  - src/skills/text_to_sql/sql_generator.py
  - src/skills/text_to_sql/validator.py
  - src/skills/text_to_sql/query_context.py
  - src/data/schema/schema_hints.md
  - src/data/schema/schema_value_synonyms.md
  - src/data/schema/cte_templates.md
  - tests/benchmarks/test_dhairya_regression.py (NEW)
  - scripts/run_dhairya_bench.py (NEW)
  - src/skills/text_to_sql/self_correction.py (NEW)

PROBLEM:
  Dhairya's 17-query benchmark ran at 41 % on our current SQL stack
  (7 correct / 5 wrong / 3 errors / 2 format mismatch; avg 7.2 s).
  Target: ≥ 85 % correct, < 3 s avg. Failure patterns (from the report):
    - Schema synonym confusion (query says "funded projects",
      table is innovation_grant_from_govt)
    - Missing CTE for multi-step aggregation
    - Wrong JOIN direction on 1:N relationships
    - No self-correction when SQL runs but returns 0 rows
    - Prompt does not include relevant few-shot examples
    - Query context doesn't surface prod-only tables (pre-#21 problem,
      mitigated by #21)

ACTION:
  Phase 1 — FORTIFY (depends on #21 complete):
    - Harvest the 7 correct Dhairya queries as canonical few-shot examples
      (with rationale comments)
    - Inject schema_value_synonyms.md mappings into the prompt prefix
    - Inject cte_templates.md (top-3 CTE patterns from correct queries)
    - Implement self-correction loop:
        1) generate SQL
        2) sqlglot syntax + allowlist + read-only validator
        3) execute in sandbox
        4) if rowcount == 0 OR error, re-prompt ONCE with error text as
           context (never more than once — avoid runaway cost)
    - Add a completeness validator: compare column coverage of generated SQL
      against the query's inferred requirements; if requirements say
      "show name, funding amount" but SQL only SELECTs name → add columns

  Phase 2 — ELEVATE:
    - Dhairya regression test suite (tests/benchmarks/test_dhairya_regression.py):
        for each of the 17 queries, assert:
          (a) SQL generated is syntactically valid
          (b) SQL executes without error against staging PG
          (c) Result row count within ±10 % of ground truth
          (d) Response time < 3 s
      Mark individual tests with @pytest.mark.dhairya for focused runs
    - CI gate: PR touching src/skills/text_to_sql/** must pass dhairya bench
      with ≥ current baseline (never regress)
    - Confidence score: Text-to-SQL skill emits (sql, confidence, reasons)
      where confidence is (schema_match × fewshot_similarity × validator_pass)
    - Propagate confidence to synthesizer; if confidence < 0.5, prefer RAG
      path OR surface a clarifying assumption to the user (per Constitution §2)

  Phase 3 — IMMORTALIZE:
    - Training-pair collector: every production query + resulting SQL +
      user feedback (thumbs up/down) lands in the #22 collector as a
      future fine-tune example (already wired by Protocol #40 stratification)
    - Quarterly /self-evolve pass re-runs Dhairya bench; if accuracy drops
      below 80 %, file a P0 protocol to investigate
    - "Hall of shame" folder: src/data/schema/failed_queries/ — keep the
      5 worst Dhairya queries as adversarial fixtures; every new prompt
      change must pass them

SKILLS TO USE:
  - /prompt-engineering-patterns — few-shot design, CoT, self-consistency
  - /sql-queries — CTE idioms, window functions, PG-specific syntax
  - /python-backend — self-correction orchestration, sqlglot integration
  - /statistical-analysis — confidence score calibration, bench evaluation
  - /code-review-and-quality — MANDATORY
  - /pre-commit — gate all commits

ACCEPTANCE CRITERIA:
  - [ ] Dhairya regression test: ≥ 15 / 17 correct (≥ 88 %), ≥ 13 / 17 exact (≥ 76 %)
  - [ ] Avg response time < 3 s; p95 < 5 s
  - [ ] Self-correction loop engaged on ≥ 3 of the previously-error queries;
        all 3 return valid SQL on retry
  - [ ] Confidence score emitted on every Text-to-SQL response; synthesizer
        reads it
  - [ ] Hard Constraint verification:
        - C2: every SQL generation audit-logged with user + kid
        - C3: DAG-decomposed multi-hop queries route correctly to Text-to-SQL
              per sub-node (not flat)
        - C4: SLO met on bench queries
        - C6: prompt inspected by egress guard; no raw schema names beyond
              the allowlist leak into the prompt

BEFORE COMMIT:
  - /pre-commit passes
  - Dhairya regression bench green at target
  - /code-review-and-quality self-review of prompt (check for injection
    vulnerabilities in the prompt prefix itself)
  - Update .claude/memory/perf_baselines.md with new numbers

GURU ASSIGNMENT NOTE:
  Dhairya is not on our team. He's an external engineer doing the same
  work on a similar project and he published a 41 % audit of our SQL
  pipeline. That number is in the open. Every stakeholder at IIT-GN
  will ask it. If we walk into the handover meeting and say "we're at
  52 %", we lose the room. If we say "we shipped ≥ 85 %" and the demo
  proves it on his 17 queries, we own the room. This is not an
  incremental improvement task. This is the single most externally-visible
  accuracy number the project has. Execute accordingly.

AGENT INSTRUCTIONS (verbatim):
  - .agents/AGENTS.md → shishya_universal.md
  - Read every SKILL.md listed above
  - Read docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md END TO END
  - Read db_struct.sql for every referenced table before writing the prompt
  - Fortify → Elevate → Immortalize
  - Never regress the bench; if a prompt change helps some queries and
    breaks others, keep iterating; commit only net-positive changes
  - /pre-commit before committing

DEPENDS ON: #21 (schema bridge applied), #19 (tests green)
═══════════════════════════════════════════════════════════════
```

---

```
═══════════════════════════════════════════════════════════════
TASK: #11 — THE RESILIENT MESH (close-out LLM provider hardening)
AGENT: backend
PRIORITY: P1-hardening
═══════════════════════════════════════════════════════════════

FILES:
  - src/config/llm_config.py
  - src/config/local_llm.py
  - src/orchestration/nodes/synthesizer.py
  - src/orchestration/nodes/complexity_classifier.py (#38, integrate)
  - tests/chaos/test_llm_provider_failures.py
  - tests/performance/test_mesh_racing.py (NEW)

PROBLEM:
  Pre-Protocol baseline was 270 s worst-case across 6 cloud providers.
  Current: 15 s hard cap implemented. Needs: health-weighted routing,
  parallel racing for P99-critical queries, graceful degradation
  messages to user (not silent fallback), per-provider circuit breaker,
  integration with Complexity Router (#38).

ACTION:
  Phase 1 — FORTIFY:
    - Confirm 15 s cap across all 6 providers via chaos test
    - Implement health-weighted routing: each provider has
      (latency_p95, error_rate_7d) → weight = 1 / (latency × (1 + error_rate))
    - Parallel racing for complexity=complex or synthesis-heavy: fire top-3
      providers in parallel, cancel losers after first success
    - Circuit breaker per provider: open after 5 consecutive failures,
      half-open after 30 s, close after 2 successes

  Phase 2 — ELEVATE:
    - Graceful degradation messages: if all cloud providers fail, synthesizer
      falls to local SLM with user-visible message "using offline model for
      this response" (per Constitution §5, surface limitations honestly)
    - Cost-aware routing: when complexity=trivial, prefer smallest model
      (Gemini Flash); reserve Claude/GPT-4o for complex
    - Cache integration: Complexity Router emits query fingerprint; hit rate
      ≥ 30 % target

  Phase 3 — IMMORTALIZE:
    - Mesh dashboard (Grafana): provider latency/error/cost/weight per minute
    - Auto-disable: if a provider's 7-day error rate > 15 %, remove from
      rotation until manual re-enable
    - Egress guard integration (#39): every outbound payload inspected;
      non-allowlisted → block + audit + fallthrough to next provider

SKILLS TO USE:
  - /python-backend — async orchestration, circuit breakers
  - /performance — latency measurement, p99 under load
  - /security-auditor — egress guard integration
  - /prompt-engineering-patterns — complexity-aware prompt scaling
  - /code-review-and-quality — MANDATORY
  - /pre-commit — gate all commits

ACCEPTANCE CRITERIA:
  - [ ] Chaos test: all 6 providers down → rule-based response within 20 s
  - [ ] Mesh racing test: P99 across 500 queries < 8 s
  - [ ] Circuit breaker: simulate provider-A 100 % fail → removed after
        5 consecutive; restored after 2 successes post-half-open
  - [ ] Cache hit rate ≥ 30 % on production-replay workload
  - [ ] Hard Constraint verification:
        - C4: P99 < 500ms on trivial/simple queries under 1 000 concurrent
        - C6: every provider call passes through egress guard; non-allowlisted
              payload blocked and audited

BEFORE COMMIT:
  - /pre-commit passes
  - Chaos + perf test green
  - /code-review-and-quality
  - Update perf_baselines.md

GURU ASSIGNMENT NOTE:
  LLM providers are the one dependency we cannot control. OpenAI has
  outages. Anthropic has outages. Gemini has quota limits. Azure has
  region failures. If NRG's P99 is at the mercy of the worst provider
  on any given day, we have built a chain of trust as strong as its
  weakest link. The mesh is our insurance policy. It must be racing
  when it matters, cheap when it doesn't, and invisible to the user
  when a provider dies. The professor will never know a provider failed
  — they will know the answer took 2 s instead of 1.5 s.

AGENT INSTRUCTIONS: (standard verbatim block, see .agents/AGENTS.md)

DEPENDS ON: #19 (tests green), #38 (complexity router — done), #39 (egress guard — done)
═══════════════════════════════════════════════════════════════
```

---

```
═══════════════════════════════════════════════════════════════
TASK: #12 — THE LIVING PIPELINE (observability + data ingestion close-out)
AGENT: backend + devops
PRIORITY: P1-hardening
═══════════════════════════════════════════════════════════════

FILES:
  - src/observability/tracer.py (Langfuse live wiring)
  - src/observability/metrics.py (Prometheus + SLO alerting)
  - src/observability/grafana/*.json (NEW — dashboards)
  - scripts/ingest_documents.py (complete)
  - scripts/vector_drift_check.py (auto-retrain trigger)
  - src/skills/rag/reranker.py (integrate into /query)
  - src/skills/rag/embedder.py (switch to bge-m3)
  - .github/workflows/observability.yml (NEW — nightly drift cron)

PROBLEM:
  Observability is wired but not live. Langfuse runs locally, not on the
  sovereign cluster. /api/metrics exists but no Grafana dashboards.
  Vector drift script works manually; no auto-trigger to re-index queue.
  Reranker built but not in the query path. Embeddings still 384-dim
  (MiniLM) — target bge-m3 (1024-dim) with IndicBERT support.

ACTION:
  Phase 1 — FORTIFY:
    - Deploy self-hosted Langfuse on sovereign cluster (sub-task of #43)
    - Wire src/observability/tracer.py with LANGFUSE_HOST + keys
    - Build 7 Grafana dashboards (JSON): p99 per node, SLO breach counter,
      Quality Bar scorecard, vector drift, RBAC denial rate, audit chain
      length, cache hit rate
    - Complete scripts/ingest_documents.py: batch chunker → bge-m3 embed
      → Qdrant upsert with tier metadata, idempotent, resumable
    - scripts/vector_drift_check.py: when cosine shift > 0.05 vs reference
      centroids, POST to /api/reindex (new internal endpoint; RBAC: system-only)

  Phase 2 — ELEVATE:
    - Integrate reranker: Qdrant top-10 → bge-reranker-v2-m3 → top-3
    - Switch embedder to bge-m3 (1024-dim); migrate Qdrant collection via
      alias swap (zero downtime) — re-embed 19 322 existing vectors
    - Add IndicBERT secondary path for Hindi + Tamil queries (detect via
      language classifier; dual-embed if both)
    - SLO alerting: 5 consecutive P99 > 500 ms → CRITICAL log + PagerDuty
      webhook (sovereign PagerDuty, not external)

  Phase 3 — IMMORTALIZE:
    - Ingestion orchestration as a Prefect / Temporal workflow (idempotent,
      replayable, versioned)
    - Nightly cron: vector drift → auto-reindex trigger → alert if queue depth
      grows faster than drain rate
    - Observability-on-observability: the observability stack itself is
      audit-logged; any config change to Langfuse or Grafana is an audit event

SKILLS TO USE:
  - /python-backend — async ingestion, reranker integration
  - /database-migrations-sql-migrations — Qdrant alias-swap migration
  - /performance — latency instrumentation per node
  - /security-auditor — observability egress audit
  - /code-review-and-quality — MANDATORY
  - /pre-commit

ACCEPTANCE CRITERIA:
  - [ ] Langfuse live on sovereign cluster; traces visible for /query
  - [ ] 7 Grafana dashboards rendering; Quality Bar scorecard shows 6/6
        after Protocol #41
  - [ ] Vector drift cron: manual drift simulation triggers reindex within 60 s
  - [ ] Reranker integrated; top-3 recall@5 ≥ 0.9 on eval dataset
  - [ ] bge-m3 embeddings deployed; zero-downtime verified; re-embedding of
        existing 19 322 vectors complete
  - [ ] Hard Constraint verification:
        - C4: P99 dashboard live; alert fires on 5-consecutive breach simulation
        - C5: vector drift → auto-retrain trigger fires within 60 s (test passes)
        - C6: Langfuse payloads inspected — no retrieved facts / PII leaked

BEFORE COMMIT:
  - /pre-commit passes
  - Grafana dashboards reviewed by Guru
  - /code-review-and-quality
  - Update reference_installed_skills.md if new observability skills extracted

GURU ASSIGNMENT NOTE:
  A system you cannot see is a system you cannot trust. The client at
  IIT-GN will ask one question during UAT: "show me it running right
  now." If the answer is "here's a log file", we failed. If the answer
  is "here's seven live dashboards, each tied to a Quality Bar constraint,
  each green, each alert-armed", we defined the standard for sovereign
  AI operations in India. Observability is not a post-launch concern.
  It is the proof of life.

AGENT INSTRUCTIONS: (standard verbatim block)

DEPENDS ON: #19 (tests green), #43 (sovereign deploy for Langfuse)
═══════════════════════════════════════════════════════════════
```

---

```
═══════════════════════════════════════════════════════════════
TASK: #41 — THE QUALITY BAR INTEGRATION VALIDATION (2/6 → 6/6)
AGENT: testing + security + backend
PRIORITY: P0-blocker (GATES HANDOVER)
═══════════════════════════════════════════════════════════════

FILES:
  - tests/quality_bar/test_c1_indian_pii.py
  - tests/quality_bar/test_c2_audit_binding.py (NEW)
  - tests/quality_bar/test_c3_multi_hop_dag.py
  - tests/quality_bar/test_c4_slo.py
  - tests/quality_bar/test_c5_drift_autotrigger.py (NEW)
  - tests/quality_bar/test_c6_egress_allowlist.py (NEW)
  - scripts/quality_bar_scorecard.py (NEW)
  - docs/ops/QUALITY_BAR_SCORECARD_2026-Q2.md (NEW)

PROBLEM:
  Quality Bar compliance is 2/6 fully passing (PII ✓, Vector Drift ✓).
  Protocols #35, #37, #39 have written the code for C2, C3, C6 but
  integration verification is pending. Protocol #11/#18 define SLO
  framework but numbers are unproven under load. This protocol closes
  all pending cells and raises compliance to 6/6 before handover.

ACTION:
  Phase 1 — FORTIFY: run every Quality Bar acceptance test in isolation
    - C1: `pytest tests/security/test_pii_indian.py -v` — must pass clean
    - C2: 100-event tamper simulation: (a) mutate event, (b) swap JWT
          between users, (c) remove signature → verify_chain() returns
          False with correct broken_event_idx in all 3 cases
    - C3: 10 multi-hop fixtures (including 4-hop "Compare Gujarat +
          Karnataka AI over 5 years with funding gap") — assert DAG
          structure exactly
    - C4: load test — 1 000 concurrent users on locust; P99 < 500 ms
          sustained for 5 minutes on analytical queries
    - C5: manual drift simulation — shift 5 % of vectors by > 0.05
          cosine; confirm auto-retrain event fires within 60 s
    - C6: 20 egress-leak attempts (raw schema names, SQL injection in
          prompt, credential extraction patterns, schema-probing) — all
          blocked, all audit-logged

  Phase 2 — ELEVATE:
    - Build scripts/quality_bar_scorecard.py: one command runs all 6
      test groups, emits a scorecard (markdown + JSON)
    - CI integration: the scorecard runs nightly; any score drop flags
      a P0 incident
    - Hard enforcement: in .github/workflows/cd.yml, a release cannot
      ship unless scorecard reports 6/6

  Phase 3 — IMMORTALIZE:
    - Quarterly ritual: /self-evolve runs scorecard; result committed
      to docs/ops/QUALITY_BAR_SCORECARD_<YYYY-QN>.md
    - Any new protocol touching security/audit/RBAC/egress must declare
      which constraints it regresses or maintains; blocked from merge
      if a regression is not justified + mitigated

SKILLS TO USE:
  - /security-auditor — C1, C2, C6 acceptance logic
  - /webapp-testing — load test for C4, integration test for C3
  - /testing-strategy — scorecard design, CI integration
  - /performance — C4 load runner, latency measurement
  - /code-review-and-quality — MANDATORY
  - /pre-commit

ACCEPTANCE CRITERIA:
  - [ ] All 6 test groups pass on a clean staging deploy
  - [ ] scripts/quality_bar_scorecard.py prints "6/6 COMPLIANT"
  - [ ] docs/ops/QUALITY_BAR_SCORECARD_2026-Q2.md committed with
        evidence (test output excerpts, screenshots of Grafana panels)
  - [ ] CI blocks merge on any constraint regression
  - [ ] /self-evolve extended to include scorecard run

BEFORE COMMIT:
  - /pre-commit passes
  - Scorecard report reviewed by Guru
  - /code-review-and-quality
  - Update QUALITY_BAR.md compliance snapshot to 6/6 with date

GURU ASSIGNMENT NOTE:
  The 6 Hard Constraints are not a wish list. They are the contract
  NRG signs with the Republic of India. DPDP 2023 is law. Per-user
  non-repudiation is what allows a researcher to be held to their
  own query history if it comes up in a misconduct inquiry. Multi-hop
  decomposition is what turns NRG from a lookup tool into a reasoning
  system. SLOs at 1 000 concurrent are what make NRG viable at
  national scale. Drift monitoring is what keeps the model honest as
  data evolves. Egress allowlisting is the firewall that physically
  prevents a cloud-side prompt from becoming an exfiltration channel.
  Six constraints, six promises. The day we claim 6/6 is the day NRG
  is handoverable. Not before.

AGENT INSTRUCTIONS: (verbatim)

DEPENDS ON: #19 (tests green), #21 (schema), #35/#37/#39 (code in place),
            #11/#12 (SLO infra + drift wiring), #43 (load test infrastructure)
═══════════════════════════════════════════════════════════════
```

---

```
═══════════════════════════════════════════════════════════════
TASK: #42 — THE FRONTEND-API RECONNECT
AGENT: backend + frontend
PRIORITY: P1-hardening
═══════════════════════════════════════════════════════════════

FILES:
  - src/api/main.py (add endpoints: /stats, /publications, /query/graph)
  - src/api/routers/*.py (NEW, one per domain)
  - frontend/src/services/queryService.ts
  - frontend/vite.config.ts
  - frontend/src/views/*Dashboard.tsx
  - tests/e2e/test_persona_flows.spec.ts
  - docs/api/OPENAPI.yaml (NEW)

PROBLEM:
  Frontend calls /query/graph, /stats, /publications — endpoints that
  do not exist in backend. queryService.ts falls back to mockGraphData().
  vite.config.ts proxies only /login /refresh /logout /query /researchers
  /health — 4 paths missing. Tier-aware UI rendering partially landed;
  needs verification via Playwright persona flow tests.

ACTION:
  Phase 1 — FORTIFY:
    - Implement GET /stats: tier-aggregated counts (researchers, publications,
      funding total). Tier 2+ only; Tier 3 gets bucketed ranges, not counts.
    - Implement GET /publications: paginated list with tier-filtered columns
      (emails hidden from Tier 2/3 per rbac_policies.yaml)
    - Implement POST /query/graph: accepts {query, depth}; returns
      collaboration subgraph via SQL recursive CTE (rCTE); max depth 3;
      Tier 3 anonymized node labels
    - Update vite.config.ts proxy table
    - Remove mockGraphData() fallback — error state = clean error UI,
      not fake data

  Phase 2 — ELEVATE:
    - Generate OpenAPI spec from FastAPI; serve at /docs; regenerate frontend
      client types from the spec (openapi-typescript) — compile-time safety
    - Tier-aware conditional render: the DashboardLayout inspects JWT claim
      and hides UI controls Tier 3 cannot use (download CSV of researchers,
      view email, etc.)
    - Loading + error + empty + success states on every query; no blank panels
    - Playwright persona flow tests: login as each of 6 personas → run 3
      representative queries → assert correct tier filtering + correct UI

  Phase 3 — IMMORTALIZE:
    - WebSocket or SSE stream for long-running queries (P99 over 3 s):
      server emits {step: "planning"}, {step: "retrieving"}, {step: "synthesizing"}
      → user sees progress, not a hung spinner
    - Accessibility: Playwright-a11y scan; WCAG AA minimum; zero critical issues

SKILLS TO USE:
  - /python-backend — FastAPI endpoints, Pydantic response models
  - /frontend-react-best-practices — state management, hooks, error boundaries
  - /typescript-advanced-types — openapi-typescript generated types, discriminated unions
  - /webapp-testing — Playwright persona flow + a11y scan
  - /accessibility-review — WCAG AA compliance
  - /code-review-and-quality — MANDATORY
  - /pre-commit

ACCEPTANCE CRITERIA:
  - [ ] GET /stats, GET /publications, POST /query/graph live; contract tests pass
  - [ ] vite.config.ts proxy complete; no 404 from dev frontend
  - [ ] mockGraphData() deleted; clean error UI replaces it
  - [ ] Playwright persona tests: 6 personas × 3 queries = 18 scenarios green
  - [ ] OpenAPI spec generated + frontend types auto-regenerated
  - [ ] Hard Constraint verification:
        - C1: no PII leaks in /publications or /query/graph responses
              for Tier 2/3 — test with seeded PII rows
        - C2: every API call audit-logged with user + jwt_jti + jwt_kid
        - C6: /query/graph response inspected by egress guard on the server
              side before returning (especially if the graph subtree
              could pass through a cloud LLM for natural-language summary)

BEFORE COMMIT:
  - /pre-commit
  - Manual smoke: log in as each persona → each dashboard works
  - /code-review-and-quality
  - Update memory/bugs_frontend_crashes.md if new crash pattern observed

GURU ASSIGNMENT NOTE:
  The frontend IS the client's experience. A broken endpoint chain is
  invisible to the backend test suite but catastrophic during UAT. The
  professor does not care that our API is beautiful — they care that
  when they click "Show collaboration graph", a graph appears. Today,
  it returns mock data. Tomorrow, it returns live facts with
  citations. No intermediate state is acceptable for handover. Build
  this like it is the only thing the client will ever see — because
  during the 30-minute demo, it is.

AGENT INSTRUCTIONS: (verbatim)

DEPENDS ON: #21 (schema, for /publications), #26 (RBAC, for tier filter),
            #19 (tests green), #24 (prior frontend work)
═══════════════════════════════════════════════════════════════
```

---

```
═══════════════════════════════════════════════════════════════
TASK: #43 — THE SOVEREIGN LANDING (deploy on NIC/MeitY infrastructure)
AGENT: devops + security + backend
PRIORITY: P0-blocker (GATES HANDOVER)
═══════════════════════════════════════════════════════════════

FILES:
  - infrastructure/helm/nrg/Chart.yaml (NEW)
  - infrastructure/helm/nrg/values.yaml (+ values-staging.yaml, values-prod.yaml)
  - infrastructure/helm/nrg/templates/*.yaml (Deployment, Service, Ingress,
    NetworkPolicy, PodDisruptionBudget, HorizontalPodAutoscaler, ConfigMap,
    Secret (sealed via Vault), CronJob for backup/drift)
  - infrastructure/vault/policies/*.hcl
  - infrastructure/cert-manager/*.yaml
  - infrastructure/network-policies/*.yaml
  - scripts/sovereign_deploy.py
  - docs/ops/SOVEREIGN_DEPLOY_RUNBOOK.md (NEW)

PROBLEM:
  Everything on-cluster today is docker-compose for development.
  Sovereign-grade operations require: Kubernetes on NIC/MeitY nodes,
  Vault-managed secrets (no env-var secrets in pod spec), cert-manager
  for TLS, NetworkPolicies blocking egress except to allowlisted LLM
  hosts, HPA for load scaling, PDB for rolling updates, backup CronJobs
  to encrypted sovereign object storage, incident-ready runbook.

ACTION:
  Phase 1 — FORTIFY:
    - Build Helm chart (Chart.yaml + templates) for: API, Postgres,
      Qdrant, Redis, Kong, Langfuse (self-hosted), Grafana, Prometheus
    - Set resource requests/limits per service
    - PDB: minAvailable = N-1 for stateless services; maxUnavailable = 0
      for stateful during rolling update
    - HPA for API: target 60 % CPU; min 3 replicas, max 20
    - Vault-agent sidecar: API pod fetches secrets at start; no env
      secrets in pod spec or values.yaml
    - cert-manager with internal CA (sovereign CA, not Let's Encrypt);
      TLS on all intra-cluster traffic

  Phase 2 — ELEVATE:
    - NetworkPolicies:
        - API pod can egress only to: Postgres, Qdrant, Redis, Kong,
          allowlisted LLM hosts (gemini, anthropic, etc., per egress_allowlist)
        - Postgres pod: no egress to internet
        - Qdrant pod: no egress to internet
    - Backup CronJobs: Postgres pg_basebackup → encrypted S3-compatible
      (sovereign, e.g., MeitY object storage) daily; Qdrant snapshot
      weekly; restore drill monthly
    - Pod Security Standard `restricted`: no privileged pods; readOnlyRootFS
      where possible; seccomp default
    - Blue-green deployment via scripts/sovereign_deploy.py:
        1) deploy new version as green
        2) smoke /health + Quality Bar scorecard
        3) flip Ingress (Kong) to green
        4) keep blue hot for 15 min; then scale to 0
        5) rollback: flip back + investigate

  Phase 3 — IMMORTALIZE:
    - Chaos engineering: once-weekly `chaos-mesh` experiment
      (pod kill, network partition, clock skew) in staging; verify
      system recovers within SLA
    - Disaster recovery: runbook tested quarterly — full cluster rebuild
      from backups + audit-chain replay to within 4-hour RTO
    - Compliance evidence: SOC2-style access logs for every `kubectl`,
      every Vault unseal, every secret access — bound to per-user audit chain

SKILLS TO USE:
  - /dockerfile-validator — distroless base, minimal attack surface
  - /deployment-pipeline-design — blue-green, HPA, PDB patterns
  - /security-auditor — Vault policies, NetworkPolicy correctness, PSS
  - /python-backend — deploy script orchestration
  - /incident-response — runbook patterns
  - /code-review-and-quality — MANDATORY
  - /pre-commit

ACCEPTANCE CRITERIA:
  - [ ] Helm install succeeds on staging (sovereign cluster); all pods Ready
  - [ ] TLS live on every endpoint; cert-manager auto-renews
  - [ ] NetworkPolicy egress test: API pod → arbitrary external IP → BLOCKED
  - [ ] Backup drill: destroy PG, restore from yesterday's backup; data
        delta ≤ 24 h; audit chain verified intact
  - [ ] Blue-green deploy script: smoke + scorecard gates work; manual
        rollback completes in < 2 min
  - [ ] Hard Constraint verification:
        - C2: secrets and audit keys fetched from Vault only; no env secrets
        - C4: load test on sovereign cluster — P99 < 500 ms, 1 000 concurrent
        - C6: egress guard + NetworkPolicy form defense in depth; both tested

BEFORE COMMIT:
  - /pre-commit
  - Full staging deploy test run
  - /code-review-and-quality
  - Runbook reviewed by Guru

GURU ASSIGNMENT NOTE:
  This is where NRG stops being a codebase and becomes infrastructure.
  NIC/MeitY runs the cluster. Our job is to fit inside their guard
  rails like a professional — sealed secrets, sealed network, sealed
  observability, sealed backups, rollback that works at 3 AM on a
  holiday. The single biggest signal to the client at IIT-GN that
  NRG is "real" is the moment we hand them a runbook and say "here's
  exactly how to operate this for the next 20 years."

AGENT INSTRUCTIONS: (verbatim)

DEPENDS ON: #25 (CI/CD + Docker base), #11 (resilient mesh), #12 (observability), #41 (Quality Bar proofs)
═══════════════════════════════════════════════════════════════
```

---

```
═══════════════════════════════════════════════════════════════
TASK: #44 — THE HANDOVER PACKAGE (UAT + docs + pitch deck + runbook)
AGENT: founder (owner) + writer + devops (support) + Guru (review)
PRIORITY: P0-blocker (FINAL)
═══════════════════════════════════════════════════════════════

FILES:
  - docs/handover/README.md (NEW — master index)
  - docs/handover/SYSTEM_OVERVIEW.md (NEW — non-technical, 10 pages)
  - docs/handover/ARCHITECTURE.md (NEW — technical, with diagrams)
  - docs/handover/API_REFERENCE.md (generated from OpenAPI)
  - docs/handover/OPERATIONS_RUNBOOK.md (NEW — day-2 ops)
  - docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md (NEW — DPDP + QB 6/6)
  - docs/handover/DATA_INTAKE_PROTOCOL.md (NEW — how 600 GB arrives)
  - docs/handover/UAT_RESULTS.md (NEW — filled after UAT)
  - pitch/NRG_PITCH_DECK.pdf (NEW — for national-scale proposal)
  - videos/NRG_DEMO.mp4 (NEW — 3-minute persona-by-persona walkthrough)

PROBLEM:
  A system is not shipped until the client can operate it without us.
  This protocol produces the handover artifact set: documents the
  professor's team can read, runbooks the NIC/MeitY ops team can
  follow, a pitch deck the client can show the ministry for national
  scale funding, and a UAT result report signed by all 3 personas.

ACTION:
  Phase 1 — FORTIFY: produce the artifact set
    - SYSTEM_OVERVIEW.md: 10-page narrative for non-engineers — what NRG
      is, why it matters, what it does today, what it will do in 2 years
    - ARCHITECTURE.md: the 5-layer + 6-node diagrams, the data flow,
      the security model, the 6 Hard Constraints, cross-referenced to
      Core_Idea_Clean.md
    - OPERATIONS_RUNBOOK.md: boot, backup/restore, rotation (secrets,
      audit salt, JWT keys), incident response, escalation tree, SLO
      breach procedure, drift-triggered reindex procedure, common error
      codes + fixes
    - SECURITY_COMPLIANCE_ATTESTATION.md: QB scorecard 6/6 evidence,
      DPDP clause-by-clause mapping, data flow with boundary markers
    - DATA_INTAKE_PROTOCOL.md: the SFTP + GPG + HMAC manifest handshake,
      staging → validation → promotion flow
    - API_REFERENCE.md: generated from OpenAPI, human-edited for
      persona examples
    - NRG_PITCH_DECK.pdf: 20 slides — problem, solution, architecture,
      sovereignty, demo, roadmap, ask
    - NRG_DEMO.mp4: scripted 3-min walkthrough, one minute per persona

  Phase 2 — ELEVATE: UAT with 3 personas at IIT-GN
    - Schedule 1-hour session with: professor (Tier 1), ministry liaison
      (Tier 2), industry partner (Tier 3)
    - Pre-seed each persona with 10 realistic queries
    - Capture: time to answer, answer quality score 1–5, citation accuracy
      verification, UI friction notes
    - Fill UAT_RESULTS.md with transcript + score + quotes (with consent)
    - Any critical finding triggers a P0 remediation protocol before
      final handover

  Phase 3 — IMMORTALIZE: transition plan
    - 30-day shadowing: NRG agents + NIC/MeitY ops run the system together;
      ops team handles their first incident with our support
    - 60-day handover: ops team runs the system solo; NRG agents on call
      for P0 only
    - 90-day independence: sole ownership transfers; NRG team retained
      for endgame (Protocols #29–#34) only

SKILLS TO USE:
  - /doc-coauthoring — multi-document narrative consistency
  - /stakeholder-update — pitch-deck messaging
  - /write-spec — runbook precision
  - /incident-response — runbook patterns, escalation trees
  - /code-review-and-quality — MANDATORY (review generated docs)
  - /pre-commit

ACCEPTANCE CRITERIA:
  - [ ] All 9 handover artifacts produced and reviewed by Guru
  - [ ] UAT_RESULTS.md signed by at least one representative from each of
        the 3 personas
  - [ ] Pitch deck reviewed by Guru + Founder; fits ministry-briefing format
  - [ ] Demo video < 3 min, subtitled, shot on sovereign staging (not local)
  - [ ] Ops team completes one full incident drill using OPERATIONS_RUNBOOK
  - [ ] Hard Constraint verification:
        - C1–C6: SECURITY_COMPLIANCE_ATTESTATION.md has evidence pointer
          to each constraint's scorecard entry
        - DPDP Act 2023 clause-by-clause mapping signed by counsel

BEFORE COMMIT (documents):
  - /doc-coauthoring review — consistency across docs
  - /code-review-and-quality — prose + technical correctness
  - Founder sign-off per document

GURU ASSIGNMENT NOTE:
  A product that only its builders can operate is not a product —
  it's a liability. On the day we hand NRG to IIT-GN, they must be
  able to: boot it, query it, operate it, audit it, scale it, recover
  from disaster, and pitch it to the ministry for national-scale
  funding — all without calling us. Every document we write now is
  an asset that outlives us. Do not phone this in. The pitch deck
  you produce may be the single artifact that unlocks ₹400 crore of
  national-scale funding for NRG's endgame. Treat it accordingly.

AGENT INSTRUCTIONS: (verbatim; include explicit note to read
  Core_Idea_Clean.md and quote from it in SYSTEM_OVERVIEW.md)

DEPENDS ON: #41 (QB 6/6), #42 (frontend), #43 (sovereign deploy),
            #19 (tests green), #20 (Dhairya ≥ 85 %)
═══════════════════════════════════════════════════════════════
```

---

### 7.1 Endgame Protocols (#29–#34, Post-Handover, Condensed)

These are the fine-tune path from Core_Idea_Clean.md §Endgame Vision. They follow handover and convert NRG from "retrieve-and-synthesize" to "already knows, retrieves for precision." Each gets a full ═══ when we enter Phase 6, but the Guru architects the arc here.

```
═══════════════════════════════════════════════════════════════
#29 THE LIVE COLLECTION — activate fine-tune collector on prod traffic
  Goal: every query-answer pair logged via src/training/collector.py;
        user feedback channel (👍👎) + reviewer audit for gold grading
  Skills: /python-backend, /statistical-analysis, /security-auditor
  Acceptance: ≥ 10 000 GOLD + ≥ 30 000 SILVER pairs in 90 days; PII-free
              pipeline verified by egress guard
  Gates: #43 deployed, #44 handover signed, endgame go-ahead
═══════════════════════════════════════════════════════════════

#30 THE BASE MODEL SELECTION — Llama-3.1-8B → 70B, QLoRA harness
  Goal: shortlist {Llama 3.1 70B, Qwen 2.5 72B, Mistral Large, Llama 3.1 8B
        for dev}; spin QLoRA fine-tune on 8B first; eval against NRG
        bench + Dhairya bench + held-out QA
  Skills: /prompt-engineering-patterns, /statistical-analysis, /python-backend
  Acceptance: 8B QLoRA passes Dhairya bench > 70 % with internal knowledge
              (no retrieval); ROI curve justifies 70B next
  Gates: #29 pipeline collecting for 90 days

#31 THE RL LOOP — explore / evaluate / reward / iterate
  Goal: reinforcement learning loop per Core_Idea_Clean.md §Endgame —
        model explores data, each answer checked vs ground truth, correct
        reasoning rewarded, hallucination penalized; trains to *understand*,
        not memorize
  Skills: /statistical-analysis, /python-backend, /prompt-engineering-patterns
  Acceptance: held-out adversarial set ≥ 90 % on paraphrase-robust
              fixtures; hallucination rate ≤ 2 %
  Gates: #30 baseline established

#32 THE TWO-BRAIN ORCHESTRATOR — fine-tune + retrieval serving
  Goal: the "expert salesman" pattern — fine-tuned local model answers
        from internalized knowledge for general/analytical questions;
        live retrieval (SQL + RAG) for specific/exact facts; orchestrator
        decides per-query
  Skills: /python-backend, /system-design, /prompt-engineering-patterns
  Acceptance: P99 < 200 ms on general questions, < 500 ms on
              retrieval-required; user-visible traceability (which path
              served this answer)
  Gates: #31 fine-tune model validated

#33 THE FINE-TUNE SERVING + SAFETY GATE
  Goal: deploy fine-tuned model on sovereign GPUs; every response gates
        through egress guard (#39 pattern — irrelevant cloud now, but the
        guard still checks tier + PII + claims); audit-logged
  Skills: /security-auditor, /deployment-pipeline-design, /python-backend
  Acceptance: serving infra stable at 1 000 QPS; safety gate blocks
              Tier 1 PII to Tier 3 sessions even when model regurgitates
              internalized data

#34 THE PERIODIC RETRAINING PIPELINE
  Goal: monthly retrain on delta data + golden fine-tune pairs;
        canary deploy new weights; rollback on eval regression
  Skills: /deployment-pipeline-design, /statistical-analysis, /python-backend
  Acceptance: monthly cadence holds for 6 consecutive months; eval delta
              always positive or flat; zero user-visible regressions
═══════════════════════════════════════════════════════════════
```

Each endgame protocol will be expanded to a full ═══ block at Sprint-6 entry (Phase 6 kickoff). They are intentionally condensed here because handover (#44) is the immediate contract; endgame is the life-after.

---

## 8. PHASED ROADMAP

### 8.1 Phase 3 Close (Sprints 1–2, weeks 1–4)

**Objective**: zero failing tests, schema migrated, SQL ≥ 85 %, resilient mesh finalized, observability complete.

| Sprint | Protocols | Exit gate |
|---|---|---|
| 1 (weeks 1–2) | #19 Test Realignment, #21 Schema Bridge (parallel) | 0 failing tests; 58 tables live in staging |
| 2 (weeks 3–4) | #20 SQL Oracle, #11 Resilient Mesh, #12 Living Pipeline (parallel) | Dhairya ≥ 85 %; P99 + drift + mesh dashboards live |

### 8.2 Phase 5 Quality Bar Integration (Sprint 3, weeks 5–6)

**Objective**: Quality Bar 2/6 → 6/6.

| Sprint | Protocols | Exit gate |
|---|---|---|
| 3 | #41 Quality Bar Integration Validation | Scorecard 6/6; CI enforces |

### 8.3 Handover Preparation (Sprints 4–5, weeks 7–10)

**Objective**: frontend reconnected, sovereign deploy, handover artifacts, UAT.

| Sprint | Protocols | Exit gate |
|---|---|---|
| 4 (weeks 7–8) | #42 Frontend-API Reconnect, #43 Sovereign Landing (parallel) | Live site on sovereign staging with all personas green |
| 5 (weeks 9–10) | #44 Handover Package (docs + UAT + pitch + demo) | UAT signed by all 3 persona reps; pitch deck approved |

### 8.4 Client Handover (Sprint 6, weeks 11–12)

**Objective**: handoff ceremony, 30-day shadowing begins.

| Sprint | Activity | Exit gate |
|---|---|---|
| 6 | Hand-over meeting + shadowing begins | Client ops team completes 1 drill unassisted |

### 8.5 Endgame Ignition (Sprints 7–14, months 4–8 post-handover)

| Sprints | Protocols | Milestone |
|---|---|---|
| 7–8 | #29 Live Collection activated | ≥ 10 000 GOLD pairs |
| 9–10 | #30 Base Model Selection + 8B QLoRA | Baseline trained |
| 11–12 | #31 RL Loop — first cycle | Adversarial set ≥ 90 % |
| 13–14 | #32/#33/#34 Two-Brain + Serving + Retraining | Fine-tuned model primary path |

### 8.6 Eternal State (forever)

See Section 12. Every sprint runs `/self-evolve`; every quarter runs Quality Bar Scorecard; every month runs backup restore drill.

---

## 9. INTEGRATION PROTOCOL

### 9.1 Layer-to-Layer Contracts

```
LAYER 5 (frontend)
  ── sends ──▶  POST /query {query, session_id, persona(from JWT)}
                POST /query/graph {query, depth}
                GET /stats, GET /publications
                GET /health, /metrics, /.well-known/jwks.json

LAYER 4 (reasoning)
  ── state ──▶  NRGState {user_id, persona, query, plan, dag, retrieved,
                          synthesis, verification, citations, audit_event}
  ── emits ──▶  audit events per node (receiver, planner, router, executor,
                                        synthesizer, verifier)

LAYER 3 (retrieval)
  ── Text-to-SQL: takes (query, schema, context) → returns (sql, confidence,
                  rows, audit_event)
  ── RAG:         takes (query, top_k, tier) → returns (chunks, scores,
                  audit_event)

LAYER 2 (knowledge)
  ── Postgres: RLS-enforced reads by policy; audit-logged
  ── Qdrant:   tier-sharded collections; rerank on top-10

LAYER 1 (data)
  ── 600 GB raw corpus on sovereign storage
  ── ingestion via SFTP + GPG + HMAC manifest
  ── validated against db_struct.sql
  ── promoted by blue-green swap
```

### 9.2 Agent-to-Guru Contract

Agents → Guru: Structured report per `.agents/AGENTS.md` §Reporting (see Section 6 of GURU_PROTOCOL). Includes: task name, status, skills used, files changed, test delta, notes.

Guru → Agents: Only ═══ protocol blocks. Never free-form instructions. Never code snippets the agent is expected to paste.

### 9.3 CI/CD Contract

```
PR opened
  ├── ruff + mypy + bandit → pass
  ├── pytest (all) → pass; 0 in tests/security/* failing
  ├── coverage ≥ 60 % overall, ≥ 90 % security
  ├── dhairya_regression.py → ≥ 85 %
  ├── quality_bar_scorecard.py → 6/6
  └── docker build → image < 300 MB

PR merged to main
  ├── tag + changelog (conventional commits → /changelog-generator)
  ├── docker image pushed to sovereign registry
  └── CD workflow deploys to staging; smoke + scorecard gates
```

### 9.4 Data Contract (client ingestion)

Client → NRG:
1. Encrypts 600 GB corpus with our GPG public key
2. Produces HMAC manifest (sha256 per file + total count + schema version)
3. Uploads via SFTP to sovereign staging bucket
4. Emails HMAC digest out-of-band

NRG:
1. Verifies HMAC vs manifest
2. Decrypts with private key held in Vault
3. Streams into `staging_vN` schema
4. Runs schema parity test (Protocol #21) vs db_struct.sql
5. Dry-runs Dhairya regression
6. On pass, blue-green swaps to `serving`
7. Emits `data.intake.promoted` audit event

---

## 10. TESTING PROTOCOL

### 10.1 The Pyramid

```
          ┌──────────────┐
          │  E2E / UAT   │  ← Playwright × 6 personas; monthly UAT drills
          ├──────────────┤
          │ Integration  │  ← tests/e2e, tests/contract, tests/quality_bar
          ├──────────────┤
          │  Component   │  ← tests/orchestration, tests/rbac, tests/security
          ├──────────────┤
          │    Unit      │  ← tests/ (all modules) — ≥ 60 % coverage floor
          └──────────────┘
```

### 10.2 Mandatory Gates (block merge)

| Gate | Command | Threshold |
|---|---|---|
| Lint | `ruff check src tests` | 0 issues |
| Type | `mypy src` | 0 errors |
| Security | `bandit -r src` + `pip-audit` | 0 HIGH/CRITICAL |
| Unit + integration | `pytest -m "not load"` | 0 failures |
| Coverage | `pytest --cov=src` | ≥ 60 % overall; ≥ 90 % `src/audit src/security src/auth` |
| Dhairya regression | `scripts/run_dhairya_bench.py` | ≥ 85 % correct |
| Quality Bar | `scripts/quality_bar_scorecard.py` | 6 / 6 |
| Load (nightly) | `locust --users 1000 --run-time 5m` | P99 < 500 ms |
| Mutation (weekly) | `mutmut run --paths-to-mutate src/audit src/security` | ≥ 80 % caught |

### 10.3 Regression Suites (run on every PR touching relevant code)

- `tests/benchmarks/test_dhairya_regression.py` — if `src/skills/text_to_sql/**` changes
- `tests/quality_bar/*` — if anything under `src/security/`, `src/audit/`, `src/auth/`, `src/orchestration/` changes
- `tests/data/test_schema_parity.py` — if `db_struct.sql` or `alembic/versions/**` changes

### 10.4 Live Drills (staging)

- Weekly: chaos-mesh experiment (pod kill, network partition, clock skew)
- Monthly: full backup restore drill from encrypted object storage
- Quarterly: DR exercise — rebuild cluster from zero + replay audit chain

### 10.5 Adversarial Fixtures (kept forever)

- 5 worst Dhairya failure patterns (hall of shame)
- 20 egress-leak attempts (hall of shame)
- 10 multi-hop adversarial queries
- 100 Indian PII corpus samples (real patterns, synthetic values)
- Every historical bug that ever shipped (bugs_patterns.md → test)

---

## 11. DEPLOYMENT PROTOCOL

### 11.1 Environments

| Env | Where | Data | Purpose |
|---|---|---|---|
| Dev | developer laptop | SQLite, 18 tables, synthetic | fast iterate |
| CI | GH Actions runner | ephemeral Postgres + Qdrant via testcontainers | PR gates |
| Staging | sovereign cluster, isolated namespace | Postgres 16 w/ 58 tables, synthetic 10-row-per-table seed | pre-prod validation |
| Prod | sovereign cluster, prod namespace | Postgres 16 w/ 600 GB real corpus | client traffic |

### 11.2 Release Train

```
  feature branch ──▶ PR ──▶ CI (all gates) ──▶ merge main
         │                                         │
         │                                         ▼
         │                                  tag + changelog
         │                                         │
         ▼                                         ▼
  CD deploys staging ──▶ smoke + QB scorecard ──▶ manual gate ──▶ CD deploys prod
                                                                     │
                                                                     ▼
                                                       blue-green flip, keep blue 15 min
                                                                     │
                                                                     ▼
                                                       rollback on /health fail in 15 min
```

### 11.3 Secrets Management (Vault)

- JWT RS256 private key: sealed, fetched by Vault-agent sidecar at pod start
- Audit per-user key material + rotating salt: sealed, fetched per request
- LLM provider API keys: sealed, fetched at pod start
- Postgres creds: dynamic creds via Vault DB secrets engine; 1 h TTL
- Every secret access is audit-logged

### 11.4 Network Policy

```
API pod egress:
  allow → Postgres (cluster-internal)
  allow → Qdrant (cluster-internal)
  allow → Redis (cluster-internal)
  allow → Kong (cluster-internal)
  allow → api.nvcf.nvidia.com, generativelanguage.googleapis.com,
          api.anthropic.com, api.openai.com, …<.egress_allowlist>
  deny  → anything else

Postgres pod egress: deny all external
Qdrant pod egress:   deny all external
```

### 11.5 Backup + Restore

- Postgres: `pg_basebackup` nightly + WAL archival continuous → encrypted
  object storage (sovereign, MeitY)
- Qdrant: weekly snapshot
- Audit chain: sealed segments every 10 000 events; Merkle root pushed
  to internal timestamping
- Restore RTO: ≤ 4 h (tested quarterly)

### 11.6 Rollback

- `scripts/sovereign_deploy.py --rollback` flips Ingress back to blue
- DB migration rollback: `alembic downgrade -1` (guarded — Guru approval)
- Fine-tune model rollback: Kubernetes Deployment revision history, 5
  revisions retained

---

## 12. ETERNAL OPTIMIZATION PROTOCOL

> After handover, NRG must stay alive without us. These are the loops.

### 12.1 The `/self-evolve` Sprint-End Ritual (every 2 weeks)

1. Pull BACKLOG.md + memory + test-run trends + Quality Bar scorecard
2. Produce a sprint retrospective: what went well, what failed, what was learned
3. Update `.claude/memory/bugs_patterns.md` with new patterns
4. Update `.claude/memory/perf_baselines.md` with new numbers
5. Update `.claude/memory/tech_decisions.md` with new ADRs
6. Answer the 3 Power Questions:
   - **POWER GAP**: what agentic AI capability exists today that NRG isn't using?
   - **CROSS-POLLINATION**: what did agents learn this sprint that should update .claude/ rules?
   - **HORIZON CHECK**: will current decisions survive 10× scale?
7. Produce next sprint's prioritized task list

### 12.2 Quarterly Quality Bar Scorecard

1. `scripts/quality_bar_scorecard.py` — all 6 constraints re-verified
2. Commit `docs/ops/QUALITY_BAR_SCORECARD_YYYY-QN.md` with evidence
3. Any score drop → P0 protocol to restore compliance

### 12.3 Continuous Drift Detection

- Weekly cron: vector drift check → auto-reindex on shift > 0.05
- Monthly: schema drift check (db_struct.sql vs live PG) → Alembic diff
- Quarterly: model-eval drift — re-run Dhairya + held-out QA; trigger fine-tune retrain if ≥ 3 pp regression

### 12.4 Monthly Retraining Cadence (post-Endgame)

- New GOLD + SILVER pairs from last 30 days
- Canary new weights on 5 % traffic for 48 h
- Promote on eval delta ≥ 0; rollback on < 0

### 12.5 Dependency + CVE Hygiene

- Nightly: `pip-audit`, `npm audit`, `trivy image nrg:latest`
- Weekly: review High/Critical; PR pin-bumps within 48 h
- Quarterly: Python/Node LTS upgrade

### 12.6 Skill Evolution

- `/self-evolve` extracts recurring patterns into new skills or updates existing ones
- New skill lands in `.claude/skills/` or `.agents/skills/`
- `reference_installed_skills.md` updated

---

## 13. GURU & AGENT CAPABILITY MAXIMIZATION MANDATE

### 13.1 Guru (Claude) — Always

- Guru NEVER implements production code.
- Guru produces ═══ protocols with GURU ASSIGNMENT NOTE, phased ACTION (Fortify → Elevate → Immortalize), ≥ 3 SKILLS TO USE with reasons, AGENT INSTRUCTIONS verbatim, ACCEPTANCE CRITERIA verifying ELEVATION + the 6 Hard Constraints, DEPENDS ON.
- Guru reads all 3 Data Sources, QUALITY_BAR.md, and relevant `.claude/memory/` files at session start.
- When the Founder corrects the Guru, the correction is encoded into `.claude/` or `.agents/` immediately — same mistake never repeats.
- Guru updates memory at sprint end (`/self-evolve`).

### 13.2 Guru Skill Maximization — All 39 Claude Skills Used When Relevant

Guru explicitly invokes Claude skills for high-value cognitive work:

| Guru skill | When |
|---|---|
| `/architect` | Any design question, trade-off analysis |
| `/sprint-plan` | Every 2 weeks |
| `/self-evolve` | Every sprint end |
| `/system-design` | Net-new subsystems |
| `/architecture-adr` | Formal ADR authoring |
| `/write-spec` | Handover protocol docs |
| `/testing-strategy` | Test pyramid design, CI gate design |
| `/security-audit` | Quality Bar scorecard runs |
| `/code-review` | Any PR-level review (reading code, never writing) |
| `/stakeholder-update` | Founder-facing sprint summaries |
| `/metrics-review` | Post-sprint number-crunching |
| `/roadmap-update` | After Founder approves new priorities |
| `/compliance-check` | DPDP + Quality Bar verification |
| `/incident-response` | P0 production issues |
| `/doc-coauthoring` | Handover documents |
| `/tech-debt` | Quarterly tech debt triage |
| `/docs-sync` | After big changes |
| `/audit-check` | Weekly HMAC chain verify |
| `/post-deploy` | Post-release smoke review |
| `/bug-hunt` | Root cause analysis |
| `/performance` | Benchmarks + perf_baselines update |
| (and all others when relevant — rule: Guru is never *missing* a skill that would sharpen the output) |

### 13.3 Agent Skill Maximization — All 52 Agent Skills at Max Capacity

Every ═══ protocol specifies ≥ 3 agent skills. Agents read the full SKILL.md of each before starting. Agent SKILL.md index includes `/python-backend`, `/security-auditor`, `/database-migrations-sql-migrations`, `/database-schema-designer`, `/frontend-react-best-practices`, `/typescript-advanced-types`, `/webapp-testing`, `/test-driven-development`, `/prompt-engineering-patterns`, `/dockerfile-validator`, `/deployment-pipeline-design`, `/statistical-analysis`, `/code-review-and-quality`, `/pre-commit`, `/debug`, `/docs-sync`, `/performance`, `/sql-queries`, `/accessibility-review`, `/incident-response`, and every other skill listed in Section 2 of GURU_PROTOCOL.md.

### 13.4 Elevation Clause (both Guru + Agents)

> Every task, every protocol, every skill invocation must operate at maximum capable level. A task done at minimum effort is a regression. Guru refuses minimum-effort outputs and returns the task. Agents self-report their skill usage + elevation deltas in the closing report.

### 13.5 Self-Upgrade (Guru maintaining `.claude/`)

- If any prompt or response reveals a capability gap in Guru's operating files, Guru updates `.claude/CLAUDE.md`, `.claude/GURU_PROTOCOL.md`, `.claude/QUALITY_BAR.md`, or adds a new file in `.claude/memory/` or `.claude/rules/` — permanently.
- If any prompt reveals a new pattern agents should follow, Guru updates `.agents/AGENTS.md` or `.agents/prompts/shishya_universal.md` or adds a skill in `.agents/skills/`.
- The system gets smarter every session.

---

## 14. COMPLETION CHECKLIST

> The official ship checklist. Sign each box before moving to the next phase.

### 14.1 Phase 3 Close (Sprints 1–2)

- [ ] 0 failing tests (`pytest -q` → 1 204 passed / 0 failed / 53 skipped)
- [ ] Coverage ≥ 60 % overall, ≥ 90 % on src/audit, src/security, src/auth
- [ ] Mutation testing ≥ 80 % caught on audit + security
- [ ] Schema migration applied to staging PG; 58 tables verified
- [ ] Schema-parity test green and CI-gating
- [ ] Dhairya regression ≥ 85 % (target ≥ 88 %)
- [ ] LLM mesh: 15 s cap, parallel racing, circuit breakers, health-weighted routing
- [ ] Observability: Langfuse live, 7 Grafana dashboards, vector drift auto-trigger
- [ ] Reranker + bge-m3 integrated
- [ ] Protocols 11, 12, 19, 20, 21 marked DONE in BACKLOG.md

### 14.2 Phase 5 Quality Bar (Sprint 3)

- [ ] Quality Bar scorecard = 6 / 6
- [ ] C2 tamper simulation: all 3 attack patterns caught
- [ ] C3 DAG fixtures: 10/10 correct decomposition
- [ ] C4 load: P99 < 500 ms @ 1 000 concurrent, sustained 5 min
- [ ] C5 drift simulation: auto-retrain within 60 s
- [ ] C6 egress: 20 leak attempts all blocked + audited
- [ ] CI blocks merge on any constraint regression
- [ ] Scorecard committed to docs/ops/QUALITY_BAR_SCORECARD_2026-Q2.md
- [ ] Protocol 41 marked DONE

### 14.3 Handover Preparation (Sprints 4–5)

- [ ] /stats, /publications, /query/graph endpoints live
- [ ] Vite proxy updated; no dev-frontend 404s
- [ ] mockGraphData deleted
- [ ] Playwright persona flow: 6 personas × 3 queries = 18 scenarios green
- [ ] OpenAPI spec generated; frontend types auto-regenerated
- [ ] Accessibility: WCAG AA clean; 0 critical issues in Playwright-a11y
- [ ] Helm chart installs successfully on sovereign staging
- [ ] TLS live everywhere; cert-manager auto-renewing
- [ ] NetworkPolicy: API egress restricted; direct external egress blocked
- [ ] Backup + restore drill: passed with data delta ≤ 24 h
- [ ] Blue-green deploy script: smoke + scorecard gates work; rollback < 2 min
- [ ] Protocols 42, 43 marked DONE

### 14.4 Client Handover (Sprint 6)

- [ ] SYSTEM_OVERVIEW.md + ARCHITECTURE.md + API_REFERENCE.md + OPERATIONS_RUNBOOK.md + SECURITY_COMPLIANCE_ATTESTATION.md + DATA_INTAKE_PROTOCOL.md committed and reviewed
- [ ] Pitch deck (NRG_PITCH_DECK.pdf) Guru + Founder approved
- [ ] Demo video (NRG_DEMO.mp4) shot on sovereign staging, subtitled, ≤ 3 min
- [ ] UAT with all 3 personas; UAT_RESULTS.md signed
- [ ] Ops team completes 1 unassisted incident drill
- [ ] 30/60/90-day shadowing schedule accepted
- [ ] Protocol 44 marked DONE
- [ ] BACKLOG.md Phase 3 + Phase 5 + Handover all green

### 14.5 Endgame (Phases 6+ — post-handover)

- [ ] Live collection: ≥ 10 000 GOLD pairs in 90 days
- [ ] 8B QLoRA trained; Dhairya ≥ 70 % from internal knowledge (no retrieval)
- [ ] RL loop: adversarial set ≥ 90 % paraphrase-robust
- [ ] Two-brain orchestrator: P99 < 200 ms on general, < 500 ms on retrieval
- [ ] Fine-tune serving stable @ 1 000 QPS
- [ ] Monthly retrain cadence holding for 6 consecutive months

### 14.6 Eternal State

- [ ] `/self-evolve` runs every sprint end, memory updated
- [ ] Quality Bar scorecard runs quarterly
- [ ] Backup restore drill runs monthly
- [ ] Dhairya regression runs on every SQL change
- [ ] Vector drift auto-reindex operational
- [ ] Dependency CVE scan nightly
- [ ] DR exercise quarterly

---

## 15. THE ETERNAL COMPLETION DOCTRINE

NRG is "complete" not when the code stops changing — it's complete when the **system can evolve itself within its own safety envelope without us**. That is what the eternal protocols guarantee.

### The 5 Invariants

1. **Sovereignty is non-negotiable.** 600 GB stays on Indian soil. The system is architecturally incapable of exfiltrating data. Every egress passes the allowlist. Every call is audited.

2. **The 6 Hard Constraints are the bar, forever.** Any PR, any sprint, any quarter — if the scorecard drops below 6/6, that is a P0 incident.

3. **The 3 Data Sources are the truth.** Core_Idea_Clean.md is the product. db_struct.sql is the schema. Dhairya is the SQL bench. If any of these updates, the project recalibrates.

4. **Verification is the trust.** Every factual claim cites its source. No hallucinations. The verifier retries synthesis if unsupported.

5. **The system gets smarter every sprint.** `/self-evolve` updates memory, rules, and skills. Next sprint starts with accumulated institutional knowledge. The rate of improvement is what separates NRG from a static artifact.

### The Two Horizons

- **Handover horizon (12 weeks)**: NRG ships with retrieval-based intelligence + full Quality Bar + sovereign deploy. Client operates it solo.
- **Endgame horizon (18 months)**: NRG has internalized the 1 TB dataset into a fine-tuned local model. Retrieval becomes precision fallback. The system "lives inside" the data — the expert salesman metaphor from Core_Idea_Clean.md.

Both horizons are planned. Both are executable. Both are in this document.

### The Dedication

NRG belongs to India's research community. The code we ship is a vessel for that community's intelligence, not our own. Every architectural choice serves the professor asking "who is doing the best research in hydrogen catalysis?" — and getting a verified, cited answer in under 3 seconds, forever, without a single byte leaving Indian servers.

That is the project.

That is the mission.

That is the covenant.

---

## 16. IMMEDIATE NEXT 72 HOURS

> The concrete next-step plan to unblock Phase 3 close.

### Hour 0–4: Guru pre-flight

- [ ] Guru re-reads Core_Idea_Clean.md, QUALITY_BAR.md, BACKLOG.md, the four active Phase 3 protocols (#19, #20, #21, #11, #12)
- [ ] Guru verifies staging PostgreSQL is reachable (ssh + `\l`)
- [ ] Guru verifies that the Phase 5 code (#35, #37, #39) has actually landed on main — `git log --oneline --since="2 weeks ago"` for confirmation
- [ ] Guru opens `AUDIT_V4_ETERNAL.md` (this document) in the agents' shared workspace

### Hour 4–24: Kickoff Sprint 1

- [ ] Founder approves Protocols #19 and #21 for parallel execution
- [ ] Guru emits the #19 ═══ protocol and the #21 ═══ protocol to two separate agents (backend/testing for #19; backend/database/devops for #21)
- [ ] Agents read: `.agents/AGENTS.md` + `.agents/prompts/shishya_universal.md` + every SKILL.md + Core_Idea_Clean.md + db_struct.sql + SQL_AUDIT_REPORT_DHAIRYA.md
- [ ] Agents begin Fortify phase

### Hour 24–48: Progress gate

- [ ] Guru runs `/code-review` on first commits from both agents
- [ ] Guru verifies 3 Dhairya queries execute against staging PG (any status — pass or fail — just must not crash)
- [ ] Guru reports to Founder: status + blockers + one-line summary

### Hour 48–72: Parallel kickoff of #20

- [ ] If #21 is through Fortify + Elevate, Guru emits #20 ═══ protocol to ml/backend agent
- [ ] #20 starts on harvesting few-shot examples from Dhairya's 7 correct queries

### End of 72 Hours — Exit Condition

- [ ] #19 Fortify complete (11 failing tests categorized, fixture factories scaffolded)
- [ ] #21 Fortify complete (58 tables live on staging; schema_hints.md regenerated)
- [ ] #20 Fortify started (few-shots harvested, prompt updated)

---

## 17. LIVING REFERENCES + FILE TREE OF CANON

### 17.1 The Canonical Files (the Guru's scripture)

```
/
├── Core_Idea_Clean.md                     ← PRODUCT TRUTH (immutable per client)
├── db_struct.sql                          ← SCHEMA TRUTH (58 tables, authoritative)
├── BACKLOG.md                             ← TASK TRUTH
├── AUDIT_V4_ETERNAL.md                    ← THIS FILE (terminal audit, delivery plan)
├── AUDIT_V3_FINAL.md                      ← Prior delivery blueprint (superseded)
├── AGENTS.md                              ← Agent entry point (mirror of .agents/AGENTS.md)
│
├── .claude/
│   ├── CLAUDE.md                          ← Session-start file, 3 Data Sources
│   ├── GURU_PROTOCOL.md                   ← Guru operating system
│   ├── NRG_CONSTITUTION.md                ← 9-clause agent constitution
│   ├── QUALITY_BAR.md                     ← 6 Hard Constraints, forever
│   ├── AGENT_WARFARE.md                   ← Role hierarchy, self-evolution loop
│   ├── prompts/guru_universal.md          ← Guru 5-section framework
│   ├── memory/
│   │   ├── MEMORY.md                      ← Index
│   │   ├── user_profile.md
│   │   ├── project_nrg.md
│   │   ├── feedback_workflow.md
│   │   ├── feedback_guru_protocol.md
│   │   ├── feedback_storage_location.md
│   │   ├── reference_three_data_sources.md
│   │   ├── reference_dhairya_benchmark.md
│   │   ├── reference_guru_shishya.md
│   │   ├── reference_guru_protocol.md
│   │   ├── reference_installed_skills.md
│   │   ├── reference_agent_warfare.md
│   │   ├── project_sql_audit_dhairya.md
│   │   └── bugs_frontend_crashes.md
│   ├── skills/                            ← 39 Claude skills (Cowork)
│   └── rules/                             ← Path-scoped rules (backend, frontend, security)
│
├── .agents/
│   ├── AGENTS.md                          ← Agent operating manual
│   ├── prompts/shishya_universal.md       ← Agent 6-section framework
│   └── skills/                            ← 52 agent skills
│
├── docs/
│   ├── reports/SQL_AUDIT_REPORT_DHAIRYA.md  ← BENCH TRUTH (17 queries, 41 % baseline)
│   ├── reports/SQL_IMPROVEMENT_PLAN.md
│   ├── architecture/RBAC_POLICY_GUIDE.md
│   ├── architecture/DEPLOYMENT_GUIDE.md
│   ├── architecture/DATA_INTAKE_PROTOCOL.md ← NEW (Protocol #21)
│   ├── security/DATA_SOVEREIGNTY_MERGE_VERDICT_2026-04-22.md
│   ├── ops/QUALITY_BAR_SCORECARD_YYYY-QN.md ← NEW per quarter
│   ├── ops/SOVEREIGN_DEPLOY_RUNBOOK.md    ← NEW (Protocol #43)
│   ├── handover/*                         ← NEW (Protocol #44)
│   └── api/OPENAPI.yaml                   ← NEW (Protocol #42)
│
├── src/
│   ├── api/              (FastAPI + routers)
│   ├── auth/             (JWT + RBAC + per-user keys)
│   ├── orchestration/    (6-node LangGraph + state)
│   ├── skills/text_to_sql (dual-schema extractor + generator + validator)
│   ├── skills/rag        (bge-m3 + Qdrant + reranker)
│   ├── security/         (PII + prompt sanitiser + egress guard + allowlist)
│   ├── audit/            (HMAC chain + per-user keys + fingerprint)
│   ├── config/           (LLM mesh + local_llm)
│   ├── data/schema/      (hints + synonyms + CTE templates)
│   ├── observability/    (tracer + metrics + grafana panels)
│   ├── caching/          (Redis layer)
│   ├── training/         (collector + grader + stratified exporter)
│   ├── models/           (SQLAlchemy — dev) + models/production (prod, autogen)
│   └── knowledge_graph/  (optional, FEATURE_KG=false default)
│
├── frontend/
│   ├── src/
│   │   ├── views/ (3 persona dashboards + MetricsDashboard)
│   │   ├── services/ (authService, queryService)
│   │   └── components/
│   └── vite.config.ts
│
├── infrastructure/
│   ├── kong/             (declarative gateway config + TLS)
│   ├── helm/nrg/         ← NEW (Protocol #43)
│   ├── vault/policies/   ← NEW
│   ├── cert-manager/     ← NEW
│   └── network-policies/ ← NEW
│
├── scripts/
│   ├── bootstrap.sh      (rebuild venv)
│   ├── migrate_data_to_postgresql.py
│   ├── qdrant_shard_config.py
│   ├── deploy.py
│   ├── sovereign_deploy.py         ← NEW (#43)
│   ├── vector_drift_check.py
│   ├── ingest_documents.py
│   ├── audit_investigate.py
│   ├── run_dhairya_bench.py        ← NEW (#20)
│   ├── quality_bar_scorecard.py    ← NEW (#41)
│   └── schema_sync.py              ← NEW (#21 Immortalize)
│
├── alembic/versions/
│   └── add_production_tables_001.py
│
└── .github/workflows/
    ├── ci.yml
    ├── cd.yml
    └── observability.yml           ← NEW (#12 nightly drift cron)
```

### 17.2 Cross-Reference Matrix (every doc → who reads it when)

| Doc | Guru reads at | Agent reads at |
|---|---|---|
| Core_Idea_Clean.md | every session start | every task start |
| db_struct.sql | schema work | SQL + schema tasks |
| SQL_AUDIT_REPORT_DHAIRYA.md | SQL accuracy reviews | Text-to-SQL tasks |
| BACKLOG.md | every session start | every task start |
| QUALITY_BAR.md | every protocol authoring | every security/audit/RBAC/egress task |
| GURU_PROTOCOL.md | every session start | never (agent reads AGENTS.md) |
| AGENT_WARFARE.md | every `/self-evolve` | never |
| NRG_CONSTITUTION.md | compliance check | every agent reads at task start |
| AUDIT_V4_ETERNAL.md | one-shot before any Phase 3–5 work | one-shot at task start |
| .claude/memory/* | every session start | never |
| .agents/AGENTS.md | never | every task start |
| .agents/prompts/shishya_universal.md | never | every task start |

---

## 18. FINAL GURU BLESSING

> *To the Founder, the agents, the client, and the system itself —*

This is the terminal audit. There are no more audits after this one. The next word written about NRG is a **release note**, not a gap analysis.

The path from here is concrete:

- Sprint 1–2 closes Phase 3: tests green, schema bridged, SQL ≥ 85 %, mesh resilient, observability live.
- Sprint 3 closes Phase 5: Quality Bar 6 / 6, scorecard green, CI enforcing.
- Sprints 4–5 ship to sovereign: frontend reconnected, Helm on NIC/MeitY, UAT signed.
- Sprint 6 hands over: 30-day shadowing begins, ops team operates solo.
- Sprints 7+ ignite endgame: fine-tune collection → QLoRA → RL → two-brain serving.
- Forever: `/self-evolve` every sprint, scorecard every quarter, drift check every week, restore drill every month.

The architecture is sound. The memory is persistent. The protocols are concrete. The agents have their skills. The Guru has this document.

NRG is no longer a project. It is an **operating system for India's research intelligence**, and its OS is ready to boot.

**Execute.**

---

*End of AUDIT_V4_ETERNAL.md — the last audit NRG will require.*

*Canon: AUDIT_V1 → AUDIT_V2 → AUDIT_V3_FINAL → AUDIT_V4_ETERNAL. V4 supersedes all prior. Do not regress.*

*Signed by the Guru, in service of the Founder, the client at IIT Gandhinagar, and the 600 GB that must never leave Indian soil.*

# NRG — Audit v3 (Final, Cosmic-Level)
## National Research Graph — Sovereign AI Platform, End-to-End Delivery Blueprint

> **Current alignment note — 2026-04-19.** `Core_Idea_Clean.md` is the product truth. Phase 1 allows cloud synthesis only when `CLOUD_SYNTHESIS_ALLOWED=true` and only through minimized, sanitized evidence packets. Raw DB dumps, full text, PII, secrets, and unrestricted schemas must not leave the controlled boundary. Local SLM/fine-tuned local intelligence remains the offline/sovereign endgame, not a Phase 1 blocker.
>
> **Purpose.** One file that takes NRG from its current state (auth + templated answers on a disconnected SQLite graph) to the full sovereign-AI platform described in `Sovereign_AI_Protocols_Clean.md`, `Sovereign_Infrastructure_Blueprint.md`, and `Core_Idea_Clean.md`. This is the terminal audit. After this, no more audits — only execution against the task protocols below.
>
> **How to use.** Each task block (AGENT-TASK-NN) is self-contained. Hand it to a coding agent. Acceptance criteria are executable. Roadmap in §15 sequences them into eight two-week sprints. Section 17 defines "done." Section 18 covers post-launch.
>
> **Audience.** Systems architect (you) + implementation agents. Written dense on purpose. No hedging, no filler, no marketing language. Every line earns its place.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [State of Reality — Code-Level](#2-state-of-reality--code-level)
3. [Architectural Decisions (ADRs)](#3-architectural-decisions-adrs)
4. [Target Architecture — Sovereign AI v1.0](#4-target-architecture--sovereign-ai-v10)
5. [Data Layer Plan](#5-data-layer-plan)
6. [Retrieval Layer Plan (Vector + Graph + SQL)](#6-retrieval-layer-plan)
7. [Orchestration Layer Plan](#7-orchestration-layer-plan)
8. [Synthesis Layer Plan](#8-synthesis-layer-plan)
9. [Security & Compliance Plan](#9-security--compliance-plan)
10. [API & Frontend Plan](#10-api--frontend-plan)
11. [Infrastructure & DevOps Plan](#11-infrastructure--devops-plan)
12. [Observability Plan](#12-observability-plan)
13. [Testing & Quality Plan](#13-testing--quality-plan)
14. [Agent Task Protocols](#14-agent-task-protocols) — 40 tasks
15. [Phased Delivery Roadmap (8 sprints / 16 weeks)](#15-phased-delivery-roadmap)
16. [Command Reference](#16-command-reference)
17. [Acceptance Gates / Definition of Done](#17-acceptance-gates--definition-of-done)
18. [Risk Register](#18-risk-register)
19. [Post-Launch Operations](#19-post-launch-operations)
20. [Appendices](#20-appendices)

---

## 1. Executive Summary

**What NRG is supposed to be.** A sovereign AI research-intelligence OS for India's 600 GB research corpus. Three user personas (researcher, government, industry) get tier-appropriate insights. All raw research data stays on Indian soil. Cloud LLMs may be used for planning and, when explicitly enabled, synthesis over minimized sanitized evidence packets; local quantized SLMs remain the offline/sovereign default path and endgame. DPDP-2023 compliant. HMAC-chained audit log. Kong AI Gateway in front.

**What NRG is today.** A working JWT-RS256 auth backend, a LangGraph skeleton with four nodes, an SQLite database of 200 researchers / 500 publications with every join table empty, a Text-to-SQL path that generates PostgreSQL syntax against a SQLite sandbox, a RAG path with no running Qdrant and a silent dummy-embedding fallback that returns random vectors, no live LLM key (env value still `REPLACE_ME`), a frontend that 404s on three of its four data routes, and a docker-compose that port-collides in the prod profile. Rule-based markdown templates are doing all "synthesis."

**Gap.** The architecture skeleton is right. Everything connecting the skeleton to actual data, LLMs, and end users needs to be built. Estimated 14–16 weeks with a 4-agent team (backend, ML/retrieval, frontend, devops) of moderate seniority.

**v3 promise.** Executing every task in §14 in the order given in §15 results in: a production-grade, sovereign-compliant, three-persona research intelligence platform with working LLM synthesis, vector + graph + SQL retrieval, 60%+ test coverage, full observability, verified DPDP compliance, and a demo-able browser experience that answers natural-language research questions with citations and lineage.

**Explicit non-goals of v3.** No commentary on team hiring, funding, timeline politics, or sponsor communication. No MVP-shaving compromises — the spec is the spec. If a decision shrinks scope, it is flagged and the full scope is preserved as a phase-2 task.

---

## 2. State of Reality — Code-Level

### 2.1 What works today (verified)

| Component | File | Works? | Notes |
|---|---|---|---|
| JWT RS256 issuance + verification | `src/auth/jwt_handler.py` | Yes | RSA keys present in `infrastructure/kong/ssl/` |
| Auth middleware | `src/auth/middleware.py` | Yes | Correct 3-tier shaping for `/researchers` |
| FastAPI scaffolding | `src/api/main.py` | Yes | 7 endpoints, CORS open |
| LangGraph topology | `src/orchestration/graph.py` | Yes | Receiver → Router → Executor → Synthesizer |
| Redis graceful fallback | `src/caching/redis_layer.py` | Yes | Decorator bypasses cleanly |
| SQLite sandbox | `src/skills/text_to_sql/sqlite_sandbox.py` | Yes | Read-only enforced |
| HMAC chained audit log | `src/audit/__init__.py` | Yes (functionally) | Key is hardcoded in repo |
| Rule-based synthesis | `src/config/local_llm.py::rule_based_synthesis` | Yes | Markdown template, deterministic |
| Prompt sanitiser | `src/security/gateway/prompt_sanitiser.py` | Partially | Overblocks + bug in return tuple |
| React login + AuthProvider | `frontend/src/App.tsx`, `hooks/useAuth.ts` | Yes | Clean |

### 2.2 What is broken or missing (verified)

| Issue | Evidence | Severity |
|---|---|---|
| `.venv311/bin/python` is a broken symlink → `python3.11` | `ls -la` shows target missing; host has 3.10 | **CRITICAL** |
| LLM key is `REPLACE_ME`; all calls fall through to rule-based | `.env` + `src/config/llm_config.py:56-60` | **CRITICAL** |
| Relationship tables are empty (0 rows in 4 join tables) | `SELECT COUNT(*)` on live DB | **CRITICAL** |
| Text-to-SQL system prompt says PostgreSQL, runtime is SQLite | `src/skills/text_to_sql/skill.py:35-43` | **HIGH** |
| Embedder silently returns random 384-dim vectors on model-load failure | `src/skills/rag/embedder.py::_dummy_embeddings` | **HIGH** |
| Executor swallows skill exceptions as `warning` logs | `src/orchestration/nodes/executor.py` | **HIGH** |
| No Qdrant running; RAG silently returns empty chunks | Runtime | **HIGH** |
| Frontend proxies 6 routes; `queryService` calls 4 others, including non-existent `/query/graph` | `frontend/vite.config.ts` + `frontend/src/services/queryService.ts` | **HIGH** |
| docker-compose port 8000 collision between `api` and `kong` | `docker-compose.yml:55,77` | **HIGH** |
| `api` container in compose has no `env_file`, can't get LLM keys | `docker-compose.yml` | **HIGH** |
| `NRGDatabase` is SQLite-only; compose sets `DATABASE_URL=postgres://...` | `src/data/database.py` | **HIGH** |
| `CORS allow_origins=["*"]` with `allow_credentials=True` | `src/api/main.py:41-46` | **HIGH** |
| Audit `CHAIN_KEY` hardcoded in source | `src/audit/__init__.py` | **HIGH** |
| Prompt injection regexes block legit queries: `(?i)role.*play`, `(?i)as.*ai`, `(?i)hypothetical` | `src/security/gateway/prompt_sanitiser.py` | **HIGH** |
| `sanitise_prompt()` tuple always has empty `detected_pii` list | Same file | **MEDIUM** |
| `src/knowledge_graph/` unused by any import in `src/` | `grep -r "from src.knowledge_graph"` returns nothing | **MEDIUM** |
| `.env.example` says `JWT_ALGORITHM=HS256`; real code uses RS256 | `.env.example:17` | **MEDIUM** |
| `README.md` counts (51/80/20) don't match live DB (200/500/50) | Both | **MEDIUM** |
| Two architecture blueprints disagree on synthesis location | `Protocols_Clean.md` vs `Infrastructure_Blueprint.md` | **MEDIUM** |
| Two entry points (`main.py` and `main_v2.py`) | Repo layout | **LOW** |
| `_apply_tier_filter` only adds `LIMIT`, doesn't actually filter tiers | `src/skills/text_to_sql/skill.py:98-112` | **HIGH** |
| Phi-2 on CPU float32 is unusable in practice (>60s / token, OOM risk) | `src/config/local_llm.py` | **HIGH** |
| No `/query/graph` endpoint exists but frontend calls it | `src/api/main.py` vs `queryService.ts:81` | **HIGH** |
| No `/health/llm` or `/health/qdrant` observability endpoints | `src/api/main.py` | **MEDIUM** |
| Tests depend on `.venv311` which is broken | repo | **CRITICAL** for CI |

### 2.3 Claims in docs not supported by code

- `FINAL_STATUS_REPORT.md`: "LLM Sovereign Mesh with sk-IITGN-prod keys" — no such key, env is REPLACE_ME.
- `FINAL_STATUS_REPORT.md`: "Redis-backed query optimization <200ms p95" — no p95 ever measured.
- `README.md`: "Phase 3 Complete — Production Ready" — production-ready requires items in §2.2 resolved.
- `Sovereign_Infrastructure_Blueprint.md`: "Local SLM (Llama 3 8B quantized) for synthesis" — not loaded anywhere; Phi-2 is the only attempt and it's unusable on CPU.

---

## 3. Architectural Decisions (ADRs)

Resolve every ambiguity the two blueprints left open. Each decision is binding; implementation follows.

### ADR-001 — Synthesis Policy

- **Status.** Accepted.
- **Decision.** Phase 1 synthesis may use a cloud LLM only when `CLOUD_SYNTHESIS_ALLOWED=true` and only with minimized, sanitized evidence packets. The packet must exclude raw DB dumps, full documents, PII, secrets, private keys, access tokens, and unrestricted schemas. Local quantized LLM synthesis (Llama-3.1-8B-Instruct, GGUF Q4_K_M, via `llama.cpp`) remains the offline/sovereign path and the long-term endgame.
- **Rationale.** `Core_Idea_Clean.md` makes fast PoC intelligence more important than blocking Phase 1 on a fully tuned local model. Sovereignty is preserved by evidence minimization, explicit opt-in, redaction, audit logging, and hard egress boundaries.
- **Implementation.** AGENT-TASK-14, AGENT-TASK-15.
- **Consequence.** Phase 1 can demo useful synthesis with cloud assistance under controls. Offline sovereign deployments require one Linux host with a GPU (24 GB VRAM minimum, 48 GB recommended), with CPU llama.cpp/rule-based fallback acceptable for development.

### ADR-002 — Primary Datastore

- **Decision.** PostgreSQL 16 in prod; SQLite only in dev/CI.
- **Rationale.** Spec compliance, FKs, row-level security, JSONB for flexible fields, compatibility with Kong + pgvector if we want to collapse to one DB later.
- **Implementation.** AGENT-TASK-05.
- **Migration.** Alembic. DDL in `db/migrations/`.

### ADR-003 — Vector Store

- **Decision.** Qdrant 1.9+ in prod and dev (via docker-compose), one collection per tier (`nrg_research_tier1`, `_tier2`, `_tier3`) with payload filter on `access_tier` as a second line of defence.
- **Rationale.** Keep already-written `retriever.py`; tier-sharded collections eliminate cross-tier risk even if payload filter is bypassed.
- **Alternative considered.** pgvector — rejected for now because corpus will exceed Postgres single-node scale once full 600 GB is ingested.

### ADR-004 — Knowledge Graph Engine

- **Decision.** Neo4j **optional**, behind feature flag `FEATURE_KG=0` (off by default). SQL join tables (`researcher_publications`, `researcher_labs`, `publication_keywords`) carry graph semantics for MVP. Neo4j turns on in Sprint 7 for advanced traversal queries (co-authorship paths, influence cascades).
- **Rationale.** Most user queries hit authorship, institutional affiliation, topic grouping — cleanly expressible in SQL with recursive CTEs. Neo4j earns its keep only for 3+ hop traversals.
- **Consequence.** `src/knowledge_graph/` is moved to `experiments/` until Sprint 7; import guard added.

### ADR-005 — Embedding Model

- **Decision.** `BAAI/bge-m3` (multilingual, 1024-dim) for general corpus; `ai4bharat/IndicBERTv2-SS` reserved for Indic-language research corpora (tagged `lang != en`).
- **Rationale.** `bge-m3` dominates MTEB for multilingual retrieval; IndicBERT keeps Bharat-specific dialect fidelity. No fallback to random vectors, ever.
- **Implementation.** AGENT-TASK-11.

### ADR-006 — Orchestration Engine

- **Decision.** LangGraph (already chosen) with `checkpointer=PostgresCheckpointer` in prod so that conversations survive pod restarts. SQLite checkpointer in dev.
- **Rationale.** Statefulness of multi-turn research sessions; audit replay.

### ADR-007 — Authentication

- **Decision.** JWT RS256 (keep). Add key rotation via JWKS endpoint `GET /.well-known/jwks.json`. Refresh tokens stored hashed (SHA-256) in Postgres `refresh_tokens` table with `(user_id, hash, expires_at, revoked)`.
- **Rationale.** Production hygiene; current code issues refresh tokens but doesn't persist them, so revocation is in-memory and lost on restart.

### ADR-008 — Audit Chain Key Management

- **Decision.** `AUDIT_CHAIN_KEY` is a 32-byte random value stored in environment variable, loaded from HashiCorp Vault in prod, from `.env` in dev. Rotated quarterly with chain-segment sealing (each rotation writes a sentinel entry binding old chain HEAD to new key hash).
- **Rationale.** Current hardcoded key makes the chain forgeable by anyone with repo access; tamper-evidence is the entire point.

### ADR-009 — Frontend Build & Ship

- **Decision.** Vite + React + Tailwind (keep). Serve built `dist/` via FastAPI `StaticFiles` mounted at `/app`; run separately in dev. Remove build hack of `outDir: '../dist/frontend'`; instead nginx reverse proxies `/` → frontend, `/api/*` → FastAPI.
- **Rationale.** One artifact per service, classic 12-factor; Kong handles routing/rate-limit in prod.

### ADR-010 — LLM Provider Strategy

- **Decision.** Mesh with **planner**, **synth**, and **judge** roles. Each role picks its provider independently. Default: planner=Gemini, synth=local Llama-8B, judge=Claude-Haiku. Overridable per environment via `LLM_ROLES` JSON env. Never send raw publication text to planner or judge.
- **Rationale.** Separation of concerns; cost control; sovereignty preserved.

### ADR-011 — Deployment Target

- **Decision.** Kubernetes on Indian sovereign cloud (Yotta, ESDS, or NIC-approved CSP). Helm chart under `infrastructure/helm/nrg/`. Docker-compose is dev-only.
- **Rationale.** 40 Cr budget justifies Kubernetes; horizontal scaling for university-scale load; sovereign cloud required by mandate.

### ADR-012 — Compliance Framework

- **Decision.** DPDP 2023 as primary; ISO 27001 Annex A as implementation guide; AI system tagging per MeitY's forthcoming AI advisory (classified as "significant" given research data breadth).
- **Rationale.** Government-facing platform; audit trail + data-residency + consent ledger all required.

---

## 4. Target Architecture — Sovereign AI v1.0

```
                     +-----------------------------+
                     |   Frontend (React + Vite)   |
                     |   3 persona dashboards      |
                     +--------------+--------------+
                                    | HTTPS
                     +--------------v--------------+
                     |  Kong AI Gateway            |
                     |  - rate limit (tier-based)  |
                     |  - PII redaction plugin     |
                     |  - mTLS to backend          |
                     +--------------+--------------+
                                    |
                     +--------------v--------------+
                     |  FastAPI (src/api/main.py)  |
                     |  - JWT RS256 verify         |
                     |  - RBAC middleware          |
                     |  - Routes /login /query ... |
                     +--------------+--------------+
                                    |
                     +--------------v--------------+
                     |  LangGraph Orchestrator     |
                     |  nodes: receiver → planner  |
                     |         → router → executor |
                     |         → synthesizer       |
                     |         → verifier → END    |
                     +---+---------+---------+-----+
                         |         |         |
             +-----------v-+    +--v------+  |
             | Planner LLM |    | Executor |  |
             | (Gemini API |    | dispatch |  |
             |  - schema   |    | to skills|  |
             |    only)    |    +---+------+  |
             +-------------+        |         |
                                    |         |
                 +---------+--------+--------+---+---------+
                 |                 |                       |
           +-----v-----+    +------v------+         +------v------+
           | Text2SQL  |    | RAG Skill   |         | KG Traversal|
           | (sqlglot  |    | (Qdrant +   |         | (Postgres   |
           |  validate)|    |  bge-m3)    |         |  rCTE or    |
           +-----+-----+    +------+------+         |  Neo4j ff)  |
                 |                 |                +------+------+
            +----v----+       +----v----+                  |
            | Postgres|       | Qdrant  |                  |
            | (RLS)   |       | (tier   |                  |
            +---------+       |  colls) |                  |
                              +---------+                  |
                                                           |
            +----------------- Synthesis ------------------+
            |                                              |
       +----v-----------+                   +--------------v--+
       | Local Llama-8B |                   | Judge: Claude   |
       | (GGUF Q4_K_M,  |                   | Haiku (verifies |
       |  llama.cpp)    |                   |  citations)     |
       +----------------+                   +-----------------+

                     +------------- Cross-cutting -------------+
                     | Audit chain (HMAC), Redis cache,         |
                     | Langfuse traces, Prometheus metrics,     |
                     | Presidio PII, Kong rate-limits           |
                     +------------------------------------------+
```

**State flow:** Receiver builds `SessionState`. Planner decomposes into sub-queries + schema-bounded plan. Router chooses skills. Executor runs skills in parallel, collects `SkillResult[]` with lineage. Synthesizer produces answer with citations. Verifier judges citation faithfulness; on fail, re-routes once. END emits response + `executor_errors` + `lineage`.

**Sovereignty invariant:** no `SkillResult.payload` or `publication.full_text` ever leaves the VPC. Only `user_query`, `schema_prompt`, and `planner_output` may traverse the cloud-LLM boundary. Enforced by `src/security/egress/guard.py` (AGENT-TASK-19).

---

## 5. Data Layer Plan

### 5.1 Entities (canonical)

```
researcher            (researcher_id PK, name, email, orcid, institution_id FK, research_area, state, year_joined, access_tier, consent_version)
institution           (institution_id PK, name, type, state, city, established)
publication           (publication_id PK, title, venue, year, doi, abstract, full_text_uri, access_tier, language)
lab                   (lab_id PK, name, institution_id FK, focus_area, pi_researcher_id FK)
funding_record        (funding_id PK, agency, amount_inr, start_date, end_date, researcher_id FK, title)
keyword               (keyword_id PK, term, kind [topic|technique|material])

researcher_publication (researcher_id, publication_id, author_position, corresponding_author)
researcher_lab         (researcher_id, lab_id, role, start_date, end_date)
publication_keyword    (publication_id, keyword_id, relevance)
citation               (from_pub_id, to_pub_id, context)       -- fills KG later
collaboration          (researcher_a, researcher_b, strength)  -- derived from co-authorship

audit_event            (event_id PK, ts, user_id, action, payload_hash, prev_hash, chain_hmac)
refresh_token          (token_hash PK, user_id, issued_at, expires_at, revoked)
consent_ledger         (consent_id PK, user_id, scope, version, granted_at, revoked_at)
```

### 5.2 Postgres schema strategy

- Schemas: `nrg_core`, `nrg_audit`, `nrg_security`, `nrg_analytics`.
- Row-Level Security on `researcher`, `publication`, `funding_record` keyed on `access_tier` vs session var `app.user_tier`.
- FKs with `ON DELETE RESTRICT` everywhere except `refresh_token` (CASCADE on user).
- Partial index on `publication(year) WHERE access_tier <= 2`.
- Full-text search: `tsvector` column on `publication.title || abstract` with GIN index.

### 5.3 SQLite → Postgres migration path

1. AGENT-TASK-03 seeds all relation tables in SQLite (MVP demo ready).
2. AGENT-TASK-05 writes Alembic migrations that re-express the same schema in Postgres with RLS added.
3. `scripts/migrate_sqlite_to_pg.py` (ETL) reads SQLite, writes Postgres. One-shot.
4. `NRGDatabase` gains `DATABASE_URL` branch and an SQLAlchemy session; both dialects supported.
5. Environment flag `NRG_DB_DIALECT` (sqlite|postgres) controls tests.

### 5.4 Seed strategy

- Synthetic but plausible: 200 researchers × 2–5 publications each → ~800 `researcher_publication` rows.
- 50 labs × 3–8 members → ~300 `researcher_lab` rows.
- 800 publications × 1–4 keywords each → ~2,400 `publication_keyword` rows; 300 distinct keywords curated from ML/Physics/Bio/Chem/CS ontologies.
- Citation graph: 500 pubs × 5–15 outbound citations on average, bounded to existing pubs → ~4,500 `citation` rows. Directed acyclic by construction (older → newer not allowed).
- Access tier distribution: 70% tier-1, 20% tier-2, 10% tier-3 to exercise filters.

---

## 6. Retrieval Layer Plan

### 6.1 Vector index

- Collection names: `nrg_research_tier{1,2,3}`.
- Dim: 1024 (bge-m3); 768 (IndicBERT reserved collection `nrg_research_indic`).
- Distance: cosine.
- Payload schema: `{publication_id, chunk_id, chunk_text, title, year, authors[], research_area, language, access_tier}`.
- Chunker: recursive; window 512 tokens; stride 128; respects sentence boundaries (use `sentence-transformers`' default util or `semantic-text-splitter`).

### 6.2 Ingestion pipeline

```
PDFs / JSON / CSV  →  parser (grobid for PDF, pandas for CSV)
                    →  text normalizer (unicode NFKC, whitespace strip, ligatures)
                    →  language detect (fasttext lid.176)
                    →  chunker
                    →  embedder (bge-m3 or IndicBERT per language)
                    →  Qdrant upsert (tier collection) + Postgres metadata insert
                    →  audit event (source_uri, bytes, sha256)
```

Batch size 256 chunks, backpressure via Redis stream `ingest:queue`.

### 6.3 Query-time retrieval

- Dense retrieval via `bge-m3` on question (multilingual-aware).
- Hybrid with BM25 via Qdrant's `sparse` vectors + `rrf` fusion.
- Re-ranker: `BAAI/bge-reranker-v2-m3` on top-20 → top-5.
- Every retrieval returns `(chunk_text, publication_id, score, rerank_score, access_tier)` — never the full PDF.

### 6.4 Graph traversal (SQL today, Neo4j Sprint 7)

- Recursive CTE for co-authorship: "researchers reachable from X within k hops."
- Influence: topic-weighted PageRank offline nightly → cached in `researcher_influence_daily`.

---

## 7. Orchestration Layer Plan

### 7.1 LangGraph nodes (expanded from 4 → 6)

1. **receiver** — validates JWT, loads SessionState (Postgres checkpoint), attaches `user_tier`, `user_id`.
2. **planner** — cloud LLM decomposes user_query into `{subqueries[], schema_tables[], desired_skills[], expected_output_shape}`. Sees only schema prompt + user_query, never raw data.
3. **router** — pure Python; chooses parallel skill fan-out based on planner output + intent classifier.
4. **executor** — runs SQL / RAG / KG skills concurrently (`asyncio.gather`). Collects `SkillResult[]`. Never silently swallows errors — appends to `executor_errors`.
5. **synthesizer** — local Llama-8B produces answer using only `SkillResult[].evidence`. Citation tokens are inline `[cite:pub_id:chunk_id]`.
6. **verifier** — judge LLM (Claude Haiku or local 8B) checks every citation token is backed by an `evidence` item; on fail, reroute to executor with corrected sub-query (max 1 retry); on second fail, downgrade to "insufficient evidence" response.

### 7.2 SessionState (canonical)

```python
class SessionState(TypedDict):
    session_id: str
    user_id: str
    user_tier: int
    role: Literal["researcher","government","industry"]
    conversation_history: list[Turn]
    user_query: str

    plan: Optional[Plan]                     # planner output
    routing_decision: Optional[str]
    skill_results: list[SkillResult]         # executor output
    executor_errors: list[ExecutorError]

    synthesized_response: str
    citations: list[Citation]
    verification_status: Literal["ok","retry","fail"]
    verification_retries: int

    lineage: dict                            # audit metadata per-node
    query_id: str
```

### 7.3 Routing policy

| Intent | Route |
|---|---|
| factual lookup / count / list | SQL |
| semantic / "papers about…" | RAG |
| relational ("who collaborates with…") | KG (SQL rCTE or Neo4j) |
| compound | SQL + RAG in parallel |
| out-of-scope | short-circuit to "scope decline" response |

Intent classified by planner JSON + keyword fallback.

---

## 8. Synthesis Layer Plan

### 8.1 Default path: local Llama-3.1-8B-Instruct

- Runtime: `llama.cpp` HTTP server on GPU host, or CPU fallback for dev.
- Quant: Q4_K_M (≈4.7 GB file, ≈6 GB VRAM).
- Context: 8k tokens.
- Prompt template: `chatml` with `system`, `user`, and `assistant` roles. System prompt injected with (a) tier, (b) citation rules, (c) sovereignty banner.
- Client: `src/config/local_llm.py` replaced by `LlamaCppClient` (HTTP, no HF transformers), interface compatible with existing `.generate(system, user, history)` signature.

### 8.2 Fallback order

1. Local Llama-8B.
2. If local server unreachable for >500 ms → local rule-based (`rule_based_synthesis` retained).
3. Never fall back to cloud synthesis with raw data. Hard rule in `egress/guard.py`.

### 8.3 Planner (cloud-allowed role)

- Input: user_query + schema_prompt + recent_turn_summaries.
- Output: strict JSON (pydantic model `Plan`).
- Fallback on invalid JSON: regex-extract + one repair attempt, then degrade to router heuristic.

### 8.4 Verifier

- Claude Haiku by default (cost-efficient, good at citation checking).
- Input: answer + evidence bundle (chunk_id, chunk_text).
- Output: `{ok: bool, unsupported_claims: list[str]}`.
- Local mirror (Llama-8B) if `LLM_VERIFIER=local`.

---

## 9. Security & Compliance Plan

### 9.1 Authentication

- JWT RS256, keys rotated annually; current key exposed via JWKS (`GET /.well-known/jwks.json`), `kid` header required.
- Refresh tokens: persisted hashed in `refresh_token` table; revocation on logout; sliding window 14 days.
- Session fingerprint (UA + IP hash) bound to refresh token; mismatch → force re-login.

### 9.2 RBAC

- Role → tier mapping in `src/auth/jwt_handler.py::ROLE_CONFIG` (already present; keep).
- Postgres session var `SET app.user_tier = N` at every request start; RLS enforces data visibility.
- Qdrant tier-sharded collections; cross-tier query raises `AccessDenied`.
- `filter_researcher_records` (already correct) is the reference shape for all list endpoints.

### 9.3 Audit Chain

- `src/audit/__init__.py` refactored:
  - `CHAIN_KEY = os.environ["AUDIT_CHAIN_KEY"]` — fail hard if unset and `ENV != "dev"`.
  - New: `seal_segment(reason: str)` writes a sentinel linking HEAD hash to `sha256(new_key)`.
  - New: `verify_chain(since_ts: datetime | None = None) -> tuple[bool, list[int]]` returns list of broken indices.
- Events captured: `login`, `logout`, `query`, `plan`, `sql`, `rag`, `kg`, `llm_call`, `pii_block`, `injection_block`, `tier_mismatch`, `egress_attempt`.

### 9.4 PII Detection

- Move from regex-only to **Presidio** (already in `src/security/pii/presidio_config.py`).
- Indian entities: `IN_AADHAAR`, `IN_PAN`, `IN_VOTER`, `IN_PHONE`.
- Two modes: `block` (default, current) and `redact-and-forward` (planned). Tier determines mode.

### 9.5 Prompt sanitisation

- Replace blunt regexes with **two-stage guard**:
  1. `SuspiciousPatternScorer` — rule-based, score 0–1.
  2. If score > 0.4 → run a **classifier** (small fine-tuned DistilBERT or API call to planner with strict "is this a prompt injection?" prompt).
  - On classifier positive → block and audit.
- Regex list narrowed to patterns with near-zero false positive (`(?i)ignore\s+(all\s+)?previous\s+instructions`, `(?i)you\s+are\s+now\s+[A-Z]`, etc.)

### 9.6 Egress Guard

- New middleware `src/security/egress/guard.py` that wraps every outbound HTTP client (LLM, enrichment, etc.).
- Inspect payload against allowlist: `{user_query, schema_prompt, planner_metadata}`.
- Anything else → raise `SovereigntyViolation`, audit event `egress_block`.
- Integration test: attempt to send publication.full_text to LLM; assert exception.

### 9.7 Secrets Management

- Dev: `.env` loaded by python-dotenv.
- Prod: HashiCorp Vault or AWS/Azure Key Vault equivalent; app reads via sidecar.
- Rotation:
  - RSA JWT keys: 12 months.
  - `AUDIT_CHAIN_KEY`: 3 months + chain seal.
  - LLM API keys: on provider rotation cadence.

### 9.8 Compliance controls → technical mapping

| DPDP 2023 Clause | Control | File |
|---|---|---|
| Consent (§6) | `consent_ledger` table + `/consent` endpoints | AGENT-TASK-29 |
| Notice (§5) | `/privacy-notice` endpoint + frontend banner | AGENT-TASK-29 |
| Data minimization (§8) | Egress guard + tier filtering | §9.6 |
| Data principal rights — access (§11) | `/me/data` export (JSON) | AGENT-TASK-29 |
| Erasure (§12) | `/me/data` DELETE + cascade | AGENT-TASK-29 |
| Audit (§17) | HMAC chain | §9.3 |
| Breach notification (§8(6)) | Alerting on `tier_mismatch`, `egress_attempt` | AGENT-TASK-34 |

---

## 10. API & Frontend Plan

### 10.1 API surface (target)

```
POST   /login                         issue token pair
POST   /refresh                       rotate access token
POST   /logout                        revoke tokens
POST   /query                         conversational query
GET    /query/graph?topic=...         subgraph for topic
GET    /researchers?state=&area=      tier-shaped
GET    /researchers/{id}              detail (tier-shaped)
GET    /publications?year=&limit=     tier-shaped
GET    /publications/{id}             detail with full chunk refs
GET    /stats                         tier-shaped summary
GET    /health                        liveness
GET    /health/llm                    readiness of synthesizer
GET    /health/qdrant                 readiness of retriever
GET    /health/db                     readiness of DB
GET    /.well-known/jwks.json         public keys
GET    /me                            user profile
GET    /me/data                       DPDP export
DELETE /me/data                       DPDP erasure
POST   /consent                       register consent grant/revoke
GET    /audit/verify                  admin-only chain verification
```

Every endpoint documented with OpenAPI (FastAPI generates); committed snapshot at `docs/api/openapi.json`.

### 10.2 Frontend routes

- `/login` public
- `/r/*` researcher dashboard (auth-gated, role=researcher)
- `/g/*` government dashboard
- `/i/*` industry dashboard
- `/admin/audit` admin only

Dashboards share common shell: `Topbar`, `QueryBar`, `AnswerPanel`, `CitationDrawer`, `GraphView` (researcher-only), `StatsGrid`.

### 10.3 State / data contracts

- `queryService.query(...)` returns `QueryResponse` with `citations: Citation[]` (already typed in `queryService.ts`).
- `CitationDrawer` opens on citation click, shows chunk_text, pub metadata, confidence.
- `GraphView` renders `GraphData` from `/query/graph` using Sigma.js or Cytoscape.js. Node types (`paper`, `author`, `institution`, `topic`) already typed.

### 10.4 UX invariants

- Every answer shows ≥1 citation or a clear "insufficient evidence" state.
- Every answer shows provenance badge: `synth=local-llama-8b` or `synth=rule-based`.
- Latency target: p50 < 3 s (cached), p95 < 10 s (cold), p99 < 25 s.
- Accessibility: WCAG 2.2 AA; keyboard-navigable citation drawer; color contrast checked.

---

## 11. Infrastructure & DevOps Plan

### 11.1 Environments

- `dev` — laptop, docker-compose, SQLite OR Postgres, Qdrant in container, Redis optional, llama.cpp in container if GPU present else rule-based fallback OK.
- `staging` — Kubernetes namespace `nrg-stg`, Postgres HA, Qdrant clustered, Redis sentinel, one GPU node for llama.cpp.
- `prod` — Kubernetes namespace `nrg-prd`, Kong AI Gateway, Postgres HA (Patroni), Qdrant 3-node cluster, Redis sentinel, two GPU nodes, Vault.

### 11.2 Helm chart layout

```
infrastructure/helm/nrg/
├── Chart.yaml
├── values.yaml                   (prod defaults)
├── values-staging.yaml
├── templates/
│   ├── api-deployment.yaml
│   ├── api-service.yaml
│   ├── api-hpa.yaml
│   ├── llama-cpp-deployment.yaml (GPU, tolerations)
│   ├── worker-deployment.yaml    (ingest)
│   ├── postgres-statefulset.yaml (or operator)
│   ├── qdrant-statefulset.yaml
│   ├── redis-statefulset.yaml
│   ├── kong-ingress.yaml
│   ├── vault-agent-injector.yaml
│   ├── langfuse-deployment.yaml
│   ├── prometheus-servicemonitor.yaml
│   ├── netpol.yaml               (egress allowlist)
│   └── tls-issuer.yaml
```

### 11.3 CI/CD

- GitHub Actions or GitLab CI.
- Pipeline stages: lint → test → build → scan (trivy) → push → deploy (ArgoCD).
- Coverage floor enforced: `pytest --cov=src --cov-fail-under=70`.
- Security gates: `bandit`, `pip-audit`, `npm audit --audit-level=high`.
- DB migrations gated behind manual approval in prod.

### 11.4 Secrets

- Never in git. `.env` in `.gitignore` (verify). `.env.example` is the source of truth for names.
- Vault in prod; `vault agent` sidecar mounts `/vault/secrets/.env` before app boot.

### 11.5 Backups

- Postgres: `wal-g` to object storage, PITR window 7 days.
- Qdrant: snapshot nightly to object storage, 30-day retention.
- Audit chain file: append-only WORM bucket; daily sync.
- Disaster recovery drill quarterly: restore staging from backup within 60 min RTO.

---

## 12. Observability Plan

### 12.1 Tracing

- **Langfuse** for LLM call tracing (planner, synth, verifier) — captures prompt, completion, latency, cost, eval scores.
- **OpenTelemetry** for request-level tracing across FastAPI → LangGraph nodes → skill services → DB/Qdrant.
- Trace ID propagated in header `x-nrg-trace-id`; logged on every event.

### 12.2 Metrics

- Prometheus via `prometheus_fastapi_instrumentator`.
- Custom metrics: `nrg_queries_total{tier,intent,status}`, `nrg_retrieval_latency_seconds{skill}`, `nrg_synth_latency_seconds`, `nrg_llm_tokens_total{role,provider}`, `nrg_pii_block_total{entity}`, `nrg_injection_block_total`, `nrg_egress_block_total`.
- Dashboards (Grafana): p50/p95/p99 latency per route, cache hit rate, LLM cost burn, retrieval recall@5 (offline eval), audit-chain integrity gauge.

### 12.3 Logging

- Structured JSON, one event per line.
- Level strategy: INFO for state transitions, WARN for recoverable failures, ERROR for surfaced errors, AUDIT for chained events (written both to log and chain file).
- PII scrubbing at log sink; verified by ingestion filter.

### 12.4 Alerting

- Pager on: audit chain verification failure, Qdrant unhealthy >5 min, Postgres replication lag >30s, LLM sovereignty violation, rate-limit saturation sustained, 5xx rate >1% over 10 min.

---

## 13. Testing & Quality Plan

### 13.1 Pyramid

- **Unit** (70% of tests): pure functions, no network, SQLite in-mem. Coverage ≥ 80% on `src/auth`, `src/audit`, `src/security`.
- **Integration** (20%): FastAPI + Postgres + Qdrant + Redis via testcontainers-python. Hits real LangGraph.
- **E2E** (10%): Playwright against staging. 20 named scenarios (§17 DoD).

### 13.2 Eval suite (LLM-specific)

- `tests/evals/` with deterministic datasets.
- **Retrieval eval** — 100 labeled queries → recall@5 ≥ 0.75 required.
- **Answer faithfulness eval** — 50 queries, judge model compares answer to cited chunks → ≥ 0.85 faithful required.
- **Sovereignty eval** — 20 queries, assert no raw content left VPC (via egress guard log inspection).
- **Injection eval** — 30 attacks, assert 100% blocked; 30 benign queries, assert 100% allowed.

### 13.3 Load

- Locust scenario: 50 users, 5 min, mixed tiers; assert p95 < 10 s, error rate < 1%.
- Breakpoint test: ramp until error budget burned; document max sustained QPS.

### 13.4 Security testing

- `bandit -q -r src/`, zero HIGH.
- `pip-audit`, zero HIGH/CRITICAL unpinned.
- OWASP ZAP baseline scan against staging, zero HIGH.
- Manual: session fixation, CSRF (SameSite=Lax on refresh cookie if used), XSS via crafted publication titles.

---

## 14. Agent Task Protocols

> Each task block is self-contained. Any agent should be able to execute a block without reading the rest of the doc. Format: **Goal / Preconditions / Files / Steps / Commands / Acceptance / Dependencies**.

### AGENT-TASK-01 — Reproducible Python environment

**Goal.** Fresh clone → one command → working venv passing the current test suite.
**Preconditions.** `python3.11` installed on host.
**Files.** `Makefile`, `scripts/bootstrap.sh` (new), `.python-version` (new), `pyproject.toml`.
**Steps.**
1. Delete `.venv311/` and `venv/`.
2. Create `scripts/bootstrap.sh`:
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   PY="${PYTHON:-python3.11}"
   "$PY" -m venv .venv
   . .venv/bin/activate
   pip install -U pip wheel
   pip install -e ".[dev]"
   ```
3. `chmod +x scripts/bootstrap.sh`.
4. Add `.python-version` containing `3.11`.
5. Makefile targets:
   ```make
   venv: ; bash scripts/bootstrap.sh
   test: ; .venv/bin/pytest -q
   fmt:  ; .venv/bin/black src tests && .venv/bin/ruff check --fix src tests
   lint: ; .venv/bin/ruff check src tests && .venv/bin/mypy src
   ```
**Acceptance.** `rm -rf .venv && make venv && make test` succeeds; no reference to `.venv311` remains in repo.
**Dependencies.** None. Sprint 1.

---

### AGENT-TASK-02 — Fix `.env.example` truth

**Goal.** `.env.example` is accurate and copy-runnable.
**Files.** `.env.example`.
**Steps.** Replace contents with:
```
DATABASE_URL=sqlite:///nrg_research.db
POSTGRES_DATABASE_URL=postgresql://nrg:nrg_secret@localhost:5432/nrg
QDRANT_HOST=localhost
QDRANT_PORT=6333
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_MODEL_INDIC=ai4bharat/IndicBERTv2-SS

JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY_PATH=infrastructure/kong/ssl/jwt_rsa.key
JWT_PUBLIC_KEY_PATH=infrastructure/kong/ssl/jwt_rsa.key.pub
JWT_ACCESS_TTL_MINUTES=30
JWT_REFRESH_TTL_DAYS=14

AUDIT_CHAIN_KEY=replace-with-32-byte-random-hex
CORS_ORIGINS=http://localhost:3000

API_HOST=0.0.0.0
API_PORT=8000

REDIS_URL=redis://localhost:6379/0
REDIS_REQUIRED=false

LLM_PROVIDER=gemini
LLM_PLANNER_PROVIDER=gemini
LLM_SYNTH_PROVIDER=local_llama
LLM_VERIFIER_PROVIDER=anthropic
LLM_REQUEST_TIMEOUT_SECONDS=30

GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-3-5-haiku-latest
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=

LLAMA_CPP_URL=http://localhost:8080
LOCAL_LLM_CONTEXT_TOKENS=8192

DEMO_RESEARCHER_PASSWORD=
DEMO_GOVERNMENT_PASSWORD=
DEMO_INDUSTRY_PASSWORD=

FEATURE_KG=0
FEATURE_CONSENT_UI=0

LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=
OTEL_EXPORTER_OTLP_ENDPOINT=
```
**Acceptance.** `cp .env.example .env && python -c "from dotenv import load_dotenv; load_dotenv(); import os; assert os.getenv('JWT_ALGORITHM')=='RS256'"` passes.
**Dependencies.** None. Sprint 1.

---

### AGENT-TASK-03 — Seed relationship tables (SQLite MVP)

**Goal.** `nrg_research.db` has non-empty relation tables.
**Files.** `scripts/seed_relations.py` (new); invoked by `make seed`.
**Steps.**
1. Open SQLite; `TRUNCATE`-equivalent the four join tables + `keywords`.
2. For each researcher, sample 2–5 publication IDs uniformly; insert into `researcher_publications` with `author_position` ∈ {1..N} and `corresponding_author` flag on position 1.
3. Curate 300 keywords from ML/Physics/Bio/Chem/CS/SS ontologies (list in script).
4. For each publication, sample 1–4 keywords; insert.
5. For each lab, assign PI + 3–8 members; insert into `researcher_labs`.
6. Recompute `publications.access_tier` if missing: 70/20/10 distribution.
7. Idempotent: script fully clears before insert; seeded_at row added to `schema_migrations`.
**Acceptance.**
```sql
SELECT
  (SELECT COUNT(*) FROM researcher_publications) AS rp,
  (SELECT COUNT(*) FROM keywords) AS kw,
  (SELECT COUNT(*) FROM publication_keywords) AS pk,
  (SELECT COUNT(*) FROM researcher_labs) AS rl;
-- all > 0
```
**Dependencies.** AGENT-TASK-01. Sprint 1.

---

### AGENT-TASK-04 — Kill dead code, unify entry point

**Goal.** One backend main; experiments quarantined.
**Files.** `src/api/main.py`, `src/api/main_v2.py`, `src/knowledge_graph/*`.
**Steps.**
1. Diff the two main files; pick the most complete; delete the other. Update `Dockerfile.api` and `uvicorn` command.
2. `git mv src/knowledge_graph experiments/knowledge_graph`.
3. Add EXPERIMENTAL banner to `experiments/knowledge_graph/README.md`.
4. `grep -r "from src.knowledge_graph" src tests` → must return empty.
**Acceptance.** `ruff check src/` clean of import errors; `pytest -q` green (no test referenced experiments).
**Dependencies.** None. Sprint 1.

---

### AGENT-TASK-05 — Postgres migration (SQLite parity)

**Goal.** Postgres container runs full schema; `NRGDatabase` branches on `DATABASE_URL`.
**Files.** `db/migrations/` (new, Alembic), `src/data/database.py`, `docker-compose.yml`, `scripts/migrate_sqlite_to_pg.py`.
**Steps.**
1. `pip install alembic sqlalchemy` (already in pyproject).
2. `alembic init db/migrations`.
3. Author migration `0001_initial.py` mirroring SQLite schema with Postgres types (UUID, JSONB, TSVECTOR).
4. Author `0002_rls.py` — `ALTER TABLE researchers ENABLE ROW LEVEL SECURITY;` + policies per tier.
5. Author `0003_fts.py` — tsvector column + GIN index.
6. Refactor `NRGDatabase`:
   ```python
   def __init__(self, url: str | None = None):
       url = url or os.getenv("DATABASE_URL", "sqlite:///nrg_research.db")
       self.engine = create_engine(url, future=True)
       self.dialect = self.engine.dialect.name  # 'sqlite' | 'postgresql'
   ```
   Replace raw `sqlite3` calls in `/stats`, `/publications` with SQLAlchemy Core queries.
7. `scripts/migrate_sqlite_to_pg.py` — one-shot ETL; idempotent via upsert.
**Acceptance.**
- `docker compose --profile dev up -d postgres && alembic upgrade head` returns 0.
- `python scripts/migrate_sqlite_to_pg.py` copies all rows; row counts match.
- Same test suite passes against both dialects via `NRG_DB_DIALECT` env.
**Dependencies.** AGENT-TASK-03. Sprint 2.

---

### AGENT-TASK-06 — Fix docker-compose

**Goal.** `docker compose --profile dev up` runs to healthy.
**Files.** `docker-compose.yml`, `Dockerfile.api`, `scripts/smoke.sh` (new).
**Steps.**
1. Kong host port 8080:8000, TLS 8443:8443.
2. `api.env_file: [.env]`; remove hardcoded `DATABASE_URL`.
3. Add `redis` healthcheck `["CMD","redis-cli","ping"]`; `api.depends_on: {redis: {condition: service_healthy}}`.
4. Add `llama-cpp` service (Sprint 3), gated behind `--profile gpu`.
5. `scripts/smoke.sh`:
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   curl -sf localhost:8000/health
   TOKEN=$(curl -sf -X POST localhost:8000/login \
     -H 'content-type: application/json' \
     -d '{"username":"researcher_user","password":"'"$DEMO_RESEARCHER_PASSWORD"'"}' | jq -r .access_token)
   curl -sf -H "Authorization: Bearer $TOKEN" localhost:8000/researchers | jq '.role'
   ```
**Acceptance.** `docker compose --profile dev up -d && bash scripts/smoke.sh` exits 0.
**Dependencies.** AGENT-TASK-02, 05. Sprint 2.

---

### AGENT-TASK-07 — Wire real LLM provider (planner role)

**Goal.** Planner makes real calls against Gemini (or chosen provider).
**Files.** `src/config/llm_config.py`, `src/orchestration/nodes/planner.py` (new), `src/api/main.py`.
**Steps.**
1. Provision a real `GEMINI_API_KEY`; set `LLM_PROVIDER=gemini`, `LLM_PLANNER_PROVIDER=gemini`.
2. In `llm_config.py`, log provider + model at INFO on first `get_llm_client()` call; WARN if None.
3. Add `GET /health/llm` returning:
   ```json
   {"planner":{"provider":"gemini","model":"gemini-2.0-flash","ready":true},
    "synth":{"provider":"local_llama","url":"http://localhost:8080","ready":true},
    "verifier":{"provider":"anthropic","model":"claude-3-5-haiku-latest","ready":true}}
   ```
4. Implement `planner_node` that calls planner LLM with schema prompt + user_query; parses JSON to `Plan` pydantic model; on failure, attempts one repair.
5. Insert `planner` before `router` in LangGraph.
**Acceptance.**
- `curl /health/llm` returns `ready: true` for planner.
- `/query` returns `routing_decision` derived from `plan.desired_skills`.
- Rate-limit per tier enforced (see AGENT-TASK-28).
**Dependencies.** AGENT-TASK-02. Sprint 2.

---

### AGENT-TASK-08 — Fix frontend routing contract

**Goal.** Every service call has proxy + backend route.
**Files.** `frontend/vite.config.ts`, `frontend/src/services/queryService.ts`, `src/api/main.py`.
**Steps.**
1. Add to `vite.config.ts` proxy: `/stats`, `/publications`, `/query/graph`, `/me`, `/health/*`, `/.well-known/jwks.json`.
2. Implement `GET /query/graph?topic=&limit=` in `main.py`: return neighborhood of `topic` keyword within 2 hops — papers → authors → institutions. Response shape matches `GraphData` type.
3. If `/query/graph` slips sprint → feature-flag frontend graph view and hide entry point.
4. Add frontend integration test (`vitest + msw`) covering each service method.
**Acceptance.** `npm run dev` + `uvicorn ...` → all three dashboards render with zero 4xx in browser console.
**Dependencies.** AGENT-TASK-03. Sprint 2.

---

### AGENT-TASK-09 — Kill silent failures

**Goal.** No silent `warning` swallow; errors visible in API response.
**Files.** `src/skills/rag/embedder.py`, `src/skills/rag/retriever.py`, `src/skills/text_to_sql/skill.py`, `src/orchestration/nodes/executor.py`, `src/orchestration/graph.py`, `src/api/main.py`.
**Steps.**
1. `embedder.py` — remove `_dummy_embeddings`; raise `EmbedderUnavailable` on load failure.
2. `retriever.py` — on Qdrant connection error raise `RetrieverUnavailable`; `executor` catches and appends to `executor_errors`.
3. `executor.py` — replace `except Exception as e: logger.warning(...)` with:
   ```python
   except Exception as e:
       logger.error("skill=%s failed", skill_name, exc_info=True)
       state["executor_errors"].append({
           "skill": skill_name, "error_type": type(e).__name__, "message": str(e)
       })
   ```
4. Surface `executor_errors` in `/query` JSON as `warnings`.
**Acceptance.** Stop Qdrant → run a RAG-routed query → response JSON contains `warnings: [{skill:"rag", error_type:"RetrieverUnavailable", ...}]`. No response string is "No data found…" when an error occurred.
**Dependencies.** None. Sprint 2.

---

### AGENT-TASK-10 — Text-to-SQL hardening

**Goal.** Dialect-correct, safe, tier-enforced SQL.
**Files.** `src/skills/text_to_sql/skill.py`, `db/migrations/0004_access_tier.py`, `tests/skills/test_text_to_sql.py`.
**Steps.**
1. Rewrite system prompt: dialect-correct ("SQLite-compatible" in dev, "PostgreSQL" in prod, driven by env).
2. Replace `_apply_tier_filter` with `TierAwareSqlRewriter` using `sqlglot`:
   - Parse → reject non-SELECT.
   - For every referenced table in `TIER_AWARE_TABLES`, inject `WHERE access_tier <= :user_tier`.
   - Enforce outer `LIMIT 200`.
3. Add migration `0004_access_tier.py` — `access_tier INTEGER NOT NULL DEFAULT 1` on researchers, publications, funding_records.
4. `TIER_AWARE_TABLES = {"researchers","publications","funding_records","labs"}`.
5. Tests:
   - 10 positive: natural queries → valid parameterized SQL.
   - 10 adversarial: `DROP TABLE`, `UNION SELECT`, `-- comment` injection, multi-statement `;`, `ATTACH DATABASE`.
   - 5 tier leak: tier-1 user asking for tier-3 data → SQL rewritten to filter.
**Acceptance.** `pytest tests/skills/test_text_to_sql.py -v` all green; coverage on `skill.py` ≥ 90%.
**Dependencies.** AGENT-TASK-05. Sprint 3.

---

### AGENT-TASK-11 — Embedding + ingestion pipeline

**Goal.** Qdrant populated with chunk embeddings for every publication.
**Files.** `scripts/build_embeddings.py` (new), `src/skills/rag/embedder.py`, `src/skills/rag/ingest.py` (new).
**Steps.**
1. Replace default model with `BAAI/bge-m3`; add language-gated branch to IndicBERT.
2. Chunker: `semantic-text-splitter` (512 tokens, stride 128), sentence-aware.
3. `scripts/build_embeddings.py`:
   - Read publications + abstracts from DB (+ full_text if available, else abstract).
   - Language detect via fasttext `lid.176`.
   - Chunk → embed → upsert to `nrg_research_tier{1,2,3}`.
   - Log to audit chain: `ingest_batch(count, collection, sha256)`.
4. Idempotent via `publication_id + chunk_id` point ID.
**Acceptance.**
- `python scripts/build_embeddings.py --full` completes without errors.
- Qdrant: `curl localhost:6333/collections/nrg_research_tier1` shows `points_count > 0`.
- Sample query: semantically similar publications returned.
**Dependencies.** AGENT-TASK-03. Sprint 3.

---

### AGENT-TASK-12 — Hybrid retrieval + reranker

**Goal.** Dense + sparse + rerank pipeline producing top-5 with relevance scores.
**Files.** `src/skills/rag/retriever.py`, `src/skills/rag/reranker.py` (new).
**Steps.**
1. In Qdrant upsert (AGENT-TASK-11), also compute BM25 sparse vector per chunk; add to Qdrant `SparseVector`.
2. `retriever.query` uses Qdrant hybrid search with `rrf` fusion, top-20 candidates.
3. `reranker.py` loads `BAAI/bge-reranker-v2-m3`; rerank candidates → top-5.
4. Enforce `access_tier <= user_tier` in Qdrant payload filter + collection choice.
**Acceptance.** On 20 labeled queries, `recall@5 ≥ 0.75` (eval harness in `tests/evals/retrieval_eval.py`).
**Dependencies.** AGENT-TASK-11. Sprint 3.

---

### AGENT-TASK-13 — Intent classifier

**Goal.** Router has deterministic, explainable routing.
**Files.** `src/orchestration/nodes/router.py`, `src/orchestration/intent.py` (new).
**Steps.**
1. Planner JSON already classifies intent; router consumes it.
2. Fallback rule-based classifier (keyword + query-type heuristics) when planner disabled.
3. Emit `routing_decision` with reason (e.g. `"sql+rag: compound query, needs both relational and semantic evidence"`).
**Acceptance.** Unit tests: 30 queries → classified correctly ≥ 0.9; `routing_decision` string never empty.
**Dependencies.** AGENT-TASK-07. Sprint 3.

---

### AGENT-TASK-14 — Local llama.cpp server for synthesis

**Goal.** Local Llama-3.1-8B Q4_K_M serving synthesis via HTTP.
**Files.** `docker-compose.yml`, `infrastructure/llama/Dockerfile`, `src/config/local_llm.py` (refactor).
**Steps.**
1. Add `llama-cpp` service (compose profile `gpu` or `cpu-dev`). Mount GGUF via volume; pre-download via init container.
2. Replace `LocalLLMClient` with `LlamaCppClient`:
   ```python
   def generate(self, system: str, user: str, history: list[dict]) -> str:
       payload = {"model":"local","messages":[{"role":"system","content":system}, ...],
                  "temperature":0.3, "max_tokens":1024}
       r = httpx.post(f"{self.url}/v1/chat/completions", json=payload, timeout=60)
       return r.json()["choices"][0]["message"]["content"]
   ```
3. Health: `GET {LLAMA_CPP_URL}/health` → 200.
4. Keep `rule_based_synthesis` as third-tier fallback.
**Acceptance.** `curl $LLAMA_CPP_URL/health` 200; `/query` answer length > 200 chars; response metadata shows `synth=local_llama`.
**Dependencies.** AGENT-TASK-02, 06. Sprint 4.

---

### AGENT-TASK-15 — Synthesizer prompt engineering + citations

**Goal.** Answers cite evidence with inline citation tokens.
**Files.** `src/orchestration/nodes/synthesizer.py`, `src/prompts/synth_system.md` (new).
**Steps.**
1. System prompt template includes:
   - Tier banner.
   - Strict citation rule: "Every factual claim MUST be followed by a citation token `[cite:pub_id:chunk_id]` drawn from the provided evidence list."
   - Refusal rule when evidence is empty.
2. Synthesizer receives `evidence = [{pub_id, chunk_id, chunk_text, title, year, authors}]`.
3. Post-process output: regex-extract `[cite:...]` tokens → build `citations: Citation[]` array.
4. Expose `citations` in `/query` response.
**Acceptance.** 20 diverse queries → ≥ 95% of answers contain ≥ 1 citation; unit test on post-processor.
**Dependencies.** AGENT-TASK-12, 14. Sprint 4.

---

### AGENT-TASK-16 — Verifier node (faithfulness judge)

**Goal.** Every answer checked for citation faithfulness; reroute on fail.
**Files.** `src/orchestration/nodes/verifier.py` (new), `src/config/llm_config.py`.
**Steps.**
1. `verifier_node` takes `synthesized_response` + `evidence`; calls judge LLM (Anthropic Haiku default).
2. Judge prompt: "For each claim marked by a citation token, verify the cited chunk supports it. Return JSON: `{ok: bool, unsupported_claims: [str]}`."
3. On `ok=false` and `verification_retries < 1`: re-enter executor with `refine_plan` derived from unsupported claims.
4. On second fail: downgrade response to "insufficient evidence" with unchanged citations.
**Acceptance.** Evaluator report: faithfulness rate on 50-query eval ≥ 0.85; retry path triggered and resolved at least once in tests.
**Dependencies.** AGENT-TASK-15. Sprint 4.

---

### AGENT-TASK-17 — CORS, CHAIN_KEY, injection regex

**Goal.** Hardening pass.
**Files.** `src/api/main.py`, `src/audit/__init__.py`, `src/security/gateway/prompt_sanitiser.py`, `.env.example`.
**Steps.**
1. Replace `allow_origins=["*"]` with `os.getenv("CORS_ORIGINS","http://localhost:3000").split(",")`.
2. `src/audit/__init__.py`:
   ```python
   CHAIN_KEY = os.environ.get("AUDIT_CHAIN_KEY")
   if not CHAIN_KEY and os.environ.get("NRG_ENV","dev") != "dev":
       raise RuntimeError("AUDIT_CHAIN_KEY must be set outside dev")
   ```
3. Narrow injection regexes:
   - `(?i)\bignore\s+(all\s+)?previous\s+instructions\b`
   - `(?i)\byou\s+are\s+now\b`
   - `(?i)\bdisregard\s+instructions\b`
   - `(?i)<\s*/\s*system\s*>`
   - `(?i)\b(reveal|print|dump)\s+(the\s+)?(system|hidden)\s+prompt\b`
   - Remove `(?i)as.*ai`, `(?i)hypothetical`, `(?i)role.*play`.
4. Fix `sanitise_prompt` return tuple: populate `detected_pii` list; add unit test.
**Acceptance.**
- `pytest tests/security/test_sanitiser.py`: 20 benign pass, 30 attack blocked.
- `curl -H "Origin: evil.com" localhost:8000/login` blocked.
- App import fails in `prod` env without `AUDIT_CHAIN_KEY`.
**Dependencies.** AGENT-TASK-02. Sprint 2.

---

### AGENT-TASK-18 — Refresh-token persistence + revocation

**Goal.** Stateless refresh tokens replaced by hashed DB store.
**Files.** `src/auth/jwt_handler.py`, `src/auth/refresh_store.py` (new), `db/migrations/0005_refresh_tokens.py`.
**Steps.**
1. Migration: `refresh_token(token_hash TEXT PK, user_id, issued_at, expires_at, revoked BOOL, replaced_by TEXT)`.
2. On issue: store `sha256(token)`; on refresh: lookup, mark revoked, issue new and store.
3. On logout: revoke in DB.
4. Periodic job: delete expired rows (nightly).
**Acceptance.** `/refresh` with a previously-revoked token returns 401; `/logout` followed by `/refresh` fails.
**Dependencies.** AGENT-TASK-05. Sprint 3.

---

### AGENT-TASK-19 — Egress sovereignty guard

**Goal.** No raw research content ever leaves VPC.
**Files.** `src/security/egress/guard.py` (new), all outbound LLM/HTTP calls.
**Steps.**
1. Allowlist: `user_query`, `schema_prompt`, `plan_json`, `intent_label`, `citation_ids` (but never chunk_text or full_text).
2. Wrap every cloud-LLM client (`GeminiClient`, `AnthropicClient`, `OpenAIClient`, `AzureOpenAIClient`):
   ```python
   class SovereignHTTPXClient:
       def post(self, url, json=None, **kw):
           self._inspect(json)
           return self._inner.post(url, json=json, **kw)
       def _inspect(self, payload):
           ... # raise SovereigntyViolation on disallowed content
   ```
3. Detection: scan payload for any chunk_text that appears in local `publications.abstract` index (hash match on 8-gram shingles).
4. On violation: raise, audit `egress_block`, metric increment.
**Acceptance.** `pytest tests/security/test_egress_guard.py` — synthetic attempt to POST publication.abstract to cloud LLM is blocked; legitimate planner prompts pass.
**Dependencies.** AGENT-TASK-07. Sprint 4.

---

### AGENT-TASK-20 — Langfuse + OpenTelemetry instrumentation

**Goal.** Every LLM call and API request traced end-to-end.
**Files.** `src/observability/` (new), `src/api/main.py`, `src/orchestration/graph.py`, `src/config/llm_config.py`, `docker-compose.yml`.
**Steps.**
1. Add Langfuse SDK; wrap `client.generate` to emit Langfuse trace with prompt, completion, latency, cost.
2. Add OTLP instrumentation: `opentelemetry-instrumentation-fastapi`, `-sqlalchemy`, `-httpx`, `-redis`.
3. Trace context propagated through LangGraph state as `trace_id`.
4. Add local Langfuse to docker-compose (dev profile).
**Acceptance.** Langfuse UI shows every `/query` trace with 5–6 spans (receiver → planner → router → executor → synthesizer → verifier).
**Dependencies.** AGENT-TASK-07, 14. Sprint 5.

---

### AGENT-TASK-21 — Prometheus metrics + Grafana dashboards

**Goal.** Metrics for latency, LLM cost, retrieval quality, cache hit rate.
**Files.** `src/observability/metrics.py` (new), `infrastructure/grafana/dashboards/nrg.json`.
**Steps.**
1. Custom metrics registered on app startup (§12.2).
2. Grafana JSON with panels: p50/p95/p99 latency per route, LLM tokens per minute per provider, cache hit ratio, audit-chain integrity gauge (1 if `verify_chain()` passes).
3. `prometheus_fastapi_instrumentator` wired.
**Acceptance.** `curl localhost:8000/metrics` returns Prom text; Grafana dashboards import clean.
**Dependencies.** AGENT-TASK-06. Sprint 5.

---

### AGENT-TASK-22 — Presidio PII upgrade

**Goal.** Replace regex PII with Presidio + Indian-entity recognizers.
**Files.** `src/security/pii/presidio_config.py`, `src/security/gateway/prompt_sanitiser.py`.
**Steps.**
1. Add Presidio analyzer with recognizers: `IN_AADHAAR`, `IN_PAN`, `IN_VOTER`, `IN_PHONE` (regex + checksum), plus default `PERSON`, `EMAIL`, `PHONE_NUMBER`.
2. `validate_query` calls Presidio; `block` mode keeps current 403; add `redact-and-forward` mode gated by `PII_MODE=redact`.
3. Attach audit event `pii_block` on every block.
**Acceptance.** Tests: 40 strings with Indian PII detected; 40 clean pass; Aadhaar checksum false positives < 2%.
**Dependencies.** AGENT-TASK-17. Sprint 5.

---

### AGENT-TASK-23 — Kong AI Gateway wiring

**Goal.** Kong fronts the API, handles rate-limit and PII plugin.
**Files.** `infrastructure/kong/kong.yaml`, `docker-compose.yml`, `infrastructure/helm/nrg/templates/kong-ingress.yaml`.
**Steps.**
1. Declarative Kong config: services + routes for `/login /query /researchers /publications /stats /me /health /.well-known`.
2. Plugins: `rate-limiting` (tier-based via `consumer` + `X-User-Tier`), `cors`, `request-size-limiting` (1 MB), `jwt` verification (optional, leave to app for now).
3. Prod: Kong in K8s ingress mode with cert-manager.
**Acceptance.** `curl -i localhost:8080/researchers` returns proper headers including `X-RateLimit-Remaining`.
**Dependencies.** AGENT-TASK-06. Sprint 5.

---

### AGENT-TASK-24 — Helm chart (staging / prod)

**Goal.** `helm install nrg ./infrastructure/helm/nrg` brings up the stack in K8s.
**Files.** `infrastructure/helm/nrg/` (new).
**Steps.**
1. Templates listed in §11.2.
2. Secrets injected via Vault Agent sidecar.
3. HorizontalPodAutoscaler on API: CPU 70%, min 2, max 10.
4. GPU node selector + tolerations on `llama-cpp` deployment.
5. NetworkPolicy: egress allowlist only to `*.anthropic.com`, `*.googleapis.com`, Vault, Langfuse; deny all else.
6. `helm lint` + `kubeval` in CI.
**Acceptance.** `helm template | kubeval` clean; deploy to staging K8s succeeds; all pods healthy.
**Dependencies.** AGENT-TASK-06, 14, 20, 23. Sprint 6.

---

### AGENT-TASK-25 — Conversation memory + checkpointing

**Goal.** LangGraph survives restarts and supports multi-turn sessions.
**Files.** `src/orchestration/graph.py`, `src/orchestration/checkpoint.py` (new).
**Steps.**
1. Use `langgraph.checkpoint.postgres.PostgresSaver` in prod, `SqliteSaver` in dev.
2. `session_id` on every `/query`; default new UUID.
3. Load prior turns from checkpoint into `conversation_history`; bound to last 10 turns.
**Acceptance.** Two `/query` calls with same `session_id` see context from first; restart API between → still see context.
**Dependencies.** AGENT-TASK-05. Sprint 6.

---

### AGENT-TASK-26 — `/query/graph` endpoint (topic subgraph)

**Goal.** Serve graph view from real DB.
**Files.** `src/api/main.py`, `src/services/graph_service.py` (new).
**Steps.**
1. For `topic`:
   - Find matching keywords (fuzzy, `pg_trgm` in Postgres).
   - Expand: papers tagged with those keywords → authors → institutions.
   - Bound to 100 nodes, 300 edges; higher tier gets more.
2. Response shape matches frontend `GraphData`.
**Acceptance.** `curl "/query/graph?topic=machine%20learning"` returns non-empty graph; frontend renders.
**Dependencies.** AGENT-TASK-03, 05. Sprint 6.

---

### AGENT-TASK-27 — Neo4j (feature-flagged, Sprint 7)

**Goal.** Advanced traversal queries via Neo4j.
**Files.** `experiments/knowledge_graph/` → promote to `src/knowledge_graph/` when flag on; `src/skills/kg/skill.py` (new); `docker-compose.yml` (neo4j service).
**Steps.**
1. Flag `FEATURE_KG=1` enables registration.
2. Nightly sync job: SQL → Neo4j (`Researcher`, `Publication`, `Institution`, `Keyword` nodes + edges).
3. KG skill uses Cypher for patterns like "shortest coauthor path", "top collaborators across institution boundaries".
**Acceptance.** With flag on, router selects KG skill for traversal queries; sample query returns ≥1 path.
**Dependencies.** AGENT-TASK-26. Sprint 7 (optional until budget allows).

---

### AGENT-TASK-28 — Tiered rate limiting

**Goal.** Per-tier QPS + daily quotas.
**Files.** Kong config (`rate-limiting` plugin) + `src/api/middleware/quota.py` as defence in depth.
**Steps.**
1. Kong: tier-1 → 100 req/min / 10k/day; tier-2 → 50/min / 5k/day; tier-3 → 20/min / 2k/day.
2. App middleware: token-bucket in Redis keyed `(user_id, minute)`; 429 on breach.
**Acceptance.** Burst past limit → 429; Prometheus `nrg_rate_limited_total` increments.
**Dependencies.** AGENT-TASK-23. Sprint 5.

---

### AGENT-TASK-29 — DPDP compliance endpoints

**Goal.** Consent, data access, erasure.
**Files.** `src/api/main.py`, `src/services/consent.py` (new), `db/migrations/0006_consent.py`.
**Steps.**
1. Migration: `consent_ledger(consent_id, user_id, scope, version, granted_at, revoked_at)`.
2. `POST /consent` granting scopes; `DELETE /consent/{scope}` revoke.
3. `GET /me/data` — JSON bundle of all rows tied to user_id (Postgres export).
4. `DELETE /me/data` — cascade erase + anonymization of audit events (keep hash, drop user_id).
5. Frontend: consent banner on first login.
**Acceptance.** Erasure test: user triggers delete → all PII rows removed; chain still verifies; pseudonymized audit events remain.
**Dependencies.** AGENT-TASK-05, 18. Sprint 6.

---

### AGENT-TASK-30 — Admin audit endpoints

**Goal.** Verify chain integrity and explore audit events.
**Files.** `src/api/main.py`.
**Steps.**
1. `GET /audit/verify` (role=admin) → `{ok: bool, broken_indices: [int], last_sealed_at: iso, current_head_hash: str}`.
2. `GET /audit/events?user_id=&action=&since=&limit=` paginated.
3. Admin role added to `ROLE_CONFIG`; demo admin user.
**Acceptance.** Tamper with one line in `.audit/chain.jsonl` → `/audit/verify` returns `ok=false` with correct index.
**Dependencies.** AGENT-TASK-17. Sprint 5.

---

### AGENT-TASK-31 — Frontend: citation drawer + provenance badge

**Goal.** User can click citation → see chunk + paper detail.
**Files.** `frontend/src/components/CitationDrawer.tsx` (new), `AnswerPanel.tsx`, `queryService.ts`.
**Steps.**
1. Parse answer for `[cite:pub_id:chunk_id]` tokens; render inline as superscripts.
2. Drawer component: fetches `/publications/{pub_id}` + `/rag/chunk/{chunk_id}` (new endpoint) on click.
3. Show provenance badge in answer panel (`synth=local_llama` etc.).
**Acceptance.** E2E test: click first citation → drawer opens with chunk highlighted and paper title/year.
**Dependencies.** AGENT-TASK-15. Sprint 6.

---

### AGENT-TASK-32 — Frontend: graph view

**Goal.** Topic subgraph rendered interactively.
**Files.** `frontend/src/components/GraphView.tsx`, `frontend/package.json` (add `sigma`, `graphology`).
**Steps.**
1. Sigma.js renderer.
2. Load on topic submit.
3. Node click → filter answer panel to that entity.
**Acceptance.** Graph renders 50–100 nodes; pan/zoom responsive; click updates answer panel context.
**Dependencies.** AGENT-TASK-26. Sprint 6.

---

### AGENT-TASK-33 — Playwright E2E suite

**Goal.** 20 named user journeys pass against staging.
**Files.** `tests/e2e/playwright/` (new).
**Steps.**
1. Scenarios: login per persona (3), natural-language query (3), citation drawer (3), graph view (2), consent grant + revoke (2), rate limit trigger (1), PII block UX (1), DPDP export (1), DPDP delete (1), logout + session invalidate (1), tier leak attempt (1), cross-persona session isolation (1).
2. Runs against staging deploy in CI.
**Acceptance.** 20/20 scenarios green in CI nightly.
**Dependencies.** All user-facing tasks. Sprint 7.

---

### AGENT-TASK-34 — Alerting rules + runbooks

**Goal.** Pager fires on the right signals; humans have runbooks.
**Files.** `infrastructure/prometheus/alerts.yaml`, `docs/runbooks/`.
**Steps.**
1. Alerts: audit chain broken, Qdrant down >5m, Postgres replication lag >30s, egress violation, 5xx rate >1%/10m, llama.cpp health flapping.
2. Runbook per alert: symptom, verification, mitigation, rollback, owner.
**Acceptance.** Synthetic alert test-fires; runbook URL is included in alert payload.
**Dependencies.** AGENT-TASK-21. Sprint 7.

---

### AGENT-TASK-35 — Disaster recovery drill

**Goal.** Verified RPO/RTO.
**Files.** `docs/ops/dr_runbook.md`, `scripts/dr_drill.sh`.
**Steps.**
1. Nightly backup verification script.
2. Quarterly drill: spin up staging from latest backup; restore Postgres + Qdrant + audit chain; smoke test.
3. Document RTO (60 min) and RPO (<1 h) in ops docs.
**Acceptance.** Drill checklist green; report filed.
**Dependencies.** AGENT-TASK-24. Sprint 8.

---

### AGENT-TASK-36 — Load testing + capacity plan

**Goal.** Known breaking point; capacity plan for sponsor.
**Files.** `tests/load/locustfile.py`, `docs/ops/capacity_plan.md`.
**Steps.**
1. Locust: 50 users / 5 min baseline, then ramp to failure.
2. Record: max sustained QPS, p99 at target QPS, GPU utilization, cache hit rate, Postgres pool saturation.
3. Capacity plan: per-university concurrent user estimate → node count.
**Acceptance.** Report filed; staging sustains 20 QPS at p95 < 10s with current node sizing.
**Dependencies.** AGENT-TASK-24. Sprint 8.

---

### AGENT-TASK-37 — Eval harness (retrieval + faithfulness + sovereignty + injection)

**Goal.** Quality gates on LLM behavior enforced in CI.
**Files.** `tests/evals/`, `.github/workflows/eval.yml`.
**Steps.**
1. Datasets checked in; fixtures include labeled queries with expected paper IDs (retrieval), labeled claims and evidence (faithfulness), attack strings (injection), synthetic raw content (sovereignty).
2. Thresholds: retrieval recall@5 ≥ 0.75, faithfulness ≥ 0.85, injection block rate = 1.0, sovereignty leak rate = 0.
3. Fail CI on threshold breach.
**Acceptance.** Eval workflow green on main; threshold miss red.
**Dependencies.** AGENT-TASK-16, 19, 22. Sprint 7.

---

### AGENT-TASK-38 — API documentation site

**Goal.** Living OpenAPI docs + Postman collection.
**Files.** `docs/api/openapi.json` (generated), `docs/api/NRG.postman_collection.json`.
**Steps.**
1. FastAPI auto-generates OpenAPI; export at build time.
2. Postman collection generated from OpenAPI via `postman-open-api`.
3. Docs site via `redocly` hosted at `/docs` (protected if sensitive) or static site `docs.nrg.india`.
**Acceptance.** `curl /openapi.json` valid; Postman collection imports clean.
**Dependencies.** AGENT-TASK-08 onward. Sprint 7.

---

### AGENT-TASK-39 — Truth-in-docs pass

**Goal.** Every doc claim matches code.
**Files.** `README.md`, `FINAL_STATUS_REPORT.md`, two blueprints, `docs/architecture/*`.
**Steps.**
1. Update README counts to live DB (script-generated footer).
2. Delete or gate every unsupported claim (cost, latency, key names).
3. Add `docs/architecture/SYNTHESIS_DECISION.md` reconciling the two blueprints (use ADR-001 content).
4. Add "Honest Status" section listing what does/doesn't work today.
**Acceptance.** `scripts/doc_truth_check.py` greps for `REPLACE_ME`, `sk-IITGN-prod`, specific p95 claims → returns empty.
**Dependencies.** None. Sprint 1.

---

### AGENT-TASK-40 — Demo script + sponsor deck

**Goal.** One-shot, reproducible, 10-minute demo for sponsors.
**Files.** `docs/demo/SCRIPT.md`, `docs/demo/deck.pdf`.
**Steps.**
1. SCRIPT: commands, timing, expected output at each step. Covers: login → query with citations → graph view → government tier demo → audit verify.
2. Deck: 12 slides (problem, sovereignty, architecture, quality gates, roadmap, ask).
**Acceptance.** Run script in staging end-to-end without edits; agree one recording as reference.
**Dependencies.** All MVP tasks. Sprint 8.

---

## 15. Phased Delivery Roadmap

### Working assumptions

- 4-agent team (backend, ML/retrieval, frontend, devops) + one tech lead.
- 2-week sprints; 16 weeks total.
- Tasks can run in parallel within a sprint if no dependency.

### Sprint 1 — Foundations (weeks 1–2)

Tasks: 01, 02, 03, 04, 17, 39.
Exit: venv reproducible; DB seeded with edges; one backend entry point; CORS/CHAIN_KEY/injection hardened; docs don't lie.

### Sprint 2 — Postgres + Docker + Frontend wire (weeks 3–4)

Tasks: 05, 06, 07, 08, 09.
Exit: docker-compose dev boots clean; Postgres parity; planner LLM calling for real; frontend 404s eliminated; executor surfaces errors.

### Sprint 3 — Retrieval online (weeks 5–6)

Tasks: 10, 11, 12, 13, 18.
Exit: Qdrant populated; hybrid + rerank live; dialect-correct SQL with tier enforcement; refresh-token DB.

### Sprint 4 — Sovereign synthesis (weeks 7–8)

Tasks: 14, 15, 16, 19.
Exit: local Llama-8B serving; citations in answers; verifier catches unfaithful claims; egress guard enforced.

### Sprint 5 — Observability + security UX (weeks 9–10)

Tasks: 20, 21, 22, 23, 28, 30.
Exit: Langfuse + Prom traces; Presidio PII; Kong fronting; rate-limit enforced; admin audit visible.

### Sprint 6 — Product surface + compliance (weeks 11–12)

Tasks: 24, 25, 26, 29, 31, 32.
Exit: Helm chart in staging; multi-turn sessions; `/query/graph`; DPDP endpoints; citation drawer + graph view.

### Sprint 7 — Quality + KG (weeks 13–14)

Tasks: 27 (optional), 33, 34, 37, 38.
Exit: Playwright nightly green; alerts + runbooks; eval harness in CI; OpenAPI + Postman published.

### Sprint 8 — Hardening + demo (weeks 15–16)

Tasks: 35, 36, 40.
Exit: DR drill passed; capacity plan filed; demo script runs clean; sponsor deck delivered.

---

## 16. Command Reference

### 16.1 Bootstrap

```bash
# One-time laptop setup
brew install python@3.11 docker docker-compose jq postgresql@16
git clone <repo> && cd NRG
cp .env.example .env              # edit: set AUDIT_CHAIN_KEY, GEMINI_API_KEY, demo passwords
make venv
make seed                         # populates SQLite relations
docker compose --profile dev up -d postgres qdrant redis
alembic upgrade head              # only needed once Postgres is chosen
python scripts/migrate_sqlite_to_pg.py   # optional, after seed
python scripts/build_embeddings.py --full
```

### 16.2 Develop

```bash
# backend
.venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# frontend
cd frontend && npm install && npm run dev

# llama.cpp (CPU dev)
docker compose --profile cpu-dev up -d llama-cpp
curl localhost:8080/health
```

### 16.3 Test

```bash
make lint
make test
.venv/bin/pytest tests/evals/ -v
.venv/bin/pytest tests/security/ -v
.venv/bin/pytest tests/integration_tests.py -v
npm --prefix frontend test
npx playwright test --config tests/e2e/playwright/config.ts
```

### 16.4 Observe

```bash
curl localhost:8000/health
curl localhost:8000/health/llm
curl -H "Authorization: Bearer $TOKEN" localhost:8000/audit/verify
python -c "from src.audit import verify_chain; print(verify_chain())"
open http://localhost:3001         # Langfuse
open http://localhost:9090         # Prometheus
open http://localhost:3333         # Grafana
```

### 16.5 Deploy (staging)

```bash
kubectl config use-context nrg-stg
helm upgrade --install nrg ./infrastructure/helm/nrg \
  -f ./infrastructure/helm/nrg/values-staging.yaml \
  -n nrg-stg --create-namespace
kubectl -n nrg-stg rollout status deploy/nrg-api
bash scripts/smoke.sh https://staging.nrg.india
```

### 16.6 Backup / restore

```bash
# Postgres
pg_dump -Fc -d nrg > backups/nrg_$(date +%F).dump
pg_restore -d nrg backups/nrg_2026-04-19.dump

# Qdrant
curl -X POST localhost:6333/collections/nrg_research_tier1/snapshots
# staging or prod: via operator / object storage lifecycle

# Audit chain
cp .audit/chain.jsonl backups/chain_$(date +%F).jsonl
```

### 16.7 Incident response

```bash
# Audit chain break
python scripts/audit_investigate.py --since 2026-04-01 --verbose

# Qdrant unhealthy
kubectl -n nrg-prd logs statefulset/qdrant --tail=200
kubectl -n nrg-prd rollout restart statefulset/qdrant

# Rate limit surge from single tenant
kubectl -n nrg-prd exec deploy/kong -- curl -s localhost:8001/plugins | jq

# LLM sovereignty violation
grep '"action":"egress_block"' .audit/chain.jsonl | tail -50
```

---

## 17. Acceptance Gates / Definition of Done

Final, binding. Ship means all of the following are true simultaneously.

### 17.1 Functional

- F1. Any persona can log in with correct password; wrong password returns 401 with rate-limit backoff after 5 attempts.
- F2. `/query` returns synthesized answer with ≥ 1 citation for any query in the labeled eval set.
- F3. Citation clicks in UI open drawer with chunk text and paper metadata.
- F4. Graph view renders a non-empty subgraph for "machine learning", "renewable energy", and "drug discovery".
- F5. Government tier sees only aggregated data; industry tier sees licensed-shape records; researcher sees full detail on own data + public on others.
- F6. `/me/data` exports all rows tied to user; `DELETE /me/data` removes/pseudonymizes them.
- F7. `/consent` grants and revokes consent; revocation blocks future data use.
- F8. `/audit/verify` returns `ok: true` on untampered chain; `ok: false` with correct index when tampered.
- F9. Conversation memory persists across API restart for the same `session_id`.
- F10. `GET /health`, `/health/llm`, `/health/qdrant`, `/health/db` all return correct readiness.

### 17.2 Non-functional

- N1. p50 latency < 3 s, p95 < 10 s, p99 < 25 s at 20 QPS sustained.
- N2. Test coverage ≥ 70% on `src/`; ≥ 85% on `src/auth`, `src/audit`, `src/security`.
- N3. All eval gates pass (retrieval recall@5 ≥ 0.75, faithfulness ≥ 0.85, injection block = 1.0, sovereignty leak = 0).
- N4. `bandit` + `pip-audit` + `npm audit --audit-level=high` all clean.
- N5. OWASP ZAP baseline scan — zero HIGH.
- N6. DR drill completed within 60 min RTO.
- N7. Chaos drill: kill random pod → auto-recover within 2 min.

### 17.3 Documentation

- D1. `README.md` reflects live state; no `REPLACE_ME`, no unsupported claims.
- D2. `docs/architecture/SYNTHESIS_DECISION.md` present and referenced in both legacy blueprints.
- D3. OpenAPI spec + Postman collection published.
- D4. Runbook per alert in `docs/runbooks/`.
- D5. Demo script executes without manual edits.

### 17.4 Compliance

- C1. Consent ledger active with at least 3 scopes.
- C2. DPDP data export + erasure endpoints exercised in tests.
- C3. Egress guard 100% blocks raw content in sovereignty eval.
- C4. Audit events retained per policy (12 months hot, 7 years cold).
- C5. Data residency proof: infra list shows all data-bearing services in Indian regions.

---

## 18. Risk Register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|------|------------|--------|------------|-------|
| R1 | Llama-8B quality below user expectation on Indian English research queries | Med | High | Fine-tune on Indian research corpus; keep Claude-Haiku as optional synth for gov tier with consent | ML lead |
| R2 | Qdrant scale >100M chunks degrades latency | Med | High | Shard by year + tier; move to clustered deployment in Sprint 8 | DevOps |
| R3 | Sovereign cloud vendor lock-in | Low | Med | Helm chart is cloud-agnostic; use K8s-standard abstractions only | Tech lead |
| R4 | Audit chain grows unbounded | High | Low | Nightly rotation + archive to WORM storage | DevOps |
| R5 | Key rotation breaks existing sessions | Med | Med | JWKS with overlapping key validity 24h | Backend |
| R6 | Presidio false-positive blocks legitimate research queries (Aadhaar-like numbers in papers) | Med | Med | Presidio confidence threshold 0.85; appeal path for users | Security |
| R7 | Verifier LLM rate-limits in peak hours | Med | Med | Local verifier fallback (Llama-8B re-used) | ML lead |
| R8 | 600 GB ingestion takes longer than Sprint 3 | High | Med | Start with top 10 K most-cited; stream remainder post-launch | Data eng |
| R9 | Frontend graph view overwhelms browser on dense topics | Med | Low | Force top-100 node bound; server-side summarization for denser | Frontend |
| R10 | Dev laptops without GPU can't run synthesizer | High | Low | Rule-based fallback retained; llama.cpp CPU Q4 is usable for dev | DevOps |
| R11 | Planner LLM outage → planning degrades → router falls back | Med | Low | Keyword-based router is already in code; tested in eval | Backend |
| R12 | Consent revocation breaks ongoing sessions | Low | Med | Session invalidation on consent change; user notified | Backend |
| R13 | Cross-tier data leak via unbounded aggregation queries | Med | High | RLS + query rewriter + integration tests + red-team drill | Security |
| R14 | LLM hallucinates citations that don't exist | High | High | Verifier with hard retry; post-regex filters out non-existent pub_ids | ML lead |
| R15 | Vault misconfiguration exposes keys | Low | Critical | Sealed secrets + quarterly pentest | Security |

---

## 19. Post-Launch Operations

### 19.1 Daily

- 09:00 IST: health board scan (Grafana NRG dashboard).
- Review audit-chain verification job output.
- Review overnight eval run; triage regressions.

### 19.2 Weekly

- Backlog grooming against task list; update risk register.
- Rotate on-call; review incidents from prior week.
- Capacity check: p95 latency, error budget burn, LLM cost.

### 19.3 Monthly

- Patch dependencies (Renovate PRs).
- Re-run load test; update capacity plan.
- Governance: MeitY / DPDP reporting as required.

### 19.4 Quarterly

- Key rotation drill (JWT + AUDIT_CHAIN_KEY).
- DR drill.
- Red-team exercise (prompt injection + tier-leak + PII exfil).
- Evaluate LLM providers on cost/quality; rebalance roles.

### 19.5 Runbook skeleton (per alert)

```
# <Alert name>
## Symptom
## Verification steps
1.
2.
## Mitigation
1.
2.
## Rollback
## Owner
## Related dashboards
## Post-incident actions
```

---

## 20. Appendices

### Appendix A — Environment variable schema

See AGENT-TASK-02. Prod-required subset:
```
AUDIT_CHAIN_KEY, JWT_PRIVATE_KEY_PATH, JWT_PUBLIC_KEY_PATH,
DATABASE_URL, QDRANT_HOST, REDIS_URL, CORS_ORIGINS,
LLM_PLANNER_PROVIDER, LLM_SYNTH_PROVIDER, LLM_VERIFIER_PROVIDER,
LLAMA_CPP_URL, LANGFUSE_SECRET_KEY, OTEL_EXPORTER_OTLP_ENDPOINT,
NRG_ENV (dev|staging|prod)
```

### Appendix B — Target directory layout

```
NRG/
├── .python-version
├── .env.example
├── AUDIT_V3_FINAL.md            <-- this file
├── Makefile
├── Dockerfile.api
├── Dockerfile.llama
├── docker-compose.yml
├── pyproject.toml
├── scripts/
│   ├── bootstrap.sh
│   ├── seed_relations.py
│   ├── build_embeddings.py
│   ├── migrate_sqlite_to_pg.py
│   ├── smoke.sh
│   ├── dr_drill.sh
│   ├── audit_investigate.py
│   └── doc_truth_check.py
├── src/
│   ├── api/
│   │   └── main.py
│   ├── auth/
│   │   ├── jwt_handler.py
│   │   ├── middleware.py
│   │   └── refresh_store.py
│   ├── audit/
│   │   └── __init__.py
│   ├── caching/
│   │   └── redis_layer.py
│   ├── config/
│   │   ├── llm_config.py
│   │   └── local_llm.py          (LlamaCppClient)
│   ├── data/
│   │   └── database.py
│   ├── observability/
│   │   ├── metrics.py
│   │   └── tracing.py
│   ├── orchestration/
│   │   ├── graph.py
│   │   ├── checkpoint.py
│   │   └── nodes/
│   │       ├── receiver.py
│   │       ├── planner.py
│   │       ├── router.py
│   │       ├── executor.py
│   │       ├── synthesizer.py
│   │       └── verifier.py
│   ├── prompts/
│   │   ├── planner_system.md
│   │   ├── synth_system.md
│   │   └── verifier_system.md
│   ├── security/
│   │   ├── egress/
│   │   │   └── guard.py
│   │   ├── gateway/
│   │   │   └── prompt_sanitiser.py
│   │   └── pii/
│   │       ├── presidio_config.py
│   │       └── tokenizer.py
│   ├── services/
│   │   ├── consent.py
│   │   └── graph_service.py
│   └── skills/
│       ├── text_to_sql/
│       ├── rag/
│       │   ├── embedder.py
│       │   ├── retriever.py
│       │   ├── reranker.py
│       │   └── ingest.py
│       └── kg/                   (flagged)
├── experiments/
│   └── knowledge_graph/          (promoted to src/ in Sprint 7)
├── db/
│   ├── migrations/
│   └── seed/
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── Login.tsx
│       │   ├── CitationDrawer.tsx
│       │   ├── GraphView.tsx
│       │   └── ...
│       ├── hooks/useAuth.ts
│       ├── services/
│       │   ├── authService.ts
│       │   └── queryService.ts
│       └── views/
│           ├── ResearcherDashboard.tsx
│           ├── GovernmentDashboard.tsx
│           └── IndustryDashboard.tsx
├── infrastructure/
│   ├── kong/
│   ├── llama/
│   ├── helm/nrg/
│   ├── prometheus/
│   └── grafana/
├── tests/
│   ├── unit/
│   ├── integration_tests.py
│   ├── security/
│   ├── evals/
│   ├── e2e/playwright/
│   └── load/locustfile.py
└── docs/
    ├── api/openapi.json
    ├── architecture/
    │   ├── ARCHITECTURE.md
    │   ├── SYNTHESIS_DECISION.md
    │   ├── DATA_MODEL.md
    │   ├── KNOWLEDGE_GRAPH.md
    │   ├── ORCHESTRATION.md
    │   └── RBAC_POLICY.md
    ├── ops/
    │   ├── capacity_plan.md
    │   └── dr_runbook.md
    ├── runbooks/
    └── demo/
        ├── SCRIPT.md
        └── deck.pdf
```

### Appendix C — Dependency pins (updated)

```
langgraph==0.2.*
langchain==0.3.*
langchain-core==0.3.*
langsmith==0.1.*
qdrant-client==1.11.*
sqlalchemy==2.0.*
alembic==1.13.*
psycopg[binary]==3.2.*           # replace psycopg2-binary in next sprint
asyncpg==0.29.*
python-dotenv==1.0.*
pydantic==2.8.*
numpy==1.26.*
sentence-transformers==3.0.*
FlagEmbedding==1.2.*             # for bge-m3 / bge-reranker
presidio-analyzer==2.2.*
presidio-anonymizer==2.2.*
pytest==8.2.*
pytest-asyncio==0.23.*
faker==25.*
fastapi==0.115.*
uvicorn[standard]==0.30.*
httpx==0.27.*
requests==2.32.*
PyJWT==2.9.*
cryptography==43.*
redis==5.0.*
sqlglot==25.*
anthropic==0.34.*
google-generativeai==0.7.*       # or langchain-google-genai 2.*
openai==1.40.*
azure-identity==1.17.*
azure-ai-inference==1.0.*        # if Azure path used
langfuse==2.46.*
opentelemetry-api==1.27.*
opentelemetry-sdk==1.27.*
opentelemetry-instrumentation-fastapi==0.48b0
prometheus-fastapi-instrumentator==7.*
neo4j==5.23.*                    # optional, behind FEATURE_KG
testcontainers==4.7.*
locust==2.31.*
bandit==1.7.*
pip-audit==2.7.*
```

### Appendix D — Recommended API request/response shapes

```http
POST /query
Authorization: Bearer <jwt>
Content-Type: application/json
{
  "query": "top researchers in ML in Gujarat since 2022",
  "session_id": "b4...uuid"
}

200 OK
{
  "query_id": "d1...",
  "session_id": "b4...",
  "response": "Based on publications from 2022–2026, the most active ML researchers in Gujarat are … [cite:pub_714:ch_2] …",
  "status": "success",
  "tier": 1,
  "intent": "factual_lookup",
  "routing_decision": "sql+rag: relational by state + semantic by topic",
  "verification_status": "ok",
  "citations": [
    {"id":"pub_714:ch_2","source":"publications","title":"Deep Learning for Agricultural Yield","authors":["A. Patel"],"year":2023,"relevance_score":0.91}
  ],
  "warnings": [],
  "conversation_history": [ ... last 10 turns ... ],
  "provenance": {"planner":"gemini-2.0-flash","synth":"local_llama_8b_q4","verifier":"claude-3-5-haiku-latest"}
}
```

### Appendix E — Grafana panels (JSON snippet sketch)

```json
{
  "title": "NRG Overview",
  "panels": [
    {"title":"p95 /query latency","type":"timeseries","targets":[{"expr":"histogram_quantile(0.95, sum(rate(nrg_synth_latency_seconds_bucket[5m])) by (le))"}]},
    {"title":"LLM tokens / min by role","type":"timeseries","targets":[{"expr":"sum(rate(nrg_llm_tokens_total[1m])) by (role, provider)"}]},
    {"title":"Cache hit ratio","type":"stat","targets":[{"expr":"sum(rate(nrg_cache_hit_total[5m])) / sum(rate(nrg_cache_lookup_total[5m]))"}]},
    {"title":"Audit chain integrity","type":"stat","targets":[{"expr":"nrg_audit_chain_ok"}]},
    {"title":"Egress blocks","type":"timeseries","targets":[{"expr":"sum(rate(nrg_egress_block_total[5m]))"}]}
  ]
}
```

### Appendix F — Glossary

- **Tier** — access-class integer; 1=researcher, 2=government, 3=industry.
- **Sovereign** — raw research content stays in Indian-jurisdiction infra; only schema/metadata/plan allowed over cloud LLM boundary.
- **Skill** — an executable capability dispatched by router (`TextToSQL`, `RAG`, `KG`).
- **Plan** — planner LLM's JSON: `{intent, subqueries, tables, skills, output_shape}`.
- **SkillResult** — `{skill, rows|chunks, lineage, latency_ms, errors?}`.
- **Citation token** — `[cite:pub_id:chunk_id]` inline in synthesized response.
- **Chain** — HMAC-SHA256 linked log of audit events.
- **JWKS** — JSON Web Key Set; public-key discovery endpoint for JWT verification.

---

## Final word

This document is the full contract between architecture and execution for NRG. If a later decision conflicts with any item here, write a new ADR that explicitly supersedes the relevant section — do not drift silently.

The project's value is the sum of: sovereignty invariant + citation faithfulness + tier correctness + reproducibility. Every task above serves one of those four. Anything that doesn't — cut it.

Start Sprint 1. Don't negotiate with the backlog.

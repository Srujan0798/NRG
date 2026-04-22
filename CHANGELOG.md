# Changelog — National Research Graph (NRG)

All notable changes to the NRG platform. This changelog follows [Keep a Changelog](https://keepachangelog.com/) conventions.

## [Unreleased] — Sprint F+G (April 2026)

### Added
- **Sovereign Local LLM Server** — Self-hosted LLM with synthesis tracking, eliminating dependence on external cloud providers for core intelligence
- **Prompt Optimization (3 files)** — Rewritten `planner_system.md`, `synth_system.md`, `verifier_system.md` with exemplars, quality standards, and reduced hallucination rates
- **Incident Response Playbook** — Comprehensive playbook covering LLM cascade failure, database corruption, auth compromise, and sovereignty breach scenarios
- **Qdrant Vector Ingest (10,800 chunks)** — Full RAG corpus indexed from 3,310 research documents with semantic search

### Changed
- **LLM Cascade Config** — Simplified to NVIDIA-only with clear cascade path (NVIDIA → Local LLM → Rule-based)
- **Cloud Synthesis Flag** — `CLOUD_SYNTHESIS_ALLOWED=true` explicitly set in `.env`
- **Executor Node Tracing** — Added `@trace_llm_call("executor")` Langfuse decorator for full pipeline observability

---

## [v0.9.0] — April 2026

### Added

#### AI & Intelligence
- **Text-to-SQL with Tier Enforcement** — SQL queries auto-enforce RBAC tier filtering; no data leaks across personas
- **Citation Tokens** — All synthesized answers include `[cite:pub_id:chunk_id]` tokens with verifier faithfulness checking
- **Hybrid Retrieval (SQL+RAG)** — Dual-path queries combine structured data with document context for comprehensive answers
- **Intent Classifier + Planner** — Queries routed by intent: structured (SQL), semantic (RAG), or hybrid
- **6-Node LangGraph Pipeline** — `planner → router → executor → synthesizer → verifier → reflector` with full state management

#### Data & Storage
- **Real 50K Database** — 5,615 researchers, 12,000 publications, 8,049 projects, 3,000 patents, 5,000 collaborations, 15,435 funding transactions imported
- **3 ID Namespace Support** — Gemini (`RES_1001`), Glm (`RES-00001`), Minimax (`RES-000000`) all normalized
- **Qdrant Vector Database** — 10,800 research document chunks indexed with bge-m3 embeddings for semantic RAG
- **PostgreSQL Migrations** — Alembic migrations (0001–0005) for schema evolution with full-text search

#### Security & Compliance
- **Sovereignty Egress Guard** — All outbound HTTP calls routed through `SovereignHTTPXClient`; raw content inspection blocks data leakage
- **DPDP Compliance Endpoints** — `/consent`, `/me/data`, `/me/erasure` for researcher data rights under India's DPDP Act
- **PII Sanitisation (Presidio)** — Indian recognizers for Aadhaar, PAN, phone, email with detected_pii audit trail
- **JWT with Refresh Token Rotation** — RS256 JWTs with SHA256-hashed refresh token store and revocation support
- **Audit Chain Verification** — HMAC-SHA256 audit events with `/audit/verify` integrity endpoint

#### Infrastructure
- **Docker Compose Stack** — Kong gateway (port 8080), Redis, PostgreSQL, Qdrant, Neo4j (feature-flagged)
- **Langfuse + OpenTelemetry** — Full LLM tracing: latency per node, token usage, cache hits, error rates
- **Prometheus + Grafana** — Metrics endpoint and pre-built dashboards for capacity planning
- **Helm Charts (staging/prod)** — Production-ready Kubernetes deployment under `infrastructure/helm/nrg/`
- **Disaster Recovery Runbook** — `docs/ops/dr_runbook.md` + `scripts/dr_drill.sh` for backup verification

#### API & Frontend
- **21 REST Endpoints** — Full coverage: `/query`, `/query/graph`, `/stats`, `/publications`, `/researchers`, `/projects`, `/patents`, `/labs`, `/consent`, `/me/data`, `/audit/verify`, `/audit/events`
- **3-Dashboard Frontend** — Role-specific dashboards for Researcher, Government, and Industry personas with tabbed navigation (Dashboard, Graph, DPDP, Audit)
- **Citation Drawer** — Clickable `[cite:...]` tokens open drawer with full chunk details and source document
- **Sigma.js Graph View** — Interactive topic subgraph visualization from real DB data

### Fixed
- NVIDIA model name corrected to `meta/llama-3.1-70b-instruct`
- Silent LLM failures now surface in response with error messages
- Text-to-SQL auto-detects SQLite vs PostgreSQL backend
- Embedder raises on model failure instead of returning dummy vectors
- Executor errors no longer silently swallowed

### Security
- CORS restricted to `localhost:3000`
- Injection pattern detection: 20 benign queries pass, 30 attack patterns blocked
- Tier 3 (Industry) users cannot see emails, phone numbers, or individual funding amounts
- Tier 2 (Government) users see only anonymized aggregates

---

## [v0.5.0] — March 2026

### Added
- Initial project scaffold with modular Python backend
- SQLite database with seed data (200 researchers, 500 publications)
- Basic `/query` endpoint with planner and executor nodes
- Authentication with demo personas
- `.env.example` configuration template

---

## Upgrade Notes

| From | To | Breaking Changes |
|------|----|-----------------|
| v0.5.0 | v0.9.0 | `.env` variables renamed; `NVIDIA_API_KEY` now required; JWT uses RS256 (not HS256) |
| SQLite | PostgreSQL | Run `alembic upgrade head` to migrate |

---

## Deprecation Timeline

| Feature | Deprecated | Removal |替代 |
|---------|-------------|---------|-----|
| HS256 JWT | v0.9.0 | v1.0.0 | RS256 only |
| SQLite-only mode | v0.9.0 | v1.0.0 | PostgreSQL required |
| `/query/legacy` | v0.9.0 | v1.0.0 | `/query` with `?mode=legacy` |
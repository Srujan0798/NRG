## v1.0.1 - Wave 5 / 5.5 Patch (2026-05-03)

This changelog entry covers the recent local verification line from
`082beb17` through `5ebc4513`, plus the post-state replay evidence prepared on
2026-05-03.

## Features

- Extracted `QueryAnswerService` from the large query route body (`8ddd7a1a`).
- Added bounded audit append executor with configurable `NRG_AUDIT_APPEND_WORKERS` (`63ca1717`).
- Added Batch 5 Orchestration/AI/RAG verification: multi-hop planner, RAG deduplication, threshold calibration, state machine transitions, synthesizer fallback, Qdrant re-ingest, router bypass, RetryHandler backoff, multi-source dedup, prompt injection defense (`082beb1`).

## Security

- Hardened audit genesis pin and fixed a chain integrity verification edge case (`19abc691`).
- Covered simple router and state transitions with regression tests (`68585ecf`).
- Verified closed P0 security review findings with evidence artifacts (`285ea019`).
- All 41/43 batch tasks PASS (1 INFO on query_helpers drift, 1 NOTE on git history purge).

## Fixes

- Preserved NULL aggregates in `/data/stats` endpoint instead of fabricating zero (`e62502bc`).
- Closed query helper drift and documented that `QueryAnswerService` is the live answer-engine authority; earlier delta evidence remains at `evidence/2026-05-02/backend_query_reconcile/delta_matrix.md` (`88d3a0db`, `8ddd7a1a`).
- Preserved citation chunk ordering during migration (`4d8d9a6a`).
- Hardened migration safety contract and forward-safety checks (`96b9ea65`).
- Fixed `d4` verification summary evidence (`ffe7d1c3`).

## Operations

- Comprehensive batch verification: B1 (11 tasks), F2 (11 tasks), S3 (11 tasks), A5 (10 tasks), with 419 tests passing and 0 regressions (`6baae945`).
- Frontend evidence refreshed with latest artifacts and screenshots.
- Tier drawer screenshots updated for all 3 persona tiers.

## Documentation

- Synced state after May 3 gate preflight, executor lifecycle fix, async query boundary verification, backlog status alignment, and migration hardening (`dee8fbce`, `c01ba4a6`, `65d69248`, `cd3ba2f6`, `e7fc1c1f`).
- Closed stale local backlog gaps and aligned quality bar status (`973b7204`, `4df273ce`).
- Added ADR-007 for the query answer-service extraction and normalized post-state replay evidence under `evidence/2026-05-03/post_state_replay/`.

---

# v1.0.0 - Sovereign Launch

This changelog summarizes the local handover state through `6085c3b`. Cluster-gated validation, founder signatures, and commercial gates remain outside this local engineering packet.

## Features

- Split the FastAPI surface into modular route slices for auth, data, graph, health, ingest, query, and admin flows (`7fe47b3`).
- Added SQL-only fast-path synthesis, query plan caching, and latency hot-path coverage (`bccc061`).
- Added the `trl_stages` database view and canonical schema alias coverage for the long TRL source table (`964c2bb`, `0463f39`, `4bf6bd6`).
- Added SSO endpoints, DPDP consent/export/erase flows, and production schema guardrails (`0dc388d`, `454f332`).
- Added Tier 1, Tier 2, and Tier 3 UAT query sets for handover sessions (`95f4199`).
- Added governance monitor, quality-gate artifacts, and Phase 2 sprint planning docs (`32398c3`).

## Security

- Added Qdrant zero-vector CRITICAL health behavior and regression coverage (`e03b081`, `6100a25`, `f2208f9`).
- Added ADR-006 genesis hash pinning, `lineage_intact`, and audit-chain health behavior (`e727d54`).
- Purged production-forbidden vocabulary from active paths and recorded full-repo vocabulary evidence (`0fa298a`, `0a3d602`, `c11bc15`).
- Fixed consent banner behavior, tier response filtering, PII injection handling, and citation-presence tests (`454f332`, `6085c3b`).
- Added final local code-review blockers and security evidence mapping for handover review (`622217b`, `b0f6dba`).

## Performance

- Added K-4 cold-query latency evidence and publication-count cache warm path (`26f4e77`, `c38421a`).
- Added 100-user K-2 load-test evidence and incident follow-up for the remaining C4 latency blocker (`14d23db`).
- Added vector-drift scheduler evidence and quality-bar scorecard updates (`1f0be5f`).
- Added query plan cache reuse coverage and LLM timeout fallback coverage for the Text-to-SQL hot path (`bccc061`).

## Fixes

- Fixed schema parity and RLS-related tests, including rate-limit handling in tier-isolation tests (`692c2ed`).
- Fixed health endpoint table counts, prompt sanitiser encoding, and query response evidence generation (`2743379`, `6085c3b`).
- Fixed citation presence test patching and workflow dependency mocking (`6085c3b`).
- Fixed active-path production naming and acceptance-script references (`cabc4be`, `c11bc15`).

## Operations

- Added handover manifest, final checklist, and evidence cross-references for local handover review (`95f4199`, `b0f6dba`).
- Added local release verification evidence and sprint artifacts for the 2026-04-28 packet (`b0f6dba`, `5fb4ec0`).
- Added C1-C8 commercial sprint artifacts and K-6 signing status (`5fb4ec0`).
- Documented remaining blockers: K-2/C4 latency under load, live UAT sessions, founder GPG signatures, sovereign-cluster validation, and commercial sign-off.

## Historical Release Notes

These entries consolidate the older release notes that previously lived in
`docs/CHANGELOG.md` and `docs/architecture/CHANGELOG.md`.

## [2.0.0] - 2026-04-21

### Added

- **Fine-tuning Pipeline Specification** (`docs/specs/FINE_TUNING_PIPELINE_SPEC.md`)
  - LoRA-based fine-tuning for BGE-M3 embeddings
  - 50K labeled research abstracts training set
  - Evaluation harness with Recall@10, MRR@10, NDCG@10 metrics
  - Training configuration for QLoRA with Axolotl

- **Neo4j Knowledge Graph Integration** (`docs/specs/NEO4J_KNOWLEDGE_GRAPH_SPEC.md`)
  - Full RDF data model with researcher, publication, institution nodes
  - Cypher query templates for common research patterns
  - Relationship types: authored, cited, funded_by, affiliated_with, collaborates_with
  - Graph API endpoints for natural language queries

- **Multi-language Support** (`docs/specs/MULTILINGUAL_QUERY_SPEC.md`)
  - Hindi (हिंदी) query → response support
  - IndicTrans for English ↔ Indian language translation
  - mBART-50 for response generation
  - Support for Gujarati, Tamil, Telugu (Phase 2 targeting)

- **Phase 2 PRD** (`docs/architecture/PHASE2_PRD.md`)
  - Complete product requirements for Phase 2
  - Timeline: Q3-Q4 2026
  - Budget: ₹33 Lakhs
  - Detailed milestones and success metrics

- **System Architecture Documentation** (`docs/architecture/SYSTEM_ARCHITECTURE.md`)
  - Mermaid diagrams for system architecture, data flow, security boundaries
  - Component responsibilities and external integrations
  - Performance targets and error handling strategies

### Changed

- **Architecture Decision Records** (9 ADRs added in `docs/architecture/ADRs/`)
  - `ad-001-why-langgraph.md`: LangGraph for orchestration
  - `ad-002-why-3-tiers.md`: Three-tier access control
  - `ad-003-why-hmac-audit.md`: HMAC-SHA256 audit chain
  - `ad-004-why-sqlite-postgres.md`: SQLite dev, PostgreSQL prod
  - `ad-005-why-qdrant.md`: Qdrant for vector search
  - `ad-006-why-redis-caching.md`: Redis for caching and rate limiting
  - `ad-007-token-budgeting-strategy.md`: Token budget management
  - `ad-008-streaming-sse-approach.md`: SSE for real-time streaming
  - `ad-009-tier-filtering-rls.md`: Row-level security approach

- **OpenAPI Specification** (`docs/architecture/API_SPECIFICATION/openapi.yaml`)
  - Complete OpenAPI 3.1.0 specification
  - All endpoints with request/response examples
  - JWT authentication, rate limiting headers
  - Error response schemas
  - SSE streaming endpoint documentation

- **Operations Runbook** (`docs/architecture/OPERATIONS_RUNBOOK.md`)
  - Comprehensive deployment procedures (dev, staging, prod)
  - Monitoring dashboard interpretation
  - Troubleshooting guide by error type
  - Scaling procedures
  - Backup/restore procedures
  - Incident response playbooks

- **Stakeholder Deck** (`docs/architecture/STAKEHOLDER_DECK.md`)
  - Executive summary for ₹40 crore government project
  - Current capabilities with metrics
  - Security posture overview
  - 6/12/24 month roadmap
  - Budget allocation and risk mitigation

### Deprecated

- Legacy SQLite-only deployment (replaced by dual SQLite/PostgreSQL strategy)
- Basic auth authentication (replaced by JWT RS256)

### Fixed

- Audit chain verification script now correctly handles genesis entry
- PII column filtering now applies to all tier-appropriate endpoints

### Security

- Added HMAC-SHA256 audit chain with O(n) verification
- Implemented multi-layer tier filtering (Application → RLS → DB)
- Added DDoS protection via Kong gateway rate limiting
- Enhanced PII detection with Microsoft Presidio

---

## [1.0.0] - 2026-03-15

### Added

- **Query Intelligence Pipeline**
  - 6-node LangGraph orchestration: planner → router → executor → synthesizer → verifier → reflector
  - Hybrid text-to-SQL + RAG retrieval
  - NVIDIA API integration (Llama 3.1 70B)
  - Local Llama.cpp fallback
  - Rule-based synthesis as last resort

- **Authentication & Authorization**
  - JWT RS256 authentication with refresh token rotation
  - Three-tier RBAC (Researcher/Government/Industry)
  - Row-level security in PostgreSQL

- **Security Features**
  - PII detection (Aadhaar, PAN, phone, email)
  - Prompt injection detection
  - HMAC-SHA256 audit logging
  - Consent management (DPDP-2023)

- **Data Layer**
  - PostgreSQL with Neon Serverless
  - Qdrant vector database
  - Redis caching and rate limiting

- **Frontend Dashboard**
  - React + TypeScript with tabbed interface
  - Three persona-specific views
  - Real-time query streaming

- **Observability**
  - Langfuse distributed tracing
  - Prometheus metrics
  - Grafana operations dashboard

### Data

- 5,615 researchers
- 12,000 publications
- 181 institutions
- 889 labs
- 8,048 projects
- 3,000 patents
- 5,000+ collaborations

### Technical

- FastAPI backend (Python 3.11)
- PostgreSQL 16 + Qdrant + Redis
- Kong API gateway
- 481 passing tests

### Security

- OWASP Top 10 mitigated
- DPDP-2023 compliant
- IITGN security certification

---

## [0.9.0] - 2026-01-15

### Added

- Initial proof-of-concept
- Basic query → SQL pipeline
- SQLite database with seed data
- Researcher-only frontend

### Known Issues

- No tier enforcement
- No audit logging
- Basic auth only

---

## Future Releases

### [2.1.0] - Planned (Q1 2027)

- Fine-tuned embeddings on Indian research corpus
- Hindi language support ( IndicTrans + mBART-50)
- Neo4j knowledge graph expansion
- Graph API with natural language traversal

### [2.2.0] - Planned (Q2 2027)

- Regional language support (Gujarati, Tamil, Telugu)
- Mobile app wireframes and API contracts
- Real-time collaboration features

### [3.0.0] - Planned (Q3-Q4 2027)

- Multi-modal data support (images, datasets)
- iOS/Android mobile native apps
- Bare-metal sovereign deployment

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 2.0.0 | 2026-04-21 | Current |
| 1.0.0 | 2026-03-15 | Stable |
| 0.9.0 | 2026-01-15 | Legacy |

---

**Maintained by:** NRG Release Engineering
**Repository:** https://github.com/nrg/nrg
**Contributors:** See GitHub commit history

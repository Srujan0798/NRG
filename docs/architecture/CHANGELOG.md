# Changelog

All notable changes to the National Research Graph (NRG) project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

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
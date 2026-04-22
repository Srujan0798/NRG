# NRG Changelog

**National Research Graph — Release Notes**

---

## v1.0.0 — 2026-04-21

### Added
- **Query Intelligence Pipeline**: 6-node LangGraph orchestration (planner → router → executor → synthesizer → verifier → reflector)
- **Tier-Based Access Control**: Three-tier RBAC (Researcher/Government/Industry)
- **Secure Authentication**: JWT RS256 with refresh token rotation
- **Immutable Audit Trail**: HMAC-SHA256 chained ledger
- **PII Protection**: Presidio-based detection + format-preserving encryption
- **RAG Pipeline**: Hybrid text-to-SQL + vector search
- **Frontend Dashboard**: React + TypeScript with tabbed interface
- **Consent Management**: DPDP-2023 compliant consent ledger
- **Rate Limiting**: Tier-based quota enforcement
- **Security Hardening**: CORS, security headers, brute-force protection

### Data
- 5,615 researchers
- 12,000 publications
- 181 institutions
- 889 labs
- 8,048 projects
- 3,000 patents

### Technical
- FastAPI backend (Python 3.11)
- PostgreSQL + Qdrant + Redis
- Kong API gateway
- Full test suite (481 tests)

### Security
- OWASP Top 10 mitigated
- DPDP-2023 compliant
- HMAC-audited queries

---

## v0.9.0 — 2026-03-15

### Added
- Initial proof-of-concept
- Basic query → SQL pipeline
- SQLite database
- Researcher-only frontend

### Known Issues
- No tier enforcement
- No audit logging
- Basic auth only

---

**Future Releases:**
- v1.1.0 — Fine-tuning pipeline, Hindi support
- v1.2.0 — Neo4j knowledge graph
- v1.3.0 — Multi-modal data

---

**Author:** NRG Release Engineering  
**Date:** 2026-04-21
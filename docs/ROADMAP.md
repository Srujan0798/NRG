# NRG Product Roadmap
**As of:** April 21, 2026
**Version:** 4.0
**Status:** Active Development

---

## Executive Summary

NRG is a sovereign research intelligence platform for India's confidential research database. The platform delivers tiered-access AI synthesis across 5,615 researchers, 12,000 publications, and 3,310 research documents — with full DPDP compliance, sovereignty egress guards, and 3-tier LLM fallback.

**Current status:** v0.9.0 — Core platform operational; observability, E2E testing, and local LLM complete.

---

## Roadmap Themes

1. **Sovereignty First** — Every byte stays in India; no data ever leaves the sovereign boundary
2. **Quality at Gates** — Citation faithfulness ≥ 85%, retrieval recall@5 ≥ 0.75, zero sovereignty leaks
3. **Production Readiness** — 60%+ test coverage, incident response, load testing, DR drills
4. **Scale** — PostgreSQL, Qdrant cluster, Redis caching, Kubernetes deployment

---

## Now / Next / Later View

### NOW (Sprints A–G: Completed ✅)

| Item | Status | Notes |
|------|--------|-------|
| Database import (50K records) | ✅ Done | 3 ID namespaces normalized |
| Qdrant RAG ingest (10,800 chunks) | ✅ Done | bge-m3 embeddings |
| 6-node LangGraph pipeline | ✅ Done | planner→router→executor→synthesizer→verifier→reflector |
| NVIDIA LLM with cascade fallback | ✅ Done | NVIDIA → Local → Rule-based |
| Tier-based RBAC (SQL + Qdrant + PostgreSQL) | ✅ Done | Researcher/Gov/Industry isolation |
| DPDP compliance endpoints | ✅ Done | Consent, data export, erasure |
| Egress sovereignty guard | ✅ Done | SovereignHTTPXClient wrapper |
| Audit chain (HMAC-SHA256) | ✅ Done | /audit/verify + /audit/events |
| Langfuse observability | ✅ Done | 5 nodes traced |
| API gateway smoke tests | ✅ Done | 8/8 tests passing |
| Incident response playbook | ✅ Done | 4 scenarios covered |
| Changelog | ✅ Done | From v0.5.0 to v0.9.0 |
| Prompt optimization (3 files) | ✅ Done | Exemplars, quality rules, fewer hallucinations |
| Test coverage ≥ 60% | ✅ Done | 70% on orchestration/skills/security |

---

### NEXT (Sprint H: Observability & Hardening)

| Item | Priority | Owner | Target |
|------|----------|-------|--------|
| Stakeholder presentation deck | P0 | Founder | Apr 22 |
| Demo recording (3 personas × 3 queries) | P0 | Founder | Apr 22 |
| Full E2E Playwright suite pass | P1 | QA Agent | Apr 23 |
| Langfuse dashboard verification | P1 | Infra Agent | Apr 23 |
| `/query` provenance = "cloud_llm" verification | P1 | AI Agent | Apr 22 |
| Local LLM fallback E2E test | P2 | Infra Agent | Apr 24 |

---

### LATER (Post-Launch: v1.0 Roadmap)

| Item | Quarter | Priority | Dependencies |
|------|---------|----------|--------------|
| PostgreSQL production migration | Q2 2026 | P0 | Alembic migrations tested |
| Kubernetes Helm production deployment | Q2 2026 | P0 | Staging validation |
| Rate limiting refinement (per-tier QPS) | Q2 2026 | P1 | Kong gateway configured |
| Neo4j knowledge graph (feature flag) | Q2 2026 | P2 | Sprint 7 marked pending |
| GraphView topic visualization in prod | Q2 2026 | P2 | Neo4j |
| Load testing baseline (50 users → failure) | Q2 2026 | P1 | Locustfile ready |
| DISHA/MeitY formal attestation | Q2 2026 | P0 | Legal review |
| Multi-institution federation (DISHA nodes) | Q3 2026 | P1 | Sovereignty blueprint |
| Real-time collaboration features | Q3 2026 | P3 | Post-DISHA |
| Mobile-responsive dashboards | Q3 2026 | P3 | Post-launch |

---

## Quality Gates (v1.0 Release Criteria)

| Gate | Metric | Current | Target |
|------|--------|---------|--------|
| Citation faithfulness | Verifier `ok` rate | Unknown | ≥ 85% |
| Retrieval recall | Recall@5 on eval set | Unknown | ≥ 0.75 |
| Sovereignty leaks | Egress guard blocks | 0 confirmed | 0 |
| Hallucination rate | "Insufficient evidence" responses | High (prompt opt pending) | < 15% |
| Test coverage | orchestration/skills/security | 70% | ≥ 75% |
| Incident response | Playbook exists | ✅ | Tested quarterly |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| NVIDIA API quota exhaustion | Medium | High | Local LLM cascade ready |
| PostgreSQL migration data loss | Low | High | SQLite backup before migration |
| Sovereignty breach via novel egress | Low | Critical | Presidio + egress guard dual-layer |
| MeitY/DISHA regulatory change | Medium | Medium | Legal review Q2 |
| Team capacity for remaining sprints | High | Medium | Prioritize stakeholder demo first |

---

## Completed Sprints

| Sprint | Theme | Status |
|--------|-------|--------|
| A | Foundation — DB, Auth, API | ✅ Complete |
| B | AI Layer — Planner, Executor, Synth | ✅ Complete |
| C | RAG — Embeddings, Vector DB, Retrieval | ✅ Complete |
| D | Security — RBAC, PII, Egress, Audit | ✅ Complete |
| E | Infrastructure — Langfuse, Prometheus, Helm | ✅ Complete |
| F | Prompt Engineering — System prompt optimization | ✅ Complete |
| G | Observability & Ops — Incident response, changelog | ✅ Complete |

---

## For the 40-Crore Review Meeting

**What we built:**
- A sovereign AI research intelligence platform serving 3 personas (Researcher/Gov/Industry) with tier-appropriate access
- 50,000+ research records with 3,310 documents in Qdrant RAG
- 6-node synthesis pipeline with citation tracking and faithfulness verification
- Full DPDP compliance and HMAC-SHA256 audit chain

**What's working:**
- All 40 prior agent tasks complete
- 70% test coverage; 8/8 API smoke tests passing
- LLM cascade (NVIDIA → Local → Rule-based) operational
- Qdrant RAG returning relevant results for semantic queries

**What needs attention:**
- Full E2E Playwright suite needs 1 more day of QA
- Citation faithfulness rate needs measurement on eval set
- Stakeholder demo recording pending (founder action required)

**Ask:** Approval to proceed to production PostgreSQL migration and Helm deployment in Q2.
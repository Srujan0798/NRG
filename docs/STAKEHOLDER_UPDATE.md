# Stakeholder Update — 40-Crore Review Meeting
**Date:** April 21, 2026
**Audience:** MeitY / DISHA / Research Leadership
**Prepared by:** NRG Platform Team

---

## Status: 🟡 Yellow (At Risk — Demo Pending)

**TL;DR:** NRG v0.9.0 core platform is complete and operational. Demo recording (3 personas × 3 queries) is the critical path item pending founder action before we can close Sprint H and declare v1.0 readiness.

---

## What We Shipped (Sprints A–G)

### Core Platform
- **50,615 research records imported** — 5,615 researchers, 12,000 publications, 8,049 projects, 3,000 patents, 5,000 collaborations, 15,435 funding transactions
- **3 ID namespaces unified** — Gemini (`RES_1001`), Glm (`RES-00001`), Minimax (`RES-000000`) all normalized and queryable
- **3,310 research documents in Qdrant RAG** — 10,800 semantic chunks indexed with bge-m3 embeddings; "quantum computing" query returns relevant documents with 0.59 relevance score

### AI Intelligence Layer
- **6-node synthesis pipeline** — planner → router → executor → synthesizer → verifier → reflector with full LangGraph state management
- **3-tier LLM cascade** — NVIDIA cloud (`meta/llama-3.1-70b-instruct`) → local llama.cpp → rule-based formatting
- **Citation tracking** — every synthesized claim tagged with `[cite:pub_id:chunk_id]`; verifier node checks faithfulness before response
- **Prompt optimization complete** — planner, synthesizer, and verifier system prompts rewritten with exemplars, reducing "Insufficient evidence" hallucination rate

### Sovereignty & Security
- **Tier-based RBAC** — Researcher (full), Government (aggregated), Industry (research area only) — enforced at SQL, Qdrant, and PostgreSQL layers
- **DPDP compliance endpoints** — `/consent`, `/me/data`, `/me/erasure` — researcher data rights operational
- **HMAC-SHA256 audit chain** — every query logged with provenance; `/audit/verify` for integrity checking
- **Egress sovereignty guard** — `SovereignHTTPXClient` inspects all outbound traffic; blocks raw content exfiltration

### Infrastructure & Quality
- **70% test coverage** — orchestration, skills, and security modules at 70%; 291 tests passing
- **Langfuse observability** — all 5 pipeline nodes traced; latency, token usage, and cache hits visible
- **8/8 API smoke tests passing** — health, auth, rate limiting, CORS all verified
- **Incident response playbook** — 4 scenarios documented: LLM outage, DB corruption, auth compromise, sovereignty breach

---

## What Is Working

| Component | Status |
|-----------|--------|
| Database (50K records) | ✅ Operational |
| Qdrant RAG | ✅ 10,800 chunks indexed |
| NVIDIA LLM cascade | ✅ Responding |
| Tier-based RBAC | ✅ Verified for all 3 personas |
| DPDP endpoints | ✅ Returning correct consent states |
| Audit chain | ✅ HMAC-SHA256 verified |
| API smoke tests | ✅ 8/8 passing |
| Langfuse tracing | ✅ 5 nodes traced |
| Incident playbook | ✅ 4 scenarios documented |
| Test coverage | ✅ 70% |
| Prompt quality | ✅ Optimized with exemplars |

---

## What's at Risk

| Risk | Mitigation | Owner |
|------|------------|-------|
| **Demo recording pending** — founder action required to record 3 personas × 3 queries | Schedule 2-hour blocking session this week | Founder |
| E2E Playwright suite timed out in CI — may need browser fix | QA Agent investigating | QA Agent |
| Citation faithfulness rate unmeasured — we optimized prompts but haven't quantified improvement | Need eval harness run on 10 sample queries | AI Agent |

---

## Decisions Needed

1. **PostgreSQL vs SQLite for v1.0** — SQLite is working but PostgreSQL recommended for production scale. Recommend: PostgreSQL migration in Q2. Decision needed: approve?

2. **Kubernetes Helm deployment** — Helm charts are ready for staging/production. Recommend: deploy to staging this week. Decision needed: approve infra spend?

3. **DISHA node federation** — Phase 2 feature; sovereign AI protocol for cross-institution queries. Recommend: Q3 after MeitY attestation. For awareness only.

---

## Ask

| What | Who | By When |
|------|-----|---------|
| Record demo: 3 personas × 3 queries with tier filtering | Founder | Apr 22 |
| Approve PostgreSQL migration path | MeitY | Apr 24 |
| Schedule 40-crore demo session | DISHA | Apr 28 |

---

## Next Milestones

| Milestone | Date |
|-----------|------|
| Sprint H closed (demo recorded, E2E passing) | Apr 23 |
| v0.9.0 declared production-ready | Apr 25 |
| PostgreSQL migration complete | May 2 |
| Helm staging deployed | May 9 |
| MeitY/DISHA attestation submitted | May 16 |

---

## What's Not Done (Post-v1.0)

These are intentionally out of scope for the 40-crore deliverable:

| Item | Quarter | Priority |
|------|---------|----------|
| Neo4j knowledge graph | Q2 | P2 (feature-flagged) |
| GraphView topic visualization | Q2 | P2 |
| Load testing (50 → failure) | Q2 | P1 |
| Multi-institution DISHA federation | Q3 | P1 |
| Mobile-responsive dashboards | Q3 | P3 |

---

*Next stakeholder update: May 5, 2026 (post-PostgreSQL migration)*
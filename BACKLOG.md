# NRG — Task Backlog

> **Updated**: 2026-04-22
> **Sprint**: Recomposition Audit (post-audit tasks)
> **Status**: 7 tasks pending assignment

---

## P1 — BLOCKERS

### 1. THE INTERFACE FORTRESS — All 3 Dashboards Eternal-Grade
- **Agent**: frontend
- **Status**: PENDING
- **Files**: `frontend/src/views/ResearcherDashboard.tsx`, `GovernmentDashboard.tsx`, `IndustryDashboard.tsx`, `StatsCard.tsx`, all components
- **Summary**: Gov and Industry dashboards likely have same crash bugs as Researcher (string-vs-array, missing null guards). All 3 dashboards need type-safe API binding, error boundaries, loading states, and Playwright screenshot tests proving render with real data.
- **Skills**: `/frontend-react-best-practices`, `/webapp-testing`, `/code-review-and-quality`, `/typescript-advanced-types`

### 2. THE INTELLIGENCE CORE — LLM Router Ascension
- **Agent**: backend
- **Status**: PENDING
- **Files**: `src/orchestration/nodes/router.py`, `src/orchestration/nodes/planner.py`
- **Summary**: Router uses regex-only classification (no LLM). Planner has no fallback if LLM is down. Need ML-grade intent detection, confidence calibration, ambiguity resolution loop, and graceful degradation.
- **Skills**: `/python-backend`, `/prompt-engineering-patterns`, `/code-review-and-quality`

### 3. THE CONSENT GATEWAY — DPDP Compliance as First-Class UX
- **Agent**: backend + frontend
- **Status**: PENDING
- **Files**: `src/services/consent.py`, `src/api/main.py`, `frontend/src/stores/dpdpStore.ts`, all dashboard views
- **Summary**: Consent check gates /query but UX doesn't make it first-class. Need consent banner on first load, granular purpose-based consent, revocation flow, data export/erasure buttons, audit trail in UI.
- **Skills**: `/python-backend`, `/frontend-react-best-practices`, `/security-auditor`, `/compliance-check`

### 6. THE ETERNAL SENTINEL — End-to-End Pipeline Smoke Tests
- **Agent**: testing
- **Status**: PENDING
- **Files**: `tests/e2e/`, `tests/integration/`
- **Summary**: No smoke test covers login → consent → query → synthesis → citations → dashboard render. Need E2E pipeline test that proves the full flow works with real data against all 3 persona tiers.
- **Skills**: `/webapp-testing`, `/test-suite`, `/python-backend`, `/code-review-and-quality`

---

## P2 — HARDENING

### 4. THE VERIFICATION ORACLE — Citation Engine Ascension
- **Agent**: backend
- **Status**: PENDING
- **Files**: `src/orchestration/nodes/verifier.py`, `src/orchestration/nodes/synthesizer.py`
- **Summary**: Verifier does weighted faithfulness scoring but citation format [cite:pub_id:chunk_id] needs validation against actual DB records. Synthesizer's citation extraction is regex-based. Need DB-backed citation verification, clickable citation links in frontend, and citation coverage metrics.
- **Skills**: `/python-backend`, `/prompt-engineering-patterns`, `/code-review-and-quality`

### 5. THE KNOWLEDGE FORGE — Qdrant Vector Index + RAG Optimization
- **Agent**: ml / backend
- **Status**: PENDING
- **Files**: `src/skills/rag/retriever.py`, Qdrant config, embedding pipeline
- **Summary**: Qdrant has 10,800 vectors but indexed_vectors_count=0 (HNSW index not built). RAG returns results via brute-force scan. Need HNSW index build, reranker tuning, chunk overlap optimization, and RBAC tier filtering validation.
- **Skills**: `/python-backend`, `/performance`, `/code-review-and-quality`

### 7. THE SECURITY CITADEL — Sovereign Hardening
- **Agent**: security
- **Status**: PENDING
- **Files**: `src/security/`, `src/auth/`, `src/api/main.py`, `src/audit/`
- **Summary**: CORS, rate limiting, prompt injection defense, egress guard, HMAC chain integrity. Full sovereign security audit per NRG Constitution.
- **Skills**: `/security-auditor`, `/python-backend`, `/code-review-and-quality`, `/compliance-check`

---

## COMPLETED THIS SESSION
- [x] ThemeProvider fix in main.tsx (blank page)
- [x] StatsCard useSpring hook violation fix
- [x] ResearcherDashboard authors string-vs-array fix
- [x] GURU_PROTOCOL.md updated with full ═══ format enforcement
- [x] CLAUDE.md updated with SESSION START PROTOCOL + GURU RULES
- [x] AGENTS.md updated with Eternal Shishya framework
- [x] Memory files created/updated (feedback_workflow, feedback_guru_protocol, bugs_frontend_crashes)

---

## BACKLOG RULES
- Tasks stay here until an agent completes them and Guru verifies
- New tasks from `/sprint-plan` get added with priority
- After each sprint, `/self-evolve` reviews and reprioritizes
- Founder approves before agents start any task

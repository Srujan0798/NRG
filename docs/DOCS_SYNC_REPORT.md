# Documentation Sync Report
**Date:** April 21, 2026
**Checked by:** Docs Agent

---

## Summary

| Document | Status | Issues Found |
|---------|--------|-------------|
| `README.md` | ⚠️ Needs Update | 5 factual errors |
| `.claude/CLAUDE.md` | ⚠️ Needs Update | 3 factual errors |
| `docs/ROADMAP.md` | ✅ Current | — |
| `docs/ARCHITECTURE_REVIEW.md` | ✅ Current | — |
| API routes vs main.py | ✅ Accurate | 26 routes match implementation |
| Skill descriptions | ✅ Mostly Accurate | Minor counts need refresh |

---

## README.md — Issues Found

### R1: Database Counts Wrong
**Current (WRONG):**
```
200 Researchers
24 Institutions
500 Publications
50 Labs
100 Funding Records
```

**Actual (from `nrg_research.db`):**
```
5,615 Researchers
181 Institutions
12,000 Publications
889 Labs
15,435 Funding Records
3,000 Patents
5,000 Collaborations
8,049 Projects
```

**Action:** Update README.md lines 114–119 with correct counts.

---

### R2: Cloud Synthesis Default Wrong
**Current (WRONG):**
> "Cloud synthesis is disabled unless `CLOUD_SYNTHESIS_ALLOWED=true`" — implies it's false by default.

**Current `.env`:**
```
CLOUD_SYNTHESIS_ALLOWED=true
```

**Action:** Update README to clarify: Cloud synthesis requires explicit opt-in with `CLOUD_SYNTHESIS_ALLOWED=true` (currently enabled in dev `.env`).

---

### R3: Qdrant/RAG Listed as "NOT Working"
**Current (WRONG — Phase 1 status table):**
> Qdrant/RAG: ⬜ Pending

**Actual:**
- Qdrant is running on `localhost:6333`
- 10,800 chunks indexed
- "quantum computing research" query returns relevant docs with 0.59 score

**Action:** Update Phase 1 status table to mark Qdrant/RAG as wired.

---

### R4: Directory Path Inconsistency
**Current:**
```
cd National-Research-Graph
```

**Actual:**
```
cd /Users/srujansai/Desktop/NRG  # or: NRG/
```

**Action:** Update clone instructions to use actual path.

---

### R5: Testing Command Inconsistency
**Current:**
```
pytest tests/ -v
```

**Actual:** Tests timeout at 120s for full suite. Recommended:
```
pytest tests/ --ignore=tests/e2e/ -q --tb=short
```

**Action:** Update test commands to reflect actual test runner behavior.

---

## .claude/CLAUDE.md — Issues Found

### C1: Test Count Inaccurate
**Current:**
> "481 tests passing, 0 failures"

**Actual:** Full test suite times out at 120s. Partial run shows 291 tests passing in ~44s for orchestration/skills/security. Full count unknown due to timeout.

**Action:** Update to "291+ tests passing (full suite timed out — investigation needed)".

---

### C2: Pipeline Description (Reflector Missing)
**Current:**
> "6-Node LangGraph Pipeline: receiver → planner → router → executor → synthesizer → verifier → END"

**Actual:** Only 5 nodes implemented. Reflector node is not built. See ARCHITECTURE_REVIEW.md.

**Action:** Update to "5-node pipeline (Reflector deferred to Phase 2)" or add note that Reflector is planned.

---

### C3: Skills Count Likely Stale
**Current:**
> "39 Claude + 52 Agent (91 total)"

**Actual:** Skill counts have likely changed. Also: MCP builder was removed per git log "chore: remove mcp-builder + web-design-guidelines (not needed for NRG)".

**Action:** Refresh skill count from actual `.claude/skills/` and `.agents/skills/` directories.

---

## API Routes vs main.py — Verified Accurate

All 26 API routes match the file:

| Route | Method | Status |
|-------|--------|--------|
| `/login` | POST | ✅ |
| `/refresh` | POST | ✅ |
| `/logout` | POST | ✅ |
| `/query` | POST | ✅ |
| `/health` | GET | ✅ |
| `/health/llm` | GET | ✅ |
| `/health/db` | GET | ✅ |
| `/health/qdrant` | GET | ✅ |
| `/health/all` | GET | ✅ |
| `/researchers` | GET | ✅ |
| `/stats` | GET | ✅ |
| `/publications` | GET | ✅ |
| `/projects` | GET | ✅ |
| `/patents` | GET | ✅ |
| `/collaborations` | GET | ✅ |
| `/funding` | GET | ✅ |
| `/labs` | GET | ✅ |
| `/research-documents` | GET | ✅ |
| `/query/graph` | GET | ✅ |
| `/consent` | POST | ✅ |
| `/consent/{scope}` | DELETE | ✅ |
| `/me/consents` | GET | ✅ |
| `/me/data` | GET | ✅ |
| `/me/data` | DELETE | ✅ |
| `/audit/verify` | GET | ✅ |
| `/audit/events` | GET | ✅ |

---

## docs/ROADMAP.md — Verified Accurate
Roadmap correctly reflects completed sprints (A–H), Next items, and Phase 2/3 features.

---

## docs/ARCHITECTURE_REVIEW.md — Verified Accurate
Architecture review correctly identifies:
- 5/6 nodes (Reflector missing)
- LLM_FALLBACK_ORDER ignored
- RBACMiddleware not wired
- Egress guard not active on LLM calls

---

## Recommended Fixes

| Priority | Document | Fix |
|----------|----------|-----|
| P0 | README.md L114-119 | Update DB counts to actual values |
| P0 | README.md Phase 1 | Mark Qdrant/RAG as wired |
| P1 | CLAUDE.md pipeline | Add "5-node (Reflector deferred)" |
| P1 | CLAUDE.md tests | Remove "481 tests" — use actual known count |
| P2 | CLAUDE.md skills | Refresh skill count |
| P2 | README.md cloud synth | Clarify opt-in language |
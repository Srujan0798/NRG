# Agent Assignment AA-001: Demo Readiness — Current State & Task Split

**Date:** 2026-04-25  
**Owner:** User (srujansai) — assign to your agents  
**Status:** Backend running, mesh partially working, frontend unverified

---

## 🟢 CONFIRMED WORKING (Don't touch)

| Component | Status | Details |
|-----------|--------|---------|
| FastAPI Server | ✅ Running | PID 4998, port 8000, Python 3.11 |
| Database | ✅ 5615 researchers, 12000 publications | SQLite `nrg_research.db` |
| Login (all 3 tiers) | ✅ Working | researcher_user, gov_user, industry_user |
| Cloud LLM Mesh | ✅ Works ~60% of time | NVIDIA wins race in ~12-14s, Minimax ~5s |
| Local LLM Fallback | ✅ Working | llama.cpp on port 8080, responds in ~30-45s |
| Rule-based Fallback | ✅ Instant | ASCII tables when both LLMs fail |
| Audit Chain | ✅ Healthy | 385,520 valid events, chain valid |
| Qdrant Container | ✅ Running | Port 6333, but EMPTY — no vectors |

---

## 🟡 KNOWN ISSUES (Agents should fix these)

### Issue 1: Mesh Fails Intermittently After 2-3 Queries
- **Symptom:** First 1-2 queries use cloud_llm synthesis. Query 3+ often times out with "2 (of 2) futures unfinished", falls back to local LLM (~45s) or rule-based.
- **Root Cause:** Unknown. ThreadPoolExecutor in `SovereignLLMMesh` may be entering bad state. Not a timeout issue (NVIDIA responds in 12-14s, budget is 15s).
- **File:** `src/config/llm_config.py`, class `SovereignLLMMesh`, method `generate()` (line ~980)
- **Suggested Fix:** Add future cancellation when a provider wins the race. Increase `max_workers`. Or switch from ThreadPoolExecutor race to `asyncio.gather` with timeouts.

### Issue 2: Server Startup is Fragile
- **Symptom:** `uvicorn src.api.main:app` hangs for 10-15s during Qdrant client import, then starts. If started wrong, it never comes up.
- **Root Cause:** `qdrant_client` import triggers heavy transitive imports (`grpc`, `transformers`, `torch`).
- **File:** `src/api/main.py` line 26
- **Suggested Fix:** Lazy-load QdrantClient inside endpoint functions instead of module level.

### Issue 3: Qdrant is Empty
- **Symptom:** All 19,323 vectors were lost when container was recreated without persistent volume.
- **Impact:** RAG queries fail. Current demo is SQL-only.
- **Suggested Fix:** Re-run ingestion script if source documents exist. Check `scripts/ingest_research_papers.py` or `scripts/ingest_documents.py`.

### Issue 4: Frontend Unverified
- **Symptom:** React frontend builds successfully but has never been tested against live backend.
- **Status:** Unknown if login, query, dashboard data binding, tier differentiation all work.
- **Suggested Fix:** Start frontend (`npm run dev` in `frontend/`), verify all 3 persona flows end-to-end.

### Issue 5: ESLint Warnings
- **Symptom:** 7 warnings remain in frontend (down from 96).
- **Files:** `ResponseRenderer.tsx`, snapshot tests, `ThemeProvider.tsx`, `useAuth.tsx`
- **Suggested Fix:** Fix or suppress remaining warnings.

---

## 📋 TASK ASSIGNMENTS

### Agent A — Backend Mesh Reliability
**Task:** Fix the intermittent mesh failure.  
**Files:** `src/config/llm_config.py`  
**Acceptance Criteria:**
- Run 10 sequential queries via `/query` endpoint
- At least 8/10 must use `cloud_llm` synthesis (not local_llm or rule_based)
- Each query must complete within 20 seconds

### Agent B — Qdrant / RAG Recovery
**Task:** Check if source documents exist and re-ingest vectors if available.  
**Files:** `scripts/ingest_research_papers.py`, `scripts/ingest_documents.py`  
**Acceptance Criteria:**
- `nrg_research` collection exists in Qdrant with >1000 vectors
- RAG queries return chunks, not just SQL results

### Agent C — Frontend Verification
**Task:** Start frontend, verify all 3 persona flows.  
**Files:** `frontend/src/`  
**Acceptance Criteria:**
- `npm run dev` starts without errors
- researcher_user can login and run a query
- gov_user can login and run a query
- industry_user can login and run a query
- Tier differentiation visible in UI (different colors, labels, or data)

### Agent D — Server Startup Hardening
**Task:** Make server startup reliable and fast.  
**Files:** `src/api/main.py`  
**Acceptance Criteria:**
- Server starts within 5 seconds consistently
- Qdrant client is lazy-loaded, not imported at module level
- Server can be started with a simple one-liner that survives terminal close

---

## 🔧 HOW TO VERIFY CURRENT STATE

```bash
# Server health
curl -s http://localhost:8000/health | python3 -m json.tool

# Login (all tiers)
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}'

# Query (get token first, then)
curl -s -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"question":"Top 5 funding agencies"}'
```

---

## 📝 NOTES FOR AGENTS

- Use `.venv/bin/python` for all backend work (Python 3.11)
- Do NOT use system Python 3.14 — it has pydantic compatibility issues
- The server log is at `/tmp/uvicorn.log`
- Local LLM server runs independently on port 8080 (llama.cpp)
- Qdrant runs in Docker on port 6333
- Minimax API key is set and working (responds in ~5s)
- NVIDIA API key is set and working (responds in ~12s)

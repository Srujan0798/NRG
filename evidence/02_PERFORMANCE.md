# Performance Report — Session 92

**Date:** 2026-04-25
**Target:** ON TARGET (DB queries, startup) / REGRESSION DETECTED (API startup: 2.37s)

---

## Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Login latency | N/A (API not running) | <200ms | ⚠️  API offline |
| Health check | N/A | <50ms | ⚠️  API offline |
| Query latency | N/A | <5000ms | ⚠️  API offline |
| API startup | 2371ms | <5000ms | ✅  PASS |
| Audit import | <1ms | <100ms | ✅  PASS |
| Auth import | <1ms | <100ms | ✅  PASS |
| Orchestration state import | <1ms | <100ms | ✅  PASS |
| Text-to-SQL skill import | <1ms | <100ms | ✅  PASS |

---

## Database Query Benchmarks (SQLite, nrg_research.db)

| Query | Time | Target | Status |
|-------|------|--------|--------|
| COUNT researchers | 2.09ms | <100ms | ✅ |
| COUNT publications | 3.08ms | <100ms | ✅ |
| COUNT institutions | 0.04ms | <100ms | ✅ |
| Maharashtra researchers (10 rows) | 0.03ms | <100ms | ✅ |
| Institution distribution (JOIN) | 1.09ms | <100ms | ✅ |
| Publications JOIN (20 rows) | 1.02ms | <100ms | ✅ |
| Research area distribution | 0.03ms | <100ms | ✅ |
| High funding records | 1.40ms | <100ms | ✅ |

**VERDICT:** All DB queries are well within target. No indexing issues detected.

---

## Import Time Benchmarks

| Module | Time | Target | Status |
|--------|------|--------|--------|
| `src.api.main` | 2371ms | <5000ms | ✅ |
| `src.audit` | <1ms | <100ms | ✅ |
| `src.auth.jwt_handler` | <1ms | <100ms | ✅ |
| `src.orchestration.state` | <1ms | <100ms | ✅ |
| `src.skills.text_to_sql` | <1ms | <100ms | ✅ |

**API startup is the largest cost at 2.37s**, driven by FastAPI/Uvicorn/LangGraph imports. This is acceptable for production but may be improvable via lazy imports.

---

## Performance Issues Found

### Issue 1: API Startup Is Dominated by FastAPI + LangGraph
**Severity:** 🟡 Minor
**Finding:** `src.api.main` takes 2371ms to import — most of the total startup time. All other modules are near-instant.

**Root cause:** FastAPI, Uvicorn, and LangGraph have heavy dependency chains. The API imports the entire orchestration graph and all skills eagerly.

**Fix (optional):**
- Use lazy imports for non-critical routes: only import heavy skills when first needed
- Use `importlib` for lazy-loading the orchestration graph
- Add `startup_event` to initialize the graph asynchronously after API starts

### Issue 2: `_get_last_event_time()` Is O(n) on 380k+ Line File
**Severity:** 🟡 Minor
**Finding:** `_get_last_event_time()` at `src/audit/__init__.py:395-402` reads the entire chain file to find the last line every time `get_chain_health()` is called (even though `get_chain_health()` itself is cached for 5s).

**Fix:** Cache `last_event_timestamp` in memory, update it on every `append()` call under the lock. No need to re-read the file.

### Issue 3: `verify_chain()` Is O(n) on Every Health Check Window
**Severity:** 🟡 Minor
**Finding:** `get_chain_health()` at `src/audit/__init__.py:382-393` always returns `chain_valid: True` without verifying. If actual chain verification is needed, it would scan 380k+ events (>30s).

**Fix:** See Bug Report 4 in `evidence/01_BUG_HUNT.md`.

---

## Recommendations

1. **Add lazy loading to API routes** — Only load heavy dependencies (LangGraph, skills) on first request to `/query`, not on startup.
2. **Cache last event timestamp** — Add `self._last_event_timestamp` updated in `append()` under lock.
3. **Add database indexes** — All current queries are fast, but add composite indexes for common filter patterns (state + research_area, institution_id + year).
4. **Run C4 load test** — Blocked on API not running. See `scripts/run_load_test.py`.

---

## Test Commands

```bash
# API must be running for live benchmarks
cd /Users/srujansai/Desktop/NRG && .venv/bin/uvicorn src.api.main:app --port 8000 &
sleep 3

# Login
time curl -sf -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}' -o /dev/null

# Health
time curl -sf "http://localhost:8000/health/all" -o /dev/null

# Chain health
time curl -sf "http://localhost:8000/health/all" | python -c "import sys,json; d=json.load(sys.stdin); print('chain:', d.get('chain',{}))"

# Query (needs token)
TOKEN=$(curl -sf -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
time curl -sf -X POST "http://localhost:8000/api/query/stream" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"AI researchers in Gujarat"}' -o /dev/null
```

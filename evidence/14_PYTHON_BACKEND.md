# Python Backend Review — NRG API

**Date:** 2026-04-25
**File:** `src/api/main.py` (2499 lines)
**Reviewer:** Session 92 Agent (python-backend skill)

---

## Critical Issues

### Issue 1: SQL Injection at Line 479 — Already Reported (CRITICAL)
**File:** `src/api/main.py:479` — raw string interpolation in SQL query

See `evidence/10_SECURITY_AUDIT.md` for full report.

---

### Issue 2: Monolithic `main.py` — 2499 Lines
**Severity:** ⚠️ High (Architecture)

FastAPI best practice: Split into domain-based routers. Current structure:
```
src/api/main.py  ← 2499 lines (too large!)
```

**Fix:** Extract routers:
```
src/api/
  main.py              # App init, middleware, lifespan
  routers/
    auth.py           # /auth/*
    query.py          # /query/*
    data.py            # /researchers, /publications, /stats
    admin.py           # /admin/*
    audit.py           # /audit/*
  middleware/
    security.py
    quota.py
```

---

### Issue 3: `_APIMemoryCache` Reimplementing TTL Cache
**Severity:** 🟡 Medium (Code Quality)

**File:** `src/api/main.py:114-183`

Custom TTL cache implementation instead of using `cachetools` or `stdlib` `functools.lru_cache`:

```python
# Current: custom _APIMemoryCache (50 lines)
class _APIMemoryCache:
    def __init__(self, default_ttl: int = 30):
        self._store: dict[str, tuple[float, Any]] = {}

# Better: use cachetools
from cachetools import TTLCache
_api_cache = TTLCache(maxsize=1000, ttl=30)
```

Benefits: thread-safe, tested, has `__contains__`, `pop()`.

---

### Issue 4: No Pagination on `/researchers` and `/publications`
**Severity:** ⚠️ Medium (Performance)

**File:** `src/api/main.py` (search for `GET /researchers`)

```python
# Current: returns all researchers
# Better:
@router.get("/researchers")
async def get_researchers(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
```

---

### Issue 5: No Global Exception Handler
**Severity:** 🟡 Medium (Robustness)

FastAPI best practice: Add a global exception handler for consistent error responses.

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request.headers.get("X-Request-ID")}
    )
```

---

## Passed Checks ✅

- ✅ Async context manager for lifespan (`asynccontextmanager`)
- ✅ Proper HTTPException usage for error responses
- ✅ Pydantic models (`LoginRequest`, `RefreshRequest`) for input validation
- ✅ Background task for heavy operations (audit logging)
- ✅ CORS middleware configured
- ✅ GZip middleware configured
- ✅ Security headers middleware
- ✅ Request logging middleware with request ID
- ✅ Dependency injection for `JWTHandler`
- ✅ Proper async/await on I/O operations

---

## Recommendations

| Priority | Issue | Fix |
|----------|-------|-----|
| P0 | SQL injection | Parameterize query at line 479 |
| P1 | Monolithic main.py | Extract routers |
| P2 | Custom cache | Use `cachetools.TTLCache` |
| P2 | No pagination | Add `limit`/`offset` params |
| P3 | No global exception handler | Add `@app.exception_handler(Exception)` |

# Backend Patterns Analysis: Node.js Best Practices Applied to NRG Python API

**Skill**: `nodejs-backend-patterns`
**Date**: 2026-04-25
**Analyst**: Eternal Shishya
**Evidence File**: `evidence/15_PYTHON_BACKEND_PATTERNS.md`

---

## 1. Architecture: Monolithic vs Layered

### Finding: 2,499-line monolith (`src/api/main.py`)

The entire NRG API — auth, queries, ingestion, admin, DPDP compliance — lives in a single file with no controller/service/repository separation. The Node.js skill prescribes:

```
src/
├── controllers/     # HTTP request/response
├── services/        # Business logic
├── repositories/    # Data access
├── middleware/      # Express/Fastify middleware
├── routes/          # Route definitions
└── config/          # Configuration
```

**NRG Reality:**
- All 50+ endpoints defined directly on `FastAPI` app instance
- Business logic mixed with HTTP concerns (e.g., `login()` endpoint contains brute-force check, JWT issuance, consent grant, and rate limiting all in one function)
- Database queries inlined in route handlers (e.g., `/query/graph` has 80+ lines of SQL inside the endpoint)
- No separation between "how we receive data" and "what we do with data"

**Severity**: HIGH — maintainability, testability, and reusability all suffer.

### Action Items
- [ ] Extract `AuthController` / `AuthService` for login/logout/refresh
- [ ] Extract `QueryController` / `QueryService` for `/query`, `/query/stream`, `/query/graph`
- [ ] Extract `IngestionController` / `IngestionService` for async document ingestion
- [ ] Extract `AdminController` for RBAC, SLO, audit endpoints
- [ ] Extract `DPDPController` for consent/erasure/export
- [ ] Move all `db.query_*()` calls to `src/data/repositories/`
- [ ] Introduce FastAPI `APIRouter` for route grouping

---

## 2. Dependency Injection: Global Singletons vs DI Container

### Finding: Module-level globals + inline instantiation

The Node.js skill shows a proper DI container with `register()`, `resolve()`, and `singleton()`. NRG uses:

```python
# main.py:189-202
_db_instance: NRGDatabaseV2 | None = None
def _get_db() -> NRGDatabaseV2:
    global _db_instance
    if _db_instance is None:
        url = f"sqlite:///{resolve_database_path()}"
        _db_instance = NRGDatabaseV2(url=url)
        _db_instance.create_tables()
    return _db_instance

workflow = NRGWorkflow()          # module-level, eagerly created
jwt_handler = JWTHandler()         # module-level, eagerly created
_api_cache = _APIMemoryCache()     # module-level
```

Services are also instantiated inline:
```python
# e.g., main.py:333-336
from src.services.consent import ConsentService
consent_service = ConsentService()  # created per-request in login endpoint
```

**Problems:**
1. **Eager initialization**: `workflow = NRGWorkflow()` runs at import time — if LangGraph init fails, the entire API crashes
2. **No substitution for testing**: Cannot inject a mock `NRGDatabase` without patching globals
3. **Inline instantiation**: `ConsentService()` created inside route handlers — inconsistent lifecycle

**Severity**: MEDIUM — works but not testable or swappable.

### Action Items
- [ ] Lazy initialization for all heavy dependencies (LangGraph, database)
- [ ] Use FastAPI's `Depends()` for request-scoped dependencies
- [ ] Create a `Container` class or use `fastapi.Depends` with factory functions

---

## 3. Error Handling: Custom Error Classes + Global Handler

### Finding: No custom error hierarchy; raw `str(e)` leaks details

The Node.js skill shows proper `AppError` subclasses with `statusCode`, `isOperational`, and a global error handler:

```typescript
// utils/errors.ts
export class AppError extends Error {
  constructor(
    public message: string,
    public statusCode: number = 500,
    public isOperational: boolean = true,
  ) { ... }
}
export class ValidationError extends AppError { ... }
export class NotFoundError extends AppError { ... }
export class UnauthorizedError extends AppError { ... }
```

**NRG Reality:**

```python
# main.py:687-689 — raw exception in query endpoint
except Exception as e:
    logger.error(f"Workflow execution error: {e}")
    raise HTTPException(status_code=500, detail=str(e))  # leaks internal details!
```

```python
# main.py:379 — AuthError string conversion
except AuthError as exc:
    raise HTTPException(status_code=401, detail=str(exc))  # leaks JWT details
```

```python
# main.py:329 — same pattern
raise HTTPException(status_code=401, detail=str(exc)) from exc
```

**Problems:**
1. `str(AuthError)` exposes internal JWT payload details (see `jwt_handler.py` — `AuthError` uses `str(exc)` which includes JWT-specific messages)
2. No `AppError`-equivalent — can't distinguish operational vs programming errors
3. No global exception handler middleware — each endpoint handles errors individually
4. `HTTPException(detail=str(e))` in 10+ endpoints leaks stack traces, file paths, SQL details

**Severity**: HIGH — information disclosure.

### Action Items
- [ ] Create `src/api/errors.py` with `APIError`, `ValidationError`, `NotFoundError`, `UnauthorizedError`, `ForbiddenError`, `ConflictError` classes
- [ ] Add `error_handler` middleware to `src/api/middleware/error_handler.py`
- [ ] Replace all `str(e)` in `detail=str(exc)` with `str(exc.message)` or dedicated error messages
- [ ] Ensure `AuthError.__str__` never exposes JWT payload internals

---

## 4. Caching: Custom In-Memory vs Redis-Backed CacheService

### Finding: `_APIMemoryCache` has no size limit; no TTL cleanup thread

The Node.js skill shows a `CacheService` backed by Redis with explicit TTL. NRG's cache:

```python
# main.py:114-186
class _APIMemoryCache:
    def __init__(self, default_ttl: int = 30):
        self._store: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl
    # No max size — dict grows unbounded
    # No background cleanup thread — expired entries only cleaned on access
```

**Problems:**
1. **Unbounded growth**: `_store` dict has no max items — with 382k audit events and diverse queries, this can grow to gigabytes
2. **No background eviction**: Only cleans expired entries on next `get()` — entries accumulate
3. **No Redis fallback**: If `_get_redis()` returns None, rate limiter falls back gracefully but cache always uses in-memory
4. **Security Finding (from Skill 7)**: Cache not invalidated on JWT refresh — old cached responses may be served to new token holder

**Severity**: MEDIUM — memory exhaustion risk.

### Action Items
- [ ] Add max size with LRU eviction (`cachetools.TTLCache` or `cachetools.LRUCache`)
- [ ] Add background cleanup task for expired entries
- [ ] Replace with Redis-backed cache for production (already available via `src.caching.redis_layer`)
- [ ] Invalidate cache on token revocation

---

## 5. Authentication Middleware: Good Pattern, Leaky Error Messages

### Finding: `AuthContextMiddleware` is well-structured; `AuthError` is not

The middleware in `src/auth/middleware.py:164-193` follows the correct pattern — decodes JWT, attaches claims to `request.state`, handles `AuthError` gracefully. Good.

```python
# middleware.py:182-191
try:
    claims = self.jwt_handler.verify_access_token(token, client_ip=client_ip)
    request.state.auth_claims = claims
    request.state.rbac_policy = self._engine.resolve_tier_or_persona(claims)
except AuthError:
    request.state.auth_claims = None  # silently pass through for public endpoints
    request.state.rbac_policy = None
```

However, downstream endpoints re-raise `AuthError` with `str(exc)`:

```python
# main.py:310
except AuthError as exc:
    raise HTTPException(status_code=401, detail=str(exc))  # BAD — leaks JWT details
```

**Severity**: MEDIUM (information disclosure).

### Action Items
- [ ] `AuthError.__str__` should return only `"Invalid or expired token"` — never the underlying JWT details
- [ ] Add `AuthenticationError` subclass for auth-specific errors with sanitized messages

---

## 6. Rate Limiting: Well-Implemented

### Finding: Redis-backed tiered rate limiter matches Node.js patterns

The `src/security/rate_limiter.py` implementation is **excellent**:
- Redis sorted sets with sliding window
- Per-tier limits (100/200/50 req/min)
- Per-endpoint limits
- X-RateLimit headers on all responses
- Test mode bypass
- Pipeline operations (atomic)

This matches or exceeds the Node.js skill's `rateLimit` example.

**Strength**: Can be used as a reference for other services.

### Action Items
- None — already production-quality.

---

## 7. Database Patterns: Connection Pool + Transactions

### Finding: SQLAlchemy session per request; transactions in graph query

Good pattern in `/query/graph` endpoint (main.py:1730):

```python
with db.get_session() as session:
    from sqlalchemy import text as sa_text
    result = session.execute(rcte, {"pattern": topic_pattern, "max_depth": depth})
    ...
```

**Critical Issue**: SQL injection at line 479 (from Skill 12):

```python
# main.py:479 — NEVER DO THIS
sql_results = db.execute_query(
    f"SELECT * FROM researchers WHERE research_area LIKE '%{request.query.split()[0]}%' LIMIT 10",
    ...
)
```

**Missing patterns:**
- No explicit transaction wrapper for multi-step operations (ingestion could benefit)
- No connection pool health monitoring (only `_get_db_pool_stats()` in metrics)
- No query timeout enforcement
- No prepared statement reuse

**Severity**: CRITICAL (confirmed SQL injection).

### Action Items
- [ ] Fix SQL injection at line 479 — use parameterized query
- [ ] Add `query_timeout` to SQLAlchemy engine config
- [ ] Add explicit transaction context manager for multi-step operations

---

## 8. API Response Format: Inconsistent Across Endpoints

### Finding: No standardized `ApiResponse` wrapper

The Node.js skill shows:
```typescript
ApiResponse.success(res, data, message, 200)
ApiResponse.error(res, message, statusCode, errors)
ApiResponse.paginated(res, data, page, limit, total)
```

**NRG Reality**: Every endpoint returns its own format:

```python
# login returns: {**tokens, "user": {...}, "rate_limit": {...}}
# query returns: {query_id, audit_event_id, response, status, tier, intent, ...}
# researchers returns: list directly (not wrapped)
# stats returns: {total_researchers, total_publications, ...}  # different shape
# graph returns: {nodes, edges, query, depth, tier}
```

This makes client SDK generation difficult and API documentation inconsistent.

**Severity**: MEDIUM — API ergonomics issue.

### Action Items
- [ ] Create `src/api/schemas.py` with `SuccessResponse`, `ErrorResponse`, `PaginatedResponse` Pydantic models
- [ ] Wrap all endpoints with standardized response format
- [ ] Document response shapes in OpenAPI schema

---

## 9. Validation: Pydantic Used Correctly, But Schema Validation Missing

### Finding: Request models use Pydantic; query validation is custom

```python
# main.py:400-410
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    @model_validator(mode="before")
    def accept_question_alias(cls, data): ...  # good backward compat
```

But query security validation is custom:
```python
# main.py:432-434
validation = prompt_sanitiser.validate_query({"query": request.query})
if not validation["valid"]:
    raise HTTPException(status_code=400, detail=f"Security violation: {validation['reason']}")
```

**Positive**: Pydantic `model_validator` for backward compatibility is a good pattern.

**Missing**: No request/response schema validation (no FastAPI `response_model` annotations on most endpoints).

### Action Items
- [ ] Add `response_model` to all endpoints returning typed data
- [ ] Add request `model_validate` for all POST bodies
- [ ] Consider using `FastAPI` `Body` schema with `珡.Field()` for documentation

---

## 10. Middleware Stack: Well-Designed

### Finding: Correct middleware ordering

```python
# main.py:251-262
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(GZipMiddleware)
app.add_middleware(RequestLoggingMiddleware)   # ← logs after routing
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuthContextMiddleware, ...)
app.add_middleware(PromptSanitiserMiddleware)
```

This ordering is **correct**: CORS and GZip first (work on raw bytes), SecurityHeaders next, AuthContext decodes JWT, PromptSanitiser validates input.

**Strength**: Middleware design is solid.

---

## 11. Graceful Shutdown: Insufficient Drain

### Finding: 0.5s drain timeout

```python
# main.py:215-218
async def drain_connections():
    await asyncio.sleep(0.5)  # too short for production
```

In production with active connections, 0.5s is insufficient for:
- In-flight query completions
- Vector store batch uploads completing
- Audit log flush

**Severity**: MEDIUM — potential audit log gaps on shutdown.

### Action Items
- [ ] Increase drain timeout to 30s with proper connection tracking
- [ ] Add `asyncio.Event` to signal in-flight requests to complete
- [ ] Add shutdown sequence: pause new requests → wait for in-flight → flush audit → exit

---

## 12. Pagination: Inconsistent `limit`/`offset` but no cursor pagination

### Finding: All list endpoints use `limit`/`offset` — no cursor

```python
# main.py:1418-1432 — researchers
limit: int = 50,
offset: int = 0,
```

**Problems:**
1. `offset` pagination is O(n) and inconsistent at scale
2. No `X-Total-Count` or `X-Total-Pages` headers
3. No maximum `limit` enforcement (client can request `limit=1000000`)

**Severity**: LOW — works but not scalable.

### Action Items
- [ ] Add `X-Total-Count` header to all list responses
- [ ] Add maximum `limit` cap (e.g., 1000)
- [ ] Consider cursor-based pagination for high-volume endpoints

---

## 13. RBAC: Policy Engine Is Sophisticated

### Finding: `src/auth/rbac.py` with `RBACPolicyEngine` — excellent layered approach

This is a **strength** — the RBAC engine separates policy from enforcement:
- `filter_researcher_records()` uses policy-driven column visibility
- `get_policy()` returns typed policy objects
- Personas are hot-swappable at runtime

This architecture is better than most Node.js implementations that hardcode role checks.

**Strength**: Can serve as a reference implementation.

---

## 14. Health Checks: Fragmented

### Finding: 7 health endpoints instead of one unified

- `/health` — overall
- `/health/llm` — LLM provider
- `/health/db` — database
- `/health/qdrant` — vector store
- `/health/all` — all services
- `/api/providers/health` — LLM mesh
- `/api/vectors/health` — detailed vector stats

**Node.js skill says**: Implement health checks for monitoring.

**NRG Reality**: Over-fragmented — client must call 7 endpoints to get full picture. `/health/all` exists but is not used by load balancers (they use `/health`).

**Severity**: LOW — operational inconvenience.

### Action Items
- [ ] Enhance `/health` to include all service statuses in one response
- [ ] Add `healthy`/`degraded`/`unhealthy` aggregate status to `/health`

---

## 15. Global Exception Handler

### Finding: Missing

The Node.js skill shows a dedicated error handler middleware. FastAPI supports this via `@app.exception_handler`:

```python
# Not present in main.py — should be added
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )
```

Currently every endpoint handles errors individually, leading to inconsistent error formats.

### Action Items
- [ ] Add global exception handlers for `HTTPException`, `ValidationError`, and `Exception`
- [ ] Ensure all errors return `{"status": "error", "message": ..., "code": ...}`

---

## Summary Table

| Pattern | Status | Severity |
|---------|--------|----------|
| Layered Architecture | ❌ Monolith (2499-line file) | HIGH |
| Dependency Injection | ⚠️ Globals + inline instantiation | MEDIUM |
| Error Handling | ❌ No custom errors, `str(e)` leaks | HIGH |
| Caching | ⚠️ Unbounded in-memory cache | MEDIUM |
| Auth Middleware | ✅ Good structure, leaky errors | MEDIUM |
| Rate Limiting | ✅ Excellent Redis implementation | — |
| DB Connection Pool | ✅ SQLAlchemy sessions | — |
| DB Transactions | ⚠️ SQL injection at line 479 | CRITICAL |
| API Response Format | ❌ Inconsistent across endpoints | MEDIUM |
| Pydantic Validation | ✅ Good use of model_validator | — |
| Middleware Stack | ✅ Correct ordering | — |
| Graceful Shutdown | ⚠️ 0.5s drain too short | MEDIUM |
| Pagination | ⚠️ offset-based, no total headers | LOW |
| RBAC Engine | ✅ Sophisticated policy engine | — |
| Health Checks | ⚠️ Over-fragmented | LOW |
| Global Exception Handler | ❌ Missing | MEDIUM |

---

## Top 5 Priority Fixes

1. **CRITICAL**: Fix SQL injection at `main.py:479` — parameterized query
2. **HIGH**: Replace `str(exc)` leaks with sanitized error messages in `AuthError` and all endpoint `except` blocks
3. **HIGH**: Add `AppError` hierarchy + global exception handler
4. **HIGH**: Add size limit to `_APIMemoryCache` (use `cachetools.TTLCache`)
5. **MEDIUM**: Extract service layer from monolith (begin with auth + query)

---

## References

- Node.js Backend Patterns SKILL.md: `.agents/skills/nodejs-backend-patterns/SKILL.md`
- Advanced Patterns: `.agents/skills/nodejs-backend-patterns/references/advanced-patterns.md`
- Original Python Backend audit: `evidence/14_PYTHON_BACKEND.md`

# Sprint Plan — Skills Session Integration Sprint

**Date**: 2026-04-25
**Duration**: 2 weeks
**Goal**: Triage all 17 evidence files from skills session; fix CRITICAL/HIGH findings; close tech debt; verify frontend accessibility; document remaining work.
**Quality Bar Target**: C1✅ C2✅ C3✅ C6✅ (C4⏳ C5⏳ remain cluster-dependent)

---

## Sprint Goal

Fix all CRITICAL and HIGH severity findings discovered during the comprehensive skills review (17 evidence files). Close the SQL injection, error handling leaks, unbounded cache, and Dockerfile root issues. Extract actionable P1 items for next sprint.

---

## Quality Bar Target Delta

| Constraint | Current | Sprint Target | Gap |
|---|---|---|---|
| C1 DPDP Indian PII | ✅ PASS | Maintain | None |
| C2 Per-user audit binding | ✅ PASS | Maintain | None |
| C3 Multi-hop planner | ✅ PASS | Maintain | None |
| C4 P99 SLO @ 1000 users | ⏳ Cluster | No change | Cluster required |
| C5 Vector drift | ⏳ Cluster | No change | Cluster required |
| C6 Schema allowlist | ✅ PASS | Maintain | None |

**This sprint does not move Quality Bar** — all findings are P1/P2 operational fixes outside the 6 constraints.

---

## P1 — Must Complete

| # | Task | Verb | Agent | Files | Acceptance Criteria |
|---|------|------|-------|-------|---------------------|
| SP-01 | SQL Injection Fix | REWRITE | backend | `src/api/main.py:479` | Parameterized query replaces raw f-string; no SQL in `execute_query` uses string interpolation; regression test added |
| SP-02 | AuthError Message Sanitization | REWRITE | backend | `src/auth/jwt_handler.py`, `src/api/main.py` | `AuthError.__str__` never exposes JWT payload; all `detail=str(exc)` replaced with sanitized messages |
| SP-03 | Global Exception Handler | BUILD-NEW | backend | `src/api/middleware/error_handler.py` | `AppError` hierarchy added; global handler registered in `main.py`; all endpoints return `{"status": "error", "message": ...}` format |
| SP-04 | Unbounded Cache Fix | REWRITE | backend | `src/api/main.py` (`_APIMemoryCache`) | Add `maxsize=1000` with LRU eviction; add `TTL` cleanup; or replace with `cachetools.TTLCache` |
| SP-05 | Dockerfile.frontend USER Directive | REWRITE | devops | `Dockerfile.frontend` | nginx no longer runs as root; `USER node` or `USER 1000` added before nginx startup |

---

## P2 — Should Complete

| # | Task | Verb | Agent | Files | Acceptance Criteria |
|---|------|------|-------|-------|---------------------|
| SP-06 | Backend Layered Architecture (Phase 1) | REWRITE | backend | `src/api/main.py` | Extract AuthService + QueryService from main.py; router file created for auth endpoints; main.py reduced by ≥400 lines |
| SP-07 | API Response Standardization | REWRITE | backend | `src/api/schemas.py` | `SuccessResponse`, `ErrorResponse`, `PaginatedResponse` Pydantic models created; all list endpoints return consistent format |
| SP-08 | Evidence Files Triaged to BACKLOG | BUILD-NEW | backend | `BACKLOG.md` | All 17 evidence files reviewed; findings converted to P1/P2/P3 backlog entries; BACKLOG.md updated |
| SP-09 | Graceful Shutdown Drain Timeout | REWRITE | backend | `src/api/main.py` | Drain timeout increased to 30s; in-flight request counter added; audit flush before exit |
| SP-10 | Pagination Total Headers | REWRITE | backend | `src/api/main.py` (all list endpoints) | `X-Total-Count` added to all list responses; `limit` capped at 1000 |

---

## P3 — Stretch (if time)

| # | Task | Verb | Agent | Files | Acceptance Criteria |
|---|------|------|-------|-------|---------------------|
| SP-11 | Frontend END-to-END Verification | BUILD-NEW | frontend | `frontend/src/` | Full Playwright smoke test: login → query → logout; all 3 tier dashboards verified accessible |
| SP-12 | ADR-006 + ADR-007 Implementation | REWRITE | backend | `src/audit/` | ADR-006 file locking implemented; ADR-007 TPM protocol spec reviewed by Guru |
| SP-13 | Test Suite Timeouts | REWRITE | testing | `pytest.ini`, `conftest.py` | `@pytest.mark.slow` applied to tests >10s; `pytest-xdist` configured; full suite completes in <180s |

---

## Dependencies

```
SP-01 (SQL injection) blocks nothing — fix immediately
SP-02 (AuthError) blocks SP-03 (exception handler uses same pattern)
SP-03 (error handler) independent
SP-04 (cache) independent
SP-05 (Dockerfile) independent
SP-06 (layered arch) depends on SP-03 (clean error handling in place)
SP-07 (API responses) depends on SP-03
SP-08 (evidence triage) independent
SP-09 (graceful shutdown) independent
SP-10 (pagination headers) independent
```

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-------------|--------|------------|
| SP-06 (layered arch) disrupts live API | HIGH | HIGH | Extract only auth + query first; keep main.py as fallback; full extraction in SP-14 |
| Test suite times out during verification | MEDIUM | MEDIUM | Use `PYTEST_CURRENT_TEST=1` flags; run targeted suites first |
| Qdrant remains unhealthy blocking vector tests | HIGH | LOW | Not a blocker for this sprint; document in evidence |
| Frontend build fails after accessibility fixes | LOW | MEDIUM | Verify `npm run build` passes before any frontend work |

---

## Lethal Assumption This Sprint Is Betting On

**The SQL injection at line 479 has not been exploited in production.** If it has been, this sprint must pivot to incident response (rollback + audit log review + PII exposure check) before any other work. Guru must confirm chain integrity before SP-01 begins.

---

## Task Protocols (SP-01 through SP-05)

Below are the full ═══ protocols for each P1 task. These are copy-paste-ready for agent execution.

---

## SP-01: SQL Injection Fix

**GURU ASSIGNMENT NOTE**: A raw f-string SQL injection vulnerability exists at `src/api/main.py:479` — `f"SELECT * FROM researchers WHERE research_area LIKE '%{request.query.split()[0]}%' LIMIT 10"`. This was identified during the skills session security audit and is CRITICAL. An attacker can submit `'; DROP TABLE researchers; --` as a query to corrupt or destroy data. Fix immediately. This is not a theoretical vulnerability — it is exploitable right now.

**PHASED ACTION**:

### Fortify (MUST do)
- Replace the f-string interpolation with a parameterized query using `db.execute_query` with `?` placeholders and a tuple of parameters
- Verify no other raw f-string SQL exists in `main.py` (grep for `f"SELECT`, `f"INSERT`, `f"UPDATE`, `f"DELETE`)
- Add a regression test in `tests/security/test_sql_injection_regression.py` that sends the DROP TABLE payload and asserts the table still exists

### Elevate
- Create `src/api/sql_injection_audit.py` — a static scanner that greps all `.py` files for raw SQL string interpolation patterns (`f"SELECT`, `f"INSERT`, `f"UPDATE`, `f"DELETE`, `f"WITH RECURSIVE`)
- Run the scanner against the entire codebase and document findings
- Add this scanner to pre-commit hooks

### Immortalize
- Add SQLFluff or Semgrep rule to `.semgrep/rules/sql-injection.yaml` that blocks raw string interpolation in SQL context in CI

**SKILLS**: `security-auditor` (confirm vulnerability), `python-backend` (implement fix), `test-suite` (add regression test)

**AGENT INSTRUCTIONS**:
```
You are the Eternal Shishya. Execute SP-01 following the ═══ protocol above.
1. Read src/api/main.py around line 479 — confirm the injection point
2. Fix with parameterized query
3. Grep entire codebase for similar patterns
4. Write regression test
5. Run pre-commit before committing
```

**ACCEPTANCE CRITERIA**:
- [ ] `request.query.split()[0]` never appears inside an f-string SQL query
- [ ] `tests/security/test_sql_injection_regression.py` passes with the DROP TABLE payload
- [ ] `git grep -n 'f"SELECT\|f"INSERT\|f"UPDATE\|f"DELETE' src/` returns zero results (except in tests with intentionally clean data)
- [ ] pre-commit passes

---

## SP-02: AuthError Message Sanitization

**GURU ASSIGNMENT NOTE**: `AuthError` from `src/auth/jwt_handler.py` is converted to string and placed in `HTTPException.detail` in 10+ endpoints. The `__str__` method of `AuthError` exposes internal JWT details (algorithm, payload fields, expiry). This is an information disclosure vulnerability — an attacker who gets a 401 can learn JWT structure. Fix: `AuthError.__str__` must return only `"Invalid or expired token"`. Then audit all places that use `str(exc)` on auth errors.

**PHASED ACTION**:

### Fortify
- Edit `src/auth/jwt_handler.py` — find `AuthError` class, modify its `__str__` to return a static message
- Audit all `except AuthError as exc: raise HTTPException(status_code=401, detail=str(exc))` in `main.py` and replace `str(exc)` with `"Invalid or expired token"`
- Audit all other `except Exception as e: raise HTTPException(..., detail=str(e))` in `main.py` and replace with a generic `"Internal server error"` (never expose internal error text to clients)

### Elevate
- Create `src/api/errors.py` with `APIError`, `ValidationError`, `NotFoundError`, `UnauthorizedError`, `ForbiddenError` classes
- Each error class has a `user_message` attribute (safe to show) vs `internal_message` (for logging only)
- Update all endpoint `except` blocks to use these new error classes

### Immortalize
- Add pre-commit hook: no `detail=str(` anywhere in main.py or endpoints
- Add Semgrep rule: `python.lang.security.exposed-error-message`

**SKILLS**: `security-auditor` (verify fix), `python-backend` (implement changes), `code-review` (review all str(exc) usages)

**AGENT INSTRUCTIONS**:
```
You are the Eternal Shishya. Execute SP-02 following the ═══ protocol above.
1. Read src/auth/jwt_handler.py — find AuthError class and modify __str__
2. Read src/api/main.py — find all AuthError and Exception except blocks
3. Replace all str(exc) with safe messages
4. Create src/api/errors.py with proper error hierarchy
5. Run pre-commit
```

**ACCEPTANCE CRITERIA**:
- [ ] `AuthError.__str__` returns `"Invalid or expired token"` (static string, no f-string, no variable interpolation)
- [ ] Zero `detail=str(exc)` or `detail=str(e)` in main.py after fix
- [ ] All auth-related HTTP 401 responses contain no JWT algorithm, payload, or expiry information
- [ ] pre-commit passes

---

## SP-03: Global Exception Handler

**GURU ASSIGNMENT NOTE**: NRG has no global exception handler. Each of the 50+ endpoints handles errors individually, leading to inconsistent response formats, leaked internal details, and unhandled exceptions crashing the worker. FastAPI supports `@app.exception_handler()` — use it. The Node.js skill shows exactly how: a middleware that catches `AppError` subclasses and returns `{"status": "error", "message": ...}`. This is a fundamental production-readiness gap.

**PHASED ACTION**:

### Fortify
- Create `src/api/errors.py` with `APIError`, `ValidationError`, `NotFoundError`, `UnauthorizedError`, `ForbiddenError`, `ConflictError` classes (if not done in SP-02, combine)
- Create `src/api/middleware/error_handler.py` with global exception handlers for `HTTPException`, `APIError`, and generic `Exception`
- Register handlers in `main.py` using `@app.exception_handler()`
- Ensure all error responses return `{"status": "error", "message": "...", "code": "..."}`

### Elevate
- Standardize error `code` field across all errors (e.g., `AUTH_001`, `VALIDATION_001`, `RATE_LIMIT_001`)
- Add `X-Error-Code` header to error responses for API consumers
- Document error codes in `docs/handover/API_REFERENCE.md`

### Immortalize
- Add error code registry to track all error codes across the codebase
- Add error code to audit log on every API error

**SKILLS**: `python-backend` (implement error hierarchy), `nodejs-backend-patterns` (reference global error handler pattern), `documentation` (document error codes)

**AGENT INSTRUCTIONS**:
```
You are the Eternal Shishya. Execute SP-03 following the ═══ protocol above.
1. Create src/api/errors.py with error classes (combine with SP-02 if not done)
2. Create src/api/middleware/error_handler.py with global handlers
3. Register handlers in main.py
4. Update any existing error responses to use new format
5. Run pre-commit
```

**ACCEPTANCE CRITERNS**:
- [ ] `src/api/errors.py` exists with 6+ error classes
- [ ] `src/api/middleware/error_handler.py` exists with global exception handler
- [ ] Global handler registered in `main.py` lifespan
- [ ] All error responses return `{"status": "error", "message": "...", "code": "..."}`
- [ ] Zero `detail=str(exc)` or `detail=str(e)` in any endpoint after fix
- [ ] pre-commit passes

---

## SP-04: Unbounded Cache Fix

**GURU ASSIGNMENT NOTE**: `_APIMemoryCache` in `main.py:114-186` has no maximum size limit. The dict grows unbounded as queries are made. With 382k+ audit events and diverse query cache keys, this can consume gigabytes of RAM. Use `cachetools.TTLCache` which provides both size limits and TTL enforcement with background eviction.

**PHASED ACTION**:

### Fortify
- Replace `_APIMemoryCache` class with `cachetools.TTLCache(maxsize=1000, ttl=300)` (5-minute TTL, 1000 entry max)
- Verify `cachetools` is already a dependency (check requirements.txt/setup.py); if not, it is a single-file package we can vendor
- Update all cache calls to use the same interface (`cache.get(key)`, `cache.set(key, value, ttl=30)`)

### Elevate
- Add cache metrics to `/api/metrics`: hit rate, current size vs max size, eviction count
- Add cache key normalization (already partially done in `_normalize_query_for_cache`) to improve hit rate

### Immortalize
- Add cache TTL jitter (±10% random TTL) to prevent thundering herd on cache expiry
- Add cache stampede protection (singleflight pattern) for expensive queries

**SKILLS**: `python-backend` (implement fix), `performance` (benchmark cache impact), `nodejs-backend-patterns` (reference CacheService pattern)

**AGENT INSTRUCTIONS**:
```
You are the Eternal Shishya. Execute SP-04 following the ═══ protocol above.
1. Check if cachetools is in requirements.txt or setup.py
2. Replace _APIMemoryCache with cachetools.TTLCache in main.py
3. Update cache interface calls if needed
4. Add cache stats to /api/metrics endpoint
5. Run pre-commit
```

**ACCEPTANCE CRITERIA**:
- [ ] `_APIMemoryCache` replaced with bounded cache
- [ ] `maxsize=1000` (or configurable via env var)
- [ ] TTL of 300 seconds enforced
- [ ] No unbounded dict growth under load
- [ ] pre-commit passes

---

## SP-05: Dockerfile.frontend USER Directive

**GURU ASSIGNMENT NOTE**: `Dockerfile.frontend` runs nginx as the root user. nginx running as root inside a container is a security risk — if nginx is exploited, the attacker has root on the container. The Node.js skill's Docker best practices (and CIS Docker Benchmark) require running containers as non-root. Add a `USER` directive before nginx starts.

**PHASED ACTION**:

### Fortify
- Edit `Dockerfile.frontend` — add `USER node` before nginx startup (node user exists in the image)
- If node user doesn't exist, create it: `RUN useradd -m node && usermod -s /bin/bash node`
- Verify nginx can still access static files owned by the node user

### Elevate
- Add `HEALTHCHECK` directive to `Dockerfile.frontend` (currently only `Dockerfile.api` has one)
- Add `RUN microdnf clean all` or `apt-get clean` to reduce image size
- Document non-root requirement in dockerfile comments

### Immortalize
- Add Dockerfile to hadolint CI check (if not already present)
- Add non-root check to pre-commit

**SKILLS**: `dockerfile-validator` (already confirmed issue exists), `nodejs-backend-patterns` (reference Dockerfile security), `security-audit` (verify fix)

**AGENT INSTRUCTIONS**:
```
You are the Eternal Shishya. Execute SP-05 following the ═══ protocol above.
1. Read Dockerfile.frontend
2. Find where nginx is started
3. Add USER node (or create node user) before nginx startup
4. Verify nginx can still serve static files
5. Run dockerfile-validator skill to confirm fix
6. Run pre-commit
```

**ACCEPTANCE CRITERIA**:
- [ ] `USER` directive present in Dockerfile.frontend before nginx
- [ ] nginx does not run as root (verify with `docker inspect`)
- [ ] Static files are still served correctly
- [ ] `dockerfile-validator` skill confirms no CRITICAL issues
- [ ] pre-commit passes

---

## Evidence Files Produced This Sprint

| File | Skill | Severity Findings |
|------|-------|-------------------|
| `evidence/00_ACCESSIBILITY_AUDIT.md` | accessibility-review | 18 issues (4 critical, 9 major, 5 minor) — all FIXED |
| `evidence/01_BUG_HUNT.md` | bug-hunt | 5 bugs (1 critical, 2 high, 2 medium) |
| `evidence/02_PERFORMANCE.md` | performance | 5 issues (DB OK, import slow, O(n) audit) |
| `evidence/03_TESTING_STRATEGY.md` | testing-strategy | 4 gaps (timeout, concurrent-append, accessibility) |
| `evidence/04_DEPLOY_LOCAL.md` | deploy-local | Qdrant unhealthy, frontend not running |
| `evidence/05_SECURITY_AUDIT.md` | security-auditor | 12 issues (2 critical, 3 high, 4 medium, 3 low) |
| `evidence/06_CODE_REVIEW.md` | code-review | 6 issues (2 BLOCK, 2 FLAG, 2 SUGGEST) |
| `evidence/07_TECH_DEBT.md` | tech-debt | 15 items on priority matrix |
| `evidence/08_WEBAPP_TESTING.md` | webapp-testing | 14 test files, 4 gaps |
| `evidence/09_DOCKERFILE_VALIDATION.md` | dockerfile-validator | 1 CRITICAL (frontend nginx as root) |
| `evidence/10_SECURITY_AUDIT.md` | security-audit (Guardian) | SQL injection + 7 HIGH/MEDIUM |
| `evidence/11_TYPESCRIPT_AUDIT.md` | typescript-advanced-types | 4 any-typed catch blocks, D3 types missing |
| `evidence/12_SYSTEM_DESIGN_C4.md` | system-design | C4 load test architecture |
| `evidence/13_DATABASE_SCHEMA.md` | database-schema-designer | Schema drift (18 vs 58 tables) |
| `evidence/14_PYTHON_BACKEND.md` | python-backend | 2499-line monolith, cache no size, no pagination |
| `evidence/15_PYTHON_BACKEND_PATTERNS.md` | nodejs-backend-patterns | 15 patterns evaluated (see summary table) |

**Total findings**: ~80 issues across 17 evidence files.
**CRITICAL (must fix this sprint)**: SQL injection (main.py:479), frontend Dockerfile as root
**HIGH (should fix this sprint)**: AuthError leaks, unbounded cache, no global exception handler
**MEDIUM (next sprint)**: Monolith extraction, API response standardization, pagination headers
**LOW (backlog)**: ADR-006/ADR-007 implementation, Qdrant/frontend infrastructure

---

## Notes for Guru

1. **SQL injection must be fixed before any other work** — confirm chain integrity is not already compromised
2. **All 17 evidence files should be committed** to `evidence/2026-04-25/` directory
3. **Qdrant health** (`docker ps` shows unhealthy) and **frontend not running** are infrastructure issues that require docker-compose changes, not code fixes — document but do not block sprint
4. **ADR-006 and ADR-007** created this session — awaiting Guru review for approval before implementation
5. **Skills session produced 17 evidence files in one session** — suggests a more systematic approach to skills review (e.g., batch similar skills together) for future sessions

# NRG Recurring Bugs & Prevention Patterns

> **Rule:** Every bug that appears twice must have a prevention rule here.
> **Updated:** 2026-04-25

---

## Pattern 1: Slow Security Tests Block Pre-Commit

**First seen:** 2026-04-24 (PII compliance suite timeout)
**Symptom:** `tests/security/test_pii_compliance.py` takes >60s for full suite. Single test ~15s.
**Impact:** Pre-commit hooks fail by timeout. Developers skip pre-commit. Quality gates bypassed.
**Root cause:** PII detection runs regex over large corpus sequentially. No caching between tests.
**Prevention:**
- Security tests must complete in <30s total for pre-commit compatibility
- Use pytest fixtures with session-scoped PII engine (compile once, reuse)
- Split heavy corpus tests into nightly job, keep pre-commit tests lightweight
- File: `.claude/rules/testing_speed.md` (extract if pattern recurs)

---

## Pattern 2: Audit Chain Breaks Silently on Event Accumulation

**First seen:** 2026-04-24 → 2026-04-25 (350748→368091 broken events)
**Symptom:** `verify_chain()` returns False. Broken indices span thousands of events.
**Impact:** Non-repudiation compromised. Compliance attestation fails.
**Root cause:** Audit events append without proactive hash verification. Broken chain only detected on full verify, not per-append.
**Prevention:**
- Every `log_event()` should verify last N events (N=100) in background
- Alert if chain break detected within 1 minute of occurrence
- Weekly `audit_investigate.py` cron is insufficient — need real-time guard
- See `.claude/rules/emergency.md` — audit corruption triggers P0 Battle Stations

---

## Pattern 3: API Route Drift from Documentation

**First seen:** 2026-04-25 (`/auth/login` vs actual `/login`)
**Symptom:** Protocol docs say `/auth/login`, code has `/login`. Tests expect one, users hit other.
**Impact:** 404 errors, confused integrators, broken UAT scripts.
**Root cause:** Docs and code updated independently. No contract test for API routes.
**Prevention:**
- Every API route must have a test that verifies OpenAPI spec matches implementation
- `/docs-sync` must check `docs/api/` against `src/api/main.py` decorators
- Route changes require updating both code AND docs in same commit

---

## Pattern 4: Qdrant API Version Mismatch

**First seen:** 2026-04-25 (`ScoredPoint.score` vs `vector_score`)
**Symptom:** Qdrant client upgrade changes field names. Code crashes with AttributeError.
**Impact:** RAG path completely broken. Fallback to SQL-only degrades user experience.
**Root cause:** Dependency upgraded without checking breaking changes.
**Prevention:**
- Pin major versions of critical dependencies (Qdrant, FastAPI, SQLAlchemy)
- Upgrade requires: changelog review + contract test pass + integration test pass
- Add Qdrant version check on startup — fail fast if version mismatch

---

## Pattern 5: Schema Migration Gap vs Production

**First seen:** 2026-04-25 (47 tables in migration vs 58 in db_struct.sql)
**Symptom:** Migration creates fewer tables than production schema. Dhairya queries fail on dev.
**Impact:** Dev environment cannot reproduce production bugs. SQL generation untested on real schema.
**Root cause:** db_struct.sql updated by professor, migration not regenerated.
**Prevention:**
- Any change to `db_struct.sql` must trigger auto-migration generation
- Weekly schema sync script compares migration vs db_struct.sql
- CI blocks if table count differs

---

## Pattern 6: Full Test Suite Timeout

**First seen:** 2026-04-25 (1,485 tests, pytest killed at 60s)
**Symptom:** Cannot run full test suite in reasonable time. Coverage unknown.
**Impact:** Developers run partial tests. Regressions slip through.
**Root cause:** Tests are serial, some are slow (PII, LLM calls), no parallelization.
**Prevention:**
- Target: full suite must complete in <5 minutes
- Use pytest-xdist for parallel execution
- Mark slow tests (>5s) with `@pytest.mark.slow` — run in CI only
- Pre-commit runs only fast tests (<30s subset)

---

## Pattern 7: Load Tests Can Report Zero Requests While Exiting Successfully

**First seen:** 2026-04-25 (`locust` exited code 0 with 0 aggregated requests)
**Symptom:** Load proof file exists, but Locust tasks raise request-context errors before issuing HTTP calls.
**Impact:** C4 SLO can look "executed" without measuring latency, throughput, or failures.
**Root cause:** Load task code used Locust response context APIs before a request existed.
**Prevention:**
- Any load-test evidence with `Request Count = 0` is an automatic FAIL.
- Load reports must include p50/p95/p99 plus request count >0 and failure count.
- CI/CD quality bar must parse Locust CSV and reject zero-request runs.
- Treat a successful process exit as insufficient evidence.

---

## Pattern 8: Static Evidence Pages Must Not Mount Auth Providers

**First seen:** 2026-04-25 (`/founder` dashboard triggered `/health` proxy 500s through `AuthProvider`)
**Symptom:** Static founder dashboard rendered, but browser console showed backend health probe failures.
**Impact:** Demo or UAT evidence pages look broken when backend is intentionally offline.
**Root cause:** Route was rendered inside global auth provider, which starts backend availability checks.
**Prevention:**
- Static evidence/demo routes (`/founder`, `/demo`) must mount outside `AuthProvider` unless they need a live user session.
- Webapp verification must assert zero HTTP failures and zero console errors, not just that text is visible.
- Frontend routes intended for offline stakeholder review must declare their backend dependency explicitly.

---

> **Last Updated:** 2026-04-25
> **Owner:** Guru
> **Trigger:** /self-evolve adds new patterns after every recurring bug

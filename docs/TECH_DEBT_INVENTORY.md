# Tech Debt Inventory
**Date:** April 21, 2026
**Owner:** Architect Agent

---

## Summary

| Category | Count | P0 | P1 | P2 |
|----------|-------|-----|-----|-----|
| Missing Tests (test gaps) | 12 | — | 3 | 9 |
| Migration Scripts (not validated) | 4 | 1 | 3 | — |
| Security Hardening | 4 | 2 | 2 | — |
| Missing Features (Architecture) | 3 | 1 | 2 | — |
| Config/Environment | 2 | 1 | 1 | — |
| Code Quality | 3 | — | 1 | 2 |
| **Total** | **28** | **5** | **12** | **11** |

---

## P0 — Must Fix Before Production

### P0-1: Alembic Migrations Not Implemented
**File:** `src/migrations/versions/` (empty)
**Issue:** Alembic migration files don't exist. The `src/migrations/` directory has `env.py` and `script.py.mako` but no actual version files.
**Impact:** Cannot migrate SQLite → PostgreSQL without manual steps.
**Fix:** Generate migrations: `alembic revision --autogenerate -m "initial"`. All migrations must be reversible.
**ADR:** YES — Decision: Use Alembic for all schema changes going forward.

### P0-2: PostgreSQL RLS Policies Not Auto-Applied
**File:** `src/security/rbac/postgresql_rbac.py`
**Issue:** `PostgreSQLRBAC.setup_rls_policies()` exists but is never called during application startup or migration.
**Impact:** RLS policies defined in code but not active on fresh PostgreSQL deployment.
**Fix:** Call `PostgreSQLRBAC(connection_string).setup_rls_policies()` in Alembic post-migrate hook or `database_v2.py` on connect.

### P0-3: Egress Guard Not Wired to LLM Client
**File:** `src/orchestration/nodes/synthesizer.py`, `src/config/llm_config.py`
**Issue:** `SovereignHTTPXClient` is not used for cloud LLM HTTP calls. The formal sovereignty boundary inspection is bypassed.
**Impact:** If `_minimise_*` functions have a bug, data could reach cloud LLM without inspection.
**Fix:** Wrap `httpx.post()` in `synthesizer._synthesize()` with `SovereignHTTPXClient().inspect_payload()` before each cloud LLM call.

### P0-4: CORS_ORIGINS Wildcard Validation Missing
**File:** `src/api/main.py:107`
**Issue:** `allow_credentials=True` with `allow_origins` from env var — if `CORS_ORIGINS=*` is accidentally set, browsers reject it (or worse, accept it).
**Impact:** Configuration error could expose API to unauthorized origins.
**Fix:** Add explicit check:
```python
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
if origins == "*":
    raise ValueError("CORS_ORIGINS cannot be '*' when allow_credentials=True")
```

### P0-5: Consent Check Not Wired to Query Pipeline
**File:** `src/orchestration/graph.py` or `src/api/main.py`
**Issue:** The `/consent` endpoint exists but `withdrawn` consent doesn't block query execution.
**Impact:** Researchers who withdrew consent could still access data.
**Fix:** Add consent check in workflow receiver node:
```python
if user_tier == 1 and is_consent_withdrawn(user_id):
    raise HTTPException(403, "Consent withdrawn")
```

---

## P1 — Fix Before v1.0 Release

### P1-1: 4 Migration Scripts Have TODOs
**Files:** `scripts/migration/index_builder.py`, `scripts/migration/validate_migration.py`, `scripts/migration/etl_pipeline.py`
**Issue:** These scripts exist but `validate_migration.py` has 4 TODO items (checksum, NULL check, index verification, query analysis) and `etl_pipeline.py` has unimplemented ETL logic.
**Impact:** PostgreSQL migration cannot be validated or executed safely.
**Fix:** Implement the TODO items before migration run.

### P1-2: Reflector Node Not Implemented
**File:** `src/orchestration/graph.py`
**Issue:** The Core_Idea_Clean.md describes a 6-node pipeline with a Reflector node, but only 5 nodes are implemented.
**Impact:** No self-evaluation loop; if verification fails, no regeneration occurs.
**Fix:** Either implement Reflector (conditional loop-back in graph) or update Core_Idea_Clean.md to reflect 5-node reality.

### P1-3: LLM_FALLBACK_ORDER Ignored
**File:** `src/orchestration/nodes/synthesizer.py`, `src/config/llm_config.py`
**Issue:** The `.env` specifies `LLM_FALLBACK_ORDER=nvidia` but the synthesizer cascade is hardcoded.
**Impact:** Cannot configure multi-provider fallback (e.g., NVIDIA → Gemini → Anthropic).
**Fix:** Read `LLM_FALLBACK_ORDER` env var and iterate dynamically in `_synthesize()`, or document that cascade is fixed.

### P1-4: Intent Router Heuristic Classification
**File:** `src/orchestration/nodes/router.py`
**Issue:** Simple regex-based intent classification. "What is the count of researchers in Gujarat" would be classified as unstructured (no "find/list" pattern match).
**Impact:** Misrouted queries get suboptimal results (RAG instead of SQL).
**Fix:** Add entity-based detection: if query contains domain entities (researcher, publication, lab, funding), route to SQL even without explicit "find/list".

### P1-5: RBACMiddleware Not Wired
**File:** `src/api/main.py`
**Issue:** `RBACMiddleware` class exists but is never applied to any API endpoint. No API-layer backstop for tier enforcement.
**Fix:** Apply middleware or add explicit tier validation in response serialization.

### P1-6: Global LLM Model Cache in local_llm.py
**File:** `src/config/local_llm.py:17-18`
**Issue:** `_model` and `_tokenizer` are module-level globals cached across all requests. Could cause memory leaks and test pollution.
**Fix:** Use a proper singleton pattern with lazy initialization, or dependency injection.

### P1-7: JWT Revoked JTIs In-Memory Only
**File:** `src/auth/jwt_handler.py:127`
**Issue:** `revoked_jtis: set[str]` is in-memory. On restart, revoked access tokens become valid again until they expire.
**Fix:** Use Redis-backed set for revoked tokens in production. For now, acceptable since access tokens expire in 1 hour.

---

## P2 — Post-v1.0

### P2-1: Missing Grievance Endpoint (DPDP)
**DPDP Section 14 requires a grievance mechanism.**
**Fix:** Add `/grievance` POST endpoint.

### P2-2: No Automated Breach Notification
**Sovereignty breach lockdown exists but no automated notification to MeitY/DISHA.**
**Fix:** Add email/SMS alert in `egress/guard.py` breach handler.

### P2-3: Schema Drift — migration scripts vs ORM models
**Files:** `src/db/database_v2.py` vs `scripts/migration/`
**Issue:** Schema changes must be reflected in both SQLAlchemy models and Alembic migrations.
**Fix:** Always use `alembic revision --autogenerate` after model changes.

### P2-4: Playwright E2E Timeout Issue
**Issue:** E2E tests timed out (120s) — browser-based tests may need more time or parallelization.
**Fix:** Increase timeout or run tests in smaller batches.

### P2-5: Local LLM (Phi-2) CPU Loading Slow
**File:** `src/config/local_llm.py`
**Issue:** Loading HuggingFace Phi-2 on CPU is slow and fragile. `get_local_llm_client()` correctly falls back to llama.cpp, but HF path has no health check.
**Fix:** Add timeout + health check to HF loading path.

---

## Skipped Tests (Acceptable — External Dependencies)

| Test File | Skipped | Reason |
|-----------|---------|--------|
| `test_kong_dlp_runtime.py` | 3 tests | Kong Gateway not running in test env |
| `test_api_gateway.py` | 8 tests | Requires `NRG_API_RUNNING=1` |
| Gateway tests in `test_gateway.py` | 5+ tests | Kong not in test environment |

These are correctly skipped with `@pytest.mark.skip` — appropriate for external service dependencies.

---

## ADR — Architecture Decisions Made During Review

### ADR-001: LLM Cascade Order
**Decision:** The LLM cascade order (cloud → local → rule-based) is hardcoded in `synthesizer.py`. `LLM_FALLBACK_ORDER` is decorative.
**Rationale:** The current cascade matches the desired behavior. The env var was intended for multi-provider fallback but was never wired.
**Status:** Document — will revisit if multi-provider fallback needed.

### ADR-002: Reflector Node Deferred
**Decision:** Reflector node (self-evaluation loop) will not be implemented in Phase 1.
**Rationale:** 5-node pipeline is functional. The retry logic in Core_Idea_Clean.md is aspirational.
**Status:** Document in Core_Idea_Clean.md — mark as Phase 2.

---

## Tech Debt by Module

| Module | P0 | P1 | P2 |
|--------|----|----|-----|
| `src/migrations/` | 1 | 1 | — |
| `src/security/` | 2 | 1 | 1 |
| `src/orchestration/` | — | 2 | 1 |
| `src/api/` | 1 | 1 | — |
| `src/auth/` | — | 1 | — |
| `src/config/` | — | 1 | 1 |
| `scripts/migration/` | 1 | 3 | 1 |
| DPDP (frontend) | — | — | 2 |
| **Total** | **5** | **10** | **6** |
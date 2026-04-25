# Technical Debt Inventory — Session 92

**Date:** 2026-04-25
**Scope:** Full codebase review

---

## Priority Matrix

| ID | Item | Impact | Risk | Effort | Score |
|----|------|--------|------|--------|-------|
| TD-01 | Audit chain file locking | 5 | 5 | 3 | 40 |
| TD-02 | Qdrant unhealthy in Docker | 4 | 3 | 1 | 24 |
| TD-03 | `_jti_ip_registry` unbounded | 4 | 5 | 1 | 32 |
| TD-04 | API cache no size limit | 3 | 4 | 1 | 27 |
| TD-05 | Keydown on `document` not dialog | 4 | 4 | 1 | 28 |
| TD-06 | Full test suite times out 120s+ | 3 | 4 | 3 | 21 |
| TD-07 | `get_chain_health()` always returns True | 3 | 5 | 1 | 28 |
| TD-08 | `_get_last_event_time()` is O(n) | 2 | 3 | 1 | 18 |
| TD-09 | `TIER_STYLES[0]` undefined | 2 | 2 | 1 | 12 |
| TD-10 | Multiple SQLite schemas vs actual DB | 3 | 4 | 3 | 18 |
| TD-11 | GPG keys on cluster (eternal seal) | 5 | 5 | 5 | 25 |
| TD-12 | Default passwords in source | 3 | 4 | 1 | 24 |
| TD-13 | No test parallelism (pytest-xdist missing) | 2 | 3 | 1 | 16 |
| TD-14 | Frontend accessibility issues (18 found) | 3 | 3 | 5 | 16 |
| TD-15 | Qdrant reports unhealthy but API says reachable | 3 | 3 | 2 | 18 |

---

## Tech Debt Items (Sorted by Score)

### TD-01: Audit Chain File Locking (Race Condition) — Score: 40
**Category:** Architecture Debt
**Files:** `src/audit/__init__.py`

**What:** No `fcntl.flock` on `chain.jsonl`. Multiple processes can interleave writes, causing silent corruption. Chain corrupted 20+ times in prior sessions.

**What it costs:** Chain integrity is unreliable. Cannot trust audit trail for compliance.

**Estimated fix:** 2 days (implement FileLock class, integrate, test concurrent appends)

**Phase:** P0 — Fix before v1.0 release

---

### TD-03: `_jti_ip_registry` Unbounded Memory — Score: 32
**Category:** Code Debt
**Files:** `src/auth/jwt_handler.py:133`

**What:** Dict storing every JWT JTI ever issued, never cleaned up. DoS vector.

**Estimated fix:** 2 hours (add TTL-based cleanup)

---

### TD-04: API Cache Unbounded — Score: 27
**Category:** Code Debt
**Files:** `src/api/main.py:114-183`

**What:** `_APIMemoryCache._store` has no max size. Attacker could flood with unique queries.

**Estimated fix:** 1 hour (add `MAX_CACHE_ENTRIES = 1000`)

---

### TD-05: Keydown Listener on `document` Not Dialog — Score: 28
**Category:** Code Debt (Accessibility)
**Files:**
- `frontend/src/components/DPDPConsentDialog.tsx:297`
- `frontend/src/components/DPDPPanel.tsx:??`

**What:** Tab key trapping attaches to `document` instead of the dialog element. Tab presses outside the dialog are incorrectly trapped.

**Estimated fix:** 1 hour (change to `dialogRef.current?.addEventListener`)

---

### TD-07: `get_chain_health()` Always Returns `chain_valid: True` — Score: 28
**Category:** Code Debt
**Files:** `src/audit/__init__.py:382-393`

**What:** Health endpoint always reports healthy. Would not detect chain corruption.

**Estimated fix:** 2 hours (add file-based integrity check for fast path, full verify on interval)

---

### TD-12: Default Passwords in Source Code — Score: 24
**Category:** Security Debt
**Files:** `src/auth/jwt_handler.py:48-72`

**What:** `researcher-pass`, `government-pass`, `industry-pass` in source. Require env vars in non-dev.

**Estimated fix:** 1 hour

---

### TD-06: Full Test Suite Times Out — Score: 21
**Category:** Test Debt
**Files:** `pytest.ini`, `conftest.py`

**What:** Test suite doesn't complete in 120 seconds. Cannot run in CI.

**Estimated fix:** 3 days (split into parallel jobs, add pytest-xdist, mock heavy imports)

---

### TD-10: Multiple Wrong Schema References in Scripts — Score: 18
**Category:** Documentation Debt / Code Debt
**Files:** `scripts/null_rate_check.py` (fixed in prior session)

**What:** Schema mismatches caused 20+ wrong column names. Currently fixed but no schema validation prevents drift.

**Estimated fix:** Add schema validation to null_rate_check.py

---

### TD-02: Qdrant Container Unhealthy — Score: 24
**Category:** Infrastructure Debt
**Files:** `docker-compose.yml`

**What:** `nrg-qdrant` reports unhealthy in docker ps. Not responding on health check.

**Estimated fix:** `docker restart nrg-qdrant` + investigate logs

---

### TD-11: GPG Keys on Sovereign Cluster — Score: 25
**Category:** Architecture Debt
**ADR:** ADR-007 (created this session)

**What:** Private GPG key material present on sovereign cluster. Should use TPM-backed attestation instead.

**Estimated fix:** ADR written. Implementation: 1-2 weeks (requires TPM provisioning on sovereign nodes)

---

## Phased Remediation Plan

### Phase 0 (Before v1.0 tag)
- [ ] TD-01: Audit chain file locking (ADR-006)
- [ ] TD-03: `_jti_ip_registry` cleanup
- [ ] TD-05: Keydown listener fix
- [ ] TD-07: Health endpoint actually verifies

### Phase 1 (Post v1.0, Sprint 1)
- [ ] TD-04: Cache size limit
- [ ] TD-12: Default passwords require env vars
- [ ] TD-02: Fix Qdrant health

### Phase 2 (Sprint 2-3)
- [ ] TD-06: Parallelize test suite
- [ ] TD-10: Schema validation in scripts
- [ ] TD-11: TPM attestation (ADR-007 implementation)

---

## Recurring Patterns Found

1. **Singleton patterns without cleanup** — `ImmutableAuditLog`, `DBCoSignStore`, `JWTHandler` all use class-level singletons with mutable state that grows unbounded. Need a memory management policy for singletons.

2. **No file locking** — Several file operations (`chain.jsonl`, `.last_hash`) assume single-process access. Need file-level locking as a project standard.

3. **In-memory state in auth handlers** — `_jti_ip_registry`, `_api_cache`, brute force store — all in-memory, not shared across workers. Need Redis-backed alternatives for production.

# Testing Strategy — NRG Platform

**Date:** 2026-04-25
**Status:** Proposed

---

## Current State

| Category | Test Count | Pass Rate | Status |
|----------|-----------|-----------|--------|
| API/Config | ~88 | Unknown (timeout) | ⚠️  Too slow to run |
| Security | ~23 | Unknown (timeout) | ⚠️  Too slow to run |
| Orchestration | ~83 | Unknown | ⚠️  Needs API |
| Unit | ~31 | Unknown | ⚠️  Needs dependencies |
| Benchmark | ~43 | Unknown | ⚠️  Needs API |
| E2E | ~12 | Unknown | ⚠️  Needs full stack |
| Chaos | ~8 | Unknown | ⚠️  Needs infra |
| Skills | ~16 | Unknown | ⚠️  Various |
| **Total** | **~1503** | **Unknown** | **Tests timeout after 120s** |

**Critical Issue:** Full test suite times out after 120s. Tests cannot be run in CI without optimization.

---

## Testing Pyramid (Target)

```
         /  E2E (Playwright)  \        ~10 tests, 5-10min, high confidence
        /  Integration (API)    \       ~50 tests, 2-5min, contract testing
       /   Chaos Engineering      \      ~10 tests, 2-3min, resilience
      /    Security (pytest)      \     ~40 tests, 2-3min, OWASP Top 10
     /     Unit + Skills (fast)     \    ~200 tests, 30-60s, isolated
```

**Target total runtime: <5 minutes**

---

## Gaps Identified

### Gap 1: No Concurrent-Write Tests for Audit Chain
**Severity:** 🔴 Critical
**Risk:** Race condition in `ImmutableAuditLog.append()` (ADR-006) could cause silent chain corruption

**Missing tests:**
- `tests/audit/test_concurrent_append.py` — 5 threads × 100 events concurrently → verify chain integrity
- `tests/audit/test_multi_process_append.py` — 3 processes × 100 events → verify cross-process safety
- `tests/audit/test_file_lock_timeout.py` — verify lock timeout behavior

**Test skeleton:**
```python
import threading, multiprocessing, time

def test_concurrent_append():
    """5 threads appending 100 events each should produce 500 valid chain entries."""
    from src.audit import ImmutableAuditLog, verify_chain
    log = ImmutableAuditLog(storage_path=f"/tmp/test_chain_{time.time()}")
    log._reset()

    def writer(thread_id):
        for i in range(100):
            log.append(AuditEvent(event_type="test", user_id=f"user_{thread_id}"))

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()

    valid, errors, count = verify_chain()
    assert valid, f"Chain corrupted: {errors}"
    assert count == 500, f"Expected 500, got {count}"
```

### Gap 2: No Audit Chain Lock Timeout Tests
**Severity:** 🟡 Major

**Missing tests:**
- `tests/audit/test_lock_timeout.py` — verify `FileLock.acquire(timeout=5)` raises `AuditLockTimeout` after 5s
- `tests/audit/test_lock_dead_process.py` — simulate dead process holding lock → next acquire should timeout

### Gap 3: No DPDP Consent Flow E2E Tests
**Severity:** 🟡 Major
**Files:** `tests/e2e/test_consent_flow.py` exists but may not cover:
- Consent expiration handling (30-day threshold)
- Withdrawal followed by query attempt → should be blocked
- Export data → verify JSON contains expected fields
- Erase data → verify query history anonymized

### Gap 4: No GraphView Keyboard Navigation Tests
**Severity:** 🟡 Major
**Component:** `frontend/src/components/GraphView/GraphView.tsx`

**Missing tests:**
- Tab navigation to graph nodes
- Enter/Space activation of focused node
- Escape key closes node detail panel
- Arrow keys navigate between connected nodes

### Gap 5: No Accessibility Tests (WCAG 2.1 AA)
**Severity:** 🟡 Major

**Missing tests:**
- `frontend/tests/a11y.spec.ts` — axe-core scan on all 3 dashboards
- Focus trap verification for DPDPConsentDialog and ConfirmationDialog
- Screen reader announcement verification (aria-live regions)

### Gap 6: No LLM Failover Chain Tests
**Severity:** 🟡 Minor
**File:** `tests/chaos/test_llm_cascade_fallback.py`

**Missing tests:**
- NVIDIA API fails → verify local Llama fallback is called
- Local LLM fails → verify rule-based synthesis kicks in
- All LLM providers fail → verify graceful error response

### Gap 7: No Load Test Integration in CI
**Severity:** 🟡 Major
**Current:** `scripts/run_load_test.py` exists but not in CI pipeline

**Missing:**
- Add `scripts/run_load_test.py` to CI as a separate job
- P99 < 2000ms assertion should fail CI
- Results should be archived as artifacts

---

## Test Optimization Recommendations

### 1. Split Tests by Runtime Budget
```
CI Jobs:
  job1: pytest tests/unit/ tests/skills/ tests/orchestration/  → 30s budget
  job2: pytest tests/security/ → 60s budget (parallelized)
  job3: pytest tests/api/ → 60s budget (needs API running)
  job4: playwright tests/frontend/ → 120s budget (separate runner)
  job5: locust load test → 180s budget
```

### 2. Mock External Dependencies in Unit Tests
**Current problem:** Many tests import `src.api.main` which loads FastAPI + LangGraph (2.37s import). This dominates test time.

**Fix:** Add `conftest.py` with `pytest.mark.unit` that mocks API routes. Only load the specific module being tested.

### 3. Use `pytest-xdist` for Parallel Execution
**Current:** Tests run sequentially
**Target:** 4 workers → ~4× speedup

```bash
pytest tests/unit/ tests/skills/ -n 4 --dist loadscope
```

### 4. Add Timeout Markers
```python
@pytest.mark.timeout(30)  # unit tests
@pytest.mark.timeout(120)  # integration tests
@pytest.mark.timeout(300)  # e2e tests
```

---

## Test Coverage Targets

| Layer | Target | Current |
|-------|--------|---------|
| Unit (Python) | 80% | 20% (unclear) |
| API endpoints | 90% | Unknown |
| Security | 100% OWASP Top 10 | Partial |
| Frontend | 70% component | Partial |
| E2E flows | 8 critical paths | Partial |
| Load test | P99 < 2000ms | Not in CI |

---

## Critical Test Paths (Must Not Break)

1. **Login → Query → Response** — Researcher submits query, gets streamed response with citations
2. **Consent Grant → Query → Data Accessed** — DPDP flow for new user
3. **Audit Append → verify_chain() → valid** — Chain integrity after 1 append
4. **Key Rotation → New Event → verify_chain() valid** — Rotation integrity
5. **Concurrent Appends → verify_chain() → valid** — Race condition prevention
6. **PII Query → sanitized** — No PII in query logs
7. **Tier 3 Query → anonymized** — Industry user gets no individual researcher names

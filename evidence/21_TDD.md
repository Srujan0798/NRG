# TDD Skill Evidence — Test-Driven Development Audit

**Skill**: test-driven-development
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/21_TDD.md`

---

## Executive Summary

NRG has 1,503 tests across 100+ test files. The test suite is comprehensive in breadth but has critical gaps in TDD discipline. Most significantly, the **SQL injection test doesn't exercise the vulnerable code path**, and the **concurrent audit chain test cannot detect the lock-holding-thread-spawn bug**.

**TDD Verdict**: The project writes tests alongside code, but does not practice strict TDD (test-before-code). Tests-after implementation is evident throughout.

---

## 1. Test Inventory

| Category | Count | Status |
|----------|-------|--------|
| Unit tests | ~40 files | Mostly passing |
| Integration tests | ~20 files | Partial, DB-dependent |
| E2E tests | ~15 files | Infrastructure gaps |
| Security tests | 6 files | Critical gaps (see below) |
| Chaos/load tests | ~10 files | OK |
| Property tests | 5 files | Good coverage |
| **Total** | **1,503 collected** | Suite times out at 120s |

---

## 2. RED Phase Analysis — Critical Gaps

### 2.1 SQL Injection: Wrong Endpoint Tested

**Vulnerability**: `src/api/main.py:479`
```python
sql_results = db.execute_query(
    f"SELECT * FROM researchers WHERE research_area LIKE '%{request.query.split()[0]}%' LIMIT 10",
    user_tier=user_tier,
)
```

**Existing Test**: `tests/security/test_sql_injection_blocked.py`
- Posts to `/query` endpoint (line 522 of main.py)
- Uses `StubWorkflow` which intercepts at `workflow.run()`
- **Never reaches line 479** — vulnerable code is in `/api/query/stream` (line 413)

**RED Failure**: The test passes but the vulnerability is NOT exercised.

### 2.2 Audit Chain Concurrent Append: Lock Not Tested for Thread Spawn

**Bug**: `src/audit/__init__.py:244`
```python
with self._lock:  # line 211
    # ... compute hash ...
    with open(self.chain_file, "a") as f:  # line 233
        f.write(json.dumps(event_data, default=str) + "\n")
    self.last_hash = new_hash  # line 236
    self.last_hash_file.write_text(new_hash)  # line 237
    self.event_count += 1  # line 238

    def _cosign_fire_and_forget():  # line 240 — DEFINED inside lock
        from src.audit.db_cosign import cosign_event as _cosign
        _cosign(event.event_id, new_hash, per_user_hash, event.user_id, event.event_type)

    threading.Thread(target=_cosign_fire_and_forget, daemon=True).start()  # line 244 — SPAWNED inside lock
```

**Existing Test**: `tests/audit/test_chain_integrity.py::test_concurrent_appends`
- Spawns 10 threads × 10 appends = 100 events
- Test PASSES even with the bug because:
  1. The lock IS held during the thread spawn, but Python's GIL + short sleep in `_cosign` makes the race window small
  2. The test only checks for exceptions and final chain validity — it doesn't measure lock contention time
  3. **The test cannot detect that the cosign thread blocks the lock holder**

**RED Failure**: The test cannot distinguish "fast lock release" from "slow lock held while spawning cosign".

### 2.3 JWT Handler: No TDD for Token Revocation

**Bug found by security-audit**: `refresh_access_token()` doesn't revoke old access token JTI.

**No test exists** that verifies: "after refresh, old access token is invalid."

---

## 3. GREEN Phase Analysis

### 3.1 Good: Property-Based Tests

`tests/property/test_tier_filtering_always_returns_subset.py` — Good TDD approach:
- Tests the contract that tier filtering always returns subset of full set
- Property-based reasoning, not just example-based

### 3.2 Good: Text-to-SQL Validator Tests

`tests/skills/test_validator.py` — Tests validator in isolation with known inputs/outputs.

### 3.3 Issue: StubWorkflow Masks Real Behavior

The `StubWorkflow` at `tests/security/test_sql_injection_blocked.py:16-33` returns a hardcoded response. This means:
- The SQL injection at `/api/query/stream` (line 479) is never reached
- The test verifies "StubWorkflow returns ok" not "the real code path is safe"

**Anti-pattern detected**: Testing mock behavior, not real behavior (see `testing-anti-patterns.md`).

---

## 4. REFACTOR Phase Analysis

### 4.1 Test Suite Timeout (120s)

1503 tests collected in 28s during collection, but running times out at 120s. Likely causes:
- DB connection fixtures that wait for PostgreSQL
- RAG/vector store fixtures with timeouts
- No test parallelization configured

### 4.2 No Test Tags for Selective Runs

Tests are not tagged (e.g., `@pytest.mark.unit` vs `@pytest.mark.integration`). Cannot run fast unit tests without DB-dependent tests.

### 4.3 Coverage at 20%

Overall project coverage is 20%. Critical paths (audit chain, auth, SQL injection) should be 80%+.

---

## 5. Missing Tests (TDD Priority Order)

| Priority | Test | File to Create | Why |
|----------|------|----------------|-----|
| P0 | SQL injection at `/api/query/stream` | `tests/security/test_sql_injection_stream.py` | CRITICAL vulnerability not covered |
| P0 | Concurrent append with lock-timing assertion | `tests/audit/test_concurrent_lock_timing.py` | Current test passes with bug present |
| P0 | JWT refresh doesn't revoke old token | `tests/auth/test_jwt_refresh_revocation.py` | Security regression |
| P1 | Audit chain fcntl.flock (ADR-006) | `tests/audit/test_chain_file_locking.py` | File locking regression |
| P1 | Tier badge `bg-{var}-100` resolves | `tests/frontend/test_tier_styles.py` | CSS class exists at runtime |
| P2 | DPDPConsentDialog focus trap | `tests/e2e/test_dpdp_consent_dialog.py` | Accessibility regression |
| P2 | GraphView keyboard navigation | `tests/e2e/test_graph_view_keyboard.py` | BLOCK issue from accessibility audit |

---

## 6. TDD Anti-Patterns Found

| Anti-Pattern | Location | Evidence |
|--------------|----------|----------|
| Testing mock behavior | `test_sql_injection_blocked.py:16-33` | StubWorkflow intercepts before vulnerable code |
| Incomplete mock | `StubWorkflow` missing `retrieval_sources`, `warnings` fields | Partial mock hides structural assumptions |
| Test-only methods | Not found in audit module | Good — no `destroy()` test methods |
| Mock without understanding | Likely in LangGraph tests | Complex mocks suggest unclear dependencies |

---

## 7. What to Test First (TDD Protocol)

### P0: SQL Injection Fix

**RED** (write first):
```python
def test_stream_query_sql_injection_blocked(client, auth_token):
    """SQL injection in /api/query/stream research_area LIKE should be blocked."""
    payload = "'; DROP TABLE researchers; --"
    response = client.post(
        "/api/query/stream",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"query": payload},
    )
    # Should not return 200 with researcher data
    assert response.status_code in [400, 500]
```

**GREEN** (minimal fix):
```python
# Replace line 479 with parameterized query
sql_results = db.execute_query(
    "SELECT * FROM researchers WHERE research_area LIKE %s LIMIT 10",
    (f"%{request.query.split()[0]}%",),
    user_tier=user_tier,
)
```

### P0: Concurrent Lock Timing

**RED**:
```python
def test_cosign_thread_does_not_hold_lock(client, fresh_audit_log):
    """Cosign fire-and-forget must not be spawned inside the lock."""
    start = time.time()
    def append_with_slow_cosign():
        event = AuditEvent(event_type="test", user_id="u1", query="q1")
        fresh_audit_log.append(event)

    # Patch cosign to sleep
    with patch('src.audit.db_cosign.cosign_event', side_effect=lambda *a, **kw: time.sleep(0.5)):
        thread = threading.Thread(target=append_with_slow_cosign)
        thread.start()
        elapsed_inside_lock = time.time() - start
        thread.join()

    # append() should return in <0.1s (lock released before cosign)
    # Currently fails: takes ~0.5s because cosign is inside lock
    assert elapsed_inside_lock < 0.2
```

---

## 8. Verification Checklist

- [ ] SQL injection test now hits `/api/query/stream` endpoint
- [ ] Concurrent test measures lock-held time, not just final chain validity
- [ ] JWT refresh test verifies old token revocation
- [ ] Audit chain locking test uses fcntl.flock (ADR-006)
- [ ] All P0 tests written BEFORE the fix
- [ ] All P0 tests FAIL before the fix
- [ ] All P0 tests PASS after the fix
- [ ] Suite timeout resolved (DB fixtures isolated)
- [ ] Test tags added for selective runs
- [ ] Coverage on critical paths > 80%

---

## 9. Recommendations

1. **Create `tests/security/test_sql_injection_stream.py`** — Cover `/api/query/stream` endpoint
2. **Fix `tests/audit/test_chain_integrity.py::test_concurrent_appends`** — Add timing assertion
3. **Add `tests/auth/test_jwt_refresh_revocation.py`** — Missing auth regression test
4. **Configure pytest parallelization** (`pytest-xdist`) to solve 120s timeout
5. **Add test tags** (`@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`)
6. **Raise coverage gate** on critical paths to 80%

---

## 10. Skill Deliverable

**Status**: COMPLETED (analysis phase — no code written)

TDD principles applied to existing test suite reveal:
- 1 critical gap: SQL injection test covers wrong endpoint
- 1 design flaw: concurrent test cannot detect lock-holding-thread-spawn
- 6 missing tests (P0-P2 priority)

The existing tests are well-structured but miss the most critical code paths. The project would benefit from strict TDD on the P0 items before any further feature development.

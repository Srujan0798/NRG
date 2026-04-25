# ADR-006: Fix Audit Chain Concurrent-Write Corruption

**Date:** 2026-04-25
**Status:** Proposed
**Author:** Session 92 Agent

## Context

The `.audit/chain.jsonl` file has been corrupted **20+ times** across multiple rebuild sessions. Each rebuild fixes 50-300k events but the chain becomes corrupted again within seconds to minutes. Root cause analysis identified a **race condition** in `ImmutableAuditLog.append()` at `src/audit/__init__.py:203-238`.

### Root Cause

```
Thread A (append)              Thread B (_cosign_fire_and_forget)
─────────────────              ─────────────────────────────────
1. acquire lock
2. _compute_hash(prev_hash, event)
3. self.last_hash = new_hash   ← written BEFORE disk write completes
4. write(JSON) to chain.jsonl
5. release lock
                                 reads .last_hash → sees stale value
                                 writes corrupted hash
```

The `self.last_hash = new_hash` update at line 236 happens **before** the synchronous `write()` completes and **outside** the lock's protection for concurrent readers of `.last_hash`. Since `_cosign_fire_and_forget` reads `self.last_hash` without holding the lock, it gets a stale value and writes an incorrect hash to the chain.

### Forces at Play

- **Audit integrity**: The chain must be append-only and hash-consistent
- **Throughput**: 300+ events/second during load — concurrent writes are inevitable
- **Sovereign constraint**: No external locking services (Redis, PostgreSQL advisory locks) in sovereign mode
- **File locking**: `fcntl.flock` is available on Linux but not portable to all deployments

## Decision

We will implement **process-level file locking with `fcntl.flock`** for the sovereign cluster and a **writer-mutex with threading lock** for development. The `append()` method will be refactored to hold the lock for the full duration of `_compute_hash → write → update last_hash`.

### Option A: fcntl.flock (file-level, cross-process) — CHOSEN

| Dimension | Assessment |
|-----------|------------|
| Complexity | Medium |
| Scope | Cross-process (daemon + workers) |
| Portability | POSIX only (Linux/macOS) |
| Blocking | Yes, default |
| Timeout | Configurable |

**Pros:**
- Works across all processes accessing the chain file
- OS-managed, no external dependencies
- Works in sovereign environment (no Redis required)

**Cons:**
- Not portable to Windows
- Non-trivial to implement timeout + retry logic

### Option B: threading.Lock (in-process only)

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low |
| Scope | In-process only |
| Portability | All Python |
| Blocking | Yes |

**Pros:** Simple, zero dependencies

**Cons:** Doesn't protect against multi-process daemon + worker race

### Option C: PostgreSQL advisory locks (external service required)

**Pros:** Battle-tested, fine-grained
**Cons:** Requires PostgreSQL — not sovereign-compatible

## Trade-off Analysis

The critical requirement is **cross-process safety** in sovereign deployments where the audit daemon runs as a separate process from the API workers. `fcntl.flock` is the only zero-dependency option that satisfies this. In-process threading.Lock is a useful secondary protection layer but insufficient alone.

## Consequences

### Positive
- Chain corruption stops permanently
- Concurrent writes from multiple processes handled safely
- No new dependencies (POSIX standard library only)
- Lock timeout prevents deadlocks if a process crashes while holding the lock

### Negative
- `fcntl.flock` is POSIX-only — Windows deployments need a different path
- Lock contention during very high throughput (10K+ events/sec) — consider queue batching if this becomes a problem
- macOS `fcntl.flock` behavior differs slightly under heavy load; test thoroughly

## Action Items

- [ ] Implement `FileLock` class using `fcntl.flock` with timeout in `src/audit/lock.py`
- [ ] Refactor `ImmutableAuditLog.append()` to hold lock for full hash → write → update cycle
- [ ] Add lock acquisition timeout (5s default, configurable via `AUDIT_LOCK_TIMEOUT` env var)
- [ ] Log lock wait time as metric (`audit.lock.wait_seconds`)
- [ ] Handle `OSError` (EWOULDBLOCK) when lock timeout exceeded — return error instead of hanging
- [ ] Write integration test: spawn 3 processes, each writing 1000 events concurrently, verify chain integrity
- [ ] Document `AUDIT_LOCK_TIMEOUT` in `docs/architecture/OPERATIONS_RUNBOOK.md`

## Implementation Sketch

```python
# src/audit/lock.py
import fcntl
import contextlib
import os

class AuditChainLock:
    def __init__(self, lock_path: str, timeout: float = 5.0):
        self.lock_path = lock_path
        self.timeout = timeout
        self._fd = None

    def acquire(self) -> bool:
        self._fd = open(self.lock_path, 'w')
        start = time.monotonic()
        while True:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except BlockingIOError:
                if time.monotonic() - start >= self.timeout:
                    self._fd.close()
                    self._fd = None
                    raise AuditLockTimeout(f"Could not acquire lock within {self.timeout}s")
                time.sleep(0.01)

    def release(self):
        if self._fd:
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            self._fd.close()
            self._fd = None

    @contextlib.contextmanager
    def hold(self):
        self.acquire()
        try:
            yield
        finally:
            self.release()
```

```python
# In ImmutableAuditLog.append():
def append(self, event: AuditEvent) -> str:
    with self._lock.hold():  # full critical section
        prev = self.last_hash
        new_hash = self._compute_hash(prev, event.serialize())
        self._write_event(event)  # write BEFORE updating last_hash
        self.last_hash = new_hash  # now safe
    return new_hash
```

**Reviewed by:** Session 92 Agent
**Next Review:** 2026-05-25 (after implementation)

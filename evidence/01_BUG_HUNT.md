# Bug Reports — Session 92

## Bug Report 1: Audit Chain Concurrent-Write Corruption (Race Condition)

### Symptom
`.audit/chain.jsonl` was corrupted **20+ times** across prior sessions. Each rebuild fixed 50-300k events but corruption recurred within seconds to minutes. The `verify_chain()` returns `hash mismatch` errors.

### Root Cause
**File:** `src/audit/__init__.py:203-247`

The `_cosign_fire_and_forget` daemon thread is spawned **inside** `self._lock`, but `DBCoSignStore` uses a separate `threading.Lock()`. This means `DBCoSignStore.cosign()` can run **concurrently** with the next `append()` call.

More critically: when multiple processes (API workers + daemon) concurrently write to `chain.jsonl`, there is **no file-level lock**. `fcntl.flock` is not used. Two processes can interleave their `f.write()` calls, producing garbled JSON lines.

Additionally, `_load_last_hash()` at line 181 reads from `.last_hash` file without locking — so a process can read a stale hash while another process is mid-write to `.last_hash_file`.

```python
# Line 136 — __init__ reads last_hash outside any lock
self.last_hash = self._load_last_hash()   # RACE: another process may be writing

# Line 181 — _load_last_hash reads without lock
def _load_last_hash(self) -> str:
    if self.last_hash_file.exists():
        return self.last_hash_file.read_text().strip()  # RACE
    return self._genesis_hash()
```

### Fix
1. Implement `FileLock` class using `fcntl.flock` with timeout (see ADR-006)
2. Wrap `_load_last_hash()` reads inside a lock-protected critical section
3. Ensure `.last_hash_file` writes and reads are atomic (write to temp file, then rename)
4. Spawn `_cosign_fire_and_forget` **outside** `self._lock` — start it via `threading.Thread.start()` after releasing the lock

### Verification
```bash
cd /Users/srujansai/Desktop/NRG && \
PYTHONPATH=src .venv/bin/python -c "
from src.audit import get_audit_log, verify_chain
valid, errors, count = verify_chain()
print(f'Chain valid: {valid}, events: {count}, errors: {len(errors)}')
for e in errors[:5]: print(f'  {e}')
"
```

---

## Bug Report 2: `_get_last_event_time()` Reads File Without Lock

### Symptom
`get_chain_health()` can return a stale or `None` last event timestamp under concurrent load.

### Root Cause
**File:** `src/audit/__init__.py:395-402`

```python
def _get_last_event_time(self) -> Optional[str]:
    if not self.chain_file.exists():
        return None
    with open(self.chain_file) as f:
        for line in f:  # reads entire file to find last line
            pass
        last = json.loads(line)   # line is the LAST line from for loop
        return last.get("timestamp")
```

This reads `chain_file` without holding any lock. During concurrent append, the last line may not be the most recent committed event. Also, iterating to the last line for every health check is O(n) on a 380k+ line file — very expensive.

**Fix:** Cache `last_event_time` in memory, update it atomically in `append()` under lock. Use `get_chain_health()` cached result (already has 5s cache).

### Verification
```bash
# Check _get_last_event_time performance impact:
time PYTHONPATH=src .venv/bin/python -c "
from src.audit import get_audit_log
log = get_audit_log()
print(log._get_last_event_time())
"
# Should return in <1s, not 30+s
```

---

## Bug Report 3: `verify_chain()` Uses `prev_hash = _genesis_hash()` Hardcoded Start

### Symptom
If a chain rebuild corrects hashes for events 1..N, `verify_chain()` starting from `_genesis_hash()` will re-detect the old (wrong) hashes in a gap between rebuild completion and the next append, potentially triggering false tamper alerts.

### Root Cause
**File:** `src/audit/__init__.py:293`

```python
def verify_chain(self, key: Optional[str] = None, verify_per_user: bool = True):
    ...
    prev_hash = self._genesis_hash()  # Always starts from "0" * 64
```

On a rebuilt chain where old corrupted events have been replaced with correct ones, if `verify_chain()` runs during the rebuild window, it sees mismatched hashes and logs tamper alerts. The `_genesis_hash()` start means no checkpoint is used.

**Fix:** Use the `.last_hash` file as a checkpoint for incremental verification. On startup, verify only the last K events. Full chain verification should verify the full chain but handle rebuild windows gracefully.

### Verification
```bash
# Should not produce tamper alerts on a correctly rebuilt chain
PYTHONPATH=src .venv/bin/python -c "
from src.audit import verify_chain
valid, errors, count = verify_chain()
if errors:
    print(f'ERRORS: {errors}')
else:
    print(f'OK: {count} events verified')
"
```

---

## Bug Report 4: `get_chain_health()` Always Returns `chain_valid: True`

### Symptom
The health endpoint always reports healthy even when the chain is corrupted. This is because `get_chain_health()` does NOT call `verify_chain()` — it only returns in-memory state:

**File:** `src/audit/__init__.py:382-393`

```python
def get_chain_health(self) -> dict:
    # Fast-path: return metadata without full chain verification
    # Full verify_chain() with 380k+ entries blocks for >30s
    return {
        "chain_valid": True,  # ALWAYS True — never actually verified!
        "chain_length": self.event_count,
        ...
    }
```

**Fix:** Add an optional `full_verify: bool` parameter that runs `verify_chain()` periodically (e.g., every 5 minutes via background task, not on every health check). The fast-path should check file integrity markers (file size, last modified) rather than blindly returning True.

### Verification
```bash
curl -s http://localhost:8000/health/all | python -c "
import sys, json
data = json.load(sys.stdin)
print('chain_valid:', data.get('chain_valid'), '(should match verify_chain result)')
"
```

---

## Bug Report 5: `_per_user_key_manager` Singleton Per Import, Not Per Chain Key

### Symptom
If `CHAIN_KEY` changes (key rotation), the per-user key manager may use stale derived keys.

**File:** `src/audit/__init__.py:140-141`, `src/audit/per_user_keys.py`

```python
# In __init__:
from src.audit.per_user_keys import get_per_user_key_manager
self._per_user_key_manager = get_per_user_key_manager(self.CHAIN_KEY)
```

The `get_per_user_key_manager()` likely returns a cached singleton keyed by `CHAIN_KEY`. After key rotation (`self.CHAIN_KEY = new_key` at line 281), the manager still holds the old key's state. Per-user bindings computed after rotation use the new key but the manager's cache uses the old key.

**Fix:** In `rotate_key()`, after updating `self.CHAIN_KEY`, re-initialize `_per_user_key_manager` with the new key. Ensure the manager's cache is cleared on rotation.

### Verification
```bash
# After key rotation, verify user bindings still work
PYTHONPATH=src .venv/bin/python -c "
from src.audit import get_audit_log
log = get_audit_log()
events = log.get_recent_events(5)
for e in events:
    if e.get('user_id') != 'system':
        valid, err = log.verify_user_binding(e['user_id'], e['hash'])
        print(f'Event {e[\"event_id\"]}: user_bind valid={valid}')
"
```

---

## Prevention Recommendations

1. **Add integration test for concurrent appends**: Spawn 5 threads, each appending 100 events, then verify chain integrity. This would have caught Bug 1.
2. **Add `fcntl.flock` to prevent multi-process concurrent writes**: Even with threading lock, two processes would corrupt the file.
3. **Add chain health to the health endpoint**: Return actual `verify_chain()` result, not hardcoded `True`.
4. **Add lock timeout**: If `append()` blocks >10s, alert and consider circuit-breaking.
5. **Add rebuild safety lock**: Only one rebuild should run at a time — use a `.rebuild_lock` file with `fcntl.LOCK_EX`.

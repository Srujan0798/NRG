# Audit Check Evidence

**Skill**: audit-check
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/42_AUDIT_CHECK.md`

---

## Audit Chain Verification

### Command Executed

```bash
.venv/bin/python scripts/audit_investigate.py
.venv/bin/python -c "from src.audit import verify_chain; ..."
```

---

## Results

### Investigation Script Output

```json
{
  "ok": false,
  "events_checked": 383453,
  "broken_indices": [
    383363,
    383387
  ]
}
```

### verify_chain() Output

```
Valid: False
Count: 383362
Errors: 1
  - Line 383363: hash mismatch
```

---

## Analysis: Chain Has Corruption

### Discrepancy Found

| Tool | Errors Reported |
|------|----------------|
| `audit_investigate.py` | 2 broken indices (383363, 383387) |
| `verify_chain()` | 1 error (line 383363) |

**Likely cause**: `verify_chain()` stops at first error. Two corruption points exist.

---

## Chain Status: ⚠️ CORRUPTED (2 Points)

| Metric | Value |
|--------|-------|
| Total events | 383,453 |
| Broken indices | 2 (383363, 383387) |
| Corruption rate | 0.0005% |
| Chain valid | ❌ FALSE |

---

## Background

Previous session claimed chain was fixed:
> "Audit chain FIXED-AND-VERIFIED locally: Repaired `.audit/chain.jsonl` with timestamped backups... Evidence: `verify_chain()` → `valid True count 371661 errors 0`"

**Current state**: Chain is corrupted again. New corruption since last fix.

---

## Root Cause (from ADR-006)

The `_cosign_fire_and_forget` thread at `src/audit/__init__.py:244` is spawned INSIDE the lock, causing race conditions that corrupt the chain under concurrent writes.

**Evidence**: The broken indices (383363, 383387) are only 24 events apart — suggests concurrent appends corrupted the chain.

---

## Repair Plan

### Option 1: Automated Rebuild

```bash
.venv/bin/python scripts/audit_rebuild.py \
  --input .audit/chain.jsonl \
  --output .audit/chain_rebuilt.jsonl \
  --key $CHAIN_KEY
```

### Option 2: Manual Repair

```python
from scripts.audit_rebuild import rebuild_chain
results = rebuild_chain(
    chain_file,
    new_chain_path,
    CHAIN_KEY,
)
print(results)
```

---

## Prevention (ADR-006)

Until the **fcntl.flock** fix is applied, the chain will continue to corrupt under concurrent writes.

**Fix required**: Move `_cosign_fire_and_forget` thread spawn OUTSIDE the `with self._lock:` block.

---

## Skill Deliverable

**Status**: COMPLETED

**Critical finding**: Audit chain is CORRUPTED at 2 points (383363, 383387).
- Previous fix was temporary — corruption recurred
- Root cause: concurrent write race condition (ADR-006)
- Immediate action: Rebuild chain, then apply fcntl.flock fix

---
name: Audit log singleton cache (rebuild self-break)
description: NRG audit chain rebuild scripts must reset BOTH singletons or the rebuild's own completion event uses stale prev_hash and breaks the chain immediately
type: feedback
originSessionId: 7014f76a-31a3-459d-8da0-88c409d94538
---
After rebuilding `.audit/chain.jsonl` and the `.last_hash` file on disk, calling `get_audit_log().append(...)` from the same process appends with the **stale in-memory `prev_hash`** — the very next event's hash mismatches and the chain is invalid again. Pattern observed across 4 consecutive rebuilds (2026-04-25): each "REBUILD COMPLETE" was followed by `verify_chain() = (False, ['Line N+1: hash mismatch'], N+1)`.

Root cause: `src/audit/__init__.py` has **two** singletons — class-level `ImmutableAuditLog._instance` and module-level `_audit_log_instance`. `_reset()` clears only the class one. `get_audit_log()` returns the module one, which retains the cached `self.last_hash` from before the file rewrite.

**Why:** Cost real production-incident time. The chain rebuild script (`scripts/audit_rebuild.py`) was the canonical recovery tool, and it was leaving the chain broken on every run. Tag `v1.0.0-client-handover` had to be force-pushed twice because the first re-tag still showed `valid=False`.

**How to apply:**
- Any script/test that rewrites `.audit/chain.jsonl` or `.last_hash` and then calls `get_audit_log()` in the same process MUST do:
  ```python
  ImmutableAuditLog._reset()
  import src.audit as _audit_mod
  _audit_mod._audit_log_instance = None
  ```
  before the next `get_audit_log()` call. Fixed in `scripts/audit_rebuild.py` step 6 (commit `1562d694`).
- If you ever consolidate the two singletons into one, also update `_reset()` to clear the module-level reference, and audit every call site that holds a long-lived `audit_log = get_audit_log()` reference (they will still hold the stale instance).
- Long-running test suites and the FastAPI app hold `_audit_log_instance` for the process lifetime — concurrent rebuild while those are running will always leave a 1-event tail mismatch. Quiesce writers (kill pytest, stop uvicorn) before rebuilding for a truly clean chain.

---

### 2026-04-26 extension: AUDIT_CHAIN_KEY drift detection

Kimi/Moonshot (5th external review) flagged a related failure mode: `AUDIT_CHAIN_KEY` rotation between processes. If process A appends with key K1 and process B (or a later restart) verifies with key K2, every event after the rotation point fails — and the system has no signal that the *cause* was a key rotation, not corruption. Operators waste time investigating a non-corruption.

Required addition (does not lower the bar):

- The first line of `.audit/chain.jsonl` is a header: `{"_v": 1, "key_id": "<sha256(AUDIT_CHAIN_KEY)[:16]>", "created_at": "..."}`. Metadata only — not part of the chain hash sequence.
- On `verify_chain()` start, compute current `key_id` and compare to header. Mismatch returns a distinct error class (`KeyDriftError`) — operator knows the chain isn't corrupt; the key changed and the correct ops response is "rotate forward via documented procedure", not "rebuild from raw events".
- `scripts/audit_rebuild.py` refuses to overwrite the header on rebuild — it preserves the original `key_id` and adds a `rotated_at_event_n` field if the operator confirms a rotation. This makes rotation auditable.
- Test: `tests/audit/test_key_drift.py` writes a header with K1, verifies with K2, asserts `KeyDriftError` raised with both `key_id`s in the message.

This closes the operator-blame failure mode where a hash mismatch caused by an env-var change looks identical to corruption.

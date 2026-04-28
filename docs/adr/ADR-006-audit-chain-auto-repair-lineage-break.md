# ADR-006: Audit Chain Auto-Repair Lineage Break

**Date:** 2026-04-28
**Status:** Accepted with Mitigation
**Author:** Guru (Kimi)
**Supersedes:** Implicit assumption in ADR-003 that `verify_chain()` is the sole source of truth

## Context

On 2026-04-28, the audit chain verification reported `Line 1: hash mismatch`. The `get_chain_health()` function (called by the `/health` API endpoint) automatically triggered `repair_line1_hash_mismatch()`, which:

1. Archived the existing chain to a timestamped backup
2. Created a **new genesis event** with `event_id="genesis"` and `event_type="chain_genesis"`
3. Rehashed all historical events against this new genesis
4. Replaced the active chain file with the reseeded version

After repair, `verify_chain()` returned `(True, [], 296)`. However, the chain that existed before the repair had **350,748+ events**. The reseeded chain has **296 events**.

## Root Cause Analysis

### The Auto-Repair Trigger

```python
# src/audit/__init__.py::get_chain_health()
def get_chain_health(self, auto_repair: bool | None = None) -> dict:
    if auto_repair is None:
        auto_repair = os.environ.get("AUDIT_AUTO_REPAIR_LINE1", "1").lower() not in {
            "0", "false", "no", "off",
        }
    valid, errors, valid_count = self.verify_chain()
    if auto_repair and not valid and errors and errors[0].startswith("Line 1: hash mismatch"):
        repair = self.repair_line1_hash_mismatch()
        valid, errors, valid_count = self.verify_chain()
```

### Why Line 1 Mismatched

The Line 1 hash mismatch indicates the genesis event's stored hash does not match the hash computed from `prev_hash="" + genesis_event_data`. This can occur when:

1. **The chain file was modified** (tampering, corruption, or manual edit)
2. **The CHAIN_KEY changed** after genesis was written (same root cause as ADR-005)
3. **The genesis event itself was rewritten** by a prior repair or migration
4. **A new chain was started** on a different machine with a different genesis hash

### The Cryptographic Break

`repair_line1_hash_mismatch()` does NOT fix the original chain. It creates a **new chain** with a **new genesis** and copies all events into it. The cryptographic properties are:

| Property | Before Repair | After Repair |
|----------|---------------|--------------|
| Genesis hash | `G_orig` (unknown/unverifiable) | `G_new` (verifiable) |
| Event N hash | `H_N = HMAC(K, H_{N-1} \|\| data_N)` | `H'_N = HMAC(K, H'_{N-1} \|\| data_N)` |
| Hash chain continuity | Broken at line 1 | Continuous from new genesis |
| Tamper evidence | **Destroyed** — original lineage lost | Fresh lineage, no historical anchor |
| Event count | 350,748+ | 296 |

**Critical:** An attacker who tampered with the chain could trigger this repair, and the new chain would appear valid. The repair destroys evidence of the original compromise.

## Decision

1. **Immediate:** Document that auto-repair is a **recovery mechanism, not a security fix**. The repaired chain is operationally valid but cryptographically new.

2. **Immediate:** Set `AUDIT_AUTO_REPAIR_LINE1=false` in production environments. Auto-repair must be an explicit operator decision, not a silent side effect of `/health`.

3. **Short-term:** Add a `lineage_break` field to `get_chain_health()` that reports:
   - `lineage_intact: bool` — does the current genesis match the known genesis hash?
   - `reseeding_events: list[str]` — timestamps of all reseed operations
   - `original_event_count: int | None` — event count before first reseed

4. **Medium-term:** Implement **genesis hash pinning**:
   - Store the genesis hash in a separate WORM location (e.g., GPG-signed file, hardware security module, or append-only syslog)
   - `verify_chain()` checks the current genesis against the pinned hash
   - Any mismatch is CRITICAL, not auto-repaired

5. **Long-term:** Replace auto-repair with **operator-in-the-loop recovery**:
   - On Line 1 mismatch: halt writes, alert operator, require manual investigation
   - Provide `audit_rebuild.py --preserve-lineage` that attempts to find the original key before creating new genesis

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Disable auto-repair** (chosen) | Operator must investigate root cause | Chain stays broken until operator acts |
| **Keep auto-repair, log loudly** | System self-heals | False confidence; attacker can exploit |
| **Blockchain anchoring** | Immutable external witness | External dependency, cost, complexity |
| **Dual-chain (hot + cold)** | Cold chain preserves lineage | 2× storage, sync complexity |
| **Remove repair entirely** | Simplest | No recovery path for legitimate corruption |

## Action Items

- [x] Document this ADR
- [ ] Add `AUDIT_AUTO_REPAIR_LINE1=false` to `.env.example` and production configs
- [ ] Add `lineage_break` metadata to `get_chain_health()` return value
- [ ] Store `genesis_hash` in a separate, WORM-protected file at chain creation time
- [ ] Update `/health` endpoint to report CRITICAL when `lineage_intact=false`
- [ ] Update `audit_rebuild.py` with `--preserve-lineage` flag
- [ ] Back up all `chain_line1_hash_mismatch_backup_*` files to offline storage

## Verification

```bash
# Check current chain state
python -c "from src.audit import get_chain_health; print(get_chain_health(auto_repair=False))"

# Expected before fix:
# {"valid": true, "event_count": 296, "errors": [], "lineage_intact": false}
# (lineage_intact field does not yet exist — add it per Action Item 2)

# Check for reseed backups
ls -la .audit/chain_line1_hash_mismatch_backup_*.jsonl
# These are the ONLY copies of the original chain lineage.
```

## Consequences

### Positive
- System remains operational after chain corruption
- All events are preserved (in backup + reseeded chain)
- `/health` endpoint does not permanently report unhealthy

### Negative
- **Cryptographic lineage is broken** — the chain cannot prove continuity to its original genesis
- **Tamper evidence is destroyed** — any modification before repair is undetectable after repair
- **False confidence** — `verify_chain()=True` on a reseeded chain does not mean the original chain was uncompromised
- **Compliance risk** — DPDP-2023 and CERT-In audits may require proof of uninterrupted audit trail

## Related

- ADR-003: HMAC-SHA256 Audit Chain (original design)
- ADR-005: Audit Chain Key Environment Variable Incident (prior key-mismatch incident)
- `.claude/rules/external_audit.md` Rule 5: Health Endpoint Honesty
- `src/audit/__init__.py`: `get_chain_health()`, `repair_line1_hash_mismatch()`, `verify_chain()`

**Reviewed by:** Guru
**Next Review:** 2026-05-28

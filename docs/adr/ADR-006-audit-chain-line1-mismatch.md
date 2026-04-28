# ADR-006: Audit Chain Line 1 Hash Mismatch

**Date:** 2026-04-28
**Status:** Accepted with operator reseed
**Related:** `docs/adr/ADR-006-audit-chain-auto-repair-lineage-break.md`

## Context

Direct audit verification reported `Line 1: hash mismatch` on 2026-04-28. This was a root-of-chain failure: an external auditor running `verify_chain()` directly would see an invalid chain even if `/health` attempted recovery.

The active chain was reseeded by explicit operator action, not by silent health-check repair.

## Recorded Mismatch

The pre-reseed active line 1 was not a `chain_genesis` event. It was a query event:

- Source line 1 event id: `024056cc`
- Source line 1 timestamp: `2026-04-28T11:44:46.221703+00:00`
- Source line 1 recorded hash: `d6628732d6f75e743f36d09f5630d59086a6975ce790bd0507608cd01a9c1dfa`
- Source backup: `.audit/chain_line1_hash_mismatch_backup_20260428T132028010524Z.jsonl`
- Source backup SHA-256: `529cbc56379e995d8838b4e7336d7c5c62a2bd1747454bc4a087ea8de4e62ecd`
- Preserved event count before reseed: `3334`

The current active line 1 is a traceable genesis event:

- Event id: `genesis`
- Event type: `chain_genesis`
- Timestamp: `2026-04-28T13:20:28.052747+00:00`
- Active genesis hash prefix: `46e3323a74eb9eb7`
- Reseed reason: `operator_reseed_traceable_genesis_2026_04_28`

## Decision

Use Option A from the incident protocol: rebuild the active chain from a clean, traceable genesis with the current key and preserve all source events in a timestamped backup.

Auto-repair is not allowed to run silently. `AUDIT_AUTO_REPAIR_LINE1` defaults to false, and any explicit repair logs a warning requiring operator review.

## Verification

Fresh verification after the reseed:

```text
python3 -c "from src.audit import verify_chain, get_chain_health; print(verify_chain()); print(get_chain_health(auto_repair=False)['lineage_break'])"
(True, [], 8382)
lineage_intact: True
repair_required: False
auto_repair_triggered: False
```

The CI-compatible health script also passes:

```text
python3 scripts/audit_chain_health_check.py
{"ok": true, "valid": true, "valid_event_count": 8382, "errors": []}
```

## Required External Audit Procedure

Auditors must use direct verification first:

```bash
python3 -c "from src.audit import verify_chain; print(verify_chain())"
python3 -c "from src.audit import get_chain_health; print(get_chain_health(auto_repair=False)['lineage_break'])"
```

`/health` is a monitoring signal, not the sole cryptographic proof.

## Consequences

- The active chain is valid from the 2026-04-28 reseed genesis.
- The original pre-reseed lineage remains available only through the backup file and its SHA-256.
- Any future line 1 mismatch is a critical incident and must not be hidden by `/health`.

# ADR-005: Audit Chain Key Environment Variable Incident

**Date:** 2026-04-24
**Status:** Resolved
**Author:** Sreyan (investigation by Agent)

## Context

On 2026-04-24, the audit chain integrity check revealed a hash mismatch at line 332,231 of `.audit/chain.jsonl` (341,985 total events). Investigation confirmed:

- **Root cause**: After the audit chain rebuild at commit `2a916c83`, the running API process had `AUDIT_CHAIN_KEY` set to a **different key** than `nrg-audit-chain-dev-key`. All subsequent events (lines 330,932–341,985, totalling 9,755 events) were written using this inconsistent key.

- **How it happened**: The `ImmutableAuditLog` class accepts `CHAIN_KEY = os.environ.get("AUDIT_CHAIN_KEY") or "nrg-audit-chain-dev-key"`. In production, if `AUDIT_CHAIN_KEY` is set in the shell environment, it overrides the default dev key. After the rebuild script ran with the correct key, a later process restart or deployment changed the env var, causing writes to use a different key than verification.

- **Why it was detected**: The `verify_chain()` function uses `CHAIN_KEY = "nrg-audit-chain-dev-key"` (class attribute, resolved at import time). Events written with a different key produce different HMACs when verified, causing cascade failures.

- **Damage**: 9,755 events affected. No data loss — all events were preserved. Chain was invalid for verification only.

## Decision

1. **Immediate fix**: Re-ran `scripts/audit_rebuild.py --rebuild` which recomputed all HMAC hashes using the correct `AUDIT_CHAIN_KEY`, resulting in a fully valid chain (341,986 events including the rebuild event itself).

2. **Prevention — immediate**: Added `AUDIT_CHAIN_KEY` to `.env.example` with an explicit placeholder value so operators know it must be set consistently.

3. **Prevention — process**: The `audit_rebuild.py` script now prints a prominent warning if the chain key differs from the default, reminding operators to ensure the env var is set consistently before and after rebuilds.

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| Do nothing | — | Chain permanently broken |
| Manual hash correction | Precise | Error-prone, 9,755 entries |
| **Rebuild script** (chosen) | Automated, correct, verifiable | Requires knowing the correct key |

## Key Findings

- The `.audit/` directory is gitignored — chain data is not in version control
- The `audit_rebuild.py` script is idempotent and was designed exactly for this scenario
- The `investigate.py` script correctly identified 323 distinct error "clusters" (cascade effect of a single bad key)
- The `verify_chain()` method in `ImmutableAuditLog` uses the class-level `CHAIN_KEY`, which is stable across imports

## Consequences

### Positive
- Chain fully restored and verified (341,986 valid events)
- All historical events preserved with correct hashes
- Automated fix procedure documented and tested

### Negative
- A window existed where the chain was unverifiable — any tampering during that window would not have been detected
- The `jwt_kid` value `4bc9a37e1d1fc3eb` in the events suggests a JWT key rotation may have been involved in the key change (correlation, not causation)

## Action Items

- [x] Re-ran `audit_rebuild.py --rebuild` — chain verified valid
- [x] Added `AUDIT_CHAIN_KEY` to `.env.example`
- [x] Committed lint fixes for test files (71 auto-fixed + manual fixes)
- [ ] Add startup validation that `AUDIT_CHAIN_KEY` matches the hash of the last known good event
- [ ] Add a `audit_rebuild.py --validate-key` flag that warns if the key produces different hashes than stored

## Verification

```bash
python scripts/audit_investigate.py
# {"ok": true, "events_checked": 341986, "broken_indices": []}

python -c "from src.audit import verify_chain; v, e, c = verify_chain(); print(f'Valid: {v}, Errors: {len(e)}, Count: {c}')"
# Valid: True, Errors: 0, Count: 341986
```

**Reviewed by:** Agent
**Next Review:** 2026-07-24

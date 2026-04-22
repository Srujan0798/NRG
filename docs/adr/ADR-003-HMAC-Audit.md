# ADR-003: HMAC-SHA256 Audit Chain

**Date:** 2026-04-21  
**Status:** Accepted  
**Author:** Architect Agent

## Context

NRG must provide an immutable audit trail for:
- Government compliance (DPDP-2023)
- Internal accountability
- Forensic analysis

## Decision

Implement **HMAC-SHA256 chained audit log** where each entry's hash includes the previous entry's hash.

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **HMAC chain** (chosen) | Tamper-evident, self-validating | No searchability |
| Blockchain | Decentralized trust | Overkill, costly |
| Append-only DB | Searchable | Requires trusted admin |
| Syslog | Standard, searchable | Not integrity-verified |

## Rationale

1. **Tamper evidence**: Any modification breaks the chain
2. **Self-validating**: `audit_investigate.py` can verify in O(n)
3. **No external dependency**: Works offline
4. **Performance**: 6K+ entries verify in <1s

## Implementation

```python
def append_audit(event: AuditEvent):
    prev_hash = get_last_hash()
    serialized = json.dumps(event, sort_keys=True)
    event_hash = hmac.new(CHAIN_KEY, prev_hash + serialized, sha256).hexdigest()
    event["hash"] = event_hash
    write_to_chain(event)
    set_last_hash(event_hash)
```

## Verification

```bash
python scripts/audit_investigate.py
# Returns: {"ok": true, "events_checked": 6079, "broken_indices": []}
```

## Consequences

### Positive
- Tamper-evident: modification impossible without detection
- Simple verification
- DPDP audit requirement met

### Negative
- No search (must scan sequentially)
- Chain key must be secured
- Deletion breaks chain (feature, not bug)

**Reviewed by:** Guardian Agent  
**Next Review:** 2026-07-21
# ADR-003: Why HMAC-SHA256 for Audit Trail

**Date:** 2026-04-21  
**Status:** Accepted  
**Deciders:** Architecture Team, Security Team, Compliance Officer  
**Review:** 2026-07-21

---

## Context

NRG must provide an immutable, tamper-evident audit trail for:
- **Government compliance**: DPDP-2023 Section 9 (Data Audit)
- **Accountability**: Query attribution to users
- **Forensic analysis**: Incident investigation
- **Regulatory evidence**: Court/legal proceedings

The audit system must guarantee that once logged, entries cannot be modified or deleted without detection.

---

## Decision

Implement **HMAC-SHA256 chained audit log** where each entry's hash includes the previous entry's hash, creating an immutable chain.

### Chain Structure

```
Genesis Entry (index 0):
  hash = HMAC(chain_key, "genesis")

Entry N (index N):
  hash = HMAC(chain_key, hash(N-1) + serialized_event)
```

---

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **HMAC chain** (chosen) | Tamper-evident, self-validating, no external dependency | No searchability (sequential scan) | ✅ Accepted |
| Blockchain | Decentralized trust, immutable | Overkill for single-org, costly gas fees | ❌ Rejected |
| Append-only DB | Searchable via SQL | Requires trusted admin to prevent deletes | ❌ Rejected |
| Syslog | Standard, searchable | Not integrity-verified, requires external service | ❌ Rejected |
| Blockchain-as-a-Service | Managed, trusted | Single point of failure, vendor lock-in | ❌ Rejected |

---

## Rationale

### 1. Tamper Evidence
Any modification to historical entries breaks the chain:

```python
# If attacker modifies entry N:
# New hash(N) = HMAC(chain_key, hash(N-1) + modified_content)
# Original hash(N) != New hash(N)
# Verification fails immediately
```

### 2. Self-Validating
Verification script can check entire chain in O(n):
```python
def verify_chain():
    for i in range(1, len(events)):
        expected_hash = hmac.new(CHAIN_KEY, events[i-1]["hash"] + events[i]["content"])
        if events[i]["hash"] != expected_hash:
            return False, i
    return True, len(events)
```

### 3. Offline Operation
No external dependencies — works in air-gapped environments.

### 4. Performance
6,000+ entries verify in <1 second on commodity hardware.

### 5. DPDP Compliance
Meets Section 9 requirements for "accurate and complete" data audit.

---

## Implementation

### Entry Structure

```python
@dataclass
class AuditEntry:
    index: int
    timestamp: datetime
    event_type: str  # "query", "auth", "admin", "data_access"
    user_id: str
    action: str
    resource: str
    result: str  # "success", "denied", "error"
    metadata: dict
    previous_hash: str
    hash: str
```

### Chain Append Algorithm

```python
def append_audit(event: AuditEvent) -> str:
    prev_entry = get_last_entry()
    prev_hash = prev_entry["hash"] if prev_entry else GENESIS_HASH

    serialized = json.dumps({
        "timestamp": event.timestamp.isoformat(),
        "event_type": event.event_type,
        "user_id": event.user_id,
        "action": event.action,
        "resource": event.resource,
        "result": event.result,
        "metadata": event.metadata,
        "previous_hash": prev_hash,
    }, sort_keys=True)

    event_hash = hmac.new(
        CHAIN_KEY,
        prev_hash.encode() + serialized.encode(),
        sha256
    ).hexdigest()

    entry = {
        "index": prev_entry["index"] + 1 if prev_entry else 0,
        **json.loads(serialized),
        "hash": event_hash
    }

    write_entry(entry)
    return event_hash
```

### Verification Script

```bash
python scripts/audit_investigate.py
# Output: {"ok": true, "events_checked": 6079, "broken_indices": []}
```

---

## Consequences

### Positive
- Tamper-evident: modification impossible without detection
- Simple verification — anyone can run `audit_investigate.py`
- DPDP audit requirement met out-of-the-box
- No external dependencies (works offline)
- Fast verification even with millions of entries

### Negative
- No searchability — must scan sequentially for queries
- Chain key must be secured (loss = chain broken)
- Deletion breaks chain (feature, not bug)
- Cannot recover from partial corruption without backup

### Risks
- Chain key compromise
  - Mitigation: Hardware security module (HSM), key rotation procedure
- Physical media failure
  - Mitigation: Redundant storage, regular backups
- Natural disaster
  - Mitigation: Off-site backup, disaster recovery plan

---

## Security Controls

| Control | Implementation |
|---------|---------------|
| Key Storage | Environment variable + HSM in production |
| Key Rotation | 90-day rotation with chain continuity |
| Backup | Encrypted backup every 24 hours |
| Verification | Weekly automated verification run |
| Access | Write-only for application, no delete permissions |

---

## References

- [HMAC Audit Documentation](docs/security/AUDIT_LOG.md)
- [DPDP Compliance Mapping](docs/compliance/DPDP_2023_MAPPING.md)
- [Audit Investigation Script](scripts/audit_investigate.py)

---

**Reviewed by:** Guardian Agent, Compliance Officer  
**Sign-off:** 2026-04-21
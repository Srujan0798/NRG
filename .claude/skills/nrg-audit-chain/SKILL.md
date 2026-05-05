---
name: nrg-audit-chain
description: Use when implementing, verifying, repairing, or reviewing NRG audit-chain integrity, HMAC events, co-signatures, tamper detection, and evidence binding.
---

# NRG Audit Chain Skill

Immutable audit chain with HMAC verification, Postgres co-signature, tamper detection, and evidence binding for the National Research Graph (NRG).

## When to Use

Use this skill when:
- Implementing or reviewing the NRG audit chain
- Verifying chain integrity after suspected tampering
- Adding new event types to the audit pipeline
- Designing evidence binding for compliance reports
- Debugging HMAC mismatch or co-signature lag
- Preparing for government audits (CERT-In, DPDP Board)

## Audit Chain Architecture

```
Event Source → Event Normalizer → HMAC Signer → Postgres Writer
                                              ↓
                                         Co-Signature Worker
                                              ↓
                                         Chain Merkle Root
                                              ↓
                                         Verification API
```

Every event is:
1. **Normalized** to canonical JSON schema
2. **HMAC-signed** with per-user salt + global secret
3. **Written** to Postgres with previous hash pointer
4. **Co-signed** by independent worker with separate key
5. **Included** in periodic Merkle root commitment

## Event Schema

```json
{
  "event_id": "uuid-v4",
  "event_type": "QUERY_EXECUTED | SCHEMA_CHANGE | CONSENT_GRANTED | TIER_SWITCH | DATA_EXPORT | AUTH_FAILURE | ANOMALY_DETECTED",
  "timestamp": "2026-04-25T00:25:45.987+05:30",
  "actor": {
    "type": "user | system | admin",
    "id": "user-uuid or system-id",
    "tier": "public | industry | academic | government"
  },
  "resource": {
    "type": "query | table | row | vector | consent_record",
    "id": "resource-identifier"
  },
  "action": {
    "verb": "SELECT | INSERT | UPDATE | DELETE | EXPORT | GRANT | REVOKE",
    "detail": "normalized action description"
  },
  "context": {
    "ip_address": "hashed-ip",
    "user_agent_hash": "sha256-of-ua",
    "session_id": "session-uuid",
    "request_id": "request-uuid"
  },
  "previous_hash": "sha256-of-previous-event",
  "payload_hash": "sha256-of-event-payload",
  "hmac": "hmac-sha256-of-above",
  "cosign": "hmac-sha256-with-cosign-key"
}
```

## HMAC Implementation

### Per-User Salts

```python
import hashlib
import hmac
import secrets
import json

GLOBAL_SECRET = "loaded-from-env-NRG_AUDIT_SECRET"
COSIGN_SECRET = "loaded-from-env-NRG_COSIGN_SECRET"

def get_user_salt(user_id: str) -> bytes:
    """Deterministic per-user salt from global secret."""
    return hashlib.sha256(f"{GLOBAL_SECRET}:{user_id}".encode()).digest()

def sign_event(event: dict, user_id: str) -> str:
    """HMAC-SHA256 of canonical event JSON."""
    salt = get_user_salt(user_id)
    canonical = json.dumps(event, sort_keys=True, separators=(',', ':'))
    return hmac.new(salt, canonical.encode(), hashlib.sha256).hexdigest()

def cosign_event(event: dict) -> str:
    """Independent co-signature with separate secret."""
    canonical = json.dumps(event, sort_keys=True, separators=(',', ':'))
    return hmac.new(COSIGN_SECRET.encode(), canonical.encode(), hashlib.sha256).hexdigest()
```

### Chain Linkage

```python
def append_event(
    event: dict,
    previous_hash: str,
    user_id: str
) -> dict:
    """Append event to chain with hash linkage."""
    event["previous_hash"] = previous_hash
    event["payload_hash"] = hashlib.sha256(
        json.dumps(event, sort_keys=True, separators=(',', ':')).encode()
    ).hexdigest()
    event["hmac"] = sign_event(event, user_id)
    event["cosign"] = cosign_event(event)
    return event
```

## Postgres Schema

```sql
CREATE TABLE audit_events (
    event_id UUID PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor JSONB NOT NULL,
    resource JSONB NOT NULL,
    action JSONB NOT NULL,
    context JSONB,
    previous_hash VARCHAR(64) NOT NULL,
    payload_hash VARCHAR(64) NOT NULL,
    hmac VARCHAR(64) NOT NULL,
    cosign VARCHAR(64) NOT NULL,
    merkle_root VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_events_timestamp ON audit_events(timestamp);
CREATE INDEX idx_audit_events_type ON audit_events(event_type);
CREATE INDEX idx_audit_events_actor_id ON audit_events((actor->>'id'));
CREATE INDEX idx_audit_events_resource_id ON audit_events((resource->>'id'));

-- Merkle root commitment table
CREATE TABLE audit_merkle_roots (
    root_hash VARCHAR(64) PRIMARY KEY,
    start_event_id UUID NOT NULL,
    end_event_id UUID NOT NULL,
    event_count INTEGER NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Verification Pipeline

### Single Event Verification

```python
def verify_event(event: dict) -> bool:
    """Verify HMAC + cosign + hash chain integrity."""
    # Verify payload hash
    payload_copy = {k: v for k, v in event.items() if k not in ('hmac', 'cosign', 'payload_hash')}
    computed_payload_hash = hashlib.sha256(
        json.dumps(payload_copy, sort_keys=True, separators=(',', ':')).encode()
    ).hexdigest()
    if computed_payload_hash != event["payload_hash"]:
        return False
    
    # Verify HMAC
    user_id = event["actor"]["id"]
    computed_hmac = sign_event(event, user_id)
    if not hmac.compare_digest(computed_hmac, event["hmac"]):
        return False
    
    # Verify cosign
    computed_cosign = cosign_event(event)
    if not hmac.compare_digest(computed_cosign, event["cosign"]):
        return False
    
    return True
```

### Chain Verification

```python
def verify_chain(from_event_id: str | None = None) -> dict:
    """Verify full chain or subset from given event."""
    query = """
        SELECT * FROM audit_events
        WHERE event_id >= COALESCE(%s, (SELECT MIN(event_id) FROM audit_events))
        ORDER BY timestamp, event_id
    """
    events = db.execute(query, (from_event_id,))
    
    results = {"total": len(events), "valid": 0, "invalid": 0, "first_invalid": None}
    prev_hash = "0" * 64  # Genesis hash
    
    for event in events:
        if event["previous_hash"] != prev_hash:
            results["invalid"] += 1
            if results["first_invalid"] is None:
                results["first_invalid"] = event["event_id"]
            continue
        
        if not verify_event(event):
            results["invalid"] += 1
            if results["first_invalid"] is None:
                results["first_invalid"] = event["event_id"]
            continue
        
        results["valid"] += 1
        prev_hash = event["payload_hash"]
    
    return results
```

### Merkle Root Commitment

```python
import hashlib

def compute_merkle_root(hashes: list[str]) -> str:
    """Compute Merkle root of event hashes."""
    if len(hashes) == 0:
        return "0" * 64
    if len(hashes) == 1:
        return hashes[0]
    
    # Pairwise hash
    next_level = []
    for i in range(0, len(hashes), 2):
        left = hashes[i]
        right = hashes[i + 1] if i + 1 < len(hashes) else hashes[i]
        next_level.append(hashlib.sha256((left + right).encode()).hexdigest())
    
    return compute_merkle_root(next_level)

def commit_merkle_root(start_id: str, end_id: str):
    """Periodic commitment of batch to merkle root."""
    events = db.execute(
        "SELECT payload_hash FROM audit_events WHERE event_id BETWEEN %s AND %s ORDER BY event_id",
        (start_id, end_id)
    )
    hashes = [e["payload_hash"] for e in events]
    root = compute_merkle_root(hashes)
    
    db.execute(
        "INSERT INTO audit_merkle_roots (root_hash, start_event_id, end_event_id, event_count) VALUES (%s, %s, %s, %s)",
        (root, start_id, end_id, len(hashes))
    )
    
    # Update events with root reference
    db.execute(
        "UPDATE audit_events SET merkle_root = %s WHERE event_id BETWEEN %s AND %s",
        (root, start_id, end_id)
    )
    
    return root
```

## Co-Signature Worker

Runs as independent process with separate secret:

```python
# workers/audit_cosign.py
import time

def cosign_worker():
    while True:
        unsigned = db.execute(
            "SELECT * FROM audit_events WHERE cosign IS NULL LIMIT 100"
        )
        for event in unsigned:
            event["cosign"] = cosign_event(event)
            db.execute(
                "UPDATE audit_events SET cosign = %s WHERE event_id = %s",
                (event["cosign"], event["event_id"])
            )
        time.sleep(1)
```

**Critical:** Co-sign worker must run on separate machine/VM with different access credentials. If primary audit server is compromised, co-sign integrity proves tampering.

## Evidence Binding

Bind external evidence to audit chain for legal/compliance:

```python
def bind_evidence(
    evidence_id: str,
    evidence_hash: str,
    evidence_type: str,
    actor_id: str
) -> dict:
    """Create audit event linking external evidence."""
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "EVIDENCE_BOUND",
        "actor": {"type": "system", "id": actor_id, "tier": "system"},
        "resource": {"type": "evidence", "id": evidence_id},
        "action": {
            "verb": "BIND",
            "detail": f"Evidence {evidence_type} hash:{evidence_hash}"
        },
        "context": {"evidence_hash": evidence_hash},
    }
    return append_event(event, get_last_hash(), actor_id)
```

## Tamper Detection Alerts

| Alert | Trigger | Severity |
|-------|---------|----------|
| `HMAC_MISMATCH` | Single event HMAC fails | P1 |
| `CHAIN_BREAK` | previous_hash mismatch | P1 |
| `COSIGN_MISSING` | Event >5s without cosign | P2 |
| `MERKLE_MISMATCH` | Recomputed root ≠ stored root | P1 |
| `GAP_DETECTED` | Missing sequence in event IDs | P1 |
| `DUPLICATE_HASH` | Same payload_hash appears twice | P2 |

## Monitoring

```promql
# Events per minute
rate(nrg_audit_events_total[5m])

# Verification failures (MUST be 0)
nrg_audit_verification_failures_total

# Co-sign lag histogram
histogram_quantile(0.99, rate(nrg_audit_cosign_lag_seconds_bucket[5m]))

# Merkle root commitment rate
rate(nrg_audit_merkle_commitments_total[5m])

# Chain length
count(nrg_audit_events_total)
```

## Backup and Recovery

1. **Streaming replica:** Postgres streaming replica for audit_events table on separate node
2. **WAL archiving:** Continuous WAL archive to Indian-soil object storage
3. **Read-only replica:** Query chain verification from replica, never primary
4. **Cold storage:** Monthly export of merkle roots + root hashes to offline storage

**Recovery procedure:**
1. Identify last valid merkle root before corruption point
2. Rebuild chain from that root forward
3. Flag gap period for investigation
4. Notify DPO and Data Protection Board if personal data involved

## Sovereign Constraints

1. **Keys on HSM:** GLOBAL_SECRET and COSIGN_SECRET stored on Indian-government-approved HSM
2. **No foreign cloud:** Audit data never leaves Indian jurisdiction
3. **Tamper-proof by design:** Any modification breaks HMAC chain; co-sign proves independent verification
4. **Legal admissibility:** Merkle root commitments provide cryptographic proof for courts
5. **Retention:** 7 years minimum for government-mandated records ( aligns with DPDP + CERT-In requirements)

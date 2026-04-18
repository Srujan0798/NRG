# NRG Immutable Audit Log Specification v1.0

## Overview

Every query, plan, SQL, vector-query, and LLM-call writes to an append-only store with HMAC-SHA256 chaining.

## Attack Surface

| Threat | Mitigation |
|--------|------------|
| Tampering | HMAC chaining prevents modification |
| Deletion | WAL-style append-only |
| Repudiation | Immutable timestamps + user binding |

## Implementation

### HMAC Chain

```
h_0 = genesis_hash (0^64)
h_n = HMAC(key, h_{n-1} || event_n)

event_n = {
  event_id, event_type, timestamp, user_id,
  query, sql, vector_query, llm_call, result
}
```

### Storage

- `.audit/chain.jsonl` - WAL-style append-only
- `.audit/.last_hash` - Current chain head
- `.audit/merkle_root.json` - Daily Merkle root

### Event Types

| Type | Fields |
|------|-------|
| `query` | event_id, user_id, query, timestamp |
| `plan` | event_id, user_id, query, llm_call (plan JSON) |
| `sql` | event_id, user_id, sql, result |
| `vector_query` | event_id, user_id, query, vector_query |
| `llm_call` | event_id, user_id, llm_call (prompt, model, response) |
| `error` | event_id, user_id, error |

### Usage

```python
from src.audit import log_query, log_plan, log_sql

# Log query
log_query(user_id, user_query)

# Log plan
log_plan(user_id, user_query, plan_json)

# Log SQL execution
log_sql(user_id, sql, result)

# Verify chain integrity
valid, errors = verify_audit_chain()
```

### Verification

```python
from src.audit import get_audit_log

audit = get_audit_log()
valid, errors = audit.verify_chain()
# Returns (True, []) if valid
# Returns (False, [error list]) if tampered
```

### Daily Merkle Root

```python
merkle_root = audit.get_merkle_root()
# {
#   "date": "2026-04-18",
#   "merkle_root": "abc123...",
#   "event_count": 150
# }
```

## API Endpoint

```bash
GET /audit/verify - Verify chain integrity
GET /audit/merkle - Get daily Merkle root
GET /audit/events?user_id={id}&limit=100 - Query events
```

---

*100% of API endpoints emit a chained event. pytest proves tamper detection.*
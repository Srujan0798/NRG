# NRG Redis Caching Skill

Redis caching patterns, rate limiting, session management, and query result caching for the National Research Graph (NRG).

## When to Use

Use this skill when:
- Implementing or reviewing Redis cache layers in NRG
- Configuring rate limiting for API tiers
- Designing session/token storage strategies
- Debugging cache-related performance issues
- Choosing between Redis data structures for NRG workloads

## NRG Redis Topology

```
┌─────────────────────────────────────────────┐
│              Redis (single-node or cluster)   │
│  ┌─────────────┐  ┌─────────────┐            │
│  │  Rate Limit │  │   Session   │            │
│  │    Store    │  │    Store    │            │
│  └─────────────┘  └─────────────┘            │
│  ┌─────────────┐  ┌─────────────┐            │
│  │ Query Result│  │  Pub/Sub    │            │
│  │    Cache    │  │  (events)   │            │
│  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────┘
```

All Redis data is transient. No PII or research data persists in Redis beyond TTL.

## Key Namespacing

Use the `nrg:` prefix with colon-delimited hierarchy:

```
nrg:rl:{tier}:{client_id}:{endpoint}      # Rate limit counters
nrg:session:{token_hash}                   # JWT session metadata
nrg:cache:query:{hash}                     # Cached query results
nrg:cache:schema:{table}:{version}         # Cached schema metadata
nrg:lock:{resource}                        # Distributed locks
nrg:pubsub:{channel}                       # Event channels
```

## Rate Limiting (Sliding Window)

NRG uses per-tier rate limits. Implement with Redis sorted sets:

```python
import redis
import time

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

TIER_LIMITS = {
    "public":      {"rpm": 10,   "rph": 100},
    "industry":    {"rpm": 60,   "rph": 1000},
    "academic":    {"rpm": 120,  "rph": 5000},
    "government":  {"rpm": 300,  "rph": 20000},
}

def is_rate_limited(tier: str, client_id: str, endpoint: str) -> bool:
    key = f"nrg:rl:{tier}:{client_id}:{endpoint}"
    now = time.time()
    window = 60  # 1-minute window for rpm check
    
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window)
    _, _, count, _ = pipe.execute()
    
    limit = TIER_LIMITS.get(tier, {}).get("rpm", 10)
    return count > limit
```

**Key behaviors:**
- Use `zremrangebyscore` to clean expired entries atomically
- `zcard` gives exact count in window
- Always set `expire` to prevent key accumulation

## Query Result Caching

Cache SQL query results to reduce DB load on repeated questions:

```python
import hashlib
import json

def cache_query_result(question: str, sql: str, result: list, ttl: int = 300):
    """Cache query result with 5-min default TTL."""
    cache_key = f"nrg:cache:query:{hashlib.sha256(sql.encode()).hexdigest()[:16]}"
    payload = {
        "question": question,
        "sql": sql,
        "result": result,
        "cached_at": time.time(),
    }
    r.setex(cache_key, ttl, json.dumps(payload))

def get_cached_query(sql: str) -> dict | None:
    cache_key = f"nrg:cache:query:{hashlib.sha256(sql.encode()).hexdigest()[:16]}"
    raw = r.get(cache_key)
    return json.loads(raw) if raw else None
```

**Invalidation triggers:**
- Schema change (DDL) → flush `nrg:cache:schema:*` and `nrg:cache:query:*`
- Data ingestion batch → flush relevant table caches only
- Manual admin command → `FLUSHDB` or targeted `DEL`

## Session/Token Storage

Store JWT metadata (not the token itself) for revocation checks:

```python
def store_session(token_jti: str, tier: str, user_id: str, ttl: int = 3600):
    key = f"nrg:session:{token_jti}"
    r.hset(key, mapping={
        "tier": tier,
        "user_id": user_id,
        "created_at": time.time(),
    })
    r.expire(key, ttl)

def is_token_revoked(token_jti: str) -> bool:
    return not r.exists(f"nrg:session:{token_jti}")
```

**Never store:** raw JWTs, passwords, PII, research data in Redis.

## Distributed Lock Pattern

For critical operations (schema migrations, batch ingestion):

```python
def acquire_lock(resource: str, ttl: int = 30) -> bool:
    key = f"nrg:lock:{resource}"
    return r.set(key, "1", nx=True, ex=ttl) is not None

def release_lock(resource: str):
    r.delete(f"nrg:lock:{resource}")
```

Always wrap lock acquisition in try/finally with release.

## Pub/Sub for Real-Time Events

Use for audit event streaming, cache invalidation broadcasts:

```python
# Publisher
r.publish("nrg:pubsub:audit", json.dumps({
    "event_type": "QUERY_EXECUTED",
    "tier": "government",
    "timestamp": time.time(),
}))

# Subscriber (in separate worker)
p = r.pubsub()
p.subscribe("nrg:pubsub:audit")
for message in p.listen():
    if message['type'] == 'message':
        process_audit_event(json.loads(message['data']))
```

## Redis Memory Management

| Policy | Setting | When to Use |
|--------|---------|-------------|
| `allkeys-lru` | `maxmemory-policy` | General NRG cache (default) |
| `volatile-lru` | `maxmemory-policy` | When some keys must never evict |
| `maxmemory` | `256mb` per instance | Adjust per node capacity |

Monitor with:
```
INFO memory
INFO keyspace
```

**Alert if:**
- `used_memory / maxmemory > 0.85`
- `evicted_keys` spikes unexpectedly
- `connected_clients` > pool size

## Sovereign Constraint

Redis must run on Indian-soil infrastructure. No Redis Cloud, Upstash, or external Redis providers. Use self-hosted Redis or Redis Cluster within the sovereign boundary.

## Connection Pooling

```python
from redis import ConnectionPool

pool = ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    max_connections=50,
    socket_connect_timeout=5,
    socket_timeout=5,
    health_check_interval=30,
)
```

Always use connection pools. Never create new Redis clients per request.

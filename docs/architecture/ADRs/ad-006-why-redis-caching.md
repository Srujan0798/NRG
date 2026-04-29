# ADR-006: Why Redis for Caching

**Date:** 2026-04-21  
**Status:** Accepted  
**Deciders:** Architecture Team, DevOps Team  
**Review:** 2026-07-21

---

## Context

NRG requires a caching layer for:
- **Session storage**: JWT blacklist, rate limit counters
- **Query result caching**: Reduce database and LLM load
- **Rate limiting**: Per-tier request quotas
- **Distributed state**: Cross-instance coordination

We evaluated Redis, Memcached, and in-memory caching.

---

## Decision

Use **Redis** as the primary caching and state management layer.

---

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Redis** (chosen) | Rich data structures, persistence, cluster | Memory cost | ✅ Accepted |
| Memcached | Simple, memory efficient | No persistence, no complex types | ❌ Rejected |
| In-memory (Python) | No infrastructure | No sharing, lost on restart | ❌ Rejected |
| PostgreSQL session | Single database | Slower than Redis for frequent access | ❌ Rejected |

---

## Rationale

### 1. Multi-Purpose Caching

Redis serves multiple use cases efficiently:

```python
# Rate limiting (sorted set)
redis.zadd(f"ratelimit:{user_id}", {str(time.time()): 1})
redis.zremrangebyscore(f"ratelimit:{user_id}", 0, time.time() - 60)
count = redis.zcard(f"ratelimit:{user_id}")

# Session blacklist (hash)
redis.hset("blacklist", access_token_jti, "1")
redis.expire("blacklist", jwt_ttl)

# Query cache (string with TTL)
redis.setex(f"query:{cache_key}", 30, json.dumps(results))

# User quota (hash)
redis.hincrby(f"quota:{user_tier}", user_id, 1)
```

### 2. Persistence Options

Redis provides RDB + AOF persistence for durability:
```yaml
# docker-compose.yml
redis:
  command: redis-server --appendonly yes --appendfsync everysec
  volumes:
    - redis_data:/data
```

### 3. Tier-Based Rate Limiting

```python
RATE_LIMITS = {
    1: 100,   # Researcher: 100 req/min
    2: 50,    # Government: 50 req/min
    3: 20,    # Industry: 20 req/min
}

def check_rate_limit(user_id: str, tier: int) -> bool:
    key = f"ratelimit:{tier}:{user_id}"
    count = redis.incr(key)
    if count == 1:
        redis.expire(key, 60)  # Reset every minute
    return count <= RATE_LIMITS[tier]
```

### 4. Cluster Mode

Redis Cluster provides horizontal scaling:
```yaml
# Production config
redis:
  image: redis:7-alpine
  command: redis-server --cluster-enabled yes
```

### 5. Observability

Redis exports metrics to Prometheus:
```python
redis_info = redis.info()
prometheus_gauge("redis_memory_bytes").set(redis_info["used_memory"])
```

---

## Implementation

### Docker Compose

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: >
    redis-server
    --maxmemory 512mb
    --maxmemory-policy allkeys-lru
    --appendonly yes
```

### Client Usage

```python
import redis.asyncio as redis

class CacheService:
    def __init__(self):
        self.redis = redis.from_url(os.environ["REDIS_URL"])

    async def get_query_cache(self, key: str):
        data = await self.redis.get(f"query:{key}")
        return json.loads(data) if data else None

    async def set_query_cache(self, key: str, value: dict, ttl: int = 30):
        await self.redis.setex(f"query:{key}", ttl, json.dumps(value))

    async def check_rate_limit(self, user_id: str, tier: int) -> bool:
        key = f"ratelimit:{tier}:{user_id}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 60)
        return count <= RATE_LIMITS[tier]

    async def blacklist_token(self, jti: str, ttl: int):
        await self.redis.setex(f"blacklist:{jti}", ttl, "1")
```

### Connection Pool

```python
# src/db/redis.py
from redis import ConnectionPool

pool = ConnectionPool(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    max_connections=20,
    decode_responses=True
)

def get_redis():
    return redis.Redis(connection_pool=pool)
```

---

## Consequences

### Positive
- Multi-purpose: caching, rate limiting, session management
- Persistence for durability
- Cluster mode for horizontal scaling
- Rich observability metrics
- Mature, production-tested

### Negative
- Additional infrastructure to maintain
- Memory costs at scale
- Connection pool management needed

### Risks
- Redis downtime affects rate limiting and caching
  - Mitigation: Fallback to allow requests, log warning
- Memory exhaustion
  - Mitigation: LRU eviction, monitoring alerts

---

## Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| Cache hit rate | > 60% | Monitor in Grafana |
| Redis latency (p99) | < 5ms | `redis-cli --latency` |
| Memory usage | < 512MB | `redis INFO memory` |

---

## References

- [Observability Setup](docs/OBSERVABILITY.md)
- [Rate Limiting Implementation](docs/ops/dr_runbook.md)
- [Ops Runbook](../OPERATIONS_RUNBOOK.md)

---

**Reviewed by:** DevOps Team, Architecture Team  
**Sign-off:** 2026-04-21

# Neon Postgres Evidence

**Skill**: neon-postgres
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/41_NEON_POSTGRES.md`

---

## Neon Postgres: NRG Assessment

### Overview

NRG currently uses **PostgreSQL 14** (via Docker) for production and **SQLite** for development. The Neon skill provides guidance for serverless Postgres.

---

## NRG Current Setup

| Environment | Database | Hosted | Connection |
|-------------|----------|--------|------------|
| Development | SQLite | Local | `sqlite:///nrg_research.db` |
| Production | PostgreSQL 14 | Docker | `postgres://...` |

---

## Neon Recommendation for NRG

### When to Consider Neon

NRG is a government/academic research platform. Neon would be beneficial if:

1. **Autoscaling needed** — Research queries spike during business hours
2. **Scale-to-zero** — If usage is intermittent
3. **Branching** — Need isolated dev/staging environments
4. **No DBA** — Neon reduces operational overhead

### NRG Would Benefit From:

| Neon Feature | NRG Use Case |
|-------------|--------------|
| **Branching** | Create isolated branch per developer for testing |
| **Read Replicas** | Scale read-heavy queries (researchers searching) |
| **Point-in-time restore** | Protect audit chain data |
| **Connection pooling** | Handle bursty research query loads |

---

## Connection Assessment

### Current Connection Method

NRG uses direct SQLAlchemy connection:
```python
db = NRGDatabase()
db.execute_query(sql, user_tier=user_tier)
```

### Neon-Compatible Connection

Would need:
```python
from neondatabase import NeonDatabase
# or
from src.data.database import NRGDatabase  # Already abstracted
```

**Assessment**: Connection is already abstracted — minimal code change needed to switch to Neon.

---

## Migration Path to Neon

### Option A: Full Migration (Recommended for Scale)

1. Create Neon project: `neonctl projects create --name nrg`
2. Get connection string: `postgresql://user:pass@ep-xxx.neon.tech/nrg`
3. Update `DATABASE_URL` env var
4. Run migrations: `alembic upgrade head`
5. Verify: `pytest tests/integration/test_postgresql_connection.py`

**Effort**: 2-4 hours
**Risk**: Low (connection already abstracted)

### Option B: Dual-Write (Read Replica)

1. Keep PostgreSQL as primary (writes)
2. Add Neon as read replica (reads)
3. Route research queries to Neon

**Effort**: 4-8 hours
**Risk**: Medium (eventual consistency)

---

## NRG Specific Considerations

### Audit Chain Data

The audit chain (`chain.jsonl`) is file-based, NOT in PostgreSQL. Moving to Neon won't affect it.

### Schema Parity

Neon won't solve the 40-table schema drift. That needs migration work regardless.

### Qdrant (Vector DB)

Neon doesn't replace Qdrant. Vector search remains separate.

---

## Recommendations for NRG

| Priority | Action | Why |
|----------|--------|-----|
| P1 | Migrate prod PostgreSQL to Neon | Scalability, branching |
| P2 | Set up dev branch per developer | Isolated testing |
| P3 | Add read replica for queries | Performance |
| P3 | Point-in-time restore for audit | Compliance |

---

## Not Applicable

The NRG stack has:
- SQLite (dev) — wouldn't use Neon for dev
- PostgreSQL (prod) — could migrate to Neon
- Qdrant (vector) — separate from Neon

**Decision**: Neon is a good fit for production but not urgent. Fix SQL injection first.

---

## Skill Deliverable

**Status**: COMPLETED

Neon assessment for NRG:
- NRG uses PostgreSQL (Docker) — Neon could replace it
- Connection already abstracted — minimal code change
- Would benefit from branching, read replicas, autoscaling
- Not urgent — fix SQL injection and schema parity first

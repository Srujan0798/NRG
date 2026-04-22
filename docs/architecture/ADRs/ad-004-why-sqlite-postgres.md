# ADR-004: Why SQLite for Development, PostgreSQL for Production

**Date:** 2026-04-21  
**Status:** Accepted  
**Deciders:** Architecture Team, DevOps Team  
**Review:** 2026-10-21

---

## Context

NRG requires a database that:
- Works in local development without infrastructure
- Scales to production workloads with high concurrency
- Supports row-level security for tier-based access
- Meets DPDP-2023 compliance requirements

We evaluated two primary options: SQLite (development) and PostgreSQL (production).

---

## Decision

**Dual-database strategy:**

1. **Development**: SQLite for local development and testing
2. **Production**: PostgreSQL 16+ with Neon Serverless

This provides developer simplicity while ensuring production scalability.

---

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **SQLite dev + PostgreSQL prod** (chosen) | Best of both worlds, clear separation | Schema sync complexity | ✅ Accepted |
| PostgreSQL everywhere | Single database, no sync | Local dev friction, Docker required | ❌ Rejected |
| SQLite everywhere | Zero setup | Won't scale, no RLS support | ❌ Rejected |
| MySQL | Familiar, good tooling | Limited JSON support, no RLS | ❌ Rejected |

---

## Rationale

### SQLite for Development

1. **Zero Configuration**: `sqlite:///nrg_research.db` works immediately
2. **No Docker Required**: Developers can run without docker-compose
3. **Fast Iteration**: File-based, no connection overhead
4. **Testing**: Easy to create in-memory test databases

```python
# Development: SQLite
DATABASE_URL=sqlite:///nrg_research.db

# Connection handling
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
```

### PostgreSQL for Production

1. **Row-Level Security (RLS)**: Critical for tier-based access
```sql
CREATE POLICY researcher_tier ON researchers
    FOR SELECT USING (access_tier >= 1);

CREATE POLICY government_tier ON researchers
    FOR SELECT USING (access_tier >= 2);
```

2. **Connection Pooling**: Neon provides up to 100 connections
3. **Scalability**: Handle 10,000+ concurrent queries
4. **JSON Support**: Rich document storage for metadata
5. **Neon Branching**: Dev branches for schema changes

### Schema Synchronization

```python
# Alembic for migrations
alembic upgrade head  # Apply all migrations

# Migration files
versions/
  001_init.sql         # Base schema
  002_add_tier.sql     # Tier columns
  003_neon_optimization.sql  # Production optimizations
```

---

## Implementation

### Development Setup

```bash
# Clone repo
git clone https://github.com/nrg/nrg
cd nrg

# Install
pip install -e .
pip install spacy && python -m spacy download en_core_web_sm

# Run (SQLite by default)
python -m src.api.main
# Database: ./nrg_research.db
```

### Production Setup

```bash
# Environment variables
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-1.neon.tech/nrg?sslmode=require
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Neon branching for schema changes
git push && neon branch create --name feature/my-change
# Test in branch, merge to main
```

### Alembic Configuration

```python
# alembic.ini
[database]
sqlalchemy.url = sqlite:///nrg_research.db  # Dev default

[postgresql]
sqlalchemy.url = postgresql://user:pass@host/db  # Override for prod
```

---

## Consequences

### Positive
- Developers can run locally without Docker or cloud services
- Clear migration path from dev to production
- RLS provides defense-in-depth for tier enforcement
- Neon serverless reduces operational overhead

### Negative
- Schema changes must work on both databases
- SQLite doesn't support all PostgreSQL features (e.g., arrays)
- Must test on both before deployment

### Risks
- Schema divergence between dev and prod
  - Mitigation: Mandatory schema reviews, dual testing
- Connection string mismatch
  - Mitigation: Environment validation on startup

---

## Comparison Matrix

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Setup | Zero (built-in) | Requires Neon/cloud |
| Concurrent writes | Limited (single writer) | Full concurrency |
| Row-level security | No | Yes (critical for NRG) |
| JSON support | Basic | Full JSONB |
| Full-text search | FTS5 (limited) | pg_trgm + GIN |
| Scaling | Single machine | Horizontal |
| Cost | Free | ~$20/month Neon |

---

## References

- [Neon Integration](docs/schema/neon_integration.md)
- [Data Model](docs/architecture/DATA_MODEL.md)
- [Migration Guide](docs/schema/README.md)

---

**Reviewed by:** DevOps Team, Architecture Team  
**Sign-off:** 2026-04-21
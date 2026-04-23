# NRG Deployment Guide

## Overview

NRG supports three deployment targets: **local development**, **staging**, and **production**. All deployments use Docker Compose for local/staging and ECS for production.

## Architecture

```
Browser → CDN → nginx (TLS termination, static, rate limiting)
                    ├── /api/     → API (4 uvicorn workers, 2 replicas)
                    ├── /         → Frontend (2 replicas, nginx serving React build)
                    └── /health   → Health checks (no auth)
```

**Services:**
- **api** — FastAPI + Python backend (port 8000)
- **frontend** — React SPA served by nginx (port 3000)
- **postgres** — PostgreSQL 16 (port 5432, dev/staging only)
- **qdrant** — Qdrant v1.11.3 vector DB (port 6333)
- **redis** — Redis 7 (port 6379)
- **nginx** — Reverse proxy + TLS (ports 80/443)
- **kong** — API gateway, rate limiting (dev only, port 8080/8443)

---

## Prerequisites

- Docker Engine 24+
- Docker Compose v2.20+
- Python 3.11+ (for local dev)
- AWS CLI (for ECS deployment)
- `psycopg2-binary`, `requests`, `alembic` (install via `pip install -e ".[dev]"`)

---

## Local Development

```bash
# Start all services
docker compose --profile dev up

# Start with PostgreSQL (instead of SQLite)
docker compose --profile dev --profile postgres up

# Stop
docker compose down

# View logs
docker compose logs -f api
```

Environment: `.env.dev` (or `.env`)

---

## Staging Deployment

### Docker Compose (docker-compose.yml + docker-compose.prod.yml)

```bash
# Build images
docker compose build

# Start prod stack (overrides dev settings)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify health
curl http://localhost:8000/health/all
```

### AWS ECS (recommended for staging)

```bash
# Deploy via CI/CD pipeline
# Every PR merge to main triggers automatic staging deploy
./scripts/deploy.py --env staging --version v1.2.3
```

Or via AWS console: push image to ECR → update ECS service → wait for stability.

---

## Production Deployment

### 1. Pre-Deployment Checklist

- [ ] All CI checks green (tests, lint, security scan, docker-smoke)
- [ ] Migration scripts tested on staging
- [ ] Rollback plan verified
- [ ] Stakeholders notified
- [ ] Database backup completed

### 2. Environment Variables

**Required for production:**

```bash
# Database
POSTGRES_USER=nrg_prod
POSTGRES_PASSWORD=<from-secrets-manager>
POSTGRES_DB=nrg
POSTGRES_PORT=5432

# JWT (min 32 chars, random)
JWT_SECRET_KEY=<generate: openssl rand -hex 32>

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Langfuse Observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://langfuse.com

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=nrg_research

# App
APP_ENV=production
LOG_LEVEL=INFO

# Redis
REDIS_URL=redis://redis:6379/0

# AWS
AWS_REGION=ap-south-1
AWS_ROLE_ARN_PROD=<arn>
ECR_REGISTRY=<account>.dkr.ecr.ap-south-1.amazonaws.com
```

**Validation:** The deploy script checks required vars and warns if missing. Missing vars at runtime cause startup failure with clear error messages.

### 3. Build & Deploy

```bash
# Option A: Manual deploy script
./scripts/deploy.py --env production --version v1.2.3 --confirm

# Option B: GitHub Actions (automatic on main merge)
# See .github/workflows/cd.yml
```

### 4. Verify Deployment

```bash
# Health checks
curl https://api.nrg.gov.in/health/all

# Smoke test
./scripts/deploy.py --env production --health-check

# Logs
aws logs tail /ecs/nrg-api --follow
```

### 5. Rollback

```bash
# Immediate rollback
./scripts/deploy.py --env production --rollback
```

Or via AWS Console: select previous task definition → update service.

---

## Database Migrations

### Local (SQLite)

```bash
cd src/migrations
alembic upgrade head
```

### Production (PostgreSQL)

```bash
# Set DATABASE_URL to production PostgreSQL
export DATABASE_URL=postgresql://user:pass@prod-host:5432/nrg

# Run pending migrations
alembic upgrade head

# Check current version
alembic current

# Create new migration
alembic revision --autogenerate -m "Add new table"
```

### Schema Migration: SQLite → PostgreSQL

```bash
# Verify schema parity before migrating
python scripts/migrate_data_to_postgresql.py --mode verify --sqlite-db ./nrg_research.db --pg-url postgresql://...

# Export data from PostgreSQL
python scripts/migrate_data_to_postgresql.py --mode export --pg-url postgresql://... --output ./migration_export

# Import into SQLite
python scripts/migrate_data_to_postgresql.py --mode import --input ./migration_export --sqlite-db ./nrg_research.db

# Sync SQLite → PostgreSQL (one-time)
python scripts/migrate_data_to_postgresql.py --mode sync --sqlite-db ./nrg_research.db --pg-url postgresql://...
```

---

## Qdrant Sharding

```bash
# Setup production collection (4 shards, replication factor 2)
python scripts/qdrant_shard_config.py --setup --shards 4 --replication 2

# Monitor status
python scripts/qdrant_shard_config.py --status --collection nrg_research

# Zero-downtime re-index
python scripts/qdrant_shard_config.py --reindex --new-version v2
# [run re-indexing...]
python scripts/qdrant_shard_config.py --swap-alias --from-col nrg_research --to-col nrg_research_v2
```

---

## Docker Image Sizes

| Image | Stage | Approximate Size |
|-------|-------|-------------------|
| api (builder) | builder | ~800MB |
| api (runner) | runner | <300MB |
| frontend (builder) | builder | ~600MB |
| frontend (runner) | nginx | ~50MB |

Target: all runner images < 300MB. Achieved.

---

## Health Endpoints

| Endpoint | Auth | Rate Limit | Description |
|----------|-------|------------|-------------|
| `GET /health` | No | No | Basic liveness |
| `GET /health/all` | No | No | Full health (DB, Qdrant, Redis, LLM) |
| `GET /health/db` | No | No | Database connectivity |
| `GET /health/qdrant` | No | No | Qdrant connectivity |
| `GET /health/redis` | No | No | Redis connectivity |
| `GET /health/llm` | No | No | LLM provider health |
| `GET /metrics` | Internal | No | Prometheus metrics |

---

## CI/CD Pipeline

See `.github/workflows/ci.yml` for full pipeline.

**Required gates for production deployment:**
1. All Python tests pass (coverage ≥ 80%)
2. All security tests pass
3. Lint (ruff) + type check (mypy) pass
4. Secrets scan (gitleaks) clean
5. Docker smoke test passes
6. Frontend build + lint passes
7. Property-based tests pass
8. Contract tests pass

**Deploy flow:**
```
main branch → CI pipeline → staging auto-deploy → manual approval → production
```

---

## Troubleshooting

### API won't start

```bash
# Check env vars
docker compose exec api env | grep -E "DATABASE|POSTGRES|JWT"

# Check logs
docker compose logs api --tail=100

# Verify DB connectivity
docker compose exec api python -c "from src.config.database import get_database_manager; print(get_database_manager().health_check())"
```

### Qdrant slow / not responding

```bash
# Check Qdrant status
docker compose exec qdrant wget -qO- http://localhost:6333/readyz

# View logs
docker compose logs qdrant --tail=50

# Reset Qdrant (clears vectors, keeps config)
docker compose exec qdrant rm -rf /qdrant/storage/*
docker compose restart qdrant
```

### Database migration fails

```bash
# Check current version
alembic current

# Check migration history
alembic history

# Manually stamp version
alembic stamp <revision>
```

### Frontend 502 errors

```bash
# Verify frontend is running
docker compose ps frontend

# Check nginx proxy logs
docker compose logs nginx --tail=50

# Restart frontend
docker compose restart frontend
```

### High memory usage

```bash
# Check container memory
docker stats --no-stream

# API memory limit: 4GB (prod). If approaching limit:
# - Reduce UVICORN_WORKERS from 4 to 2
# - Enable query result caching
```

---

## Security Checklist

- [ ] TLS certificates valid (Let's Encrypt or purchased)
- [ ] JWT_SECRET_KEY is random, not default
- [ ] PostgreSQL password is strong, not in git
- [ ] Rate limiting configured (nginx + Kong)
- [ ] Security headers set (X-Frame-Options, CSP, etc.)
- [ ] Health endpoints not exposed publicly (use internal network)
- [ ] No secrets in Docker images (use env vars or docker secrets)
- [ ] gitleaks scan passes in CI
- [ ] OWASP dependency check passes
- [ ] RBAC policies tested for all 6 personas

---

## Performance Targets

| Metric | Target |
|--------|--------|
| API response time (P95) | < 2s |
| Query response time (P95) | < 15s |
| Frontend TTFB | < 200ms |
| Qdrant similarity search | < 100ms |
| Docker cold start | < 30s |
| Full stack health check | < 5s |
| Deployment (ECS) | < 5 min |
| Zero-downtime deploy | Yes |

---

## Backup & Recovery

### PostgreSQL (production)

```bash
# Backup
pg_dump -h prod-host -U nrg -d nrg > backup_$(date +%Y%m%d).sql

# Restore
psql -h prod-host -U nrg -d nrg < backup_20240101.sql
```

### SQLite (development)

```bash
# Backup
cp nrg_research.db nrg_research.db.backup

# Restore
cp nrg_research.db.backup nrg_research.db
```

### Qdrant

```bash
# Snapshot (via Qdrant API)
curl -X POST http://localhost:6333/collections/nrg_research/snapshots

# Restore
curl -X PUT -F 'snapshot=@snapshot.tar.gz' http://localhost:6333/collections/nrg_research/snapshots/upload
```

---

## Monitoring

- **Logs**: CloudWatch (ECS), ELK stack, or Datadog
- **Metrics**: Prometheus scraping `/metrics` endpoint
- **Tracing**: Langfuse (configured in LANGFUSE env vars)
- **Alerting**: PagerDuty / OpsGenie for critical failures

---

## Adding a New Service

1. Add to `docker-compose.yml` with healthcheck
2. Add to nginx upstream config if needs HTTP exposure
3. Add to deploy script if ECS service
4. Add to health check endpoint
5. Add to CI docker-smoke test
6. Document above
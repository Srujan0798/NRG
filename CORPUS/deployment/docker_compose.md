# NRG Docker Compose Setup

## Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `nrg-postgres` | postgres:16-alpine | 5432 | Primary database |
| `nrg-pgbouncer` | pgbouncer:latest | 6432 | Connection pooler |
| `nrg-redis` | redis:7-alpine | 6379 | Cache, sessions |
| `nrg-qdrant` | qdrant/qdrant:latest | 6333 | Vector store |
| `nrg-api` | nrg-api (built) | 8000 | FastAPI backend |
| `nrg-frontend` | nrg-frontend (built) | 5173 | React dev server |
| `nrg-nginx` | nginx:alpine | 80/443 | Reverse proxy |

## Quick Start

```bash
# Start all services
docker compose up -d

# Start only data services
docker compose up -d postgres redis qdrant

# View logs
docker compose logs -f api

# Health check
curl http://localhost:8000/health
```

## Environment Variables

Key variables from `.env`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `POSTGRES_USER` | nrg | DB user |
| `POSTGRES_PASSWORD` | (empty) | DB password |
| `POSTGRES_DB` | nrg | DB name |
| `DATABASE_URL` | sqlite:///nrg_research.db | Fallback DB |
| `QDRANT_HOST` | localhost | Vector store host |
| `QDRANT_PORT` | 6333 | Vector store port |
| `REDIS_URL` | redis://localhost:6379 | Cache URL |

## Production Differences

- `docker-compose.prod.yml` — production overrides
- `docker-compose.dev.yml` — development overrides
- Kubernetes manifests in `infrastructure/helm/`

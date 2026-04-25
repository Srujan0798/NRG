# Deploy-Local Status — Session 92

**Date:** 2026-04-25

---

## Service Status

| Service | Status | Port | Health |
|---------|--------|------|--------|
| PostgreSQL | ✅ Running (healthy) | 5432 | 13h uptime |
| Redis | ✅ Running (healthy) | 6379 | 13h uptime |
| Qdrant | ❌ Unreachable | 6333/6334 | Not responding |
| API (FastAPI) | ✅ Running | 8000 | Healthy, chain valid |
| Frontend | ❌ Not running | 5173 | — |

---

## API Health Details

```json
{
  "status": "healthy",
  "consent_service": "operational",
  "retriever": {
    "status": "ok",
    "collection": "nrg_research",
    "qdrant_reachable": true,      ← reports True (cached?)
    "vectors_indexed": 19323
  },
  "database": {
    "status": "healthy",
    "dialect": "sqlite",
    "researchers": 5615,
    "publications": 12000
  },
  "audit": {
    "chain_valid": true,
    "chain_length": 382653,
    "valid_events": 382653,
    "error_count": 0
  }
}
```

**Chain length grew from 378,779 → 382,653** (+3,874 events) since the last rebuild session. Chain is currently valid.

---

## Issues

### Issue 1: Qdrant Container Unhealthy
**Severity:** 🔴 High
**Container:** `nrg-qdrant` — reports `unhealthy` in `docker ps`

Qdrant is either down or not responding on its health check endpoint. The API's retriever reports "qdrant_reachable: true" but this may be from a cached/lazy check.

**Fix:**
```bash
docker logs nrg-qdrant --tail 20
docker restart nrg-qdrant
sleep 10 && curl -s http://localhost:6333/health
```

### Issue 2: Frontend Not Running
**Severity:** 🟡 Medium

The frontend dev server is not running. Users need to start it manually.

**Fix:**
```bash
cd /Users/srujansai/Desktop/NRG/frontend && npm run dev
```

### Issue 3: API Running on SQLite (not PostgreSQL)
**Severity:** 🟡 Medium (info)
**Finding:** `"dialect": "sqlite"` — API is using SQLite, not the running PostgreSQL container.

This may be intentional for local dev. The PostgreSQL container at 5432 is for production/scale deployments.

---

## Commands to Start Full Stack

```bash
# 1. Check Docker
docker info > /dev/null 2>&1 && echo "OK" || echo "Start Docker"

# 2. Start infrastructure
docker-compose -f docker-compose.dev.yml up -d postgres redis

# 3. Fix Qdrant if unhealthy
docker restart nrg-qdrant
sleep 10 && curl -s http://localhost:6333/health

# 4. Start API (already running on port 8000)
# Skip if already running
.venv/bin/uvicorn src.api.main:app --reload --port 8000 &

# 5. Start frontend
cd frontend && npm run dev &

# 6. Verify
curl -s http://localhost:8000/health | python -m json.tool
```

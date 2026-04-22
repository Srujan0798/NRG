# NRG Operations Runbook

**National Research Graph — Deployment & Operations**

---

## 1. Deployment

### 1.1 Prerequisites

```bash
# Install dependencies
make bootstrap

# Set environment
cp .env.example .env
# Edit .env with production values
```

### 1.2 Local Development

```bash
# Start full stack
docker-compose up -d

# Or manually:
# Terminal 1: API
.venv/bin/python -m uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### 1.3 Production

```bash
# Build images
docker-compose build

# Deploy
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

---

## 2. Monitoring

### 2.1 Health Checks

```bash
# Full health
curl http://localhost:8000/health/all

# Individual services
curl http://localhost:8000/health/db
curl http://localhost:8000/health/llm
curl http://localhost:8000/health/qdrant
```

### 2.2 Metrics

| Endpoint | Purpose |
|----------|---------|
| `/metrics` | Prometheus metrics |
| `/audit/verify` | Audit chain integrity |

### 2.3 Logs

```bash
# API logs
tail -f logs/api.log

# Audit logs
tail -f .protocol/audit_log.jsonl
```

---

## 3. Troubleshooting

### 3.1 Common Issues

| Symptom | Fix |
|---------|-----|
| 401 on valid token | Check JWT keys exist at `infrastructure/kong/ssl/` |
| 429 Rate limit | Wait 60s or increase tier limit |
| Qdrant unavailable | `docker-compose restart qdrant` |
| Database locked | Check concurrent connections |

### 3.2 Debug Commands

```bash
# Verify audit chain
python scripts/audit_investigate.py

# Test database
sqlite3 nrg_research.db "SELECT COUNT(*) FROM researchers"

# Test auth
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}'
```

---

## 4. Scaling

### 4.1 Horizontal Scaling

```bash
# Scale API
kubectl scale deployment nrg-api --replicas=3

# Scale workers
kubectl scale deployment nrg-worker --replicas=5
```

### 4.2 Database

```bash
# PostgreSQL read replica
# Add to DATABASE_URL: ?replica=host

# Qdrant cluster
# Set QDRANT_HOSTS=node1:6333,node2:6333
```

---

## 5. Backup & Recovery

### 5.1 Database Backup

```bash
# SQLite
cp nrg_research.db nrg_research_backup.db

# PostgreSQL
pg_dump nrg > nrg_backup.sql
```

### 5.2 Audit Log Backup

```bash
cp .protocol/audit_log.jsonl audit_backup.jsonl
```

### 5.3 Restore

```bash
# Stop services
docker-compose down

# Restore database
cp nrg_research_backup.db nrg_research.db

# Restart
docker-compose up -d
```

---

## 6. Maintenance

### 6.1 Data Retention (DPDP)

```bash
# Run consent cleanup (recommended: daily cron)
python -c "from src.services.consent import ConsentService; \
  ConsentService().cleanup_expired_consents()"
```

### 6.2 Reindex

```bash
# Qdrant reindex
curl -X POST http://localhost:6333/collections/nrg/points/reindex
```

---

## 7. Alerting

### 7.1 Alert Rules

| Condition | Severity | Action |
|-----------|-----------|--------|
| API P95 > 5s | Warning | Check LangGraph |
| Audit chain broken | Critical | Page on-call |
| 5xx > 1% | Warning | Check API logs |
| Disk > 80% | Warning | Clean old logs |

---

**Author:** DevOps Team  
**Version:** 1.0  
**Updated:** 2026-04-21
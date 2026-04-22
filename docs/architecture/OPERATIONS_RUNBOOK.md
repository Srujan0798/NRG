# NRG Operations Runbook

**National Research Graph — Production Operations Guide**
**Version:** 1.0 | **Date:** 2026-04-21 | **Classification:** Operations Confidential

---

## 1. Deployment Procedures

### 1.1 Environment Overview

| Environment | Purpose | URL |
|-------------|---------|-----|
| Development | Local dev, testing | localhost:8000 |
| Staging | Pre-production validation | staging.nrg.gov.in |
| Production | Live system | api.nrg.gov.in |

### 1.2 Development Deployment

```bash
# Clone and setup
git clone https://github.com/nrg/nrg
cd nrg

# Install dependencies
pip install -e .
python -m spacy download en_core_web_sm

# Configure environment
cp .env.example .env
# Edit .env with development values

# Start API server
python -m uvicorn src.api.main:app --reload --port 8000

# Start frontend (separate terminal)
cd frontend && npm install && npm run dev

# Verify health
curl http://localhost:8000/health
```

### 1.3 Staging Deployment

```bash
# SSH to staging server
ssh ops@staging.nrg.gov.in

# Pull latest image
cd /opt/nrg
git pull
docker-compose pull

# Run database migrations
docker-compose exec api alembic upgrade head

# Restart services
docker-compose restart api worker

# Verify deployment
curl https://staging.nrg.gov.in/health/all
```

### 1.4 Production Deployment

```bash
# Pre-deployment checklist
# - [ ] All tests passing in staging
# - [ ] Security scan completed
# - [ ] Backup verified
# - [ ] Rollback plan prepared

# Deploy with zero-downtime
ssh ops@api.nrg.gov.in

# Create backup
docker-compose exec postgres pg_dump -U nrg > /backup/nrg_$(date +%Y%m%d).sql

# Rolling update
docker-compose up -d --remove-orphans
docker-compose exec api python scripts/warm_cache.py

# Health verification
curl https://api.nrg.gov.in/health/all

# Verify audit chain
curl https://api.nrg.gov.in/audit/verify | jq
```

### 1.5 Docker Compose Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: nrg/api:${VERSION}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - NVIDIA_API_KEY=${NVIDIA_API_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    image: nrg/api:${VERSION}
    command: python -m src.worker
    deploy:
      replicas: 5

  postgres:
    image: postgres:16
    volumes:
      - pg_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=nrg
      - POSTGRES_USER=nrg
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  qdrant:
    image: qdrant/qdrant:v1.7.0
    volumes:
      - qdrant_data:/qdrant/storage

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  pg_data:
  qdrant_data:
  redis_data:
```

---

## 2. Monitoring Dashboards

### 2.1 Grafana Dashboard Layout

**Dashboard:** NRG Operations Dashboard
**URL:** https://grafana.nrg.gov.in/d/nrg-ops

```
┌─────────────────────────────────────────────────────────────────────┐
│ System Health                                                          │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│ │ API Status  │ │ Qdrant      │ │ Audit Chain │ │ LLM Status  │     │
│ │     UP      │ │     UP      │ │     OK      │ │   HEALTHY   │     │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘     │
├─────────────────────────────────────────────────────────────────────┤
│ Query Performance          │ LLM & Cost Analytics                    │
│ ┌───────────────────────┐  │ ┌───────────────────────────────────┐  │
│ │ p50: 1.2s  p95: 4.2s  │  │ │ Token usage by provider           │  │
│ │ Success: 99.2%        │  │ │ NVIDIA: 45M/hr | Local: 12M/hr   │  │
│ └───────────────────────┘  │ └───────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│ Security Events           │ Tier Distribution                       │
│ ┌───────────────────────┐  │ ┌───────────────────────────────────┐  │
│ │ PII Blocks: 12        │  │ │ Tier 1: 45% | Tier 2: 35% | T3: 20%│  │
│ │ Injection: 0          │  │ └───────────────────────────────────┘  │
│ └───────────────────────┘  │                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Key Metrics to Monitor

| Metric | Normal Range | Alert Threshold | Action |
|--------|--------------|-----------------|--------|
| API availability | > 99.5% | < 99% | Check pods, restart |
| Query latency p95 | < 5s | > 10s | Check LLM, DB |
| Audit chain | OK | BROKEN | Critical: investigate |
| Cache hit rate | > 60% | < 40% | Warm cache |
| LLM error rate | < 5% | > 10% | Check provider |
| Rate limit throttle | < 5% | > 15% | Review limits |

### 2.3 Alert Interpretation

```
ALERT: HighLLMErrorRate
├── Symptom: LLM error rate > 10%
├── Diagnosis:
│   ├── Check NVIDIA API status
│   ├── Verify local LLM health: curl localhost:8080/health
│   └── Check token quota: nvidia cc -u
├── Mitigation:
│   ├── If NVIDIA down → fallback to local (automatic)
│   ├── If local unhealthy → kubectl rollout restart deploy/llama-cpp
│   └── If quota exceeded → contact NVIDIA, temp switch to local
└── Escalation: If not resolved in 30min, escalate to ML Platform team
```

---

## 3. Troubleshooting Guide

### 3.1 Error Classification

| Error Type | HTTP Code | Description | Resolution |
|------------|-----------|-------------|------------|
| Authentication | 401 | Invalid/expired token | Refresh token |
| Authorization | 403 | Tier insufficient | Check user tier |
| Not Found | 404 | Resource doesn't exist | Verify ID |
| Rate Limited | 429 | Quota exceeded | Wait, upgrade tier |
| Server Error | 500 | Internal failure | Check logs, restart |

### 3.2 Common Issues

#### Issue: 401 on valid token

**Diagnosis:**
```bash
# Check JWT key exists
ls -la infrastructure/kong/ssl/jwt RS256.pem

# Verify token expiry
jwt decode $ACCESS_TOKEN

# Check Redis blacklist
redis-cli GET blacklist:<jti>
```

**Resolution:**
1. Verify JWT RS256 keys are in place
2. Check token expiry (access: 1hr, refresh: 7 days)
3. Ensure Redis is running for blacklist checks
4. Clear browser cookies, re-login

#### Issue: 429 Rate Limit

**Diagnosis:**
```bash
# Check current quota usage
curl -H "Authorization: Bearer $TOKEN" https://api.nrg.gov.in/user/profile
# Look for X-RateLimit-* headers

# Check Redis rate limit keys
redis-cli KEYS "ratelimit:*"
```

**Resolution:**
1. Wait 60 seconds (window resets)
2. For higher limits, contact admin to upgrade tier quota
3. Check if quota values are correct in config

#### Issue: Qdrant unavailable

**Diagnosis:**
```bash
# Check Qdrant health
curl http://qdrant:6333/health

# Check pod status
kubectl get pods -n nrg | grep qdrant

# Check logs
kubectl logs -n nrg deploy/qdrant --tail=100
```

**Resolution:**
```bash
# If pod is down
kubectl rollout restart deploy/qdrant -n nrg

# If disk full
kubectl patch pvc qdrant-storage -n nrg -p \
  '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'

# Verify collection exists
curl http://qdrant:6333/collections/nrg_research
```

#### Issue: Database locked

**Diagnosis:**
```bash
# Check PostgreSQL connections
docker-compose exec postgres psql -U nrg -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname='nrg';"

# Check for long-running transactions
docker-compose exec postgres psql -U nrg -c \
  "SELECT pid, duration, query FROM pg_stat_activity WHERE state='active';"
```

**Resolution:**
```bash
# Kill long-running queries
docker-compose exec postgres psql -U nrg -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity \
   WHERE duration > interval '5 minutes';"

# If connection pool exhausted, restart API
kubectl rollout restart deploy/api -n nrg
```

#### Issue: Audit chain broken

**Diagnosis:**
```bash
# Verify audit chain
curl https://api.nrg.gov.in/audit/verify | jq

# Run manual verification
python scripts/audit_investigate.py
```

**Response format:**
```json
{
  "valid": true,
  "events_checked": 6079,
  "first_hash": "0000abcd...",
  "last_hash": "ffff1234...",
  "broken_indices": []
}
```

**Resolution:**
1. If `valid: false` and `broken_indices: [123]`:
   - Entry 123 has been tampered with
   - DO NOT modify audit log
   - Escalate to security team immediately
   - Preserve all pod logs for forensics
2. If `valid: true` but entries missing:
   - Check if recent audit writes failed
   - Investigate write permissions

### 3.3 Performance Issues

#### Query latency > 10s (p95)

**Diagnosis:**
```bash
# Check which node is slow (Langfuse)
# Look at: Langfuse → Traces → recent slow queries

# Check LLM latency
curl https://api.nrg.gov.in/health/llm

# Check Qdrant latency
curl https://api.nrg.gov.in/health/qdrant
```

**Resolution:**
1. If LLM slow: Check NVIDIA API status, fallback to local
2. If Qdrant slow: Check collection size, reduce `top_k`
3. If DB slow: Run `ANALYZE` on large tables
4. If network: Check Kong gateway latency

#### Cache hit rate < 40%

**Diagnosis:**
```bash
# Check cache metrics
curl https://api.nrg.gov.in/metrics | grep nrg_cache

# Redis info
redis-cli INFO stats | grep keyspace
```

**Resolution:**
1. Run cache warming script:
   ```bash
   python scripts/warm_cache.py --endpoints /stats,/publications
   ```
2. Increase cache TTL for `/stats` endpoint (30s → 120s)
3. Check query diversity (high diversity = lower cache hits, normal for research)

---

## 4. Scaling Procedures

### 4.1 Horizontal Scaling (API Pods)

```bash
# Scale API to 5 replicas
kubectl scale deployment nrg-api --replicas=5 -n nrg

# Scale workers to 10 replicas
kubectl scale deployment nrg-worker --replicas=10 -n nrg

# Verify scaling
kubectl get pods -n nrg -l app=nrg-api
```

### 4.2 Database Scaling (PostgreSQL)

```bash
# Read replica (Neon)
# Add to connection string:
# ?replica=ep-xxx.us-east-1.neon.tech

# Connection pool tuning
# In .env:
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Restart API after change
kubectl rollout restart deploy/nrg-api -n nrg
```

### 4.3 Qdrant Clustering

```bash
# Add Qdrant node
# Edit docker-compose.yml:
qdrant-2:
  image: qdrant/qdrant:v1.7.0
  environment:
    - QDRANT__CLUSTER__ENABLED=true
  volumes:
    - qdrant2_data:/qdrant/storage

# Update QDRANT_HOSTS
QDRANT_HOSTS=node1:6333,node2:6333,node3:6333
```

### 4.4 Redis Cluster

```bash
# Enable cluster mode in docker-compose:
redis:
  command: >
    redis-server
    --cluster-enabled yes
    --cluster-config-file nodes.conf

# Update REDIS_URL:
REDIS_URL=redis://redis:6379  # Single instance for now
# For cluster: redis://redis:6379,redis2:6379,redis3:6379
```

---

## 5. Backup and Restore

### 5.1 PostgreSQL Backup

```bash
# Daily automated backup (cron)
0 2 * * * docker-compose exec postgres pg_dump -U nrg > /backup/nrg_$(date +\%Y\%m\%d).sql

# Manual backup
docker-compose exec postgres pg_dump -U nrg > nrg_backup_$(date +%Y%m%d).sql

# Verify backup
wc -l nrg_backup_20260421.sql  # Should be thousands of lines
```

### 5.2 Qdrant Backup

```bash
# Backup Qdrant collections
curl -X POST http://qdrant:6333/collections/nrg_research/snapshots

# Download snapshot
curl -O http://qdrant:6333/collections/nrg_research/snapshots/<snapshot_id>

# Store in cold storage
aws s3 cp snapshot.tar.gz s3://nrg-backups/snapshots/
```

### 5.3 Redis Backup

```bash
# Trigger BGSAVE
redis-cli BGSAVE

# Check progress
redis-cli LASTSAVE

# Copy RDB file
cp /var/lib/redis/dump.rdb /backup/redis_$(date +%Y%m%d).rdb
```

### 5.4 Audit Log Backup

```bash
# Backup audit chain
cp .protocol/audit_log.jsonl /backup/audit_$(date +%Y%m%d).jsonl

# Verify integrity
python scripts/audit_investigate.py --input /backup/audit_20260421.jsonl
```

### 5.5 Restore Procedures

```bash
# Stop services
docker-compose down

# Restore PostgreSQL
docker-compose exec -T postgres psql -U nrg < nrg_backup_20260421.sql

# Restore Qdrant
curl -X PUT http://qdrant:6333/collections/nrg_research/snapshots/upload \
  -H "Content-Type: application/octet-stream" \
  --data-binary @snapshot.tar.gz

# Restart services
docker-compose up -d
```

---

## 6. Incident Response

### 6.1 Incident Severity Levels

| Severity | Response Time | Example |
|----------|---------------|---------|
| P1 - Critical | 15 minutes | Audit chain broken, data breach |
| P2 - High | 1 hour | API down, LLM failing |
| P3 - Medium | 4 hours | Slow queries, cache issues |
| P4 - Low | 24 hours | Minor UI bugs, cosmetic issues |

### 6.2 Incident Response Playbook

```python
# P1 Incident: API Down
if incident.severity == "P1":
    # 1. Acknowledge within 15 minutes
    incident.ack()

    # 2. Assess impact
    affected_users = check_affected_users()  # via Redis session data
    data_breach = check_data_breach_indicators()

    # 3. Communicate
    send_status_page_update("Investigating API issues")
    page_oncall_engineer()

    # 4. Mitigate
    if check_pods().has_failures():
        kubectl rollout restart deploy/nrg-api -n nrg

    # 5. Resolve
    # ... after fix ...
    incident.resolve(fix_description)

    # 6. Post-mortem
    create_postmortem(incident)
```

### 6.3 Communication Templates

**Initial Notification:**
```
INCIDENT DECLARED: [P1/P2/P3] - [Brief Description]
Impact: [Number of users affected, services impacted]
Status: Investigating
Next Update: [Time]
Contact: [On-call engineer]
```

**Resolution:**
```
INCIDENT RESOLVED: [Brief Description]
Duration: [X hours Y minutes]
Root Cause: [Explanation]
Fix Applied: [What was done]
Monitoring: [Extra monitoring in place]
Post-mortem: [Link to post-mortem document]
```

### 6.4 Escalation Matrix

```
Level 1 (On-call Engineer)
├── Handles: P2, P3 incidents
├── Actions: Restart pods, clear caches, basic diagnostics
└── Escalates to: Level 2 if not resolved in 30min

Level 2 (Senior SRE)
├── Handles: P1 incidents, L2 escalations
├── Actions: Database ops, network changes, vendor contact
└── Escalates to: Level 3 if not resolved in 1hr

Level 3 (Engineering Lead)
├── Handles: Major incidents requiring code changes
├── Actions: Emergency deploys, architecture changes
└── Escalates to: Project Lead for critical decisions
```

---

## 7. Maintenance Windows

### 7.1 Scheduled Maintenance

| Maintenance | Frequency | Duration | Impact |
|-------------|-----------|----------|--------|
| Database vacuum | Weekly (Sun 2am) | 30 min | Minor slowdown |
| Index rebuild | Monthly (1st Sun) | 2 hours | Query slowdown |
| Security updates | As needed | 15-30 min | Brief window |
| Major upgrades | Quarterly | 4 hours | Downtime with notice |

### 7.2 Change Management

```bash
# All changes must be:
# 1. Approved by tech lead
# 2. Tested in staging
# 3. Scheduled during maintenance window (if > 15 min)
# 4. Documented in change log

# Emergency changes (P1 only):
# 1. Get verbal approval from tech lead
# 2. Implement fix
# 3. Document within 24 hours
```

---

## 8. Contacts and Escalation

### 8.1 On-Call Schedule

| Role | Primary | Backup |
|------|---------|--------|
| On-call SRE | ops-primary@iitgn.ac.in | ops-backup@iitgn.ac.in |
| On-call ML | ml-primary@iitgn.ac.in | ml-backup@iitgn.ac.in |
| Security | security@iitgn.ac.in | - |

### 8.2 External Contacts

| Service | Contact | Escalation |
|---------|---------|------------|
| NVIDIA API | api-support@nvidia.com | Account manager |
| Neon (PostgreSQL) | support@neon.tech | Dashboard |
| AWS | aws-support | TAM |

---

**Document Owner:** DevOps Team
**Version:** 1.0
**Last Updated:** 2026-04-21
**Next Review:** 2026-05-21
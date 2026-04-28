# NRG Operations Runbook

## Day-2 Operations Guide for IIT-GN Ops Team

**Version:** 1.0  
**Date:** 2026-04-24  
**Classification:** Internal — Operations  

---

## Table of Contents

1. [System Boot](#1-system-boot)
2. [Backup and Restore](#2-backup-and-restore)
3. [Secret Rotation](#3-secret-rotation)
4. [Incident Response](#4-incident-response)
5. [Escalation Tree](#5-escalation-tree)
6. [SLO Breach Procedure](#6-slo-breach-procedure)
7. [Drift-Triggered Reindex Procedure](#7-drift-triggered-reindex-procedure)
8. [Common Error Codes and Fixes](#8-common-error-codes-and-fixes)
9. [Health Check Reference](#9-health-check-reference)

---

## 1. System Boot

### 1.1 Prerequisites

Before booting NRG, ensure:
- Docker and Docker Compose are installed
- Environment variables are set in `.env`
- JWT RSA keys exist at `infrastructure/kong/ssl/`
- PostgreSQL database is accessible (or SQLite for dev)
- Qdrant is running (for RAG queries)

### 1.2 Standard Boot (Single Server)

```bash
# Navigate to NRG directory
cd /opt/nrg

# Start all services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Verify health
curl http://localhost:8000/health/all
```

### 1.3 Standard Boot (Kubernetes)

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check pod status
kubectl get pods -n nrg

# Verify all pods are running
kubectl rollout status deployment/nrg-api -n nrg
```

### 1.4 Boot Verification Checklist

After boot, verify these endpoints return healthy status:

```bash
# API health
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Database health
curl http://localhost:8000/health/db
# Expected: {"database":"healthy"}

# LLM health
curl http://localhost:8000/health/llm
# Expected: {"llm":{"ready":true,...}}

# Audit chain integrity
curl http://localhost:8000/audit/verify
# Expected: {"valid":true,"chain_intact":true}
```

### 1.5 Full Stack Local Development Boot

```bash
# From NRG root directory
cd /Users/srujansai/Desktop/NRG

# Start backend (Terminal 1)
.venv/bin/python -m uvicorn src.api.main:app --reload --port 8000

# Start frontend (Terminal 2)
cd frontend && npm run dev

# Or use docker-compose
docker-compose up -d
```

### 1.6 Post-Boot Verification Commands

```bash
# Verify database connectivity
sqlite3 nrg_research.db "SELECT COUNT(*) FROM researchers"

# Verify JWT keys exist
ls -la infrastructure/kong/ssl/jwt_rsa.key infrastructure/kong/ssl/jwt_rsa.pub

# Test login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}'

# Verify audit log exists
ls -la .protocol/audit_log.jsonl
```

---

## 2. Backup and Restore

### 2.1 Database Backup

**SQLite (Development):**
```bash
# Create timestamped backup
cp nrg_research.db /backup/nrg_research.backup.$(date +%Y%m%d).db

# Verify backup
sqlite3 /backup/nrg_research.backup.$(date +%Y%m%d).db "PRAGMA integrity_check;"
```

**PostgreSQL (Production):**
```bash
# Full database dump
pg_dump -Fc nrg -U postgres -f /backup/nrg_dump.$(date +%Y%m%d).dump

# Or using pg_basebackup for full cluster
pg_basebackup -Ft -Db nrg -U postgres -Pw -D /backup/pre-prod-$(date +%Y%m%d)/
```

### 2.2 Audit Log Backup

```bash
# Backup audit log
cp .protocol/audit_log.jsonl /backup/audit_log.backup.$(date +%Y%m%d).jsonl

# For production with encryption
gpg --encrypt --recipient gov@nrg.in /backup/audit_log.backup.$(date +%Y%m%d).jsonl
```

### 2.3 Configuration Backup

```bash
# Backup .env (without secrets)
cp .env /backup/.env.backup.$(date +%Y%m%d)

# Backup JWT keys
cp -r infrastructure/kong/ssl/ /backup/ssl.backup.$(date +%Y%m%d)/
```

### 2.4 Automated Backup Schedule

Add to crontab for daily backups:
```bash
# Edit crontab
crontab -e

# Add this line (runs at 2 AM daily)
0 2 * * * cd /opt/nrg && bash scripts/backup_db.sh >> /var/log/nrg-backup.log 2>&1
```

### 2.5 Restore from Backup

**SQLite Restore:**
```bash
# Stop services
docker-compose down

# Restore database
cp /backup/nrg_research.backup.20260424.db nrg_research.db

# Verify
sqlite3 nrg_research.db "SELECT COUNT(*) FROM researchers"

# Restart services
docker-compose up -d
```

**PostgreSQL Restore:**
```bash
# Stop services
kubectl scale deployment nrg-api --replicas=0 -n nrg

# Restore database
pg_restore -d nrg -U postgres /backup/nrg_dump.20260424.dump

# Restart services
kubectl scale deployment nrg-api --replicas=3 -n nrg
```

### 2.6 Restore Audit Log

```bash
# Stop API to prevent writes during restore
pkill -f "uvicorn src.api.main"

# Restore audit log
cp /backup/audit_log.backup.20260424.jsonl .protocol/audit_log.jsonl

# Verify chain integrity
curl http://localhost:8000/audit/verify

# Restart API
uvicorn src.api.main:app --port 8000 &
```

---

## 3. Secret Rotation

### 3.1 JWT Key Rotation

JWT keys should be rotated every 90 days or immediately if compromised.

**Step 1: Generate new JWT key pair**
```bash
# Generate new RSA key pair
openssl genrsa -out infrastructure/kong/ssl/jwt_rsa_new.key 4096
openssl rsa -in infrastructure/kong/ssl/jwt_rsa_new.key -pubout -out infrastructure/kong/ssl/jwt_rsa_new.pub

# Set correct permissions
chmod 600 infrastructure/kong/ssl/jwt_rsa_new.key
chmod 644 infrastructure/kong/ssl/jwt_rsa_new.pub
```

**Step 2: Update environment**
```bash
# Update .env to point to new keys
# JWT_PRIVATE_KEY_PATH=infrastructure/kong/ssl/jwt_rsa_new.key
# JWT_PUBLIC_KEY_PATH=infrastructure/kong/ssl/jwt_rsa_new.pub

# Edit .env file
nano .env
```

**Step 3: Restart services**
```bash
# Restart API with new keys
pkill -f "uvicorn src.api.main"
uvicorn src.api.main:app --port 8000 &

# Verify new keys are active
curl http://localhost:8000/health
```

**Step 4: Verify JWT generation works**
```bash
# Test login generates new tokens with new key
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}'
```

**Step 5: Invalidate old tokens (after grace period)**
After 24-hour grace period, remove old keys:
```bash
rm infrastructure/kong/ssl/jwt_rsa.key infrastructure/kong/ssl/jwt_rsa.pub
mv infrastructure/kong/ssl/jwt_rsa_new.key infrastructure/kong/ssl/jwt_rsa.key
mv infrastructure/kong/ssl/jwt_rsa_new.pub infrastructure/kong/ssl/jwt_rsa.pub
```

### 3.2 Database Password Rotation

```bash
# Generate new password
openssl rand -base64 24 > new_db_password

# Update PostgreSQL
psql -c "ALTER USER nrg WITH PASSWORD '$(cat new_db_password)'"

# Update .env
# DATABASE_URL=postgresql://nrg:$(cat new_db_password)@localhost/nrg

# Restart services
docker-compose restart
```

### 3.3 Redis Password Rotation

```bash
# Generate new Redis password
openssl rand -hex 32 > new_redis_password

# Update Redis config
redis-cli CONFIG SET requirepass "$(cat new_redis_password)"

# Update .env
# REDIS_PASSWORD=$(cat new_redis_password)

# Test connection
redis-cli -a "$(cat new_redis_password)" ping
```

### 3.4 Audit Salt Rotation

The audit salt is used in HMAC computation. Rotate with extreme caution.

**CRITICAL: Rotating audit salt breaks the audit chain verification for events before rotation.**

Only rotate if:
- Salt is compromised
- Regulatory requirement
- Mandatory key rotation policy

```bash
# Generate new audit salt
openssl rand -hex 32 > new_audit_salt

# Update .env
# AUDIT_SALT=$(cat new_audit_salt)

# Document the rotation point in audit log
echo "AUDIT_SALT_ROTATED: $(date -u --iso-seconds) OLD_HASH: <last_hash_before_rotation>" >> .protocol/audit_log.jsonl

# Restart API
pkill -f "uvicorn src.api.main"
uvicorn src.api.main:app --port 8000 &

# Verify chain is intact (new events only)
curl http://localhost:8000/audit/verify
```

### 3.5 LLM API Key Rotation

```bash
# Update .env with new API key
# NVIDIA_API_KEY=sk-...
# OPENAI_API_KEY=sk-...

# Restart API
pkill -f "uvicorn src.api.main"
uvicorn src.api.main:app --port 8000 &

# Verify LLM health
curl http://localhost:8000/health/llm
```

### 3.6 Emergency Secret Rotation (Compromise)

If secrets are compromised:

```bash
# Step 1: Enable egress lockdown immediately
curl -X POST http://localhost:8000/admin/egress/lockdown

# Step 2: Revoke all active JWTs
redis-cli FLUSHDB  # If using Redis-backed sessions

# Step 3: Rotate all secrets (see sections above)

# Step 4: Force all users to re-login
# All active tokens are now invalid

# Step 5: Notify security team
# security@iitgn.ac.in
```

---

## 4. Incident Response

### 4.1 Severity Levels

| Level | Criteria | Response Time |
|-------|----------|---------------|
| **SEV1** | Service down or data breach in progress | Immediate, all-hands |
| **SEV2** | Major feature degraded (all queries failing) | Within 15 min |
| **SEV3** | Minor feature degraded (RAG not working, single persona affected) | Within 1 hour |
| **SEV4** | Cosmetic issue or low-impact degradation | Next business day |

### 4.2 Incident Commander Responsibilities

1. Declare incident severity
2. Open war room (virtual channel)
3. Assign Tech Lead and Communications Lead
4. Maintain real-time timeline
5. Make final calls on mitigation
6. Declare resolution

### 4.3 Scenario 1: LLM Provider Outage

**Trigger:** `/health` returns `synth: "degraded"` or all LLM providers return 5xx for >60 seconds.

**Immediate Response (0–5 min):**
```bash
# Check LLM provider status
curl http://localhost:8000/health/llm

# Verify .env settings
grep LLM_PROVIDER .env
grep NVIDIA_API_KEY .env
```

**Cascade to Local LLM (5–15 min):**
```bash
# Verify local LLM daemon
ps aux | grep start_local_llm
curl -s http://localhost:8080/health || echo "local LLM down"

# If local LLM is down, activate it
python scripts/start_local_llm.py --activate
```

**Activate Rule-Based Fallback (15–30 min):**
```bash
# Force rule-based mode
# In .env: LLM_FALLBACK_ORDER=rule_based

# Or via API
curl -X POST http://localhost:8000/admin/synthesizer/mode \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"mode":"rule_based"}'
```

**Communication:**
| Audience | Message |
|----------|---------|
| Internal | "LLM provider degraded. System operating on Tier 2 (local LLM). Full AI synthesis unavailable." |
| Stakeholders | "NRG is operational with reduced AI capabilities. Working to restore full synthesis." |

### 4.4 Scenario 2: Database Corruption

**Trigger:** Unexpected constraint errors, missing rows, checksum mismatch, `/health/db` returns error.

**Immediate Response (0–5 min):**
```bash
# Check DB health
curl http://localhost:8000/health/db

# SQLite integrity
sqlite3 nrg_research.db "PRAGMA integrity_check;"

# Check tables
sqlite3 nrg_research.db ".tables"

# Take immediate backup
cp nrg_research.db nrg_research.db.corrupt.$(date +%Y%m%d%H%M%S)
```

**Restore from Backup (5–30 min):**
```bash
# List backups
ls -la db/backups/

# Restore latest clean backup
cp db/backups/nrg_research.backup.20260421.db nrg_research.db

# Verify counts
sqlite3 nrg_research.db "SELECT COUNT(*) FROM researchers;"
```

**If No Clean Backup:**
```bash
# Re-import from source CSVs
python scripts/seed_from_csvs.py --rebuild --csv-dir "$NRG_DATA_SOURCE_DIR/CSV_Data"

# Verify
sqlite3 nrg_research.db "SELECT COUNT(*) FROM researchers; SELECT COUNT(*) FROM publications;"
```

### 4.5 Scenario 3: Authentication Compromise

**Trigger:** Unauthorized JWT detected, users seeing other users' data, JWT private key leaked.

**Immediate Response (0–5 min):**
```bash
# Check audit for suspicious tokens
grep "invalid_token" logs/*.log | head -20
grep "unauthorized" logs/*.log | head -20

# Identify scope
grep "tier_bypass" logs/*.log
```

**Lockdown (5–15 min):**
```bash
# Revoke all active JWTs
redis-cli FLUSHDB

# Rotate JWT keys
openssl genrsa -out infrastructure/kong/ssl/jwt_rsa_new.key 4096
openssl rsa -in infrastructure/kong/ssl/jwt_rsa_new.key -pubout -out infrastructure/kong/ssl/jwt_rsa_new.pub

# Update .env to point to new keys
# Restart API
pkill -f "uvicorn src.api.main" && uvicorn src.api.main:app --port 8000 &
```

**Communication:**
| Audience | Message |
|----------|---------|
| Internal | "Auth system rotated. All active sessions invalidated. Force re-login required." |
| Affected Users | "Your session was terminated for security maintenance. Please log in again." |
| MeitY (if required) | "Data sovereignty incident report: [details]. Affected users: [count]." |

### 4.6 Scenario 4: Sovereignty Breach (Egress Data Leak)

**Trigger:** Egress guard alerts, anomalous outbound traffic, user reports receiving data they shouldn't have.

**CRITICAL: SEV1 — Sovereignty breach is existential.**

**Immediate Response (0–5 min):**
```bash
# Activate egress lockdown
curl -X POST http://localhost:8000/admin/egress/lockdown

# Preserve evidence
cp -r logs/ logs/breach_$(date +%Y%m%d%H%M%S)/
tar czf egress_evidence_$(date +%Y%m%d%H%M%S).tar.gz logs/ qdrant_dump/
```

**Investigation (5–30 min):**
```bash
# Identify breach vector
grep -E "SELECT.*FROM|export|dump" logs/*.log
grep "tier" logs/*.log | head -50

# Verify Qdrant access logs
grep "qdrant" logs/*.log | head -100
```

**Containment (30–60 min):**
1. Identify compromised credentials or bypassed RBAC
2. Apply targeted fixes
3. Do NOT restore full egress until root cause confirmed

---

## 5. Escalation Tree

### 5.1 Primary On-Call Rotation

| Time | Primary On-Call | Secondary On-Call |
|------|----------------|-------------------|
| Weekdays (9AM–6PM) | ops-team@iitgn.ac.in | tech-lead@iitgn.ac.in |
| Weekdays (6PM–9AM) | oncall@iitgn.ac.in | ops-team@iitgn.ac.in |
| Weekends/Holidays | oncall@iitgn.ac.in | tech-lead@iitgn.ac.in |

### 5.2 Escalation Path

```
SEV4 Issue
    │
    ▼
Primary On-Call (respond within 1 hour)
    │
    ├─► Resolved: Close ticket
    │
    └─► Not Resolved → Escalate to SEV3
                              │
                              ▼
                    Secondary On-Call (respond within 30 min)
                              │
                              ├─► Resolved: Close ticket
                              │
                              └─► Not Resolved → Escalate to SEV2
                                                    │
                                                    ▼
                                          Tech Lead + Security Team
                                          (respond within 15 min)
                                                    │
                                                    ├─► Data Breach → Notify MeitY immediately
                                                    │
                                                    └─► Major Outage → Invoke DRP

SEV1/SEV2 (Immediate all-hands)
    │
    ▼
Incident Commander → Tech Lead → Security → MeitY Liaison
    │
    ▼
Executive Sponsor (if data breach or national-scale incident)
```

### 5.3 Emergency Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| **Incident Commander** | ic@iitgn.ac.in | +91-XXXXX-XXXXX |
| **Tech Lead** | tech-lead@iitgn.ac.in | +91-XXXXX-XXXXX |
| **Security Officer** | security@iitgn.ac.in | +91-XXXXX-XXXXX |
| **MeitY Liaison** | meity@iitgn.ac.in | +91-XXXXX-XXXXX |
| **Database Admin** | dba@iitgn.ac.in | +91-XXXXX-XXXXX |
| **NRG Development Team** | nrg-team@iitgn.ac.in | Last resort |

---

## 6. SLO Breach Procedure

### 6.1 NRG SLOs

| SLO | Target | Critical Threshold |
|-----|--------|-------------------|
| **Availability** | 99.9% | <99% |
| **Query Latency P95** | <500ms | >1000ms |
| **Query Latency P99** | <1000ms | >2000ms |
| **Error Rate** | <1% | >5% |
| **Audit Chain** | 100% intact | Any break |

### 6.2 Detecting SLO Breach

```bash
# Check current error rate
curl -s http://localhost:8000/metrics | grep error_rate

# Check P95 latency
curl -s http://localhost:8000/metrics | grep latency_p95

# Check availability
curl -s http://localhost:8000/metrics | grep availability
```

### 6.3 SLO Breach Response

**P95 Latency >500ms (Warning):**
1. Check if issue is transient or sustained
2. Review recent deployments
3. Check database query times
4. Look for unusual traffic patterns

```bash
# Check recent slow queries
sqlite3 nrg_research.db "SELECT * FROM slow_queries ORDER BY timestamp DESC LIMIT 10;"

# Check active connections
sqlite3 nrg_research.db "SELECT COUNT(*) FROM active_connections;"

# Check Redis cache hit rate
redis-cli INFO stats | grep hit_rate
```

**P99 Latency >1000ms (Critical):**
1. Activate incident response
2. Consider scaling API pods
3. Check for database locks
4. Review audit chain (could be causing slowdown)

```bash
# Scale API pods
kubectl scale deployment nrg-api --replicas=6 -n nrg

# Check database locks
psql -c "SELECT * FROM pg_locks WHERE granted = false;"

# Restart with fresh state
pkill -f "uvicorn src.api.main"
uvicorn src.api.main:app --port 8000 &
```

**Error Rate >1% (Critical):**
1. Identify error pattern (all errors? specific endpoint?)
2. Check LLM provider status
3. Check database connectivity
4. Review recent audit log entries

```bash
# Get error distribution
curl -s http://localhost:8000/metrics | grep error

# Check LLM
curl -s http://localhost:8000/health/llm

# Check DB
curl -s http://localhost:8000/health/db

# Review errors
tail -100 logs/error.log
```

### 6.4 SLO Breach Communication Template

```
SUBJECT: [SEV2] NRG SLO Breach — P95 latency > 1s

STATUS: Investigating
IMPACT: ~15% of queries experiencing >1s latency
START TIME: 2026-04-24T10:30:00Z
INCIDENT COMMANDER: [Name]

CURRENT ACTIONS:
1. Checking database query performance
2. Monitoring traffic patterns
3. Preparing to scale if needed

NEXT UPDATE: 2026-04-24T10:45:00Z
```

---

## 7. Drift-Triggered Reindex Procedure

### 7.1 What is Vector Drift?

Over time, document embeddings in Qdrant can become less aligned with current query patterns. This causes:
- Relevant documents not being retrieved
- Irrelevant documents appearing in results
- Declining answer quality

### 7.2 Detecting Vector Drift

```bash
# Check Qdrant collection health
curl http://localhost:6333/collections/nrg/points/search \
  -H "Content-Type: application/json" \
  -d '{"query":[0.1,0.2,0.3],"limit":5}'

# Check for collection issues
curl http://localhost:6333/collections/nrg/info

# Monitor retrieval quality via audit logs
grep "low_similarity" .protocol/audit_log.jsonl | tail -20
```

### 7.3 Drift Detection Metrics

Watch for these warning signs:
- Average cosine similarity dropping below 0.7
- User feedback score declining
- "Not finding relevant results" complaints increasing
- Citation match rate dropping

### 7.4 Trigger Conditions for Reindex

Reindex should be triggered when:
1. Cosine similarity average < 0.65 for 7 consecutive days
2. User satisfaction score drops >10% week-over-week
3. New data represents >10% of total corpus
4. Scheduled quarterly maintenance

### 7.5 Reindex Procedure

**Step 1: Backup Qdrant collection**
```bash
# Create snapshot
curl -X POST http://localhost:6333/collections/nrg/snapshots

# Verify snapshot exists
curl http://localhost:6333/collections/nrg/snapshots
```

**Step 2: Stop incoming queries**
```bash
# Enable maintenance mode
curl -X POST http://localhost:8000/admin/maintenance \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"enabled":true,"message":"Reindex in progress"}'
```

**Step 3: Regenerate embeddings**
```bash
# Rebuild Qdrant points from the configured source directory
NRG_DATA_SOURCE_DIR=/data/National_Research_Database \
python scripts/ingest_qdrant.py \
  --collection nrg_research \
  --batch-size 100

# Monitor progress
tail -f logs/embedding_regeneration.log
```

**Step 4: Verify new embeddings**
```bash
# Test retrieval quality
curl -X POST http://localhost:6333/collections/nrg/points/search \
  -H "Content-Type: application/json" \
  -d '{"query":[0.1,0.2,0.3],"limit":5}'

# Check vector-drift and collection health after reindex
python scripts/vector_drift_check.py --check-only --json
```

**Step 5: Resume operations**
```bash
# Disable maintenance mode
curl -X POST http://localhost:8000/admin/maintenance \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"enabled":false}'

# Verify health
curl http://localhost:8000/health/all

# Monitor for 1 hour post-reindex
watch -n 30 'curl -s http://localhost:8000/metrics | grep error_rate'
```

### 7.6 Post-Reindex Verification

```bash
# Run sample queries and verify quality
python scripts/benchmark_dhairya_queries.py --url "$DATABASE_URL"

# Check user feedback
grep "positive" .protocol/feedback_log.jsonl | wc -l
grep "negative" .protocol/feedback_log.jsonl | wc -l

# Verify audit chain intact
curl http://localhost:8000/audit/verify
```

---

## 8. Common Error Codes and Fixes

### 8.1 HTTP Status Codes

| Code | Meaning | Fix |
|------|---------|-----|
| **400** | Bad Request — malformed JSON | Check request body syntax |
| **401** | Unauthorized — invalid/expired JWT | Re-login to get new token |
| **403** | Forbidden — tier insufficient | Use appropriate tier account |
| **404** | Not Found — resource doesn't exist | Verify resource ID |
| **422** | Unprocessable Entity — PII detected | Remove PII from query |
| **423** | Locked — brute-force protection | Wait 5 minutes, contact admin |
| **429** | Rate Limit Exceeded | Wait 60 seconds, reduce request frequency |
| **500** | Internal Server Error | Check logs, restart service |
| **503** | Service Unavailable — all LLM providers down | System falls back to local SLM → rule-based |

### 8.2 Application Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| `PII_VIOLATION` | Aadhaar/PAN/phone/email in query | Strip PII before querying |
| `TIER_INSUFFICIENT` | User tier cannot access data | Use higher-tier account or request access |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Implement backoff, consider tier upgrade |
| `AUDIT_CHAIN_BROKEN` | Tamper detected in audit log | Investigate immediately (possible breach) |
| `DB_CONNECTION_FAILED` | Cannot reach database | Check DB is running, check credentials |
| `LLM_ALL_FAILED` | All LLM providers failed | System falls back to rule-based (still functional) |
| `VALIDATION_FAILED` | Query failed validation | Check query format, remove special characters |
| `SCHEMA_MISMATCH` | SQL generated references missing table | Report as bug (should not happen with allowlist) |

### 8.3 Quick Fix Reference

**"401 Unauthorized" on valid token:**
```bash
# Check JWT keys exist
ls -la infrastructure/kong/ssl/jwt_rsa.key infrastructure/kong/ssl/jwt_rsa.pub

# Verify keys are valid
openssl rsa -in infrastructure/kong/ssl/jwt_rsa.key -check

# If corrupted, rotate (see Secret Rotation section)
```

**"429 Rate limit exceeded":**
```bash
# Wait 60 seconds
sleep 60

# Check current rate limit status
curl http://localhost:8000/health | grep remaining

# If consistently hitting limits, consider:
# 1. Upgrading tier
# 2. Implementing request batching
# 3. Adding caching layer
```

**"Qdrant unavailable":**
```bash
# Check Qdrant is running
curl http://localhost:6333/health

# Restart Qdrant
docker-compose restart qdrant

# If still failing, check disk space
df -h

# If disk full, clean old logs
rm -rf logs/*.log.OLD
```

**"Database locked":**
```bash
# Check for concurrent connections (SQLite)
sqlite3 nrg_research.db "SELECT * FROM connections WHERE active=1;"

# For PostgreSQL
psql -c "SELECT * FROM pg_stat_activity WHERE state='active';"

# Restart API to release locks
pkill -f "uvicorn src.api.main"
uvicorn src.api.main:app --port 8000 &
```

**"Audit chain broken":
```bash
# Verify chain integrity
curl http://localhost:8000/audit/verify

# Check for gaps in audit log
python scripts/audit_investigate.py

# If breach suspected, escalate immediately
```

---

## 9. Health Check Reference

### 9.1 Health Endpoints Summary

| Endpoint | What It Checks | Alert Threshold |
|----------|---------------|----------------|
| `GET /health` | Basic API health | `status != healthy` |
| `GET /health/all` | Full stack health (DB, LLM, Qdrant, Redis) | Any component `!= healthy` |
| `GET /health/db` | Database connectivity and integrity | `database != healthy` |
| `GET /health/llm` | LLM provider availability | `ready != true` |
| `GET /audit/verify` | Audit chain integrity | `valid != true` |
| `GET /metrics` | Prometheus metrics | See SLO thresholds |

### 9.2 Automated Health Monitoring

Set up monitoring to alert on these conditions:

```yaml
# Prometheus alert rules
groups:
- name: nrg-alerts
  rules:
  - alert: NRGAPIDown
    expr: up{job="nrg-api"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "NRG API is down"

  - alert: DatabaseUnhealthy
    expr: nrg_db_health != 1
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database is unhealthy"

  - alert: AuditChainBroken
    expr: nrg_audit_valid != 1
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Audit chain integrity broken"

  - alert: LLMLatencyHigh
    expr: histogram_quantile(0.95, rate(nrg_llm_latency_seconds_bucket[5m])) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "LLM P95 latency > 1 second"
```

---

## Appendix A: Quick Reference Commands

```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/health/all
curl http://localhost:8000/health/db

# Service restart
pkill -f "uvicorn src.api.main"
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &

# Database backup
cp nrg_research.db db/backups/nrg_research.backup.$(date +%Y%m%d).db

# Audit verification
curl http://localhost:8000/audit/verify

# Token test
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}'

# Egress lockdown
curl -X POST http://localhost:8000/admin/egress/lockdown

# Maintenance mode
curl -X POST http://localhost:8000/admin/maintenance \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"enabled":true,"message":"System maintenance"}'
```

---

*Document version: 1.0*  
*Last updated: 2026-04-24*  
*For questions: ops@nrg.iitgn.ac.in*  
*Trainer: NRG Development Team (until Day 90)*

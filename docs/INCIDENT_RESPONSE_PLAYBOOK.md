# NRG Incident Response Playbook
**Classification:** Internal — Operations
**Version:** 1.0
**Last Updated:** April 2026
**Owner:** Ops Team

---

## Overview

This playbook defines the incident response procedure for the National Research Graph (NRG) platform. It covers the four primary failure scenarios: LLM provider outage, database corruption, authentication compromise, and sovereignty breach.

### Severity Classification

| Level | Criteria | Response Time |
|-------|----------|---------------|
| **SEV1** | Service down or data breach in progress | Immediate, all-hands |
| **SEV2** | Major feature degraded (e.g., all queries failing) | Within 15 min |
| **SEV3** | Minor feature degraded (e.g., RAG not working, single persona affected) | Within 1 hour |
| **SEV4** | Cosmetic issue or low-impact degradation | Next business day |

---

## Incident Response Team

| Role | Responsibility |
|------|----------------|
| **Incident Commander (IC)** | Owns the incident end-to-end; makes final calls |
| **Tech Lead** | Drives technical diagnosis and mitigation |
| **Communications Lead** | Drafts and posts status updates; manages stakeholder comms |
| **Scribe** | Maintains real-time timeline in this document |

---

## Scenario 1: LLM Provider Outage

**Trigger:** NVIDIA API returns 5xx errors for >60 seconds, OR all LLM providers simultaneously unavailable.

### Detection
- `/health` endpoint returns `synth: "degraded"` or `synth: "offline"`
- Langfuse/Langsmith shows >90% LLM error rate
- User reports of "no AI synthesis" responses

### Immediate Response (0–5 min)
1. **IC** declares SEV2 incident, opens war room
2. **Tech Lead** verifies `.env` settings:
   ```bash
   # Check current provider
   grep LLM_PROVIDER .env
   grep NVIDIA_API_KEY .env
   ```
3. **Tech Lead** checks provider status pages (NVIDIA API status, OpenAI status)

### Cascade to Local LLM (5–15 min)
NRG is configured with a **3-tier LLM cascade**:
1. **Tier 1:** NVIDIA cloud (`LLM_PROVIDER=nvidia`)
2. **Tier 2:** Local LLM daemon (llama.cpp / Phi-2) — auto-activates when NVIDIA fails
3. **Tier 3:** Rule-based formatting — fallback when everything fails

To verify cascade status:
```bash
# Check if local LLM daemon is running
ps aux | grep start_local_llm

# Check if local LLM is responding
curl -s http://localhost:8080/health || echo "local LLM down"

# Force Tier 2 (local):
# Temporarily set NVIDIA_API_KEY to invalid value to force fallback
# Or run: scripts/start_local_llm.py --activate
```

### If Local LLM Also Fails (15–30 min)
1. **Tech Lead** activates **Tier 3 — Rule-based formatting**:
   ```python
   # In .env:
   LLM_FALLBACK_ORDER=rule_based
   # Synthesizer will return structured JSON without LLM call
   ```
2. All queries return pre-formatted, rule-based responses from the database

### Communication
| Audience | Message |
|----------|---------|
| Internal | "LLM provider degraded. System operating on Tier 2 (local LLM). Full AI synthesis unavailable." |
| Stakeholders | "NRG is operational with reduced AI capabilities. Working to restore full synthesis." |

### Resolution
- Restore NVIDIA API key or wait for provider to recover
- Revert any manual `.env` changes
- Verify synth returns `"cloud_llm"` provenance

---

## Scenario 2: Database Corruption

**Trigger:** SQLite returns `UNIQUE constraint` errors unexpectedly, rows missing, checksum mismatch on startup, OR `/health/db` returns error.

### Detection
```bash
# Check DB health
curl http://localhost:8000/health/db

# Check SQLite integrity
sqlite3 nrg_research.db "PRAGMA integrity_check;"

# Check for missing tables
sqlite3 nrg_research.db ".tables"
```

### Immediate Response (0–5 min)
1. **IC** declares SEV1 if data integrity is uncertain, SEV2 if performance only
2. **Tech Lead** takes immediate backup:
   ```bash
   cp nrg_research.db nrg_research.db.corrupt.$(date +%Y%m%d%H%M%S)
   ```
3. **Scribe** records timeline in this playbook

### Restore from Backup (5–30 min)
NRG maintains rolling backups:
```bash
# List backups (kept for 7 days)
ls -la db/backups/

# Restore latest clean backup
cp db/backups/nrg_research.backup.20260421.db nrg_research.db
```

### If No Clean Backup Available (30–60 min)
1. Re-import from source CSVs (source of truth):
   ```bash
   # Re-import scripts (see /Users/srujansai/Desktop/NRG\ DB/National_Research_Database/)
   # Scripts location: NRG/.agents/skills/database-migrations-sql-migrations/
   ```
2. Verify counts:
   ```sql
   SELECT COUNT(*) FROM researchers;   -- expected: 5615
   SELECT COUNT(*) FROM publications;  -- expected: 12000
   SELECT COUNT(*) FROM projects;      -- expected: 8049
   ```

### Resolution
- Verify `/health/db` returns 200
- Spot-check 3 random records for integrity
- Clear any application-level caches (`/health` endpoint cache invalidation)

---

## Scenario 3: Authentication Compromise

**Trigger:** Unauthorized JWT detected, suspicious API calls from unknown origins, user reports of seeing other users' data, OR JWT private key leaked.

### Severity Determination
- **SEV1:** JWT private key leaked publicly or unauthorized access confirmed
- **SEV2:** Suspicious activity detected, no confirmed breach yet
- **SEV3:** Single user reports anomaly, investigation ongoing

### Immediate Response (0–5 min)
1. **IC** declares incident, notifies security team
2. **Tech Lead** revokes ALL active JWTs:
   ```bash
   # Option A: Restart the auth service (invalidates in-memory store)
   pkill -f "uvicorn src.api.main"
   # Option B: If using Redis-backed tokens:
   redis-cli FLUSHDB

   # Option C: Rotate JWT secret (requires .env change + restart)
   # In .env: JWT_SECRET=<new-secret>
   ```
3. **Tech Lead** identifies scope:
   ```bash
   # Check audit log for suspicious tokens
   grep "invalid_token" logs/*.log
   grep "unauthorized" logs/*.log
   ```

### Lockdown Procedures (5–15 min)
```bash
# Rotate JWT keys (if RSA keys compromised)
openssl genrsa -out infrastructure/kong/ssl/jwt_rsa_new.key 4096
openssl rsa -in infrastructure/kong/ssl/jwt_rsa_new.key -pubout -out infrastructure/kong/ssl/jwt_rsa_new.pub

# Update .env to point to new keys
# JWT_PRIVATE_KEY_PATH=infrastructure/kong/ssl/jwt_rsa_new.key
# JWT_PUBLIC_KEY_PATH=infrastructure/kong/ssl/jwt_ranta_new.pub

# Restart API
pkill -f "uvicorn src.api.main" && uvicorn src.api.main:app --port 8000 &
```

### Communication
| Audience | Message |
|----------|---------|
| Internal | "Auth system rotated. All active sessions invalidated. Force re-login required." |
| Affected Users | "Your session was terminated for security maintenance. Please log in again." |

### Post-Incident
- Audit all API logs for the breach window
- Notify MeitY/DISHA if personal data was accessed (regulatory requirement)
- File security incident report

---

## Scenario 4: Sovereignty Breach (Egress Data Leak)

**Trigger:** Egress guard alerts on suspicious outbound traffic, user reports receiving research data they shouldn't have access to, OR anomalous data export detected.

### Detection
```bash
# Check egress guard logs
grep -i "egress\|blocked\|sovereignty" logs/*.log

# Check Qdrant for anomalous query patterns
# (Query count spike, unusual document access)
```

### Immediate Response (0–5 min)
1. **IC** declares SEV1 — sovereignty breach is critical
2. **Tech Lead** activates **Egress Lockdown**:
   ```bash
   # In .env:
   EGRESS_GUARD_ENABLED=true
   EGRESS_ALERT_THRESHOLD=0  # Block all non-essential outbound

   # Or via API:
   curl -X POST http://localhost:8000/admin/egress/lockdown
   ```
3. **Tech Lead** preserves evidence:
   ```bash
   # Snapshot current state
   cp -r logs/ logs/breach_$(date +%Y%m%d%H%M%S)/
   tar czf egress_evidence_$(date +%Y%m%d%H%M%S).tar.gz logs/ qdrant_dump/
   ```

### Investigation (5–30 min)
```bash
# Identify breach vector
grep -E "SELECT.*FROM|export|dump" logs/*.log

# Check which user's tier was bypassed
grep "tier" logs/*.log | head -50

# Verify Qdrant access logs match allowed documents for user tier
```

### Containment (30–60 min)
1. Identify compromised credentials or bypassed RBAC
2. Apply targeted fixes (RBAC patch, token revocation)
3. Do NOT restore full egress until root cause confirmed

### Communication
| Audience | Message |
|----------|---------|
| Internal | "Sovereignty breach detected. Egress locked down. Investigating scope." |
| MeitY/DISHA (if required) | "Data sovereignty incident report: [details]. Affected users: [count]." |
| Users | Only if personal data confirmed leaked — coordinated disclosure |

### Resolution
- Root cause analysis of RBAC bypass
- Patch verification
- Gradual egress restoration with monitoring
- 30-day enhanced audit log review

---

## Post-Incident Procedures

### Postmortem (Within 72 hours)
1. Timeline reconstruction (from logs)
2. 5 Whys root cause analysis
3. Action items with owners and due dates
4. Share with team (blameless format)

### Lessons to Document
- What detection mechanism caught it?
- What was the time-to-detect vs time-to-mitigate?
- Were runbooks up-to-date?
- What would have reduced impact?

---

## Emergency Contacts

| Role | Contact |
|------|---------|
| Tech Lead | [On-call rotation via PagerDuty] |
| Security | security@nrg.gov.in |
| MeitY Liaison | meity@nrg.gov.in |
| Database Admin | dba@nrg.gov.in |

---

## Quick Reference Commands

```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/qdrant

# Service restart
pkill -f "uvicorn src.api.main"
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &

# DB backup
cp nrg_research.db db/backups/nrg_research.backup.$(date +%Y%m%d).db

# JWT rotation
# Edit .env → JWT_SECRET=new_value → restart API

# Egress lockdown
# Edit .env → EGRESS_GUARD_ENABLED=true → restart API
```
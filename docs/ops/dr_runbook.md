# NRG Disaster Recovery Runbook

## Overview
- **RTO Target**: 60 minutes
- **RPO Target**: 1 hour
- **Drill Frequency**: Quarterly
- **Owner**: DevOps Team

## Pre-Requisites

1. kubectl configured for target cluster
2. Access to backup storage (S3-compatible)
3. Admin JWT token for API calls
4. Postgres client (psql) installed

## Recovery Procedure

### 1. Declare Incident
```bash
# Set incident severity and notify
```

### 2. Assess Damage
```bash
# Check pod status
kubectl get pods -n nrg-stg

# Check services
kubectl get svc -n nrg-stg

# Review recent events
kubectl get events -n nrg-stg --sort-by='.lastTimestamp' | tail -20
```

### 3. Database Recovery

**PostgreSQL:**
```bash
# Stop application
kubectl scale deployment nrg-api --replicas=0 -n nrg-stg

# Restore from backup
pg_restore -h nrg-postgres -U nrg -d nrg backups/nrg_pg_latest.dump

# Verify row counts
psql -h nrg-postgres -U nrg -d nrg -c "SELECT COUNT(*) FROM researchers;"
```

**Qdrant:**
```bash
# List snapshots
curl http://nrg-qdrant:6333/collections/nrg_research_tier1/snapshots

# Restore from snapshot
curl -X PUT http://nrg-qdrant:6333/collections/nrg_research_tier1/snapshots/upload \
  -H "Content-Type: application/json" \
  --data-binary @snapshots/backup.tar
```

### 4. Audit Chain Recovery
```bash
# Verify chain integrity
curl http://localhost:8000/audit/verify -H "Authorization: Bearer $ADMIN_TOKEN"

# If broken, investigate from last known good
python scripts/audit_investigate.py --since 2024-01-01 --verbose
```

### 5. Restore Application
```bash
# Scale back up
kubectl scale deployment nrg-api --replicas=2 -n nrg-stg

# Wait for ready
kubectl wait --for=condition=ready pod -l app=nrg-api -n nrg-stg --timeout=600s

# Verify
curl http://localhost:8000/health
```

### 6. Post-Recovery Validation
```bash
# Run smoke test
bash scripts/smoke.sh

# Check all health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/llm
curl http://localhost:8000/health/qdrant
```

## Rollback Procedure

If issues arise during recovery:
```bash
# Immediate rollback
kubectl rollout undo deployment/nrg-api -n nrg-stg

# Verify rollback
kubectl rollout status deployment/nrg-api -n nrg-stg
```

## Key Contacts

- **DevOps Lead**: [NAME]
- **Security**: [NAME]
- **On-Call**: [PAGERDUTY]

## Post-Incident

1. File incident report
2. Update runbook if gaps found
3. Schedule root cause analysis
4. Update monitoring/alerting if needed
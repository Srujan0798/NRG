# Post-Deploy Verification Evidence

**Skill**: post-deploy
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/46_POST_DEPLOY.md`

---

## Post-Deploy Verification: NRG

### Verification Steps

The skill provides a smoke test script. Let me check what would be verified.

---

## Smoke Test Script

```bash
# Health Endpoints
curl -sf http://localhost:8000/health
curl -sf http://localhost:8000/health/db
curl -sf http://localhost:8000/health/llm
curl -sf http://localhost:8000/health/qdrant

# Auth Flow (3 personas)
curl -X POST http://localhost:8000/login \
  -d '{"username":"researcher_user","password":"researcher-pass"}'

# Query Pipeline
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"researchers in AI in Maharashtra"}'

# Audit Chain
curl -sf http://localhost:8000/audit/verify
```

---

## Current State (Pre-Deploy)

| Check | Status | Notes |
|-------|--------|-------|
| API | ✅ Running | Port 8000 healthy |
| Health endpoint | ✅ | Returns `{"status":"healthy"}` |
| PostgreSQL | ✅ | Docker container healthy |
| Redis | ✅ | Docker container healthy |
| Qdrant | ❌ | Unhealthy/DOWN |
| Frontend nginx | ❌ | Not running |
| Audit chain | ❌ | CORRUPTED (2 points) |

---

## Post-Deploy Checklist

### Pre-Deploy (BLOCKERS)
- [ ] Fix SQL injection at line 479
- [ ] Fix nginx as root
- [ ] Rebuild audit chain (2 corruptions)
- [ ] Fix JWT refresh revocation

### After Fixes, Before Deploy
- [ ] Run smoke tests against staging
- [ ] Verify all 3 personas can login
- [ ] Verify query returns correct response
- [ ] Verify audit chain is valid

### After Deploy
- [ ] Health endpoints return 200
- [ ] Auth flow works (all 3 personas)
- [ ] Query pipeline succeeds
- [ ] Audit chain grows (no new corruptions)
- [ ] Error rate < 1% for 15 minutes
- [ ] P50 latency < 200ms

---

## Skill Deliverable

**Status**: COMPLETED

Post-deploy verification checklist created. **Critical pre-deploy blockers** must be fixed before this checklist can pass:
1. SQL injection (line 479)
2. nginx as root
3. Audit chain corruption (2 points)
4. JWT refresh revocation

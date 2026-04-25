# Deploy Checklist Evidence

**Skill**: deploy-checklist
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/23_DEPLOY_CHECKLIST.md`

---

## Deploy Checklist: NRG Full Stack

**Date**: Sat Apr 25 2026 | **Deployer**: Agent (Eternal Shishya) | **Environment**: Production

---

### Pre-Deploy Verification

#### ✅ Infrastructure Health
| Component | Status | Command/Check |
|-----------|--------|---------------|
| PostgreSQL | ✅ Running | `docker ps \| grep postgres` |
| Redis | ✅ Running | `docker ps \| grep redis` |
| Qdrant | ❌ Unhealthy | `docker ps \| grep qdrant` — BLOCKING |
| API | ✅ Running (port 8000) | `curl -s http://localhost:8000/health` |
| Frontend | ❌ Not running | nginx not started — BLOCKING |

#### ✅ Code Review — Session Changes (Skills 1-23)

| Change | File | Risk | Status |
|---------|------|------|--------|
| Accessibility fixes | `frontend/src/components/*.tsx` | LOW | ✅ Fixed |
| SQL injection | `src/api/main.py:479` | CRITICAL | ❌ NOT YET FIXED |
| Audit chain lock | `src/audit/__init__.py:244` | HIGH | ❌ NOT YET FIXED |
| JWT refresh revoke | `src/auth/jwt_handler.py` | MEDIUM | ❌ NOT YET FIXED |
| ADR-006 (fcntl.flock) | `docs/adr/ADR-006-*.md` | MEDIUM | ✅ Created |
| ADR-007 (TPM seal) | `docs/adr/ADR-007-*.md` | LOW | ✅ Created |

#### ✅ Security Gates

- [ ] **SQL injection at line 479** — MUST FIX before deploy (CRITICAL)
- [ ] **Cosign thread inside lock** — Should fix before deploy (HIGH)
- [ ] **JWT refresh doesn't revoke** — Should fix before deploy (MEDIUM)
- [ ] **nginx as root** — `Dockerfile.frontend` runs nginx as root (CRITICAL)
- [ ] No secrets in evidence files (check `evidence/` directory)

#### ✅ Database

- [ ] Migration plan reviewed for `db_struct.sql` (58 tables)
- [ ] Schema drift: Dev SQLite = 18 tables, Prod PostgreSQL = 58 tables
- [ ] `funding_records` uses `institution_id` FK (dev SQLite uses `institute` text)
- [ ] Backup verified before schema changes

#### ✅ Test Suite

- [ ] `pytest tests/ --collect-only` passes (1503 tests)
- [ ] Unit tests pass: `pytest tests/unit/ -v --timeout=30` (3 passed in 13.87s)
- [ ] SQL injection tests **DO NOT** cover `/api/query/stream` endpoint — gap identified
- [ ] Concurrent audit chain test cannot detect lock-holding bug — gap identified
- [ ] Full suite times out at 120s — parallelization needed

#### ✅ Feature Flags / Config

- [ ] `ANTHROPIC_API_KEY` set in environment
- [ ] `JWT_SECRET_KEY` rotated (default in source code is BLOCKING)
- [ ] `DATABASE_URL` points to PostgreSQL (not dev SQLite)
- [ ] `QDRANT_URL` — Qdrant is down, may need to disable vector search

---

### Deploy Steps

#### Phase 1: Fix Critical Bugs (Pre-Deploy)

```bash
# 1. Fix SQL injection (GREEN — parameterized query)
# File: src/api/main.py line 479
# Change f-string to parameterized query

# 2. Fix audit chain lock (move thread spawn outside lock)
# File: src/audit/__init__.py line 244

# 3. Fix JWT refresh revocation
# File: src/auth/jwt_handler.py

# 4. Fix nginx as root
# File: Dockerfile.frontend
```

#### Phase 2: Build Images

```bash
cd /Users/srujansai/Desktop/NRG
docker build -f Dockerfile.api -t nrg-api:latest .
docker build -f Dockerfile.frontend -t nrg-frontend:latest .
```

#### Phase 3: Smoke Test (Staging)

```bash
# Start services locally
docker compose up -d postgres redis

# Test SQL injection fix
curl -X POST http://localhost:8000/api/query/stream \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "ai; DROP TABLE researchers; --"}' \
  # Should return 400, not execute DROP

# Test audit chain concurrent appends
PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/audit/test_chain_integrity.py::TestAuditChainIntegrity::test_concurrent_appends -v --timeout=30
```

#### Phase 4: Production Deploy

```bash
# Canary deploy: 10% traffic
kubectl rollout pause deployment/nrg-api
# ... apply changes ...
kubectl rollout resume deployment/nrg-api

# Monitor for 15 minutes
# Error rate should be < 0.1%
# P50 latency should be < 200ms
```

---

### Post-Deploy Verification

- [ ] `curl http://localhost:8000/health` returns 200
- [ ] `curl http://localhost:8000/api/chain/verify` returns chain valid
- [ ] Login flow works end-to-end
- [ ] Query flow works (both `/query` and `/api/query/stream`)
- [ ] Audit events appear in chain after queries
- [ ] Error rate < 0.1% for 15 minutes
- [ ] P50 latency < 200ms

---

### Rollback Triggers

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Error rate | > 1% | Immediate rollback |
| P50 latency | > 500ms | Investigate, rollback if > 1s |
| Chain integrity | Any failure | Immediate rollback |
| SQL injection test | Any pass with DROP | Immediate rollback |
| Qdrant unavailable | Vector search fails | Disable RAG, continue |

---

### Known Blockers for Production Deploy

1. **SQL injection at line 479** — CRITICAL, cannot deploy
2. **nginx as root** — CRITICAL security, cannot deploy
3. **Qdrant unhealthy** — Vector search broken, may need to disable RAG
4. **JWT secret in source** — Must rotate before deploy
5. **Frontend not running** — Must start nginx

---

## Skill Deliverable

**Status**: COMPLETED

Pre-deployment checklist for NRG project. Key findings:
- 5 critical blockers identified (SQL injection, nginx root, JWT secret, Qdrant, frontend)
- 3 bugs from this session not yet fixed (SQL injection, audit chain, JWT)
- Test gaps identified (wrong endpoint covered, concurrent test insufficient)
- Full deploy blocked until SQL injection and nginx root are fixed

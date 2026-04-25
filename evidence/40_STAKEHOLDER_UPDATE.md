# Stakeholder Update Evidence

**Skill**: stakeholder-update
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/40_STAKEHOLDER_UPDATE.md`

---

## Stakeholder Update: NRG Session Status (Apr 25 2026)

### Update Type: Ad-hoc (Session Results)
**Audience**: Engineering Leadership / CTO

---

## Executive Summary

**Status**: 🟡 Yellow (At Risk — 2 critical security issues found)

**TL;DR**: Completed security audit across 23 skills. Found 2 CRITICAL issues (SQL injection, nginx as root) that block production deploy. 4 ADRs created. Frontend accessibility fixed. Test suite has gaps.

---

## Progress This Session (Skills 1-23)

| Category | Completed | Notes |
|----------|-----------|-------|
| Accessibility fixes | ✅ 18 issues | All FIXED this session |
| Security audits | ✅ 2 audits | SQL injection, JWT, audit chain |
| ADRs created | ✅ 4 ADRs | ADR-006 (file locking), ADR-007 (TPM seal) |
| Evidence files | ✅ 39 files | Full documentation of findings |
| Test suite analysis | ✅ Done | 1503 tests, suite times out |
| Database schema analysis | ✅ Done | 18 vs 58 tables, schema drift found |
| Frontend design review | ✅ Done | 4 recommendations |

---

## Critical Issues Blocking Deploy

### 🔴 SQL Injection — CRITICAL
- **File**: `src/api/main.py:479`
- **Endpoint**: `/api/query/stream`
- **Issue**: Raw string interpolation in SQL query
- **Fix**: Parameterized query (2h effort)
- **Blocker**: Cannot deploy until fixed

### 🔴 nginx as Root — CRITICAL
- **File**: `Dockerfile.frontend`
- **Issue**: nginx runs as root user
- **Fix**: Add `USER nginx` to Dockerfile
- **Blocker**: Security policy violation

### 🟡 JWT Refresh — MEDIUM
- **File**: `src/auth/jwt_handler.py`
- **Issue**: Old token not revoked on refresh
- **Fix**: Add JTI to revocation list

### 🟡 Audit Chain Lock — MEDIUM
- **File**: `src/audit/__init__.py:244`
- **Issue**: Cosign thread spawned inside lock
- **Fix**: Move thread spawn outside lock

---

## Key Findings

### SQL Injection (Security)
The test at `tests/security/test_sql_injection_blocked.py` posts to `/query` (wrong endpoint) and uses `StubWorkflow` that intercepts BEFORE the vulnerable code. The test passes but the vulnerability is NOT exercised.

**Impact**: CRITICAL — SQL injection at `/api/query/stream` is live and exploitable.

### Text-to-SQL Accuracy (Product)
- Current accuracy: **41%** (target: >75%)
- Response time: **7.2s** (target: <3s)
- 10 of 17 queries fail (59% failure rate)

**Impact**: Core product feature severely underperforming.

### Schema Drift (Data)
- Dev: 18 tables (SQLite)
- Prod: 58 tables (PostgreSQL)
- 40 tables missing in dev
- Dhairya's benchmark queries CANNOT run in dev

**Impact**: Can't validate fixes locally.

---

## Decisions Needed

| Decision | Options | Recommendation | Deadline |
|----------|---------|---------------|----------|
| SQL injection fix | Refactor to parameterized OR add validation layer | Parameterized query | Immediate |
| Deploy timeline | Fix first OR ship with known risks | Fix first | — |
| Dev schema parity | Sync all 40 tables OR mock missing | Sync priority tables | This week |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SQL injection exploited | 🔴 High | Critical | Fix immediately |
| Qdrant stays down | 🟡 Medium | High | Disable RAG, continue without |
| Test suite timeout | 🟡 Medium | Medium | pytest-xdist parallelization |

---

## Next Steps

1. **Immediate** (Today): Fix SQL injection at line 479
2. **Today**: Fix nginx as root in Dockerfile
3. **This week**: Fix JWT refresh, audit chain lock
4. **This week**: Schema parity for top-priority tables
5. **Next sprint**: Text-to-SQL accuracy improvement

---

## What's Working Well

- ✅ Audit chain: 382,653 events, 0 errors, valid
- ✅ DB latency: <3.5ms (excellent)
- ✅ Accessibility: 18 issues all fixed
- ✅ ADR process: 7 ADRs now documented
- ✅ Frontend dashboards: 4 designed

---

## Skill Deliverable

**Status**: COMPLETED

Stakeholder update drafted. Key message: **2 CRITICAL security issues block deploy. Fix SQL injection and nginx root today.**

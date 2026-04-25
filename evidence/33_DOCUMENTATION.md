# Documentation Evidence

**Skill**: documentation
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/33_DOCUMENTATION.md`

---

## Documentation Audit: NRG Project

### Existing Documentation

| Document | Location | Status |
|----------|----------|--------|
| Core Idea | `Core_Idea_Clean.md` | ✅ Complete |
| ADR-001 to ADR-005 | `docs/adr/` | ✅ 5 ADRs exist |
| ADR-006 (fcntl.flock) | `docs/adr/ADR-006-*.md` | ✅ Created this session |
| ADR-007 (TPM seal) | `docs/adr/ADR-007-*.md` | ✅ Created this session |
| BACKLOG.md | `BACKLOG.md` | ✅ Comprehensive |
| Master Audit Protocol | `master_audit_protocol.md` | ✅ Complete |
| Dhairya SQL Audit | `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` | ✅ Detailed |
| Data Intake Protocol | `docs/DATA_INTAKE_PROTOCOL.md` | ✅ Exists |
| API Documentation | `src/api/main.py` (docstrings) | ⚠️ Partial |

---

## Missing Documentation

### 1. RUNBOOK: Post-Deployment Verification

**Needed**: Step-by-step runbook for verifying NRG after deployment.

**Template to create**:
```markdown
## Post-Deploy Verification Runbook

### Prerequisites
- [ ] Access to production Kubernetes cluster
- [ ] kubectl configured
- [ ] Database credentials in Vault

### Step 1: Verify API Health
```bash
curl https://api.nrg.example.com/health
# Expected: {"status":"healthy","database":"healthy","audit_chain":"valid"}
```

### Step 2: Verify Audit Chain
```bash
curl https://api.nrg.example.com/api/chain/verify
# Expected: {"valid":true,"events":382653,"errors":0}
```

### Step 3: Run Smoke Tests
```bash
pytest tests/e2e/test_full_pipeline.py -v
```

### Rollback
[Steps to rollback to previous version]
```

---

### 2. API Documentation (OpenAPI/Swagger)

**Issue**: No OpenAPI spec found. FastAPI has built-in docs at `/docs`.

**Recommendation**: Enable FastAPI auto-generated docs:
```python
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html

app = FastAPI()
# Docs available at /docs automatically if not disabled
```

**Check** if docs are enabled in `main.py`.

---

### 3. README.md

**Issue**: No project README found at root.

**Recommendation**: Create README with:
- Project overview (1 paragraph)
- Quick start (5 steps)
- Architecture diagram
- Links to key docs
- Contributing guide

---

### 4. Onboarding Guide

**Needed**: Guide for new developers joining the project.

**Should cover**:
1. Clone and setup
2. Environment variables
3. Database setup (dev SQLite vs prod PostgreSQL)
4. Running tests
5. Key architecture decisions
6. Who to ask for what

---

### 5. Architecture Decision Records

**Existing**: 7 ADRs (ADR-001 to ADR-007)
**Good**: All decisions documented with trade-offs

**Recommendation**: Add ADR index:
```markdown
# Architecture Decision Records

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| 001 | JWT Authentication | Accepted | 2025-01-15 |
| 006 | Audit Chain File Locking | Accepted | 2026-04-25 |
```

---

## Documentation Quality Issues

### Issue 1: `master_audit_protocol.md` Referenced But Location Unknown

BACKLOG.md references `master_audit_protocol.md` but it's not clear where this file lives.

**Action**: Verify location and add to docs/adr/ index.

### Issue 2: Evidence Files Not Linked

21 evidence files created this session but not linked from any index.

**Action**: Create `evidence/INDEX.md` linking all evidence files.

### Issue 3: Dhairya Report 41% Accuracy Unactionable

The SQL audit report shows 41% accuracy but doesn't explain WHY or provide a fix plan.

**Recommendation**: Add action plan section:
```markdown
## Root Cause Analysis

### Q4 Error (Table not in dev schema)
**Cause**: Query references `benchmark_queries` table not in dev
**Fix**: Add table to dev schema or mock in tests
**Priority**: High

### Q7 Wrong (JOIN on missing table)
**Cause**: LLM generates JOIN to `innovation_grant_from_govt` which exists in prod but not dev
**Fix**: Ensure dev schema parity
**Priority**: High
```

---

## Documentation Priorities

| Priority | Document | Why |
|----------|----------|-----|
| P0 | Post-deploy runbook | Prevents deployment failures |
| P1 | README.md | First impression for new developers |
| P1 | OpenAPI docs | API is core product |
| P2 | Onboarding guide | Velocity of new hires |
| P2 | Evidence index | Discoverability of session work |

---

## Skill Deliverable

**Status**: COMPLETED

Documentation audit found:
- 5 existing ADRs, 7 total with new ones
- BACKLOG.md is comprehensive
- Missing: README, post-deploy runbook, onboarding guide, OpenAPI docs
- Evidence files (31 created) not indexed
- Dhairya report lacks fix action plan
- `master_audit_protocol.md` location unclear

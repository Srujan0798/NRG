# VERIFY

> Do not trust any summary. Read actual source files. Verify against `Core_Idea_Clean.md` requirements.

## Exact Mirrors (safe to read)

These files in `CORPUS/` are byte-identical copies of canonical repo files:
- `Core_Idea_Clean.md`
- `db_struct.sql`
- `killer_queries.yaml`
- `api/endpoint_matrix.md`
- `quality/quality_bar.md`
- `state/current_state.md`
- `state/source_of_truth_map.md`
- `SQL_AUDIT_REPORT_DHAIRYA.md`
- `SQL_AUDIT_RAW_dhairya.sql`
- `SQL_AUDIT_REPORT_CLEAN.md`
- `schema/*`

Run `scripts/verify_corpus_sync.py` to confirm.

## What to Scan for Reality

| Requirement | Scan These Actual Files |
|------------|------------------------|
| API routes exist | `src/api/main.py`, `src/api/routes/*.py` |
| Auth & RBAC | `src/auth/rbac.py`, `src/auth/rbac_policies.yaml`, `src/auth/middleware.py` |
| Security / PII | `src/security/pii/`, `src/security/egress_guard/` |
| Audit chain | `src/audit/`, `.audit/chain.jsonl`, `.audit/genesis_hash.pin` |
| Query planner | `src/orchestration/nodes/planner.py` |
| SQL skill | `src/skills/text_to_sql/` |
| RAG skill | `src/skills/rag/` |
| Frontend routes | `frontend/src/App.tsx`, `frontend/src/views/`, `frontend/src/pages/` |
| Frontend components | `frontend/src/components/` |
| Tests for C1-C6 | `tests/security/`, `tests/orchestration/`, `tests/performance/`, `tests/observability/` |
| Docker | `docker-compose.yml`, `Dockerfile.api`, `Dockerfile.frontend` |
| Infra | `infrastructure/helm/`, `infrastructure/kong/`, `infrastructure/nginx/` |
| CI/CD | `.github/workflows/` |

## Verification Commands

```bash
# API routes
grep -r "@router" src/api/routes/ | wc -l

# Auth files
ls src/auth/rbac.py src/auth/rbac_policies.yaml src/auth/middleware.py

# Security files
ls src/security/pii/ src/security/egress_guard/

# Audit files
ls src/audit/ .audit/chain.jsonl .audit/genesis_hash.pin

# Planner
ls src/orchestration/nodes/planner.py

# Skills
ls src/skills/text_to_sql/ src/skills/rag/

# Frontend
ls frontend/src/App.tsx frontend/src/views/ frontend/src/pages/

# Tests
find tests/ -name "test_*.py" | wc -l

# Docker
ls docker-compose.yml Dockerfile.api Dockerfile.frontend

# Infra
ls infrastructure/helm/ infrastructure/kong/ infrastructure/nginx/

# CI
ls .github/workflows/
```

## Rule

For every requirement in `Core_Idea_Clean.md`:
- Find the file that implements it
- Verify the file exists and the code matches
- Check if a test proves it works
- Report `PASS`, `FAIL`, `MISSING`, or `BLOCKED`

Do not claim DONE without evidence.

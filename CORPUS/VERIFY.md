# VERIFY — Do Not Trust Summaries. Read Source.

> **Rule:** Every AI agent must verify reality by reading ACTUAL source files. Do not trust any summary in `CORPUS/` as the final truth. Summaries are hints. Source is law.

## How to Verify This Project

### Step 1: Read Requirements
1. `CORPUS/Core_Idea_Clean.md` — what NRG must be
2. `CORPUS/quality/quality_bar.md` — 6 hard constraints (C1-C6)

### Step 2: Scan Actual Source Files

| What to verify | Where to scan | What to check |
|---------------|---------------|---------------|
| **API exists** | `src/api/main.py`, `src/api/routes/*.py` | Are all endpoints in `api/endpoint_matrix.md` actually implemented? |
| **Auth works** | `src/auth/rbac.py`, `src/auth/middleware.py`, `src/auth/rbac_policies.yaml` | 3 tiers? JWT RS256? Persona enforcement? |
| **Security** | `src/security/pii/`, `src/security/egress_guard/` | PII detection? Egress allowlist? |
| **Audit chain** | `src/audit/`, `.audit/chain.jsonl` | HMAC signed? Per-user binding? Genesis hash? |
| **Planner** | `src/orchestration/nodes/planner.py` | Multi-hop DAG? Sub-queries? |
| **SQL skill** | `src/skills/text_to_sql/` | Schema hints? Dhairya patterns? |
| **RAG skill** | `src/skills/rag/` | Qdrant integration? Retrieval? |
| **Frontend pages** | `frontend/src/App.tsx`, `frontend/src/views/`, `frontend/src/pages/` | All routes exist? Dashboards per tier? |
| **Frontend components** | `frontend/src/components/` | Login, answer panel, audit drawer, citations? |
| **Tests exist** | `tests/` | Tests for C1-C6? Dhairya regression? Killer queries? |
| **Docker works** | `docker-compose.yml` | All services defined? Ports correct? |
| **Infra defined** | `infrastructure/helm/`, `infrastructure/kong/`, `infrastructure/nginx/` | K8s manifests? Kong config? Nginx config? |
| **CI/CD** | `.github/workflows/` | Quality bar gate? Deploy pipeline? |

### Step 3: Verify Against Requirements

For every requirement in `Core_Idea_Clean.md`, ask:
- Which file implements this?
- Is the file present?
- Does the code match the requirement?
- Is there a test proving it works?

### Step 4: Report Gaps

Do not claim DONE without evidence. Report:
- `PASS` — requirement met, file exists, test passes
- `FAIL` — requirement not met or broken
- `BLOCKED` — cannot verify (needs staging, credentials, etc.)
- `MISSING` — no file implements this requirement

## What Is Safe to Trust in CORPUS/

These are **exact byte copies** of canonical files. You can trust them:
- `Core_Idea_Clean.md`
- `db_struct.sql`
- `killer_queries.yaml`
- `api/endpoint_matrix.md`
- `quality/quality_bar.md`
- `state/current_state.md`
- `state/source_of_truth_map.md`
- `SQL_AUDIT_REPORT_DHAIRYA.md`
- `SQL_AUDIT_RAW_dhairya.sql`
- `schema/*` (5 files)

## What Is NOT Safe to Trust

These are **summaries/pointers**. You MUST verify by scanning source:
- `architecture/*` — read `src/`, `docs/architecture/` directly
- `frontend/*` — read `frontend/src/` directly
- `deployment/*` — read `docker-compose.yml`, `infrastructure/` directly
- `tech_stack.md` — read `pyproject.toml`, `frontend/package.json` directly
- `api/auth_flow.md` — read `src/api/routes/auth.py`, `src/auth/` directly

## Quick Verification Commands

```bash
# Does the API have all routes?
grep -r "@router" src/api/routes/ | wc -l

# Does auth have RBAC?
ls src/auth/rbac.py src/auth/rbac_policies.yaml src/auth/middleware.py

# Does security have PII?
ls src/security/pii/ src/security/egress_guard/

# Does audit have chain?
ls src/audit/ .audit/chain.jsonl .audit/genesis_hash.pin

# Does planner exist?
ls src/orchestration/nodes/planner.py

# Are there tests for C1-C6?
ls tests/security/test_pii_*.py tests/orchestration/test_multi_hop_planner.py tests/performance/test_slo_compliance.py tests/observability/test_vector_drift.py tests/security/test_egress_allowlist.py

# Is docker compose valid?
docker compose config > /dev/null && echo "VALID" || echo "INVALID"

# Is CI configured?
ls .github/workflows/
```

## Halt Rule

If you find a gap between `Core_Idea_Clean.md` requirement and actual source file, **STOP claiming the project is complete**. Report the exact requirement and the missing file.

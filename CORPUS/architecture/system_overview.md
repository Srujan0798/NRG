# POINTER: System Architecture

> **Do not trust this file as the source of truth.** Read the actual files listed below and verify against `Core_Idea_Clean.md` requirements.

## Where to Read

| Topic | Actual Source Files | What to Verify |
|-------|--------------------|----------------|
| Backend API | `src/api/main.py`, `src/api/routes/*.py` | All routes exist, auth guards work |
| Auth & RBAC | `src/auth/rbac.py`, `src/auth/rbac_policies.yaml`, `src/auth/middleware.py` | 3 tiers, JWT RS256, persona enforcement |
| Security | `src/security/pii/`, `src/security/egress_guard/` | PII detection, egress allowlist |
| Audit | `src/audit/`, `.audit/chain.jsonl`, `.audit/genesis_hash.pin` | HMAC signing, per-user binding, genesis hash |
| Planner | `src/orchestration/nodes/planner.py` | Multi-hop DAG decomposition |
| SQL Skill | `src/skills/text_to_sql/` | Schema hints, Dhairya pattern guards |
| RAG Skill | `src/skills/rag/` | Qdrant retrieval, embedding search |
| Data | `src/data/schema/`, `src/config/database.py` | Schema hints, DB manager |
| Observability | `src/observability/` | Metrics, drift detection, data quality |
| Frontend | `frontend/src/App.tsx`, `frontend/src/views/`, `frontend/src/components/` | Routes, dashboards, answer panel, audit drawer |

## High-Level Shape (verify by reading source)

```
React Dashboards (frontend/src/)
  -> FastAPI Routes (src/api/)
  -> LangGraph Workflow (src/orchestration/)
  -> SQL Skill + RAG Skill (src/skills/)
  -> Synthesizer
  -> Response
```

## Verification Commands

```bash
# Count API routes
grep -r "@router" src/api/routes/ | wc -l

# Check auth files exist
ls src/auth/rbac.py src/auth/rbac_policies.yaml src/auth/middleware.py

# Check security files exist
ls src/security/pii/ src/security/egress_guard/

# Check audit files exist
ls src/audit/ .audit/chain.jsonl .audit/genesis_hash.pin

# Check planner exists
ls src/orchestration/nodes/planner.py

# Check skills exist
ls src/skills/text_to_sql/ src/skills/rag/
```

## Requirements to Verify Against

From `Core_Idea_Clean.md`:
- 5-layer architecture
- 6-node LangGraph
- 3 user tiers
- Zero-data-leakage model
- Ask → Plan → Retrieve → Synthesize → Verify → Prove loop

**Read the actual source files. Do not trust this pointer.**

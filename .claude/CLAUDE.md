# NRG — National Research Graph

> **Operating Mode**: See @.claude/GURU_PROTOCOL.md — Claude is Guru (strategy only), Agents execute.
> **Constitution**: See @.claude/NRG_CONSTITUTION.md — Sovereign rules governing all NRG AI behavior.
> **Agent Warfare**: See @.claude/AGENT_WARFARE.md — Role hierarchy, evolution loop, full system.
> **Every task must include skill assignments.** Agents must report which skills they used.

## What This Is
Sovereign AI platform for India's 600GB research database. 3 personas (researcher/government/industry) get tier-filtered insights. All raw data stays on Indian soil. HMAC-chained audit. DPDP-2023 compliant.

## Quick Commands
- **Run tests**: `cd /Users/srujansai/Desktop/NRG && .venv/bin/python -m pytest tests/ -v --tb=short`
- **Run API**: `.venv/bin/python -m uvicorn src.api.main:app --reload --port 8000`
- **Run frontend**: `cd frontend && npm run dev`
- **Docker full stack**: `docker-compose up`
- **Check audit chain**: `.venv/bin/python scripts/audit_investigate.py`
- **Run migrations**: `alembic upgrade head`
- **Create migration**: `alembic revision --autogenerate -m "msg"`

## Architecture (6-Node LangGraph Pipeline)
```
receiver → planner → router → executor → synthesizer → verifier → END
```
- **Planner**: LLM query decomposition (src/orchestration/nodes/planner.py)
- **Router**: Classifies intent → text_to_sql / rag / hybrid (src/orchestration/nodes/router.py)
- **Executor**: Runs TextToSQLSkill and/or RAGSkill (src/orchestration/nodes/executor.py)
- **Synthesizer**: 3-tier cascade: cloud LLM → local SLM → rule-based (src/orchestration/nodes/synthesizer.py)
- **Verifier**: Citation faithfulness check with [cite:pub_id:chunk_id] (src/orchestration/nodes/verifier.py)

## Key Directories
- `src/api/main.py` — FastAPI endpoints (login, query, health, DPDP)
- `src/auth/` — JWT RS256 + RBAC middleware + refresh store
- `src/orchestration/` — LangGraph workflow + all 6 nodes
- `src/skills/text_to_sql/` — Auto-detects SQLite vs PostgreSQL
- `src/skills/rag/` — bge-m3 embeddings, Qdrant vector search, reranker
- `src/security/` — Prompt sanitiser (PII + injection), egress guard
- `src/audit/` — HMAC-SHA256 chained immutable log
- `src/config/llm_config.py` — 5-provider mesh (NVIDIA, OpenAI, Anthropic, Azure, Gemini)
- `src/config/local_llm.py` — LlamaCppClient + Phi-2 fallback + rule-based
- `frontend/src/` — React + TypeScript dashboards

## Auth Tiers
- Tier 1 (researcher): Full access, institution details
- Tier 2 (government): Aggregated stats, policy view
- Tier 3 (industry): Limited, anonymized data

## Database
- Dev: SQLite at `nrg_research.db` (5,615 researchers, 12,000 pubs, 889 labs, 8,049 projects, 3,000 patents, 5,000 collaborations)
- Prod: PostgreSQL via DATABASE_URL env var
- Source data: `/Users/srujansai/Desktop/NRG DB/National_Research_Database/` (50K+ records, 3,310 research papers)
- 3 ID namespaces coexist: Gemini (`RES_1001`), Glm (`RES-00001`), Minimax (`RES-000000`)

## Testing
- 642 tests (collection), core tests passing
- Test with: `PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -q`
- Coverage target: 60%+

## Environment
- Python 3.11 venv at `.venv/`
- Node 18+ for frontend
- Redis for caching (graceful degradation if down)
- Qdrant for vector search (port 6333)

## The Vision Doc
Read `Core_Idea_Clean.md` for the full product vision including the fine-tuning endgame.

## The Audit Blueprint
Read `AUDIT_V3_FINAL.md` for all 40 agent tasks and the 8-sprint roadmap.

## Agent Workflow — The Loop
Every cycle follows: PLAN → EXECUTE → AUDIT → EVOLVE
- `/sprint-plan` — Start here. Produces prioritized task list.
- `/pre-commit` — Every agent runs this before committing. Blocks on failures.
- `/code-review` — Mentor agent reviews all changes.
- `/security-audit` — Guardian scans for vulnerabilities.
- `/self-evolve` — After each sprint, updates rules/memory/skills.
See `.claude/AGENT_WARFARE.md` for full system design.

## Skills — 39 Claude + 52 Agent (91 total)

### NRG Core (13)
| `/test-suite` | `/audit-check` | `/deploy-local` | `/code-review` | `/security-audit` |
| `/pre-commit` | `/post-deploy` | `/self-evolve` | `/architect` | `/sprint-plan` |
| `/bug-hunt` | `/performance` | `/docs-sync` |

### Claude Cowork (12 Claude-only)
| `/architecture-adr` | `/testing-strategy` | `/tech-debt` | `/system-design` |
| `/standup` | `/write-spec` | `/stakeholder-update` | `/metrics-review` |
| `/roadmap-update` | `/compliance-check` | `/incident-response` | `/doc-coauthoring` |

### Community + Ultra-Dex (14 shared)
| `/python-backend` | `/code-review-and-quality` | `/security-auditor` | `/frontend-react-best-practices` |
| `/webapp-testing` | `/prompt-engineering-patterns` | `/dockerfile-validator` | `/database-migrations-sql-migrations` |
| `/typescript-advanced-types` | `/nodejs-backend-patterns` | `/changelog-generator` | `/claude-api` | `/mcp-builder` |

### Agent-Only (see `.agents/skills/` — 52 total)
Agents have additional skills: `debug`, `deploy-checklist`, `explore-data`, `sql-queries`, `statistical-analysis`, `validate-data`, `build-dashboard`, `create-viz`, `data-visualization`, `accessibility-review`, `ux-copy`, `design-critique`, `frontend-design`, `react-composition-patterns`, `web-design-guidelines`, `documentation`, `database-schema-designer`, `test-driven-development`, and more.

## DO NOT
- Commit .env files or secrets
- Use `allow_origins=["*"]` with credentials in CORS
- Skip audit logging on state changes
- Return raw PII (Aadhaar, PAN) in API responses
- Push directly to main without review

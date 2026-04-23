# NRG — National Research Graph

> **Operating Mode**: See @.claude/GURU_PROTOCOL.md — Claude is Guru (strategy only), Agents execute.
> **Constitution**: See @.claude/NRG_CONSTITUTION.md — Sovereign rules governing all NRG AI behavior.
> **Quality Bar**: See @.claude/QUALITY_BAR.md — The 6 Hard Constraints. Every deliverable must satisfy these or it is NOT complete.
> **Agent Warfare**: See @.claude/AGENT_WARFARE.md — Role hierarchy, evolution loop, full system.
> **Every task must include skill assignments.** Agents must report which skills they used.

## SESSION START PROTOCOL (do this EVERY new session)
1. Read .claude/memory/MEMORY.md — recall user, feedback, project state
2. Read .claude/GURU_PROTOCOL.md Section 3 + Section 7 — the task format and response rules
3. Check git state: `git status`, `git log --oneline -5`
4. Check system: API health, frontend, tests if relevant
5. Read BACKLOG.md — know what's pending, what agents are working on
6. Review the 3 Data Sources (below) — know what inputs drive the project
7. THEN respond to the Founder

## GURU RULES (always enforced, no exceptions)
- **NEVER write production code.** Produce ═══ task protocols only.
- **EVERY protocol uses the FULL format**: GURU ASSIGNMENT NOTE, phased ACTION (Fortify→Elevate→Immortalize), 3+ SKILLS, AGENT INSTRUCTIONS block referencing shishya_universal.md.
- **NEVER give simple step lists, casual fixes, or flat bullet instructions.**
- **If the Founder corrects ANYTHING, update .claude/ or .agents/ files PERMANENTLY.** The Founder should never say the same thing twice.
- **Tasks are elevation protocols, not work orders.** Every task takes the system to eternal-grade.

## What This Is
Sovereign AI platform for India's 600GB research database. 3 personas (researcher/government/industry) get tier-filtered insights. All raw data stays on Indian soil. HMAC-chained audit. DPDP-2023 compliant.

---

## THE 3 DATA SOURCES (External Inputs That Drive Everything)

These are the 3 inputs from outside the codebase that shape all NRG decisions. Every session, every protocol, every agent must be aware of all 3.

### Data Source 1: Core Idea (from professor/client)
- **File**: `Core_Idea_Clean.md`
- **What**: Product vision, 3-persona model, fine-tuning endgame, sovereignty requirements
- **Status**: Fully integrated since day 1. Drives architecture, RBAC, audit chain.
- **Use**: Reference for any "why" question about NRG's design decisions.

### Data Source 2: Dhairya SQL Audit (from external engineer)
- **File**: `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` (formatted), `sesDhairya's report:.sql` (original)
- **What**: 17 real-world analytical queries with ground-truth SQL, evaluation tags, response times
- **Results**: 7/17 correct (41%), 5 wrong, 3 errors, 2 format issues. Avg 7.2s response time.
- **Who**: SesDhairya is an external engineer on a similar project — NOT on our team.
- **Status**: Report formatted, 7 failure patterns identified, agent applied fixes (schema synonyms, CTE templates, completeness validator, query context).
- **Use**: Gold-standard benchmark for Text-to-SQL accuracy. Every SQL pipeline change must be validated against these 17 queries.
- **Derived files**: `src/data/schema/schema_hints.md`, `src/data/schema/schema_value_synonyms.md`, `docs/reports/SQL_IMPROVEMENT_PLAN.md`

### Data Source 3: Official PostgreSQL Schema (from professor/client)
- **File**: `db_struct.sql` — pg_dump from PostgreSQL 14.20 (dumped 2026-01-09)
- **What**: The REAL production database schema with **58 tables** and all column definitions
- **Status**: NEW as of 2026-04-23. Needs full integration (Protocol #21).
- **Critical gap**: Our dev SQLite has only **18 tables**. The professor's PostgreSQL has **58 tables**. **40 tables are missing from our dev environment**, including ALL tables Dhairya tested against.
- **Use**: Authoritative schema reference. ALL schema hints, SQL generation prompts, and Text-to-SQL logic must eventually target this 58-table schema, not our simplified 18-table SQLite.

### Schema Gap Summary
| Environment | Tables | Status |
|---|---|---|
| Dev SQLite (`nrg_research.db`) | 18 | Working, but simplified subset |
| Prod PostgreSQL (`db_struct.sql`) | 58 | Official schema, 40 tables not in dev |
| Dhairya's queries | Reference 8+ PostgreSQL-only tables | Cannot run on dev SQLite |

### Key Missing Tables (in dev, exist in prod)
`academic_courses_details`, `innovation_grant_from_govt`, `innovations_at_various_stages_of_technology_readiness_level`, `combined_ipo_patent_data`, `incubation_details`, `financial_expenses_capital`, `financial_expenses_operational`, `actual_student_strength`, `phd_students`, `sanctioned_intake`, `placements_and_higher_studies`, `seed_funding`, `fdi_investment`, `startup_recognition`, `scraped_data`, `expertise`, `faculty_details`, `faculty_strength`, `patents_details`, `research_consultancy_details_*`, `nirf_*` tables

---

## Quick Commands
- **Run tests**: `PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -q --ignore=tests/scripts`
- **Run API**: `.venv/bin/python -m uvicorn src.api.main:app --reload --port 8000`
- **Run frontend**: `cd frontend && npm run dev`
- **Docker full stack**: `docker-compose up`
- **Check audit chain**: `.venv/bin/python scripts/audit_investigate.py`
- **Run migrations**: `alembic upgrade head`
- **Create migration**: `alembic revision --autogenerate -m "msg"`
- **List SQLite tables**: `.venv/bin/python -c "import sqlite3; conn=sqlite3.connect('nrg_research.db'); [print(t[0]) for t in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()]"`

## Architecture (6-Node LangGraph Pipeline)
```
receiver → planner → router → executor → synthesizer → verifier → END
```
- **Planner**: LLM query decomposition (src/orchestration/nodes/planner.py)
- **Router**: Classifies intent → text_to_sql / rag / hybrid (src/orchestration/nodes/router.py) — 51/51 tests passing
- **Executor**: Runs TextToSQLSkill and/or RAGSkill (src/orchestration/nodes/executor.py)
- **Synthesizer**: 3-tier cascade: cloud LLM → local SLM → rule-based (src/orchestration/nodes/synthesizer.py)
- **Verifier**: Citation faithfulness check with [cite:pub_id:chunk_id] (src/orchestration/nodes/verifier.py)

## Key Directories
- `src/api/main.py` — FastAPI endpoints (login, query, health, DPDP)
- `src/auth/` — JWT RS256 + RBAC middleware + refresh store
- `src/orchestration/` — LangGraph workflow + all 6 nodes
- `src/skills/text_to_sql/` — Schema extractor (SQLite + PostgreSQL), SQL generation, validator, query context
- `src/skills/rag/` — bge-m3 embeddings, Qdrant vector search, reranker
- `src/security/` — Prompt sanitiser (PII + injection), egress guard, schema probing defense
- `src/audit/` — HMAC-SHA256 chained immutable log (3-tuple verify_chain)
- `src/config/llm_config.py` — 6-provider mesh (NVIDIA, OpenAI, Anthropic, Azure, Gemini, Minimax)
- `src/config/local_llm.py` — LlamaCppClient + Phi-2 fallback + rule-based
- `src/data/schema/` — Schema hints, value synonyms, CTE templates (for SQL generation prompts)
- `src/observability/` — Langfuse tracer (built, unconfigured), metrics collection
- `frontend/src/` — React + TypeScript dashboards

## Auth Tiers
- Tier 1 (researcher): Full access, institution details
- Tier 2 (government): Aggregated stats, policy view
- Tier 3 (industry): Limited, anonymized data

## Database
- Dev: SQLite at `nrg_research.db` — 18 tables, simplified subset
- Prod: PostgreSQL via DATABASE_URL env var — 58 tables (official schema in `db_struct.sql`)
- Source merge verdict: `docs/security/DATA_SOVEREIGNTY_MERGE_VERDICT_2026-04-22.md`
- 3 ID namespaces coexist: Gemini (`RES_1001`), Glm (`RES-00001`), Minimax (`RES-000000`)

## Testing
- 899 tests collected, 609 passing, 263 failing (test-code mismatches from protocol #16/#17/#18 hardening)
- Router: 51/51 green
- Audit chain: rebuilt, 0 errors, thread-safe
- Coverage target: 60%+

## Environment
- Python 3.11 venv at `.venv/`
- Node 18+ for frontend
- Redis for caching (graceful degradation if down)
- Qdrant for vector search (port 6333, 19,322 vectors, 384-dim)

## The Vision Doc
Read `Core_Idea_Clean.md` for the full product vision including the fine-tuning endgame.

## The Audit Blueprint
Read `AUDIT_V3_FINAL.md` for all 40 agent tasks and the 8-sprint roadmap.

## Agent Workflow — The Loop
Every cycle follows: PLAN → EXECUTE → AUDIT → EVOLVE
- `/sprint-plan` — Start here. Produces prioritized task list → updates BACKLOG.md.
- `/pre-commit` — Every agent runs this before committing. Blocks on failures.
- `/code-review` — Mentor agent reviews all changes.
- `/security-audit` — Guardian scans for vulnerabilities.
- `/self-evolve` — After each sprint, updates rules/memory/skills.
- **BACKLOG.md** — Persistent task backlog. Check it every session. Update after task completion.
See `.claude/AGENT_WARFARE.md` for full system design.

## Session End Protocol
Before ending any session:
1. Update BACKLOG.md — mark completed tasks, add new ones discovered
2. Run `/self-evolve` mentally — what patterns emerged? Update .claude/ rules if needed
3. Answer the 3 Power Questions (see `/self-evolve` Step 2.5):
   - POWER GAP: What agentic AI capability exists today that NRG isn't using?
   - CROSS-POLLINATION: What did agents learn this session that should update system files?
   - HORIZON CHECK: Will current decisions survive 10× scale?
4. Update memory files if new learnings discovered
5. Verify all 3 Data Sources are current — any new inputs from professor or external?
6. Report session summary to Founder

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
- Give simple fix-tasks or flat step lists — ALWAYS use the full ═══ protocol format from GURU_PROTOCOL.md Section 3
- Repeat instructions the Founder already gave — if corrected once, update .claude/ or .agents/ files permanently
- Give tasks that just "fix" — every task must FORTIFY → ELEVATE → IMMORTALIZE
- Write schema hints or SQL prompts targeting only the 18-table SQLite — always consider the 58-table PostgreSQL production schema
- Assume Dhairya's queries can run on dev SQLite — they reference PostgreSQL-only tables

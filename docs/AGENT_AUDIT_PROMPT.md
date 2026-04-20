# NRG Deep Audit Prompt — For Coding Agents

Copy everything below the line and paste it to your agent.

---

You are auditing the **National Research Graph (NRG)** project — a sovereign AI platform for India's 600GB research database, built at IIT Gandhinagar with ~40 crore government backing.

## Project Context

- **Repo**: `~/Desktop/NRG`
- **Python**: 3.11 (venv at `.venv/`)
- **Backend**: FastAPI at `src/api/main.py`, runs on port 8000
- **Frontend**: React + Vite + Tailwind at `frontend/`, runs on port 3000 with Vite proxy to backend
- **Database**: Currently SQLite (`nrg_research.db`) — architecture docs say PostgreSQL
- **Orchestration**: LangGraph pipeline at `src/orchestration/graph.py` (receiver → router → executor → synthesizer)
- **Auth**: JWT RS256 with keys at `infrastructure/kong/ssl/`
- **3 User Tiers**: researcher (tier 1), government (tier 2), industry (tier 3)

## Core Documents to Read First

Read ALL of these before producing any output:
1. `Core_Idea_Clean.md` — the vision (5-layer architecture)
2. `docs/archive/Sovereign_AI_Protocols_Clean.md` — three-layer technical blueprint
3. `docs/archive/Sovereign_Infrastructure_Blueprint.md` — full implementation plan (8-month roadmap)
4. `docs/architecture/ARCHITECTURE.md` — canonical architecture spec
5. `docs/reports/FINAL_STATUS_REPORT.md` — current honest status
6. `src/api/main.py` — the FastAPI server
7. `src/orchestration/graph.py` — the LangGraph workflow
8. `src/orchestration/nodes/executor.py` — how skills get executed
9. `src/orchestration/nodes/synthesizer.py` — how responses get generated
10. `src/skills/text_to_sql/skill.py` — the Text-to-SQL skill
11. `src/skills/rag/skill.py` — the RAG skill
12. `src/skills/rag/embedder.py` — embedding generation
13. `src/config/llm_config.py` — LLM provider mesh (OpenAI/Anthropic/Gemini/Azure)
14. `src/data/database.py` — SQLite database manager
15. `src/security/gateway/prompt_sanitiser.py` — PII + injection detection
16. `src/security/pii/tokenizer.py` — PII tokenization engine
17. `src/audit/__init__.py` — HMAC-chained immutable audit log
18. `src/auth/jwt_handler.py` — JWT auth with RS256
19. `src/auth/middleware.py` — RBAC filtering per tier
20. `src/caching/redis_layer.py` — Redis caching layer
21. `docker-compose.yml` — service definitions
22. `pyproject.toml` — dependencies
23. `.env` — current environment config
24. `.env.example` — reference config
25. `frontend/src/App.tsx` — frontend entry
26. `frontend/src/components/Login.tsx` — login component
27. `frontend/src/services/authService.ts` — auth API client
28. `frontend/src/services/queryService.ts` — query API client
29. `frontend/vite.config.ts` — Vite proxy config

## What Has Already Been Fixed (do NOT redo these)

- `src/audit/__init__.py` line 44: `returnjson` → `return json` (was a syntax bug)
- DEPRECATED banners removed from core docs
- Hardcoded secrets replaced with env vars (tokenizer, jwt_handler)
- `.env.production` and `.jwt_secret` deleted from disk
- Chinese characters removed from ARCHITECTURE.md
- Root directory cleaned (reports moved to `docs/reports/`)
- README updated with honest Phase 1/2/3 status
- FINAL_STATUS_REPORT rewritten honestly
- JWT RS256 crash fixed (self.secret_key guard moved inside else block)
- Port alignment: backend=8000, Vite proxy=8000
- Frontend Login.tsx passwords updated to match .env
- Missing deps added to pyproject.toml (cryptography, redis)
- Python 3.11 venv created and all deps installed
- App starts, login works, health check works, /query returns fallback response

## What is STILL BROKEN (the actual work)

These are the known gaps. Verify each one, find any others, then produce protocols.

### 1. NO WORKING LLM SYNTHESIS
`.env` has `GEMINI_API_KEY=AIzaSy_REPLACE_ME`. The `_env()` function in `llm_config.py` detects "REPLACE_ME" and returns None. ALL queries return fallback text: "The synthesis engine is currently unavailable." The entire intelligence layer is non-functional. Need a real API key OR a working local SLM integration.

### 2. TEXT-TO-SQL SKILL — DOES IT ACTUALLY GENERATE SQL?
`src/skills/text_to_sql/skill.py` — read this carefully. Does it actually call the LLM to generate SQL from natural language? Or does it use hardcoded queries? If it depends on the LLM (which has no key), then structured queries also fail silently. The executor in `executor.py` catches all exceptions and logs them as warnings.

### 3. RAG SKILL — NO VECTOR STORE RUNNING
`src/skills/rag/skill.py` and `src/skills/rag/embedder.py` — the code exists but there's no Qdrant instance running. No embeddings have been generated. No documents have been chunked and indexed. The RAG path in the executor will fail silently every time.

### 4. SQLITE vs POSTGRESQL
`src/data/database.py` uses SQLite. `.env` says `DATABASE_URL=sqlite:///nrg_research.db`. But ALL architecture docs, docker-compose, and the Text-to-SQL sandbox (`src/skills/text_to_sql/sandbox.py`) default to `postgresql://nrg:nrg_secret@localhost:5432/nrg`. These two systems are disconnected. The API uses SQLite, the skills try PostgreSQL.

### 5. REDIS NOT RUNNING
`src/caching/redis_layer.py` is imported in `src/orchestration/graph.py` (line 19, `@cache_query` decorator). If Redis isn't running, does this crash? Or does it gracefully degrade? Read the code and verify.

### 6. FRONTEND DASHBOARD — DOES THE QUERY UI WORK?
After login, each persona sees a dashboard (`ResearcherDashboard`, `GovernmentDashboard`, `IndustryDashboard`). Read the dashboard components. Do they have a search bar that calls `/query`? Do they render the response correctly? Or are they just static shells?

### 7. TEST SUITE — HOW MANY ACTUALLY PASS?
Run: `.venv/bin/python -m pytest tests/ -v --tb=short 2>&1 | tail -40`
Report exactly how many pass, fail, and error. Fix the critical failures.

### 8. KNOWLEDGE GRAPH — DEAD CODE?
`experiments/knowledge_graph/loader.py` and `traversals.py` reference Neo4j. Is this integrated into the workflow? Or is it experimental code that exists but is never called?

### 9. DATABASE SEED DATA QUALITY
`nrg_research.db` has 200 researchers, 24 institutions, 500 publications, 50 labs, 100 funding records. Junction tables `researcher_publications` (666 rows), `researcher_labs` (284 rows), `publication_keywords` (1276 rows), and `keywords` (64 rows) are populated. Text-to-SQL queries about "publications by researcher X" will return real results.

### 10. AUDIT LOG INTEGRATION
`src/audit/__init__.py` has the HMAC chain logic. But is it actually called anywhere in the pipeline? Is every query logged? Every SQL execution? Every LLM call? Or is it standalone code that never gets invoked?

## Your Deliverables — Exactly 5 Sections

### 1. Gap Analysis
Read every file listed above. Find everything that is genuinely broken, missing, or unreliable — beyond what I listed. Be ruthlessly specific: exact file paths, line numbers, error messages, failure modes. For each gap, state the severity: CRITICAL (app crashes), HIGH (feature non-functional), MEDIUM (degraded experience), LOW (cosmetic/cleanup).

### 2. Real Value Assessment
What does a real user (IIT Gandhinagar professor, government stakeholder, researcher) actually get today? What can they do? What can't they do? What's the minimum feature set that makes this a credible Phase 1 demo? Compare honestly to what the architecture docs promise.

### 3. Priority Fix List (ordered by impact)
For each item:
- What is broken / missing
- Why it matters
- Exact steps to fix (file paths, code changes, commands)
- Success criteria (how to verify)

### 4. Agent Task Protocols
Convert EVERY item from the Priority Fix List into self-contained, copy-paste-ready tasks. Each task must include:
- Files to read first (exact paths)
- Changes to make (exact code or commands)
- Verification command
- Suggested commit message

These must be precise enough that a coding agent can execute them without asking questions.

### 5. Ship Checklist
The minimum steps to go from current state to "professor can open this, log in, type a research question, and get an intelligent answer with citations." Every step, in order, with commands.

Begin now. Read the files, then deliver all 5 sections. No filler, no philosophy — pure technical substance.

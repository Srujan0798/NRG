# NRG — National Research Graph

## What This Is
Sovereign AI platform for India's 600GB research database. 3 personas (researcher/government/industry) get tier-filtered insights. All raw data stays on Indian soil. HMAC-chained audit. DPDP-2023 compliant.

## Quick Commands
- **Run tests**: `cd /Users/srujansai/Desktop/NRG && .venv/bin/python -m pytest tests/ -v --tb=short`
- **Run API**: `.venv/bin/python -m uvicorn src.api.main:app --reload --port 8000`
- **Run frontend**: `cd frontend && npm run dev`
- **Docker full stack**: `docker-compose up`
- **Check audit chain**: `.venv/bin/python scripts/audit_investigate.py`

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
- Dev: SQLite at `src/data/nrg_research.db` (200 researchers, 500 pubs, 24 institutions, 50 labs)
- Prod: PostgreSQL via DATABASE_URL env var
- Junction tables: researcher_publications (689), researcher_labs (278), publication_keywords (1202)

## Testing
- 170 tests passing, 0 failures
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

## DO NOT
- Commit .env files or secrets
- Use `allow_origins=["*"]` with credentials in CORS
- Skip audit logging on state changes
- Return raw PII (Aadhaar, PAN) in API responses
- Push directly to main without review
# Repository Structure And Cleanup Plan

Date: 2026-05-02

This plan records the current repository structure, cleanup decisions, and the
target company-level organization for NRG. It is intentionally conservative:
canonical product, schema, Dhairya audit, source-truth, and runtime proof files
are protected from accidental cleanup.

## Current State

NRG is a working local answer-engine repository with:

- FastAPI backend for auth, query, audit, health, tier shaping, and data APIs.
- LangGraph orchestration for query planning, routing, execution, synthesis,
  verification, and retry handling.
- Text-to-SQL and RAG skill layers with schema-aware prompts, sandboxing,
  examples, validators, and Qdrant ingestion.
- React/Vite frontend with persona dashboards, query home, streaming answer,
  citations, source rows, HMAC proof drawer, DPDP surfaces, and responsive tests.
- Security layer for JWT, RBAC, PII controls, prompt sanitisation, tier filters,
  rate limiting, egress controls, and audit chain verification.
- Broad tests across API, security, audit, orchestration, skills, frontend,
  integration, property, load, and UAT surfaces.
- Infrastructure for Docker Compose, Kong, Nginx, Prometheus, Grafana, Helm,
  sovereign deployment, and model/runtime support.

The current local proof is strong for the laptop/local path, but production
claims remain blocked until deployed URLs, cluster-load access, founder signing,
and real production data ingestion are available.

## Protected Source Truth

Do not remove or relocate these without updating every reference and verification
tool in the same commit:

| File | Role |
| --- | --- |
| `Core_Idea_Clean.md` | Product and visible UX truth |
| `db_struct.sql` | Canonical minimum PostgreSQL schema |
| `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` | Official formatted Dhairya audit |
| `docs/reports/SQL_AUDIT_RAW_dhairya.sql` | Raw Dhairya audit |
| `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md` | Source hierarchy |
| `CORPUS/` | Portable mirror, verified by `scripts/verify_corpus_sync.py` |
| `.claude/CURRENT_STATE.md` | Current agent-facing project status |
| `prompts_hybrid/` | Agent execution prompt stones |

## Cleanup Decisions

| Area | Decision | Reason |
| --- | --- | --- |
| Generated caches | Remove locally and keep ignored | Recreated by tools |
| Node modules and npm cache | Remove locally and keep ignored | Reinstallable dependencies, not repo source |
| `.audit/` | Keep local chain, do not commit | Runtime compliance data |
| `data/` | Keep local DBs, do not commit | Local Docker release path depends on `data/nrg_research.db` |
| `CORPUS/` | Keep | Portable AI handoff mirror |
| Root `db_struct.sql` | Keep | Canonical schema source |
| Dhairya docs in `docs/reports/` | Keep | Official verification baseline |
| `docs/ops/` | Keep | API health reads data-quality scorecard here |
| Evidence binaries | Keep latest proof for now; later archive duplicates | Current handoff proof still references them |
| `src/api/main.py` | Split later, not during cleanup wave | High-risk hot path |
| Scripts | Consolidate later by category | Many are referenced by docs/tests |
| Agent skills | Keep tracked `.agents/skills/` and `.claude/skills/`; remove untracked duplicate imports | Prevents copied marketplace/rewritten skill clutter from becoming project truth |
| Root `AGENTS.md` | Keep as a short execution entry point | Prevents future agents from reading strategy-only Claude rules as universal coding rules |

## Target Repository Shape

```text
NRG/
  Core_Idea_Clean.md
  db_struct.sql
  README.md
  BACKLOG.md
  CHANGELOG.md

  src/
    api/
      main.py
      query_response_utils.py
      routes/
      middleware/
      contracts/
    orchestration/
    skills/
      text_to_sql/
      rag/
    auth/
    security/
    audit/
    data/
    services/
    observability/
    config/

  frontend/
    src/
    tests/
    e2e/

  tests/
    api/
    security/
    audit/
    orchestration/
    skills/
    integration/
    e2e/
    load/

  scripts/
    audit/
    deploy/
    ingest/
    load/
    maintenance/
    seed/
    verify/

  docs/
    README.md
    architecture/
    reports/
    runbooks/
    specs/
    handover/
    compliance/
    operations/
    ops/

  CORPUS/
  infrastructure/
  alembic/
  evidence/
```

## Next Cleanup Waves

### Wave 1: Safe Local Cleanup

Completed in this pass:

- Removed ignored caches and generated local dependency directories.
- Added `docs/README.md`, `scripts/README.md`, and `evidence/README.md`.
- Added this cleanup plan.

### Wave 2: Root And Runtime Hygiene

Completed in this pass:

- Removed tracked runtime env files from git index while preserving local copies:
  `.env.dev`, `.env.local`, `.env.prod`, and `.env.staging`.
- Added ignore rules for runtime env variants and added
  `.env.staging.example` as the tracked staging template.
- Removed stale root one-off browser launchers:
  `test_all_personas.js`, `test_full_website.py`, and `test_runner.js`.
- Removed stale root Playwright/npm files. Browser tooling is owned by
  `frontend/package.json`, `frontend/playwright.config.ts`, and
  `frontend/tests/playwright.config.ts`.
- Removed tracked local Qdrant runtime state from `qdrant_storage/`; vector DB
  state is generated by the running service and should not be committed.
- Added VS Code workspace hide rules for local env files, runtime DBs, caches,
  Python bytecode, node modules, and local service state so the explorer shows
  source structure instead of generated clutter.

### Wave 3: Evidence Slimming

- Keep latest evidence summaries.
- Archive duplicate screenshots/videos and old browser recordings.
- Replace repeated binary proof in git with small markdown indexes where safe.

### Wave 4: Script Consolidation

- Build a script registry with owner, category, callers, and status.
- Move scripts by category only when references and tests are updated.
- Delete only scripts with zero references and no unique behavior.

### Wave 5: Backend Architecture Split

Started in the backend split pass:

- Extracted audit proof and audit-chain routes from `src/api/main.py` into
  `src/api/routes/audit.py`.
- Registered the audit router from `src/api/main.py`.
- Removed duplicate audit route definitions from `src/api/routes/admin.py` so
  future admin-router activation does not create overlapping `/audit/*` paths.
- Extracted DPDP consent, data export, data erasure, and `/me/*` data-rights
  endpoints into `src/api/routes/dpdp.py`.
- Registered the DPDP router from `src/api/main.py`.
- Made `src/api/routes/__init__.py` import-free so route activation is explicit
  and dormant route modules do not load stale endpoint definitions.
- Removed stale DPDP/data-rights definitions from the dormant auth route module,
  leaving auth focused on login/session endpoints.
- Extracted login, SSO, session, refresh, and logout routes into
  `src/api/routes/auth.py`, configured against the same app-level `JWTHandler`
  instance used by auth middleware so token revocation semantics stay intact.
- Extracted metrics, SLO, vector reindex, and RBAC policy administration routes
  into `src/api/routes/admin.py` while preserving the existing `/api/metrics`
  JSON contract and lightweight audit-health behavior.
- Extracted researcher, stats, publication, project, patent, collaboration,
  funding, lab, and research-document data routes into
  `src/api/routes/data.py`, configured against the app-level DB getter, cache,
  and tier response filter so tests and runtime monkeypatches keep the same
  behavior.
- Replaced the stale health-route module with the live `/health`,
  `/health/all`, `/health/db`, `/health/qdrant`, `/health/llm`,
  `/api/providers/health`, `/api/vectors/health`, and killer-query health
  behavior from `src/api/main.py`, configured against the app-level DB, JWT,
  audit, drift, data-quality, and Qdrant dependencies.
- Extracted graph visualization and internal Tier 1 response-shape diff routes
  into `src/api/routes/graph.py`, configured against app-level DB, cache,
  release-seed graph, tier history, and tier response filter helpers.
- Extracted frontend UAT telemetry ingestion into `src/api/routes/telemetry.py`
  with the existing event allowlist, PII redaction, recent-event memory buffer,
  and audit-chain binding behavior.
- Replaced the stale ingestion route module with the live document ingestion
  job-store behavior from `src/api/main.py`, and moved feedback/RLHF signal
  submission into `src/api/routes/feedback.py`.
- Replaced stale `src/api/routes/query.py` with a thin live adapter for
  `/query` and `/api/query/stream`; the endpoint registration is now modular
  and the heavy answer-engine implementation now lives in
  `src/api/query_service.py`. `src/api/main.py` wires dependencies and keeps
  thin compatibility wrappers for tests and older internal call sites.
- Moved the frontend SPA catch-all into `src/api/routes/spa.py` and registered
  it last, after all API routers and static assets, to preserve route ordering.

Remaining route splits:

- None. `src/api/main.py` owns app setup, middleware, lifecycle, dependency
  wiring, and router registration. `src/api/query_service.py` owns `/query`
  and `/api/query/stream` answer-engine execution.
- 2026-05-02 wrap-up extracted query response support helpers into
  `src/api/query_response_utils.py`: PII redaction, answer-confidence mapping,
  SSE formatting, query/stream payload normalization, citation-token parsing,
  and answer-record persistence. This was intentionally limited to helper
  extraction because `src/api/query_helpers.py` and the live fast-path logic in
  `src/api/main.py` currently diverge.
- 2026-05-03 follow-up closed the active drift boundary: exported fast-path
  helpers in `src/api/query_helpers.py` now delegate to the live answer-engine
  implementation in `src/api/main.py`, and regression tests cover the known
  drift cases. The old helper copy is still present as dormant implementation
  detail and should be physically slimmed only during a broader query-service
  extraction.
- 2026-05-03 query-service extraction moved the live answer-engine body out of
  `src/api/main.py` into `src/api/query_service.py`, preserved route contracts,
  and added architecture tests that keep `main.py` wrappers thin while checking
  blocking answer paths stay behind `asyncio.to_thread`.

Next backend hardening:

- Continue query-service hardening with broader messy-query, Dhairya,
  external-template, tier-shaping, stream-contract, and frontend adapter
  regressions before any further answer-path refactor.

### Wave 5.5: Agent Workflow Hygiene

Completed in the 2026-05-02 wrap-up:

- Removed 85 untracked `.agents/skills/*` duplicate directories. All 85 had a
  matching `.claude/skills/<name>/SKILL.md`; 65 were exact `SKILL.md` matches
  and the remaining 20 were automatic text rewrites with invalid `.Codex/...`
  references.
- Removed untracked `.codex/` local hook files after verifying the hook script
  was byte-identical to `.claude/hooks/security_reminder_hook.py`.
- Added `.codex/` and root `.npm-cache/` to `.gitignore` as local tool/cache
  artifacts.
- Replaced the root `AGENTS.md` with a concise cross-tool entry point that
  points implementation agents to `.agents/AGENTS.md`, keeps source-truth rules
  visible, and blocks unsupported "100% complete" claims without evidence.

### Wave 6: Documentation Rationalization

- Replace duplicated architecture/handover/runbook content with links.
- Keep current handover material and official reports.
- Archive superseded prompt dumps and stale status reports.

## Verification Gates For Cleanup

Every cleanup commit should run the relevant subset:

```bash
python3 scripts/verify_corpus_sync.py
.venv/bin/python -m pytest tests/api/test_audit_event_endpoint.py tests/api/test_langgraph_api.py tests/api/test_query_security_validation.py -q --tb=short --no-cov
git diff --check
```

For frontend-moving work, reinstall dependencies and run:

```bash
cd frontend
npm install
npm run build
npm test -- --runInBand
```

For browser-flow claims, run the relevant Playwright spec and save evidence.

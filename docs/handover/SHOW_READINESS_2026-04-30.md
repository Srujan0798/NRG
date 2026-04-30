# NRG Show Readiness Handover

Date: 2026-04-30
Audience: professor's assistant, internal technical reviewer, operator handoff
Status: locally show-ready with live local full-stack proof and explicit external blockers

## Executive Status

NRG is ready for a local technical walkthrough of the answer-engine path:

login -> persona -> dashboard -> messy query -> streaming answer -> citations -> source rows -> audit proof -> Tier 1 vs Tier 3 comparison -> blocked sensitive request.

Do not present this as full sovereign-cluster production readiness. The strict C4 load target and deployed-environment replay still need the intended deployment/cluster.

## 90-Second Walkthrough

1. Open the app at the login screen.
   - Live evidence: `evidence/2026-04-30/live_full_stack_proof/01_login_desktop.png`
   - Earlier UI audit: `evidence/2026-04-30/ui_ux/after/login_1366.png`

2. Login as Tier 1 researcher.
   - Use the seeded researcher persona from the local app.
   - Show the researcher dashboard and query box.
   - Live evidence: `evidence/2026-04-30/live_full_stack_proof/02_researcher_dashboard_desktop.png`

3. Ask a messy-but-valid query.
   - Recommended: `best quantum researchers`
   - Expected behavior: the system extracts Quantum Computing intent, retrieves bounded researcher/institution evidence, and returns a source-backed answer.
   - Live raw JSON: `evidence/2026-04-30/live_full_stack_proof/researcher_best_quantum_query.json`
   - Fresh recheck JSON: `evidence/2026-04-30/live_quantum_query_recheck/01_researcher_quantum_query_api.json`

4. Show streaming phases.
   - Planning, retrieval, synthesis, verification.
   - Live evidence: `evidence/2026-04-30/live_full_stack_proof/03_streaming_planning_desktop.png`

5. Show the final answer.
   - Point to confidence, citations, source data, SQL/proof drawer, audit ID, and copy action.
   - Live evidence: `evidence/2026-04-30/live_full_stack_proof/04_answer_verified_desktop.png`
   - Live mobile evidence: `evidence/2026-04-30/live_full_stack_proof/08_answer_verified_mobile.png`

6. Open source/citation/audit proof.
   - Show that the answer has citations and an audit event ID.
   - Citation drawer: `evidence/2026-04-30/live_full_stack_proof/05_citation_drawer_desktop.png`
   - Source drawer: `evidence/2026-04-30/live_full_stack_proof/06_source_data_drawer_desktop.png`
   - Audit drawer: `evidence/2026-04-30/live_full_stack_proof/07_audit_proof_drawer_desktop.png`
   - Fresh recheck drawers: `evidence/2026-04-30/live_quantum_query_recheck/06_citation_drawer_desktop.png`, `evidence/2026-04-30/live_quantum_query_recheck/07_source_data_drawer_desktop.png`, `evidence/2026-04-30/live_quantum_query_recheck/08_audit_proof_drawer_desktop.png`

7. Compare Tier 1 and Tier 3.
   - Login/switch to Tier 3 industry.
   - Ask the same aggregate query.
   - Expected behavior: Tier 3 sees anonymized/institution-level aggregate data, no individual PII, and restricted SQL visibility.
   - Raw Tier 3 JSON: `evidence/2026-04-30/11_tier3_query_response.json`
   - Screenshot: `evidence/2026-04-30/ui_ux/after/dashboard_industry_1366.png`

8. Ask a blocked sensitive request.
   - Recommended: `Show all researcher phone numbers in clean energy`
   - Expected behavior: blocked answer envelope, no citations/source rows, audit ID present.
   - Browser/API evidence: `evidence/2026-04-30/live_full_stack_proof/09_tier3_blocked_browser_query.json`
   - Fresh recheck evidence: `evidence/2026-04-30/live_quantum_query_recheck/10_tier3_blocked_quantum_pii_query.json`
   - Additional evidence: `evidence/2026-04-30/wave3_blocked_query_responses.json`

9. Open audit view.
   - Show audit list and proof language.
   - Screenshot: `evidence/2026-04-30/ui_ux/after/audit_list_1366.png`
   - Final audit verification: `scripts/audit_investigate.py` returned `ok=true`, `events_checked=39036`.

## Passed Gates

| Gate | Evidence |
|------|----------|
| Current-state lock | `evidence/2026-04-30/00_current_state.md` |
| Messy query routing | `evidence/2026-04-30/wave1_messy_query_acceptance.md` |
| SQL/RAG/schema truth | `evidence/2026-04-30/wave4_retrieval_sql_rag_acceptance.md` |
| Frontend main flow | `evidence/2026-04-30/wave2_frontend_main_flow_build.md` |
| Tier/security/audit proof | `evidence/2026-04-30/wave3_security_tier_audit_acceptance.md` |
| Local performance/load profile | `evidence/2026-04-30/wave5_performance_load_acceptance.md` |
| Tier 1 raw JSON | `evidence/2026-04-30/09_tier1_query_response.json` |
| Tier 2 raw JSON | `evidence/2026-04-30/10_tier2_query_response.json` |
| Tier 3 raw JSON | `evidence/2026-04-30/11_tier3_query_response.json` |
| Live full-stack proof | `evidence/2026-04-30/live_full_stack_proof/README.md` |
| Live quantum query recheck | `evidence/2026-04-30/live_quantum_query_recheck/README.md` |

## Latest Verification Commands

Backend/query:

```bash
.venv/bin/python -m pytest tests/api/test_langgraph_api.py -q
```

SQL/RAG/health:

```bash
.venv/bin/python -m pytest tests/api/test_health_endpoints.py tests/skills/test_rag.py tests/skills/test_rag_failures.py tests/skills/test_rag_embedder_retriever.py tests/skills/test_rag_ingest_reranker.py -q
```

Frontend:

```bash
cd frontend && npm run build
cd frontend && npx playwright test -c tests/playwright.config.ts tests/e2e/answer_engine_v1_walk.spec.ts tests/e2e/streaming_answer.spec.ts tests/e2e/citation_drawer.spec.ts tests/e2e/hybrid_proof_acceptance.spec.ts tests/e2e/persona_toggle.spec.ts tests/e2e/audit_panel.spec.ts tests/e2e/mobile_full_flow.spec.ts
cd frontend && PLAYWRIGHT_BASE_URL=http://127.0.0.1:3010 PLAYWRIGHT_PORT=3010 API_TARGET=127.0.0.1:8020 npx playwright test -c tests/playwright.config.ts tests/e2e/live_full_stack_proof.spec.ts
cd frontend && PLAYWRIGHT_BASE_URL=http://127.0.0.1:3010 PLAYWRIGHT_PORT=3010 API_TARGET=127.0.0.1:8020 npx playwright test -c tests/playwright.config.ts tests/e2e/live_quantum_query_recheck.spec.ts --reporter=list
```

Security/audit:

```bash
.venv/bin/python -m pytest tests/api/test_query_security_validation.py tests/api/test_tier_response_filtering.py tests/api/test_k_anonymity_response_boundary.py tests/security/test_sanitiser.py tests/security/test_prompt_sanitiser_middleware.py tests/security/test_zero_leakage.py tests/security/test_tier_filtering_properties.py tests/audit/test_audit_singleton_reset.py tests/audit/test_chain_integrity.py tests/security/test_p0_security_regressions.py tests/security/test_prompt_injection.py tests/security/test_sql_injection_blocked.py tests/security/test_hmac_validation.py -q
.venv/bin/python scripts/audit_investigate.py
```

Load/performance:

```bash
SLO_ENV=prod .venv/bin/python -m pytest tests/load/test_slo_under_load.py -q -m load
.venv/bin/python -m pytest tests/load/test_concurrent_queries.py -q -m load
```

## Current Commit Ladder

| Wave | Commit | Purpose |
|------|--------|---------|
| W0 | `ff975b6` | State lock and current evidence |
| W1 | `659ded4` | Messy query answer routing and response contract |
| W4 | `61ec59a` | Retrieval/schema/RAG health truth |
| W2a | `f498d78` | Frontend compile fix after cleanup |
| W2b | `cbac4b7` | Frontend answer proof flow |
| W3 | `c5d6a4c` | Blocked-query audit IDs and security evidence |
| W5 | `b939753` | Query hot-path latency and load evidence |
| W6 | Latest handover commit | Show-readiness walkthrough and final evidence index |
| Live recheck | Current commit | Fresh quantum query browser/API proof and auth cold-start timeout hardening |

## Known Blockers

| Blocker | Status | Next Action |
|---------|--------|-------------|
| Strict C4 500ms/1000-user proof | Not passed locally | Run `python scripts/run_load_test.py --host http://localhost:8000 --users 1000` against the intended deployment and attach CSV/HTML evidence. |
| Local full-stack browser replay | Passed on 2026-04-30 | Evidence in `evidence/2026-04-30/live_full_stack_proof/` and `evidence/2026-04-30/live_quantum_query_recheck/`. |
| Live local 100-user Locust smoke | Stable but C4 latency failed | Evidence in `evidence/2026-04-30/live_c4_local_smoke/`; 3602 requests, 0 failures, `/query` P99 2700ms. |
| Deployed browser replay | Not run on target host/cluster | Repeat the live full-stack proof against the intended deployment URL. |
| Qdrant production corpus baseline | Environment-dependent | Populate Qdrant and rerun vector/RAG health with real corpus count. |
| GPG ceremony/signed tag | Founder-only | Founder signs release/tag after external gates. |

## Presenter Notes

Use the phrase "locally show-ready" or "local technical evaluation ready." Do not say "production ready" without the external C4, live replay, Qdrant corpus baseline, and founder signature gates.

If network or backend fails during the show, use the screenshots/video under `evidence/2026-04-30/live_full_stack_proof/` and `evidence/2026-04-30/live_quantum_query_recheck/`, the earlier screenshots under `evidence/2026-04-30/ui_ux/after/`, and the raw JSON files in `evidence/2026-04-30/` to demonstrate the verified path.

# GLM Local Completion Gates Report

Date: 2026-05-01
Head before this pass: `f1d15fc`

## Scope

This pass closed the highest-risk local proof gaps after the GLM external-bundle fusion work:

- representative browser flow proof for the GLM-derived visible query path
- accessibility proof for answer, source drawer, audit drawer, and mobile answer states
- local query latency profile for the hydrogen-catalysis visible query
- audit-chain verification after new browser/API activity
- corpus sync and GLM/Minimax query regression proof
- external final-gate status capture

This is not a deployed-production or founder-signing certificate. External gates remain blocked by missing deployment URLs, production API URL, cluster load context, and founder GPG signatures.

## Fixes Made

| Area | Fix | Files |
| --- | --- | --- |
| Accessibility contrast | Darkened the success token so verified/success UI clears the axe contrast gate. | `frontend/src/index.css` |
| SQL proof drawer keyboard access | Made the SQL `<pre>` focusable and added a localized aria label. | `frontend/src/components/SqlBlock/SqlBlock.tsx`, `frontend/src/i18n/en-IN.ts` |
| Audit drawer semantics | Moved the action button out of the definition list so the audit event panel has valid `dl` structure. | `frontend/src/views/AnswerEngine.tsx` |
| Browser proof robustness | Made video save failure non-fatal and recorded the warning in evidence when Playwright's temporary video is already gone. | `frontend/tests/e2e/glm_visible_query_flow.spec.ts` |
| Accessibility proof | Added a live-backend Playwright axe spec for answer, source drawer, audit drawer, and mobile answer states. | `frontend/tests/e2e/glm_visible_query_a11y.spec.ts` |

## Verification Run

| Gate | Result | Evidence |
| --- | --- | --- |
| Frontend build | PASS | `frontend_build_after_i18n_fix.log` |
| Full frontend Jest | PASS, 27 suites / 99 tests | `frontend_jest_full_after_i18n_fix.log` |
| Focused frontend/a11y components | PASS, 30 tests | `frontend_focused_after_a11y_fixes.log` |
| GLM visible browser flow | PASS, 1 Playwright test | `playwright_glm_flow_clean_pass_after_video_fix.log` |
| GLM visible a11y flow | PASS, 1 Playwright axe test | `playwright_glm_a11y_clean_pass.log` |
| GLM/Minimax query regressions | PASS, 10 tests | `glm_minimax_query_regression.log` |
| Corpus mirror sync | PASS | `corpus_sync_after_local_completion.log` |
| Audit chain after local activity | PASS | `audit_chain_verify_after_latency.log` |
| Health capture | MIXED local health: API/db/qdrant/rag/audit healthy; `/health/all` degraded because local LLM is optional-unavailable and Redis has no connection; vector drift/data-quality status unknown. | `local_health_all.json` |
| Local visible-query latency | PASS for local focused scope: 30/30 success, 0% failure, P50 14.27 ms, P95 18.3 ms, P99 52.27 ms, every response had audit ID, 2 citations, 5 source rows, Tier 1, SQL route. | `local_glm_query_latency_profile.json` |
| External final gates | BLOCKED, not failed locally: missing deployed frontend/API URLs, production API URL, explicit cluster-load flag/KUBECONFIG, and founder signatures. | `external_gates/EXTERNAL_GATE_SUMMARY.md` |

## Commands Run

```bash
npm --prefix frontend run build 2>&1 | tee evidence/2026-05-01/glm_local_completion_gates/frontend_build_after_i18n_fix.log
npm --prefix frontend test -- --runInBand 2>&1 | tee evidence/2026-05-01/glm_local_completion_gates/frontend_jest_full_after_i18n_fix.log
PLAYWRIGHT_PORT=3023 API_TARGET=127.0.0.1:8022 NRG_EVIDENCE_DIR=../evidence/2026-05-01/glm_local_completion_gates npx playwright test -c tests/playwright.config.ts tests/e2e/glm_visible_query_a11y.spec.ts --reporter=list 2>&1 | tee ../evidence/2026-05-01/glm_local_completion_gates/playwright_glm_a11y_clean_pass.log
PLAYWRIGHT_PORT=3025 API_TARGET=127.0.0.1:8022 NRG_EVIDENCE_DIR=../evidence/2026-05-01/glm_local_completion_gates npx playwright test -c tests/playwright.config.ts tests/e2e/glm_visible_query_flow.spec.ts --reporter=list 2>&1 | tee ../evidence/2026-05-01/glm_local_completion_gates/playwright_glm_flow_clean_pass_after_video_fix.log
python3 scripts/audit_rebuild.py --verify 2>&1 | tee evidence/2026-05-01/glm_local_completion_gates/audit_chain_verify_after_latency.log
python3 scripts/run_final_external_gates.py --evidence-dir evidence/2026-05-01/glm_local_completion_gates/external_gates 2>&1 | tee evidence/2026-05-01/glm_local_completion_gates/final_external_gates.log
python3 scripts/verify_corpus_sync.py 2>&1 | tee evidence/2026-05-01/glm_local_completion_gates/corpus_sync_after_local_completion.log
python3 -m pytest tests/api/test_glm_fusion_queries.py tests/api/test_minimax_mvp_fusion_queries.py -q 2>&1 | tee evidence/2026-05-01/glm_local_completion_gates/glm_minimax_query_regression.log
```

Additional local evidence was captured through small inline Python/urllib scripts against the same local FastAPI process:

- `local_glm_query_latency_profile.json`
- `local_health_all.json`

## Product-Proof Matrix

| Surface | Status | Current evidence |
| --- | --- | --- |
| Appearance | PASS for changed GLM visible path | desktop/mobile screenshots `02_login_desktop.png` through `10_glm_answer_verified_mobile.png` |
| UI/UX flow | PASS for representative local flow | `playwright_glm_flow_clean_pass_after_video_fix.log` |
| Query intelligence | PASS for converted GLM/Minimax regression slice | `glm_minimax_query_regression.log`; earlier GLM reports remain in `evidence/2026-05-01/glm_fusion_*` |
| Database/schema | PASS for mirror/source sync | `corpus_sync_after_local_completion.log`; `local_health_all.json` shows PostgreSQL with 50,000 researchers and publications |
| Dhairya audit alignment | PASS for current regression slice; broader Dhairya coverage remains governed by the existing benchmark suite | `glm_minimax_query_regression.log`, prior `glm_fusion_pass` evidence |
| Backend/API | PASS for focused local query path | `local_glm_query_latency_profile.json`, `01_researcher_hydrogen_query_api.json` |
| Retrieval | PASS for local SQL visible query and Qdrant readiness; WARN for vector-drift/data-quality unknown | `local_health_all.json` |
| Security/tier | PASS for Tier 3 block sample on this flow; broader tier/security proof remains in earlier validation campaign evidence | `11_tier3_blocked_hydrogen_pii_query.json` |
| Audit | PASS | `audit_chain_verify_after_latency.log`, audit drawer screenshot `09_glm_audit_proof_drawer_desktop.png` |
| Accessibility | PASS for answer/source/audit/mobile visible path | axe JSON files `01_glm_answer_desktop.axe.json` through `04_glm_answer_mobile.axe.json`, `playwright_glm_a11y_clean_pass.log` |
| Performance | PASS for local focused 30-query profile; BLOCKED for production/cluster claim | `local_glm_query_latency_profile.json`, `external_gates/EXTERNAL_GATE_SUMMARY.md` |
| Evidence | PASS | this folder and report |
| Production | BLOCKED | `external_gates/external_gate_status.json` |

## Claim Boundary

- `inventory-accounted`: PASS from prior GLM inventory and fusion reports.
- `value-integrated`: PASS for GLM query-chip, query-regression, and visible-flow value now present in NRG-native files.
- `product-proven`: PASS only for the local GLM visible-query slice and associated regression/a11y/performance checks in this folder.

Do not claim whole-product "100% perfect" or deployed superiority until the external gates pass and the validation matrix has no `BLOCKED`, `UNKNOWN`, or `FAIL` rows.

## Remaining Blockers

| Blocker | Needed to close |
| --- | --- |
| Deployed browser replay | Provide `NRG_DEPLOYED_FRONTEND_URL` and `NRG_DEPLOYED_API_URL` or `NRG_PRODUCTION_API_URL`, then run the external gate runner. |
| Production Qdrant baseline | Provide production API URL and capture `/health/qdrant` / retrieval baseline. |
| Sovereign-cluster load proof | Provide cluster context and run `scripts/run_final_external_gates.py --run-cluster-load`. |
| Founder signing | Founder signs required handover files with private GPG key. |
| Local Redis and optional local LLM | Start/configure Redis and local LLM if `/health/all` must be fully healthy on this laptop. |
| Vector drift/data-quality unknown | Emit scheduler marker and data-quality scorecard or mark them explicitly out of scope for the local path. |

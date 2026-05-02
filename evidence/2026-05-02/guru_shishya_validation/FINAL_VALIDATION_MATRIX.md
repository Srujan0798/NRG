# Guru/Shishya Validation Matrix

Date: 2026-05-02
Base commit: `65fe8be`

This report is an evidence matrix for the current local checkout. It is not a
production-readiness certificate.

## Verdict

| Surface | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Repo hygiene and source truth | PASS | `01_git_status_start.log`, `06_corpus_sync.log`, `07_forbidden_vocab.log`, `215_git_diff_check_after_live_orchestration.log`, `216_corpus_sync_after_live_orchestration.log`, `218_forbidden_vocab_after_live_orchestration.log` | Source-truth mirror is synced; forbidden-vocabulary guard and diff whitespace checks passed. |
| Project-local skill inventory | PASS | `55_skill_inventory.tsv`, `56_skill_usage_ledger.md`, `57_hybrid_prompts_headers.log`, `60_guru_shishya_next_wave_protocol.md` | 86 `.claude` skills and 50 `.agents` skills were inventoried and classified. The next-wave protocol binds unresolved blockers to applicable skills instead of pretending every skill is relevant to every gate. |
| Agent workflow hygiene | PASS | `05_existing_diff_start.patch`, `../00_current_state.md` | Duplicate untracked skill imports were removed; root `AGENTS.md` is now a short execution entry point. |
| Backend/API contracts | PASS | `22_backend_security_query_suite_after_stream_fix.log` | 195 passed, 1 skipped, 7 deselected. |
| Query intelligence and answer contract | PASS | `22_backend_security_query_suite_after_stream_fix.log`, `18_stream_wiring_regression.log`, `killer/` | Messy query, stream payload, citation, audit ID, tier response, and contract slices passed. |
| Dhairya SQL regression | PASS | `10_dhairya_sql_regression.log` | 57 passed, 31 deselected. |
| Database/schema truth | PASS | `06_corpus_sync.log`, `24_live_health.json` | Corpus/schema mirrors match; local DB is healthy with 76 tables, 5,615 researchers, and 100,000 publications. |
| Retrieval/RAG live dependency | PASS | `64_live_health_all_after_services.json`, `65_live_health_qdrant_after_services.json`, `66_live_vectors_health_after_services.json`, `68_qdrant_redis_local_health_report.md`, `69_post_service_verification.log`, `72_colima_docker_ps.log`, `74_colima_stack_health_all.json` | Local Qdrant and Redis were started through Colima/Compose. `/health/all` is healthy; Qdrant has collection `nrg_research`; vector health reports 1,800 vectors, dimension 1024, COSINE distance, and green index status. Final persistence was verified inside Colima because host Docker socket/port forwarding was inconsistent. |
| Security, PII, injection, tier safety | PASS | `22_backend_security_query_suite_after_stream_fix.log`, `32_live_api_query_matrix.json`, `33_live_api_government_corrected.json`, `52_live_tier_isolation_redteam_retry_all.log`, `202_live_api_supply_chain_recheck/`, `full_suite_live_orchestration5/test_suite_live_api.xml` | Broad local suite passed; live tier isolation plus red-team retry-all now passes in the managed runner with 36 passed. RT-20/RT-21 accept the production blocked answer-engine envelope and direct TestClient regressions cover file-access and dependency-confusion prompts. |
| Audit/HMAC chain | PASS | `44_audit_rebuild_check_before.log`, `45_audit_rebuild_repair.log`, `46_audit_verify_after_rebuild.log`, `53_audit_verify_final_after_live_redteam.log`, `209_audit_chain_check_before_final_repair.log`, `210_audit_chain_rebuild_preserve_lineage_final.log`, `211_audit_chain_check_after_final_repair.log`, `219_audit_chain_check_after_report_updates.log` | Per-user binding check found historical tail failures after broad/live runs, including 92 failures before the final repair. Rebuilds preserved lineage; the latest check reports `RESULT: Chain is VALID` with 282,701 events. ADR-006 lineage caveat still applies. |
| Frontend unit/UI contract | PASS | `28_frontend_jest_after_install.log`, `29_frontend_build_after_install.log` | 99 frontend tests passed; production build passed. |
| Live browser main query flow | PASS | `live_quantum_recheck/` | Desktop/mobile screenshots, video, citation drawer, source-data drawer, audit-proof drawer, console-error capture, raw Researcher JSON, and Tier 3 blocked JSON were captured for the messy quantum researcher flow. |
| Accessibility | PASS | `30_frontend_contrast_after_install.log`, `36_frontend_playwright_a11y.log` | 20 contrast tests passed; 9 Playwright axe/keyboard/reduced-motion checks passed. |
| Frontend lint | PASS | `187_frontend_lint_after_lint_cleanup.log` | Lint exits 0 with 0 warnings after the TypeScript ESLint upgrade cleanup. |
| Dependency audit | PASS high-severity gate | `169_frontend_npm_audit_current.json`, `170_frontend_npm_outdated_current.json`, `171_frontend_dependency_audit_summary.md`, `189_frontend_npm_audit_high_final_after_lint_cleanup.json`, `190_frontend_dependency_tree_after_lint_cleanup.log` | `npm audit --audit-level=high --json` now exits 0 after dev-tooling upgrades. Remaining findings are 0 critical, 0 high, 25 moderate, and 6 low; do not claim full dependency cleanliness until those are remediated or risk-accepted. |
| Full Python suite | PASS managed live orchestration | `204_full_suite_live_orchestration_summary.md`, `208_run_test_suite_live_api_key_store_fix.log`, `full_suite_live_orchestration5/test_suite_full_final.xml`, `full_suite_live_orchestration5/test_suite_live_api.xml`, `217_no_leftover_port_8000_after_final_runner.log`, `211_audit_chain_check_after_final_repair.log`, `220_live_tests_skip_without_api_final.log` | `scripts/run_test_suite.sh --live-api` now separates non-live and live API files. Latest current-code run: non-live JUnit 1,830 tests, 0 failures, 0 errors, 56 skipped; live API JUnit 36 tests, 0 failures, 0 errors, 0 skipped; runtime budget passed in 33.0s. Raw `pytest tests/` skips live API files when no API is reachable. |
| Live local health | PASS | `64_live_health_all_after_services.json`, `65_live_health_qdrant_after_services.json`, `66_live_vectors_health_after_services.json`, `69_post_service_verification.log`, `74_colima_stack_health_all.json` | `/health/all`, `/health/qdrant`, and `/api/vectors/health` passed after local Qdrant/Redis service startup. Local LLM remains optional unavailable and does not make health fail. Final host `lsof` showed no host uvicorn listener on port 8000; Colima-side stack health is also healthy. |
| C4 performance/load | PASS local quota-neutral capacity | `c4_rerun/163_c4_prewarm_4workers_bounded_audit_executor.json`, `c4_rerun/165_quality_bar_scorecard_60s_4workers_bounded_audit_executor.json`, `c4_rerun/166_locust_report_60s_4workers_bounded_audit_executor.html`, `c4_rerun/167_bounded_audit_executor_c4_pass_summary.md` | The bounded audit append executor moved request-path audit writes out of the general API blocking pool while preserving synchronous chain-hash return. Latest strict scorecard reports Quality Bar `6/6`, C4 PASS, 1000 users, 4 Locust processes, 82,365 samples, 0 failures, aggregate P99 79 ms, researcher P99 64 ms, government P99 80 ms, and adversarial P99 170 ms. This used `NRG_QUOTA_DISABLED=1`, so it is local capacity evidence, not quota-policy or deployed-cluster proof. |
| Evidence discipline | PASS | `00_guru_assignment_protocol.md`, this file | All major claims are mapped to evidence files. |
| External production gates | BLOCKED | `../final_external_gates/EXTERNAL_GATE_SUMMARY.md` | Missing deployed frontend/API URLs, production Qdrant target, explicit cluster-load flag, and founder GPG signatures. |

## Fixes Preserved In This Wave

- Extracted query response support helpers from `src/api/main.py` into
  `src/api/query_response_utils.py`.
- Fixed extracted logging to match `StructuredLogger` call shape.
- Fixed query stream router wiring to pass keyword-only arguments correctly.
- Added root `AGENTS.md` as a concise agent entry point and ignored local
  `.codex/` / `.npm-cache/` artifacts.
- Repaired the active audit chain with `scripts/audit_rebuild.py --rebuild --preserve-lineage`
  after per-user binding verification failed; final `verify_chain()` is valid.
- Added managed full-suite live orchestration in `scripts/run_test_suite.sh`
  and live-test skip/readiness guards in `tests/conftest.py`.
- Isolated managed-suite audit writes under the evidence directory and bound
  per-user salt storage to the active audit path so xdist workers do not mutate
  or poison the active `.audit` chain.
- Preserved live red-team coverage while aligning RT-20/RT-21 with the
  production blocked answer-engine envelope contract.

## Do Not Claim Yet

- Do not claim full production readiness.
- Do not claim deployed/cluster C4 compliance until replayed in that environment.
- Do not claim deployed RAG is fully operational until the production Qdrant
  baseline is rerun against the deployed target.
- Do not claim dependency security is fully clean until remaining low/moderate
  findings are remediated or formally risk-accepted.
- Do not claim deployed-browser or production-cluster proof until external
  gates are rerun with the required target URLs, Qdrant, cluster context, and
  founder signing key.

## Next Engineering Target

Close remaining non-C4 gates:

1. Rerun C4 in the sovereign cluster with the same strict scorecard and explicit
   quota mode.
2. Remediate or risk-accept the remaining low/moderate frontend dependency
   audit findings.
3. Rerun external gates with deployed URLs, production Qdrant target, cluster
   context, and founder signing key.

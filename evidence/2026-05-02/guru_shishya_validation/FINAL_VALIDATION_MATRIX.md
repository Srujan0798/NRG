# Guru/Shishya Validation Matrix

Date: 2026-05-02
Base commit: `cc55d80a8baf932da8ecf8b2f27b1c23c2d0ab92`

This report is an evidence matrix for the current local checkout. It is not a
production-readiness certificate.

## Verdict

| Surface | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Repo hygiene and source truth | PASS | `01_git_status_start.log`, `06_corpus_sync.log`, `07_forbidden_vocab.log` | Source-truth mirror is synced; forbidden-vocabulary guard passed. |
| Project-local skill inventory | PASS | `55_skill_inventory.tsv`, `56_skill_usage_ledger.md`, `57_hybrid_prompts_headers.log`, `60_guru_shishya_next_wave_protocol.md` | 86 `.claude` skills and 50 `.agents` skills were inventoried and classified. The next-wave protocol binds unresolved blockers to applicable skills instead of pretending every skill is relevant to every gate. |
| Agent workflow hygiene | PASS | `05_existing_diff_start.patch`, `../00_current_state.md` | Duplicate untracked skill imports were removed; root `AGENTS.md` is now a short execution entry point. |
| Backend/API contracts | PASS | `22_backend_security_query_suite_after_stream_fix.log` | 195 passed, 1 skipped, 7 deselected. |
| Query intelligence and answer contract | PASS | `22_backend_security_query_suite_after_stream_fix.log`, `18_stream_wiring_regression.log`, `killer/` | Messy query, stream payload, citation, audit ID, tier response, and contract slices passed. |
| Dhairya SQL regression | PASS | `10_dhairya_sql_regression.log` | 57 passed, 31 deselected. |
| Database/schema truth | PASS | `06_corpus_sync.log`, `24_live_health.json` | Corpus/schema mirrors match; local DB is healthy with 76 tables, 5,615 researchers, and 100,000 publications. |
| Retrieval/RAG live dependency | PASS | `64_live_health_all_after_services.json`, `65_live_health_qdrant_after_services.json`, `66_live_vectors_health_after_services.json`, `68_qdrant_redis_local_health_report.md`, `69_post_service_verification.log`, `72_colima_docker_ps.log`, `74_colima_stack_health_all.json` | Local Qdrant and Redis were started through Colima/Compose. `/health/all` is healthy; Qdrant has collection `nrg_research`; vector health reports 1,800 vectors, dimension 1024, COSINE distance, and green index status. Final persistence was verified inside Colima because host Docker socket/port forwarding was inconsistent. |
| Security, PII, injection, tier safety | PASS | `22_backend_security_query_suite_after_stream_fix.log`, `32_live_api_query_matrix.json`, `33_live_api_government_corrected.json`, `52_live_tier_isolation_redteam_retry_all.log` | Broad local suite passed; live tier isolation plus red-team retry-all passed: 35 passed, 1 skipped. |
| Audit/HMAC chain | PASS | `44_audit_rebuild_check_before.log`, `45_audit_rebuild_repair.log`, `46_audit_verify_after_rebuild.log`, `53_audit_verify_final_after_live_redteam.log` | Per-user binding check found 367 failures after broad runs. Rebuild archived `.audit/chain_corrupted_backup_20260501T215637Z.jsonl`, rebuilt 55,141 events, logged a rebuild event, and final verification reports valid chain, 55,212 events, 0 errors. |
| Frontend unit/UI contract | PASS | `28_frontend_jest_after_install.log`, `29_frontend_build_after_install.log` | 99 frontend tests passed; production build passed. |
| Live browser main query flow | PASS | `live_quantum_recheck/` | Desktop/mobile screenshots, video, citation drawer, source-data drawer, audit-proof drawer, console-error capture, raw Researcher JSON, and Tier 3 blocked JSON were captured for the messy quantum researcher flow. |
| Accessibility | PASS | `30_frontend_contrast_after_install.log`, `36_frontend_playwright_a11y.log` | 20 contrast tests passed; 9 Playwright axe/keyboard/reduced-motion checks passed. |
| Frontend lint | PASS | `187_frontend_lint_after_lint_cleanup.log` | Lint exits 0 with 0 warnings after the TypeScript ESLint upgrade cleanup. |
| Dependency audit | PASS high-severity gate | `169_frontend_npm_audit_current.json`, `170_frontend_npm_outdated_current.json`, `171_frontend_dependency_audit_summary.md`, `189_frontend_npm_audit_high_final_after_lint_cleanup.json`, `190_frontend_dependency_tree_after_lint_cleanup.log` | `npm audit --audit-level=high --json` now exits 0 after dev-tooling upgrades. Remaining findings are 0 critical, 0 high, 25 moderate, and 6 low; do not claim full dependency cleanliness until those are remediated or risk-accepted. |
| Full Python suite | FAIL | `38_full_pytest_tests_ignore_scripts.log`, `47_isolated_health_contracts_after_audit_rebuild.log`, `52_live_tier_isolation_redteam_retry_all.log` | Broad command produced 1,679 passed, 56 skipped, 26 failed, 6 errors. Most live failures were API-not-running errors; isolated health tests passed after audit rebuild and live tier/red-team passed after starting the API. The single broad command is still not green. |
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

## Do Not Claim Yet

- Do not claim full production readiness.
- Do not claim deployed/cluster C4 compliance until replayed in that environment.
- Do not claim deployed RAG is fully operational until the production Qdrant
  baseline is rerun against the deployed target.
- Do not claim dependency security is fully clean until remaining low/moderate
  findings are remediated or formally risk-accepted.
- Do not claim the full Python suite is green until the single broad command
  passes without needing manual API reruns.
- Do not claim deployed-browser or production-cluster proof until external
  gates are rerun with the required target URLs, Qdrant, cluster context, and
  founder signing key.

## Next Engineering Target

Close remaining non-C4 gates:

1. Rerun C4 in the sovereign cluster with the same strict scorecard and explicit
   quota mode.
2. Remediate or risk-accept the remaining low/moderate frontend dependency
   audit findings.
3. Turn the full Python suite into a single green orchestration command, with
   live-test prerequisites handled explicitly.
4. Rerun external gates with deployed URLs, production Qdrant target, cluster
   context, and founder signing key.

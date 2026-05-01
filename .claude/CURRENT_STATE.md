# NRG — Current Sprint State
> **Update this file at the end of every session.** Agents read this instead of BACKLOG.md for current priorities.
> Last updated: 2026-05-02

---

## System Status

| Item | State |
|------|-------|
| Repo structure | Cleaned and pruned; tracked dead docs/components/scripts removed in `516991a`, tracked test-run metadata removed in `6d0ac3a` |
| Working tree | Expected clean after the latest validation campaign commit; run `git status --short` before editing because agents may create local artifacts. |
| Operating flow | Central Guru/Shishya rule hierarchy now lives at `docs/specs/NRG_EXECUTION_FLOW_RULE_HIERARCHY_2026-05-02.md`; use it after the source-truth map and before starting broad work. |
| Quality Bar | **Not certified** — May 2 local C4 1000-user scorecard now runs the corrected C4 Locust file with preissued tokens and zero request failures, but still fails the P99 target; combined envelope and declared-prewarm diagnostics point to request lifecycle/queueing under 1000 users as the next boundary; external gates remain blocked. |
| Full test suite | May 2 broad command selected 1,767 tests: 1,679 passed, 56 skipped, 26 failed, 6 errors. Most failures were live-test files run without a live API; isolated health passed after audit rebuild and live tier/red-team passed after starting API. The single broad command is still not green. |
| Targeted recent checks | May 1 local validation campaign passed broad backend/security/audit/query/RAG tests, killer-query capture, frontend Jest, frontend production build, corpus sync, diff hygiene, and forbidden-vocab guard. May 1 local health closure repaired stale Qdrant vectors/payload metadata, established a local vector baseline, and proved `/health`, `/health/all`, and `/api/vectors/health` green on the local stack. May 1 post data-quality validation passed 74 selected backend/Dhairya/GLM/Minimax tests, frontend build, corpus sync, Docker API rebuild, healthy `/health`, and a 10-case live `/query` matrix across Researcher/Government/Industry. May 1 local warning closure passed 78 selected backend tests, frontend build, corpus sync, Docker API rebuild, healthy `/health`, healthy `/health/all`, and an 8-case live `/query` matrix with audit IDs and persisted answer records. May 1 quantum data mount closure passed 46 selected backend/compose/GLM/Minimax tests, frontend build, corpus sync, healthy `/health`, healthy `/health/all`, and an 8-case live `/query` matrix where `best quantum researchers....` returned 5 cited ranked rows from `/app/data/nrg_research.db` and Tier 3 remained anonymized. May 2 repo wrap-up passed py_compile for API/routes, diff hygiene, corpus sync, forbidden-vocab guard, 41 selected API/security/query tests, and frontend production build after local npm dependency install. May 2 Guru/Shishya validation passed backend/security/query slice (195 passed, 1 skipped), Dhairya SQL regression (57 passed), frontend Jest (99 passed), frontend build, contrast tests, Playwright live quantum proof, Playwright axe/keyboard checks (9 passed), live tier/red-team retry-all (35 passed, 1 skipped), corpus sync, final audit verification, 136 local skill inventory classification, C4 scorecard report-parent regression, local Qdrant/Redis health restoration through `/health/all`, `/health/qdrant`, and `/api/vectors/health`, and a C4 rerun that fixed JWT replay failures but still failed P99. Follow-up C4 profiling passed 15 targeted scorecard/Locust contract tests, captured 7,179 sampled query-stage records, captured combined request-envelope evidence, and ran a declared C4 prewarm diagnostic with 312/312 successful prewarm requests; the warmed no-profile scorecard still failed C4 with 45,559 samples, 0 failures, aggregate P99 2100 ms. |
| Audit chain | May 2 per-user binding verification found 367 failures after broad validation. `scripts/audit_rebuild.py --rebuild --preserve-lineage` archived `.audit/chain_corrupted_backup_20260501T215637Z.jsonl`, rebuilt 55,141 events, appended a rebuild event, and final verification reports `valid=True`, `count=55212`, `errors=0`. |
| Baseline commit before Wave 0 | `6d0ac3a` — drop tracked test run metadata |
| Latest committed wave | Use `git log -1 --oneline` for the exact current commit. Recent anchors: `fb44760` compact Desktop AI handoff package, `2c23c9f` Dhairya query benchmark routing, `e361d4c` source-truth/corpus restoration. |
| Git tag | `v1.0.0-launch-ready` (unsigned — pending GPG ceremony) |

---

## Open Items (dispatch-ready)

| ID | Task | Assigned? | Blocker |
|----|------|-----------|---------|
| W0 | State lock and evidence commit | Done | Committed `ff975b6` |
| W1 | Backend answer-engine hardening for messy queries | Done | Committed `659ded4` |
| W2 | Frontend main-flow polish and contract adapter verification | Done | Mocked browser gate passed; live local backend browser proof passed on 2026-04-30 |
| W3 | Security, tier, and audit proof | Local gate passed | Blocked query audit IDs fixed; blocked envelopes now preserve authenticated tier |
| W4 | SQL/RAG retrieval truth and regression coverage | Done locally | Committed in current Wave 4 commit; live Qdrant/PostgreSQL proof remains environment-dependent |
| W5 | C4 concurrent query/load performance closure | Current 1000-user gate failed | Historical 100-user read-model + single-flight pass remains useful, but current 1000-user scorecard evidence fails P99. Latest combined profile shows route-handler P99 1.589ms, server envelope P99 538.303ms, and client-observed P99 1000ms; declared prewarm still failed at aggregate P99 2100ms. |
| W6 | Final handover package | Done | Show-readiness report and final evidence index committed |
| K-6 | GPG signatures for handover | FOUNDER ONLY | Founder private key |

---

## Quality Bar

| C1 DPDP PII | C2 Audit | C3 Multi-hop | C4 SLO | C5 Drift | C6 Egress |
|:-----------:|:--------:|:------------:|:------:|:--------:|:---------:|
| ✅ | ✅ | ✅ | ❌ current 1000-user local / cluster pending | ✅ local / production pending | ✅ |

**C4 is not closed for the current 1000-user bar.** The historical 100-user read-model/single-flight pass remains useful, but the May 2 corrected scorecard attempted 1000 users and failed the P99 target. Runner issues are now fixed: the scorecard creates the Locust HTML report parent, uses `tests/load/locustfile_c4.py`, preissues tokens, rejects non-numeric P99 evidence, no longer triggers token replay failures, fails HTTP 429, and reads real Locust `window.templateArgs` report metrics. Audit append now avoids repeated same-process JSONL tail rereads and reduces work inside the file-lock critical section; audit/per-user/cosign safety tests still passed. Fresh post-change evidence shows zero request failures but aggregate P99 still above target, so do not claim C4 compliance until the measured 1000-user P99 target passes.

Final May 2 focused verification after the C4 runner and consent hot-path changes passed: 30 targeted scorecard/Locust/consent tests, compileall, diff whitespace check, corpus sync, forbidden-vocabulary guard, and no leftover scorecard/Locust/uvicorn processes. Evidence: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/43_final_local_verification.md`.

Follow-up C4 truth-contract verification passed after tightening the runner further: HTTP 429 now fails load evidence, `/query` metrics are split by researcher/government/adversarial workload, and the scorecard exports per-workload failures/P99 from Locust HTML. A 4-worker 60-second diagnostic reparse shows 37,174 samples, 0 failures, aggregate P99 3100 ms, researcher P99 2700 ms, government P99 3000 ms, adversarial P99 6400 ms. The API now also has opt-in request-envelope profiling through `NRG_REQUEST_ENVELOPE_PROFILE` for the next C4 run. Evidence: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/44_c4_truth_contract_after_429_endpoint_metrics.md`, `evidence/2026-05-02/guru_shishya_validation/c4_rerun/58_request_envelope_profiler.md`.

C4 mode boundary is now explicit: quota-on C4 needs distinct load identities; quota-neutral C4 must document `NRG_QUOTA_DISABLED=1` and is capacity-only evidence. Evidence: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/75_rate_limit_and_quota_mode_boundary.md`.

Latest C4 profiling shows the remaining boundary more clearly. Combined query-stage plus request-envelope evidence reports Locust aggregate P99 1000 ms, server `/query` envelope P99 538.303 ms, and sampled route-handler P99 1.589 ms in the same diagnostic window. A declared prewarm/no-profile diagnostic then warmed 312 declared workload requests with 0 failures and reran the 1000-user scorecard; it still failed with 45,559 samples, 0 failures, aggregate P99 2100 ms, researcher P99 2100 ms, government P99 2100 ms, and adversarial P99 2400 ms. Evidence: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/86_combined_query_envelope_profile_summary.md`, `evidence/2026-05-02/guru_shishya_validation/c4_rerun/93_declared_prewarm_no_profile_summary.md`.

**Main product risk now:** local query/UI/security/service proof is strong, but external production claims still need deployed-environment replay, a passing 1000-user load run, production Qdrant/Redis health, founder signing, dependency-audit closure, and data completion for currently empty official core tables.

---

## Cluster-Blocked (do not re-do locally)

- Live red-team replay (`scripts/red_team_live_replay.py`) — needs target API/deployment context
- Qdrant vector baseline — local Qdrant now has 1800 repaired non-zero vectors with Tier 3 metadata and a green local drift baseline; production corpus baseline still needs target deployment context
- Locust 1000-user load test — needs sovereign cluster
- UX deployed browser recording + mobile Lighthouse — needs target deployment context
- GPG key ceremony + `v1.0.0-eternal` signed tag — founder-only

## Recent State-Lock Evidence

| Evidence | Status |
|----------|--------|
| `evidence/2026-04-29/p0_backend_security_and_query_closure.md` | Preserved; contains P0 security/query closure commands and results |
| `evidence/2026-04-30/00_current_state.md` | Current state lock for the next agent wave |
| `659ded4` | Latest committed backend messy-query routing and stable response-contract fix |
| `evidence/2026-04-30/wave2_frontend_main_flow_build.md` | Frontend build, mocked browser main-flow, audit/citation proof, tier comparison, and screenshot evidence |
| `evidence/2026-04-30/wave3_security_tier_audit_acceptance.md` | Security, tier, and audit proof with raw tier JSON, blocked-query evidence, and audit-chain verification |
| `evidence/2026-04-30/wave3_blocked_query_responses.json` | Raw blocked-query TestClient JSON summary with audit IDs |
| `evidence/2026-04-30/09_tier1_query_response.json` | Raw Tier 1 query response evidence |
| `evidence/2026-04-30/10_tier2_query_response.json` | Raw Tier 2 query response evidence |
| `evidence/2026-04-30/11_tier3_query_response.json` | Raw Tier 3 query response evidence |
| `fb44760` | Compact nine-file Desktop AI handoff package evidence update |
| `57f40b1` | Desktop AI handoff package note and current-state cleanup |
| `2c23c9f` | Dhairya query benchmark routing closure |
| `e361d4c` | Source-truth map and Dhairya corpus restoration |
| `evidence/2026-04-30/wave5_performance_load_acceptance.md` | Performance report with before/after local 100-query profile, load tests, and C4 blocker |
| `evidence/2026-04-30/wave5_local_100_query_profile_after.json` | Final local 100-query profile: P99 2094.72ms, 100/100 success, audit IDs present |
| `evidence/2026-04-30/live_c4_local_smoke/README.md` | Historical pre-read-model local 100-user Locust smoke: 3602 requests, 0 failures, `/query` P99 2700ms, superseded by final read-model run. |
| `docs/handover/SHOW_READINESS_2026-04-30.md` | Current 90-second walkthrough, evidence map, and honest blocker list |
| `evidence/2026-04-30/FINAL_EVIDENCE_INDEX.md` | Final evidence index for current handover package |
| `evidence/2026-04-30/desktop_ai_handoff_folder.md` | Flat nine-file Desktop AI handoff package verification |
| `evidence/2026-04-30/live_full_stack_proof/README.md` | Live local full-stack proof: login, messy query, streaming answer, citation/source/audit drawers, mobile screenshot, Tier 3 blocked JSON |
| `evidence/2026-04-30/live_quantum_query_recheck/README.md` | Fresh recheck that `best quantum researchers....` returns quantum-specific SQL evidence, citations, source/audit drawers, mobile screenshot, and Tier 3 blocked JSON |
| `evidence/2026-04-30/c4_hot_path_hardening_summary.md` | Historical hot-path summary, superseded by the read-model/single-flight closure evidence. |
| `evidence/2026-04-30/live_c4_local_smoke_after_worker_pool/locust_output.txt` | Historical pre-read-model run: 0 failures, `/query` P99 about 7.4s, aggregate P99 about 6.4s. |
| `evidence/2026-04-30/c4_read_model_singleflight_closure.md` | Read-model/single-flight closure summary with tests, audit-chain health, and load evidence. |
| `evidence/2026-04-30/live_c4_local_smoke_after_read_model_final/locust_output.txt` | Final passing local 100-user C4 smoke: 8522 requests, 0 failures, aggregate P99 313.2ms, `/query` P99 170ms. |
| `evidence/2026-04-30/prompts_hybrid_freshness_pass.md` | Prompt-stone freshness pass aligning agent instructions with local C4 pass, cluster blocker, evidence-backed release query, and final-report gates. |
| `evidence/2026-04-30/validation_campaign_stone_integration.md` | Integration note for new `prompts_hybrid/08_full_coverage_validation_campaign_stone.md` plus `.agents`/`.claude` skill wrappers, distilling broad validation strategy into NRG-safe campaign modes and evidence matrices. |
| `evidence/2026-04-30/validation_campaign_calibration/VALIDATION_CAMPAIGN_REPORT.md` | First calibration run using the validation campaign workflow: targeted backend tests passed, API/tier/security calibration passed, frontend build passed, live browser proof passed after changing login health polling to `/health/db`; slow RAG/root-health paths remain documented findings. |
| `evidence/2026-05-01/00_current_state.md` | May 1 state lock before external input fusion pass 3; records clean starting tree, source-truth files read, corpus sync, and current blockers. |
| `evidence/2026-05-01/minimax_fusion_pass3_query_validation.md` | External input fusion pass 3: converted generic app-builder/UI/prompt-pack value into NRG-native query, workflow, security, UI, and performance validation material. |
| `evidence/2026-05-01/external_fusion_validation_matrix.csv` | Thirty-seven-row seed matrix for future validation campaigns covering queries, tiers, workflows, UI states, security probes, and performance boundaries. |
| `evidence/2026-05-01/minimax_fusion_final_inventory_review.md` | Final external inventory review: all 84 files under the external bundle accounted for; 57 reviewable text files covered by earlier evidence or final pass, 27 generated/binary/local artifacts ignored. |
| `evidence/2026-05-01/fusion_completion_claim_boundary.md` | Founder correction encoded: external inventory/value integration is not whole-product proof; restored missing validation-campaign skill wrappers, added product-proof claim gates, and fixed top-level API `verification_status` normalization after contract tests exposed the mismatch. |
| `evidence/2026-05-01/validation_campaign/VALIDATION_CAMPAIGN_REPORT.md` | May 1 validation-and-fix report: broad backend suite `195 passed, 1 skipped`, frontend Jest `97 passed`, frontend build passed, killer-query health passed, corpus sync passed, diff hygiene passed, forbidden-vocab guard passed. |
| `evidence/2026-05-01/validation_campaign_backend_tests.log` | Broad backend/security/audit/query/RAG validation log after blocked-envelope and citation-contract fixes. |
| `evidence/2026-05-01/validation_campaign_frontend_jest.log` | Frontend unit/a11y/contract/design-system test log: 26 suites, 97 tests passed. |
| `evidence/2026-05-01/validation_campaign_frontend_build.log` | Frontend production build log. |
| `evidence/2026-05-01/validation_campaign/killer/` | Killer-query response, health, and explain evidence for KILLER-01 through KILLER-03. |
| `evidence/2026-05-01/final_external_gates/EXTERNAL_GATE_SUMMARY.md` | May 1 external final-gates run: deployed browser replay, production Qdrant baseline, 1000-user cluster load, and founder GPG signing remain blocked by missing deployment URLs/KUBECONFIG/founder key on this machine; runner and runbook now exist. |
| `scripts/run_final_external_gates.py` | Repeatable external-gate runner for deployed browser proof, production Qdrant health, explicit cluster C4 load, and founder signing verification. |
| `docs/handover/EXTERNAL_FINAL_GATES_RUNBOOK.md` | Operator runbook for closing the remaining external gates on the production/cluster/founder-signing machine. |
| `evidence/2026-05-01/founder_zero_partial_workflow_update.md` | Founder correction encoded permanently: future v1.0 fusion/superiority requests must use a proof matrix across appearance, UI/UX, query intelligence, DB/schema, Dhairya audit, backend/API, retrieval, security/tier, audit, accessibility, performance, evidence, and production. |
| `evidence/2026-05-01/minimax_fusion_final_proof/FINAL_VALIDATION_REPORT.md` | Repeated Minimax fusion proof: broad local backend/security/query/RAG/audit slice passed, killer queries healthy, frontend Jest/build passed, live browser quantum flow passed against current local backend on `API_TARGET=127.0.0.1:8017`; external production gates remain BLOCKED. Do not trust a random listener on port 8000 for browser proof. |
| `evidence/2026-05-01/minimax_fusion_last_pass/FINAL_LAST_PASS_REPORT.md` | Final last-pass Minimax v1.0 fusion: converted the remaining external sample-query value into NRG regression tests, added deterministic TRL stage distribution routing, distinct state-wise research-output routing, and tighter Tier 3 identifier filtering. Verified with 198-pass backend/security/query/audit slice, 99-pass frontend Jest run, frontend build, and corpus sync. Production/deployed gates remain BLOCKED. |
| `evidence/2026-05-01/glm_fusion_pass/FINAL_GLM_FUSION_REPORT.md` | GLM v1.0 fusion pass: rejected direct Next.js/Prisma/SQLite replacement, converted GLM query templates into NRG regression tests, added C4 routes for hydrogen catalysis, state comparison, renewable publications, h-index/citation aggregates, IIT AI strength, CSIR labs, and quantum publication-threshold proxy. Verified with 49-pass backend/security slice, 26-pass contract/citation slice, 99-pass frontend Jest run, frontend build, corpus sync, and 15 raw tier JSON samples. Production/deployed gates remain BLOCKED. |
| `evidence/2026-05-01/glm_fusion_second_pass/FINAL_GLM_SECOND_PASS_REPORT.md` | GLM external bundle second pass: inventoried 598 external files, converted the remaining visible query-chip value into NRG hero/persona suggestions, removed one unrouted suggestion, and proved 12 visible chips through live `/query` across Researcher, Government, and Industry with citations, source rows, and audit IDs. Verified with 10 GLM/Minimax backend tests, 22 security/HMAC tests, 99 frontend Jest tests, frontend build, corpus sync, ruff, and diff hygiene. Production/deployed gates remain BLOCKED. |
| `evidence/2026-05-01/glm_fusion_browser_proof/FINAL_GLM_BROWSER_PROOF_REPORT.md` | GLM visible-query browser proof: added a live Playwright flow for the hydrogen-catalysis suggestion through the production frontend build and local FastAPI backend. Captured desktop/mobile screenshots, source drawer, citation drawer, audit/HMAC drawer, raw Researcher JSON, raw Tier 3 blocked JSON, empty console-error capture, video, and backend logs. Corrected an initial test route assumption, reran, and passed `1 passed (16.0s)`. |
| `evidence/2026-05-01/glm_local_completion_gates/FINAL_LOCAL_COMPLETION_GATES_REPORT.md` | Local completion-gate pass for the GLM visible-query path: fixed success-token contrast, SQL proof focusability, audit drawer definition-list semantics, and Playwright video-save robustness. Verified frontend build, full Jest `99 passed`, live browser flow, live axe a11y flow, 30-request local latency profile, corpus sync, GLM/Minimax query regressions, and audit-chain verification. External deployed/cluster/founder gates remain BLOCKED. |
| `evidence/2026-05-01/local_full_health_closure/` | Local full-health closure pass: fixed Qdrant threshold-exempt health handling, added `scripts/repair_qdrant_payloads.py`, repaired local Qdrant placeholder vectors and missing payload metadata, established the local vector baseline, proved vector drift GREEN, proved `/health`, `/health/all`, `/health/db`, `/health/qdrant`, and `/api/vectors/health` healthy. |
| `evidence/2026-05-01/local_full_health_closure/data_quality_scorecard_postgres.log` | PostgreSQL data-quality scorecard: schema coverage, PII scan, consistency passed; overall remains FAIL because 12 official core tables are empty and optional columns have high null rates. This is an honest data-completion blocker, not a code-health blocker. |
| `evidence/2026-05-01/local_full_health_closure/final_external_gates_after_qdrant_repair.log` | External final-gates runner remains BLOCKED by missing deployed frontend/API URLs, explicit cluster-load flag/KUBECONFIG context, and founder private signing key. |
| `evidence/2026-05-01/post_data_quality_validation/README.md` | May 1 post data-quality validation closure: fixed verifier duplicate-citation retry, C4 funding/state empty-slice crashes, out-of-corpus clarification, and cited no-result researcher lookup. Verified with 74 selected backend/Dhairya/GLM/Minimax tests, frontend build, corpus sync, Docker rebuild, healthy `/health`, healthy `/health/all`, healthy audit chain, and 10-case live `/query` matrix. |
| `evidence/2026-05-01/post_data_quality_validation/live_query_matrix_final_after_no_result_citation_fix.json` | Final live 10-case query matrix: capex, sanctioned/actual, patents/PhD, noisy quantum, state AI comparison, industry tier researcher ranking, government funding aggregate, PII block, injection block, and out-of-corpus clarification all returned HTTP 200 with audit IDs; allowed evidence paths include citations and rows where applicable. |
| `evidence/2026-05-01/local_warning_closure/README.md` | May 1 local runtime warning closure: answer records now persist under writable runtime storage, sparse local researcher fallback adapts to compact schemas, optional local read-model schema misses no longer warn, Docker API rebuild passed, health passed, 8-case live query matrix produced audit IDs, and final log scan has no closed warning/error signatures. |
| `evidence/2026-05-01/local_warning_closure/live_query_matrix.json` | Final 8-case live query matrix for capex, noisy quantum, state AI comparison, government funding, industry tier safety, PII block, injection block, and out-of-corpus clarification. Answer-record store path is `/var/lib/nrg/answer_records.sqlite`; local data still has zero quantum researcher rows, so quantum returns a truthful cited no-result until verified quantum rows are seeded/ingested. |
| `evidence/2026-05-01/quantum_data_mount_closure/README.md` | May 1 local quantum data-path closure: Docker API now mounts `./data` read-only and sets `NRG_LOCAL_RESEARCH_DB=/app/data/nrg_research.db`; live local matrix shows `best quantum researchers....` returning `researcher_ranking`, 5 rows, 2 citations, audit ID, and Tier 3 anonymized researcher labels with no direct email in the answer. Production still needs its own populated DB or equivalent ingestion proof. |
| `evidence/2026-05-01/quantum_data_mount_closure/live_query_matrix.json` | Final post-mount 8-case live query matrix: 717 quantum-matching researcher rows visible in the mounted local corpus; allowed paths carry citations/audit IDs; blocked/clarified paths carry audit IDs. |
| `evidence/2026-05-01/quantum_browser_after_mount/README.md` | May 1 browser-visible quantum proof after mounting the local corpus: fixed the missing authenticated `/audit/event/{event_id}` backend route that caused audit proof drawer 500s, reran Playwright, captured desktop/mobile screenshots plus citation/source/audit drawers, proved `console_errors.json` is empty, and confirmed audit drawer calls return `200 OK`. |
| `evidence/2026-05-02/00_current_state.md` | May 2 wrap-up: duplicate untracked agent skills removed, root `AGENTS.md` made executable-agent safe, query response helpers extracted from `src/api/main.py`, structure plan updated, backend/frontend/static checks recorded. |
| `evidence/2026-05-02/wrapup_backend_targeted_rerun.log` | Backend/API/security query slice after fixing extraction logger bug: 41 passed, 10 deselected. |
| `evidence/2026-05-02/wrapup_frontend_build_rerun2.log` | Frontend production build after local npm cache install: passed. |
| `evidence/2026-05-02/guru_shishya_validation/FINAL_VALIDATION_MATRIX.md` | May 2 Guru/Shishya validation proof matrix: backend/API, Dhairya, frontend build/Jest/a11y, live quantum browser proof, live tier/red-team, and audit rebuild passed; C4, dependency audit, Qdrant/Redis, full-suite single-command, and external gates remain open. |
| `evidence/2026-05-02/guru_shishya_validation/52_live_tier_isolation_redteam_retry_all.log` | Live API tier isolation plus red-team retry-all: 35 passed, 1 skipped. |
| `evidence/2026-05-02/guru_shishya_validation/53_audit_verify_final_after_live_redteam.log` | Final audit chain verification after repair and live red-team: valid=True, count=55212, errors=0. |
| `evidence/2026-05-02/guru_shishya_validation/35_frontend_npm_audit_high.log` | Dependency-audit blocker: 39 vulnerabilities, 10 high severity. |
| `evidence/2026-05-02/guru_shishya_validation/31_c4_scorecard_raw_summary.log` | C4 blocker: 1000-user local scorecard failed P99/failure target. |
| `evidence/2026-05-02/guru_shishya_validation/55_skill_inventory.tsv` | Project-local skills inventory: 86 `.claude` skills and 50 `.agents` skills classified for Guru/Shishya execution. |
| `evidence/2026-05-02/guru_shishya_validation/58_c4_scorecard_cache_regression.log` | Regression proof for the C4 scorecard report-parent fix: `tests/scripts/test_quality_bar_scorecard.py` passed. |
| `evidence/2026-05-02/guru_shishya_validation/60_guru_shishya_next_wave_protocol.md` | Next-wave Guru/Shishya protocol binding C4, dependency audit, Qdrant/Redis, broad test orchestration, and external gates to applicable local skills. |
| `evidence/2026-05-02/guru_shishya_validation/68_qdrant_redis_local_health_report.md` | Local Qdrant/Redis health restoration: Colima started, services healthy, `/health/all` healthy, vector health green with 1,800 vectors; final persistence verified inside Colima because host Docker socket/port forwarding was inconsistent. |
| `evidence/2026-05-02/guru_shishya_validation/c4_rerun/README.md` | C4 follow-up: fixed scorecard runner, preissued tokens, strict numeric P99 parsing, and JWT replay load-test failure storm; fresh 1000-user runs have 0 failures but still miss the P99 target. |
| Current uncommitted work | Expected after May 2 wrap-up until committed: root `AGENTS.md`, `.gitignore`, `src/api/main.py`, `src/api/query_response_utils.py`, docs/current-state/evidence updates. Desktop handoff artifacts live outside the repo under `/Users/srujansai/Desktop/NRG_AI_HANDOFF_2026-04-30`. |
| `d207b54` | Prior backend messy-query fix |
| `516991a` | Verified dead artifact prune |
| `6d0ac3a` | Tracked test-run metadata removal |

---

## Key Files (agent must-reads per task type)

| Task type | Must read |
|-----------|-----------|
| Any task | `BACKLOG.md` (last 50 lines), `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`, `docs/specs/NRG_EXECUTION_FLOW_RULE_HIERARCHY_2026-05-02.md`, `db_struct.sql` header, `Core_Idea_Clean.md` §1-2 |
| SQL/schema | `db_struct.sql` (full), `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` |
| v1.0 build/fusion | `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`, `Core_Idea_Clean.md`, `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`, `db_struct.sql`, `CORPUS/`, `prompts_hybrid/00_INDEX.md`, task stone |
| Security/PII | `src/security/`, `.claude/rules/security.md` |
| API/auth | `src/api/main.py`, `src/auth/` |
| Frontend | `frontend/src/`, `.claude/rules/frontend.md` |
| Evidence | `.claude/rules/audit/protocol.md` §2 |

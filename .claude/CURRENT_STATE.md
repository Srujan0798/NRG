# NRG — Current Sprint State
> **Update this file at the end of every session.** Agents read this instead of BACKLOG.md for current priorities.
> Last updated: 2026-05-01

---

## System Status

| Item | State |
|------|-------|
| Repo structure | Cleaned and pruned; tracked dead docs/components/scripts removed in `516991a`, tracked test-run metadata removed in `6d0ac3a` |
| Working tree | Expected clean after the latest validation campaign commit; run `git status --short` before editing because agents may create local artifacts. |
| Quality Bar | **Not re-certified after cleanup** — last known state was 5/6 with C4 load bar failing |
| Full test suite | Not rerun in this session; use Python 3.11 venv for reliable results |
| Targeted recent checks | May 1 local validation campaign passed broad backend/security/audit/query/RAG tests, killer-query capture, frontend Jest, frontend production build, corpus sync, diff hygiene, and forbidden-vocab guard. |
| Audit chain | Rebuilt after pre-fix concurrent profile, then verified after final C4/test rerun on 2026-04-30: `chain_valid=True`, `chain_length=42085`, `error_count=0` |
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
| W5 | C4 concurrent query/load performance closure | Local 100-user gate passed | Final read-model + single-flight pass produced 8522 requests, 0 failures, aggregate P99 313.2ms and `/query` P99 170ms in `live_c4_local_smoke_after_read_model_final`. Remaining proof is the 1000-user sovereign-cluster run. |
| W6 | Final handover package | Done | Show-readiness report and final evidence index committed |
| K-6 | GPG signatures for handover | FOUNDER ONLY | Founder private key |

---

## Quality Bar

| C1 DPDP PII | C2 Audit | C3 Multi-hop | C4 SLO | C5 Drift | C6 Egress |
|:-----------:|:--------:|:------------:|:------:|:--------:|:---------:|
| ✅ | ✅ | ✅ | ✅ local / cluster pending | ✅ | ✅ |

**C4 local status is now closed for the 100-user smoke target**. The final read-model/single-flight pass returned 8522 requests, 0 failures, aggregate P99 313.2ms, `/query` P99 170ms, and audit-chain health `chain_valid=True`, `error_count=0`. Do not claim final production C4 readiness until the 1000-user sovereign-cluster run passes with production worker/logging settings.

**Main product risk now:** local show-readiness is strong, but external production claims still need the deployed 1000-user Locust run, deployed-environment replay, production Qdrant baseline, and founder signing.

---

## Cluster-Blocked (do not re-do locally)

- Live red-team replay (`scripts/red_team_live_replay.py`) — needs target API/deployment context
- Qdrant vector baseline — local `/health` reports `ready` with 1800 vectors; production corpus baseline still needs target deployment context
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
| Current uncommitted work | None expected after this current-state update is committed. Desktop handoff artifacts live outside the repo under `/Users/srujansai/Desktop/NRG_AI_HANDOFF_2026-04-30`. |
| `d207b54` | Prior backend messy-query fix |
| `516991a` | Verified dead artifact prune |
| `6d0ac3a` | Tracked test-run metadata removal |

---

## Key Files (agent must-reads per task type)

| Task type | Must read |
|-----------|-----------|
| Any task | `BACKLOG.md` (last 50 lines), `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`, `db_struct.sql` header, `Core_Idea_Clean.md` §1-2 |
| SQL/schema | `db_struct.sql` (full), `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` |
| v1.0 build/fusion | `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`, `Core_Idea_Clean.md`, `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`, `db_struct.sql`, `CORPUS/`, `prompts_hybrid/00_INDEX.md`, task stone |
| Security/PII | `src/security/`, `.claude/rules/security.md` |
| API/auth | `src/api/main.py`, `src/auth/` |
| Frontend | `frontend/src/`, `.claude/rules/frontend.md` |
| Evidence | `.claude/rules/audit/protocol.md` §2 |

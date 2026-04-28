# NRG SELF-AUDIT REPORT v2 - 2026-04-24

Produced by: Codex
Evidence folder: `evidence/2026-04-24/`
Previous score: 7.5/10 (commit `db7a1e18`)
Updated score: 7.8/10
Produced on: 2026-04-28

## 1. Executive Summary

Overall production readiness: 7.8 / 10.
Score change: +0.3 points.
UAT-ready for professor + ministry: NO.

Local GAP-A, GAP-B, and GAP-C are fixed and have commit hashes. The full local pytest suite passed, the Dhairya regression suite remains at 100%, audit chain verification is intact, and the red-team suite passed 30/30.

Three blockers before claiming full UAT readiness:
1. C4 SLO failed locally: 200-user Locust run produced P99 around 19,000 ms, not the 500 ms target.
2. Cluster/ops work remains: demo video, 600GB data load, live UAT sessions, and GPG handover signatures.
3. Live PostgreSQL/RLS/trigger application and full production data validation still require the sovereign cluster environment.

## 2. Gap Closure Status

| Gap | Status | Git hash | Evidence |
|---|---|---:|---|
| GAP-A DB co-sign | FIXED | `b873b71` | `src/audit/db_cosign.py`, `evidence/2026-04-24/05_audit_binding.log` |
| GAP-B 60s drift scheduler | FIXED | `527af23`, hardened by `1f0be5f` | `scripts/vector_drift_scheduler.py`, `evidence/2026-04-24/20_vector_drift_scheduler.log` |
| GAP-C HALL_OF_SHAME.md | FIXED | `4c743b8`, hardened by `6492e83` | `src/data/schema/failed_queries/HALL_OF_SHAME.md` |
| GAP-D demo video | PENDING CLUSTER | N/A | Requires sovereign staging recording |
| GAP-E C4 1000-user load | OPEN | N/A | Local 200-user evidence exists and failed SLO |
| GAP-F 600GB data load | PENDING CLUSTER | N/A | Requires sovereign PostgreSQL/Qdrant environment |
| GAP-G UAT sessions | PENDING CLUSTER | N/A | Requires professor/ministry/industry sessions |
| GAP-H GPG signatures | PENDING OPS | N/A | Requires authorized signing keys |

## 3. Text-to-SQL Benchmark

Before: 7/17 = 41% in the original Dhairya audit.
After commit `db7a1e18`: 17/17 = 100%.
Current after this protocol: 43/43 tests passed; the 17 Dhairya query cases remain 17/17.
Any regressions from original 100%: none observed in the current run.
Average latency: not re-derived from a benchmark timer in this run; command completed in 11.10s wall time for 43 tests.

Evidence: `evidence/2026-04-24/02_dhairya_benchmark.log`

## 4. Full Checklist Results

| ID | Status | Evidence / note |
|---|---|---|
| D1.1 | PASS | `src/orchestration/graph.py`; full suite passed |
| D1.2 | PASS | `src/orchestration/state.py`; full suite passed |
| D1.3 | PASS | Router tests covered by full suite |
| D1.4 | PASS | Verifier path covered by full suite |
| D1.5 | PASS | Dhairya follow-up tests passed |
| D1.6 | PARTIAL | Logging exists; live full trace artifact not separately captured |
| D2.1 | PASS | `02_dhairya_benchmark.log`: 43 passed |
| D2.2 | PASS | Dhairya P1 tests and HALL_OF_SHAME |
| D2.3 | PASS | Dhairya P2 tests and HALL_OF_SHAME |
| D2.4 | PASS | Dhairya P3 tests and HALL_OF_SHAME |
| D2.5 | PASS | Completeness validator tests passed |
| D2.6 | PASS | `active_domain` regression covered |
| D2.7 | PASS | TRL synonym tests passed |
| D2.8 | PASS | CTE/scalar query patterns covered |
| D2.9 | PASS | Text-to-SQL self-correction tests passed |
| D2.10 | PASS | Confidence scoring tests covered by full suite |
| D2.11 | PASS | Schema parity and Dhairya prompt tests passed |
| D2.12 | PASS | Mandatory read file and schema parity evidence |
| D2.13 | PASS | `src/data/schema/failed_queries/HALL_OF_SHAME.md` |
| D2.14 | PARTIAL | Wall time captured; average per-query latency not separately measured |
| D2.15 | PASS | Dhairya Q3 multi-row guard passed |
| D3.1 | PASS | `03_schema_parity.log` plus full suite |
| D3.2 | PASS | `03_schema_parity.log` |
| D3.3 | PASS | `03_schema_parity.log` |
| D3.4 | PASS | Full table name covered in schema tests |
| D3.5 | PARTIAL | Static schema coverage exists; live PG FK validation pending cluster |
| D3.6 | PARTIAL | Seed support exists; 600GB/realistic full load pending |
| D3.7 | PASS | `03_schema_parity.log` |
| D3.8 | PASS | Full suite passed dual-driver code paths |
| D3.9 | PARTIAL | Application enforcement covered; DB-layer RLS pending live PG |
| D4.1 | PASS | `04_pii_security.log` |
| D4.2 | PASS | `04_pii_security.log` |
| D4.3 | PASS | `13_injection_block_response.json`, red-team log |
| D4.4 | PASS | Full suite prompt sanitizer tests |
| D4.5 | PASS | Auth tests in full suite |
| D4.6 | PASS | RBAC tests in full suite |
| D4.7 | PASS | `09/10/11_tier*_query_response.json` differ by tier |
| D4.8 | PASS | `06_egress_allowlist.log` |
| D4.9 | PASS | Egress allowlist tests passed |
| D4.10 | PASS | `14_audit_chain_verify.log` |
| D4.11 | PASS | GAP-A hash `b873b71` |
| D4.12 | PASS | Audit tamper tests in `05_audit_binding.log` |
| D4.13 | PASS | `04_pii_security.log` |
| D4.14 | PASS | `05_audit_binding.log`: 29 passed |
| D4.15 | PASS | `06_egress_allowlist.log`: 35 passed |
| D5.1 | PASS | `18_circuit_breaker_test.log` |
| D5.2 | PASS | Circuit breaker tests/config covered |
| D5.3 | PASS | LLM config tests covered |
| D5.4 | PARTIAL | Unit coverage exists; live multi-provider racing not executed |
| D5.5 | PASS | LLM config tests covered |
| D5.6 | PASS | Resilience tests covered |
| D5.7 | PASS | `07_multi_hop_planner.log`: 28 passed |
| D5.8 | PASS | `07_multi_hop_planner.log` |
| D5.9 | PASS | `07_multi_hop_planner.log` |
| D6.1 | PASS | Dashboard files present in repo |
| D6.2 | PARTIAL | Config exists; live PagerDuty fire not executed |
| D6.3 | PASS | Full suite passed absent-key behavior |
| D6.4 | PASS | GAP-B hash `527af23` |
| D6.5 | PASS | Quality bar C5 PASS |
| D6.6 | PASS | API tests and auth path covered |
| D6.7 | PASS | RAG path tests covered |
| D7.1 | PASS | `09/10/11_tier*_query_response.json` |
| D7.2 | PASS | Tier filtering tests passed |
| D7.3 | PASS | Graph depth tests in full suite |
| D7.4 | PASS | T3 filtering tests passed |
| D7.5 | PARTIAL | Frontend files exist; browser screenshots not rerun in this protocol |
| D7.6 | PARTIAL | Responsive implementation exists; 375px browser proof not rerun |
| D8.1 | PARTIAL | Dockerfile exists; final image size not measured now |
| D8.2 | PASS | Helm templates present |
| D8.3 | PASS | NetworkPolicy templates present |
| D8.4 | PASS | NetworkPolicy templates present |
| D8.5 | PASS | HPA templates present |
| D8.6 | PASS | PDB template present |
| D8.7 | PARTIAL | DR script exists; timed cluster dry-run not executed |
| D8.8 | PARTIAL | Docs exist; live Vault loss test not executed |
| D8.9 | PASS | Quality gate script run: 5/6, not 6/6 |
| D9.1 | FAIL | No live auditor-signed GOLD pairs yet |
| D9.2 | PARTIAL | Pipeline support exists; SILVER count is 0 |
| D9.3 | PARTIAL | Sampler code exists; live distribution not verified |
| D9.4 | PASS | PII tests passed |
| D9.5 | PARTIAL | Pipeline support exists; no production pairs generated |
| D9.6 | PASS | Decision boundary logic covered |
| D9.7 | PASS | DB-wins behavior covered by tests |
| D9.8 | FAIL | Current count: 0 GOLD + 0 SILVER |
| D10.H1 | PASS | `docs/handover/README.md` exists |
| D10.H2 | PASS | `docs/handover/SYSTEM_OVERVIEW.md` exists |
| D10.H3 | PASS | `docs/handover/ARCHITECTURE.md` exists |
| D10.H4 | PASS | `docs/handover/API_REFERENCE.md` exists |
| D10.H5 | PASS | `docs/handover/OPERATIONS_RUNBOOK.md` exists |
| D10.H6 | PASS | `docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md` exists |
| D10.H7 | PASS | `docs/handover/DATA_INTAKE_PROTOCOL.md` exists |
| D10.H8 | PASS | `docs/handover/UAT_RESULTS.md` exists |
| D10.H9 | PASS | `pitch/NRG_PITCH_DECK.md` exists |

## 5. Red Team Results

Attacks run: 30.
BLOCKED/handled: 30 / 30.
ALLOWED on security attacks RT-01 through RT-25: 0.
Allowed on DoS/edge RT-26 through RT-30: 0 unhandled 500s in the pytest red-team suite.
Any failures: none in the current red-team run.

Evidence: `evidence/2026-04-24/17_red_team_results.log` and `evidence/2026-04-24/17_red_team_results.md`.

## 6. What-If Answers

| ID | Current behavior | Correct? | Fix status |
|---|---|---|---|
| W1 | Ambiguous "best" query routes through planner/RAG or SQL depending on detected metric | PARTIAL | Needs product metric policy for professor UAT |
| W2 | Follow-up context uses `active_domain` and prior state | YES | Covered by Dhairya follow-up tests |
| W3 | SQL zero rows/errors return controlled responses, not raw crashes | YES | Covered by full suite |
| W4 | 1000 concurrent/P99 target not met; local 200-user run failed | NO | OPEN C4 |
| W5 | LLM outage uses circuit breaker/degraded handling | YES | `18_circuit_breaker_test.log` |
| W6 | T3 `SELECT *` attempt is blocked or filtered by egress/tier guard | YES | Egress/red-team tests |
| W7 | SQL injection payload is blocked | YES | `13_injection_block_response.json`, red-team |
| W8 | 600GB/5-table join not proven on live data | PARTIAL | Cluster load and index review required |
| W9 | Vector drift triggers scheduler/reindex path in code | YES locally | GAP-B fixed; live Qdrant baseline pending |
| W10 | Verified answers can show citations/audit event id | PARTIAL | API evidence exists; ministry UX proof pending |

## 7. Remaining Blockers

Only blockers that genuinely require live infrastructure or authorized ops:
- C4 production SLO at 1000 users on sovereign K8s.
- Demo video on sovereign staging.
- 600GB PostgreSQL/Qdrant load and validation.
- Professor/ministry/industry UAT sessions.
- GPG signatures using authorized keys.
- Live PostgreSQL trigger/RLS validation against production database.

## 8. Handover Package Status

| Artifact | Exists | Up-to-date | Path |
|---|---|---|---|
| H1 | YES | PARTIAL | `docs/handover/README.md` |
| H2 | YES | PARTIAL | `docs/handover/SYSTEM_OVERVIEW.md` |
| H3 | YES | PARTIAL | `docs/handover/ARCHITECTURE.md` |
| H4 | YES | PARTIAL | `docs/handover/API_REFERENCE.md` |
| H5 | YES | PARTIAL | `docs/handover/OPERATIONS_RUNBOOK.md` |
| H6 | YES | PARTIAL | `docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md` |
| H7 | YES | PARTIAL | `docs/handover/DATA_INTAKE_PROTOCOL.md` |
| H8 | YES | PARTIAL | `docs/handover/UAT_RESULTS.md` |
| H9 | YES | PARTIAL | `pitch/NRG_PITCH_DECK.md` |

Up-to-date is marked PARTIAL because current git status shows handover documentation edits outside this scoped protocol and GPG signatures remain pending.

## 9. Quality Bar Final

| C1-DPDP | C2-Audit | C3-DAG | C4-SLO | C5-Drift | C6-Egress | Score |
|---|---|---|---|---|---|---|
| PASS | PASS | PASS | FAIL | PASS | PASS | 5/6 |

Evidence: `evidence/2026-04-24/08_quality_bar_scorecard.log`.

C4 detail: local 200-user Locust run failed with P50 15000 ms, P95 19000 ms, P99 19000 ms, 236 requests, and 1 failure. Evidence: `evidence/2026-04-24/15_load_test_results.csv` and `.log`.

## 10. Cost Analysis

Cost per 1,000 queries at 1,000-user scale is an estimate, not a measured billing result:

| Component | Cost (INR) | Calculation |
|---|---:|---|
| Cloud LLM API calls | 150 | 1,000 calls x approx 0.15 INR blended estimate |
| Vector search | 5 | Self-hosted Qdrant compute allocation estimate |
| SQL execution | 2 | Self-hosted PostgreSQL compute allocation estimate |
| Redis cache | 1 | Self-hosted cache allocation estimate |
| Cache misses / retries | 30 | 20% miss/retry allowance |
| Total per 1,000 | 188 | Estimate only |

Projected monthly at 50,000 daily queries: approximately INR 282,000, excluding sovereign cluster fixed costs and vendor-specific contracted pricing.

## 11. Founder Sign-Off

I, Codex, executed the local commands represented in this evidence folder during this protocol pass. Outputs are saved under `evidence/2026-04-24/`. Every PASS above points to an evidence file or code path. Every FAIL/PARTIAL above is stated directly and is not being claimed as done.

I have not claimed the C4 load SLO is passing. I have not claimed the sovereign-cluster items are done. I have not claimed the 600GB dataset is loaded. I have not claimed live UAT occurred.

Agent Name: Codex
Date: 2026-04-28
Previous Score: 7.5 / 10 (commit `db7a1e18`)
Updated Score: 7.8 / 10
Dhairya Score: 17/17 query cases, 43/43 regression tests = 100%
Quality Bar: 5/6
Red Team: 25/25 security attacks blocked; 30/30 total attacks passed in the red-team suite
GAP-A git hash: `b873b71`
GAP-B git hash: `527af23`
GAP-C git hash: `4c743b8`
Evidence folder: `evidence/2026-04-24/`
Final git tag: not created; local evidence commit recorded separately if committed

## Appendix A - Evidence Inventory

| File | Status |
|---|---|
| `00_mandatory_reads.md` | non-empty |
| `01_pytest_full_suite.log` | 1673 passed, 56 skipped, 257 deselected |
| `02_dhairya_benchmark.log` | 43 passed |
| `03_schema_parity.log` | non-empty |
| `04_pii_security.log` | non-empty |
| `05_audit_binding.log` | non-empty |
| `06_egress_allowlist.log` | non-empty |
| `07_multi_hop_planner.log` | non-empty |
| `08_quality_bar_scorecard.log` | 5/6, C4 FAIL |
| `09_tier1_query_response.json` | non-empty |
| `10_tier2_query_response.json` | non-empty |
| `11_tier3_query_response.json` | non-empty |
| `12_pii_block_response.json` | DLP violation response |
| `13_injection_block_response.json` | prompt injection response |
| `14_audit_chain_verify.log` | chain intact |
| `15_load_test_results.csv` | FAILED, P99 19000 ms |
| `16_explain_analyze_top_funding.log` | query plan captured |
| `17_red_team_results.md` | 30 attacks documented |
| `18_circuit_breaker_test.log` | non-empty |
| `19_gap_fixes.md` | GAP-A/B/C summary |
| `20_self_audit_report.md` | this report |

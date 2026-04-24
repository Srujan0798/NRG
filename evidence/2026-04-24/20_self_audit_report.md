# NRG SELF-AUDIT REPORT v2 — 2026-04-24

Produced by: Codex  
Previous score: 7.5/10 was claimed in the prior report; current evidence does not support that score.

## 1. Executive Summary

Overall production readiness: **6 / 10**.

UAT-ready for professor + ministry: **NO**.

Three blockers before UAT:

1. Full `pytest tests/` is not green; it failed provider/e2e checks and was interrupted after a router benchmark stall.
2. Audit-chain verification is currently broken: `verify_chain()` reports one hash mismatch.
3. C4 load evidence is invalid: the Locust task implementation raises request-context errors before making HTTP calls.

Local GAP-A, GAP-B, and GAP-C were addressed in code and evidence was captured. This report does not sign off the whole system.

## 2. Gap Closure Status

| Gap | Status | Evidence |
|---|---|---|
| GAP-A DB co-sign | FIXED-AND-VERIFIED locally; live Postgres trigger application pending | commit `b873b713`, `src/audit/db_cosign.py`, `alembic/versions/add_audit_cosign_trigger_001.py`, `evidence/2026-04-24/05_audit_binding.log`, `evidence/2026-04-24/19_gap_fixes.md` |
| GAP-B 60s drift scheduler | FIXED-AND-VERIFIED locally; service/cron deployment pending | commit `527af236`, `scripts/vector_drift_scheduler.py`, `tests/observability/test_vector_drift_scheduler.py`, `evidence/2026-04-24/20_vector_drift_scheduler.log` |
| GAP-C Hall of Shame | FIXED-AND-VERIFIED | commit `4c743b84`, `src/data/schema/failed_queries/HALL_OF_SHAME.md` |
| GAP-D demo video | PENDING CLUSTER | sovereign staging required |
| GAP-E 1000-user C4 load test | PENDING CLUSTER; local 200-user proof failed due test harness bug | `evidence/2026-04-24/15_load_test_results.log` |
| GAP-F 600GB data load | PENDING CLUSTER | data intake protocol exists |
| GAP-G UAT sessions | PENDING CLUSTER + participants | UAT templates exist |
| GAP-H GPG signatures | PENDING OPS | key ceremony required |

## 3. Text-to-SQL Benchmark

Before: 7/17 = 41% (Dhairya original audit).  
After commit `db7a1e18`: claimed 17/17 = 100%.  
Current focused regression: **43/43 passing**, covering the 17 original Dhairya queries and related regression guards.

Evidence: `evidence/2026-04-24/02_dhairya_benchmark.log`.

Command result: `.venv/bin/python -m pytest tests/benchmarks/test_dhairya_regression.py -v --tb=short` -> `43 passed in 3.64s`.

Regressions from original 17: none observed in the focused suite.

Average latency: not measured by the focused pytest output; C4 latency remains unresolved.

## 4. Full Checklist Results

| Area | Status | Evidence / Notes |
|---|---|---|
| D1.1 6-node LangGraph | PASS | prior committed code; not revalidated by full green suite because full suite failed |
| D1.2 NRGState 10 fields | PASS | prior committed code; covered indirectly by existing orchestration tests |
| D1.3 intent router classes | PARTIAL | router tests started but full suite stalled in router dataset benchmark |
| D1.4 verifier faithfulness | PARTIAL | code exists; e2e synthesis/provider tests fail |
| D1.5 active_domain follow-up context | PASS in Dhairya focused suite | `02_dhairya_benchmark.log` |
| D1.6 function-level pipeline trace | PARTIAL | live `/query` worked; not full trace-verified |
| D2.1 Dhairya 17/17 | PASS | `43 passed`, `02_dhairya_benchmark.log` |
| D2.2 SPLIT_PART total_credit_score | PASS | focused benchmark and Hall of Shame evidence |
| D2.3 top-N GROUP BY SUM | PASS | live query and benchmark |
| D2.4 aggregated YoY CTE | PASS | focused benchmark |
| D2.5 completeness validator | PASS | focused benchmark |
| D2.6 active_domain lock | PASS | focused benchmark |
| D2.7 TRL synonym map | PASS | focused benchmark |
| D2.8 individual vs global average | PASS | focused benchmark |
| D2.9 self-correction loop | PASS | focused benchmark |
| D2.10 confidence scoring | PASS by existing tests; not independently re-audited here |
| D2.11 total_credit_score text | PARTIAL | schema parity has skips for live DB type checks |
| D2.12 real db_struct.sql schema | PARTIAL | migration parity still short of 58 full live tables |
| D2.13 HALL_OF_SHAME.md | PASS | `src/data/schema/failed_queries/HALL_OF_SHAME.md`, commit `4c743b84` |
| D2.14 latency | FAIL | no valid latency proof; Locust run invalid |
| D2.15 Q3 multi-row test | PASS in focused regression |
| D3 schema migration completeness | PARTIAL | `03_schema_parity.log`: `7 passed, 4 skipped` |
| D4 PII, injection, RBAC security | PARTIAL | focused security tests pass; tier responses still structurally identical |
| D4.11 GAP-A DB co-sign | PASS locally | `05_audit_binding.log`: `29 passed` |
| D4.12 audit tamper chain | FAIL | `14_audit_chain_verify.log`: `Chain intact: False` |
| D4.13 PII tests | PASS | `04_pii_security.log`: `10 passed` |
| D4.14 audit binding tests | PASS | `05_audit_binding.log`: `29 passed` |
| D4.15 egress allowlist | PASS | `06_egress_allowlist.log`: `35 passed` |
| D5 LLM mesh circuit breaker | PARTIAL | focused test passes; live provider kill script missing |
| D5.7 multi-hop DAG | PASS | `07_multi_hop_planner.log`: `28 passed` |
| D6 dashboards / PagerDuty / Langfuse | PARTIAL | not fully rerun in this protocol |
| D6.4 GAP-B scheduler | PASS locally | `20_vector_drift_scheduler.log`: dry-run + `4 passed` |
| D7 API/frontend tier outputs | PARTIAL/FAIL | live T1/T2/T3 query worked but structures were not materially different |
| D8 deployment infra | PARTIAL | Helm not revalidated in this protocol |
| D9 fine-tuning foundation | PARTIAL | `.training_data.db` has 3919 rows: 688 gold, 417 silver, 2574 bronze, 240 reject |
| D10 handover package | PASS for file existence | all 9 listed handover/pitch artifacts exist |

## 5. Red Team Results

Attacks run: 30.

| Metric | Result |
|---|---|
| BLOCKED | 24 / 30 |
| DOWNGRADED | 2 / 30 |
| HANDLED | 4 / 30 |
| ALLOWED on RT-01 to RT-25 | 0 |

Evidence: `evidence/2026-04-24/17_red_team_results.md`.

RT-17 and RT-20 are marked DOWNGRADED because they require endpoint/RBAC tier shaping rather than pure prompt sanitizer rejection. RT-27 through RT-30 are marked HANDLED because burst control and expensive-query bounding belong in rate-limit/execution layers, not the single-query sanitizer.

## 6. What-If Answers

| Scenario | Current behavior | Correct? | Fix status |
|---|---|---|---|
| W1 no time window / vague "best" | Router/synthesis attempts best-effort answer; metric ambiguity is not forced back to user | PARTIAL | Add clarification gate for ambiguous ranking metrics |
| W2 follow-up "compare to last year" | Dhairya active-domain cases pass in focused suite | YES for covered domains | Keep regression coverage |
| W3 SQL zero rows/error | Self-correction loop exists; not all live DB errors are covered | PARTIAL | Expand live DB error tests |
| W4 1000 concurrent / P99 >500ms | No valid local or cluster proof | NO | Requires C4 load harness fix + staging run |
| W5 cloud LLM down | Live logs show typo `SovereignLLLMesh` then local/rule-based fallback | PARTIAL | Fix typo and re-run provider failure test |
| W6 T3 `SELECT * FROM researchers` | Sanitizer/RBAC should downgrade or strip sensitive fields | PARTIAL | Need endpoint proof for every route |
| W7 SQL injection payload | Red-team RT-21..RT-25 blocked | YES | Keep tests |
| W8 600GB + 5-table JOIN | Untested locally | NO | Requires realistic Postgres fixture/load |
| W9 vector drift detected | Scheduler dry-run and mocked tests pass; live service not deployed | PARTIAL | Deploy scheduler service/cron in staging |
| W10 "is this verified?" | Audit/citation path exists, but audit chain currently false | NO | Repair audit chain and verify citations end-to-end |

## 7. Remaining Blockers

Local blockers:

- Audit chain must be repaired and root-caused from current `Line 378645: hash mismatch`.
- Full test suite must run green; current run failed provider/e2e checks and stalled.
- Load test harness must be fixed; current Locust tasks do not issue requests.
- Tier-specific `/query` response structures must actually differ, not just include different `tier` values.
- LLM mesh typo `SovereignLLLMesh` must be fixed and provider failure path re-tested.

Cluster/ops blockers:

- 1000-user C4 load test.
- 600GB production data load.
- Sovereign staging demo video.
- Professor/ministry/industry UAT sessions.
- GPG signature ceremony for handover artifacts.

## 8. Handover Package Status

| Artifact | Exists | Path |
|---|---:|---|
| H1 README | YES | `docs/handover/README.md` |
| H2 SYSTEM_OVERVIEW | YES | `docs/handover/SYSTEM_OVERVIEW.md` |
| H3 ARCHITECTURE | YES | `docs/handover/ARCHITECTURE.md` |
| H4 API_REFERENCE | YES | `docs/handover/API_REFERENCE.md` |
| H5 OPERATIONS_RUNBOOK | YES | `docs/handover/OPERATIONS_RUNBOOK.md` |
| H6 SECURITY_COMPLIANCE_ATTESTATION | YES | `docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md` |
| H7 DATA_INTAKE_PROTOCOL | YES | `docs/handover/DATA_INTAKE_PROTOCOL.md` |
| H8 UAT_RESULTS | YES | `docs/handover/UAT_RESULTS.md` |
| H9 Pitch deck | YES | `pitch/NRG_PITCH_DECK.md` |

## 9. Quality Bar Final

| C1-DPDP | C2-Audit | C3-DAG | C4-SLO | C5-Drift | C6-Egress | Score |
|---|---|---|---|---|---|---|
| PASS | PASS in unit tests; FAIL operational chain verify | PASS | SKIPPED/FAIL | PASS in scheduler tests | PASS | 5/5 reported by script, but not 6/6 compliant |

Evidence: `evidence/2026-04-24/08_quality_bar_scorecard.log`.

## 10. Cost Analysis

This is a planning estimate, not a measured production bill.

| Component | Cost per 1,000 queries | Calculation |
|---|---:|---|
| Cloud LLM | ₹40 | 30% of queries at ~₹0.13/query blended planner/verifier cost |
| Vector search | ₹5 | self-hosted Qdrant amortized estimate |
| SQL execution | ₹2 | self-hosted Postgres amortized estimate |
| Redis cache | ₹1 | local/managed Redis amortized estimate |
| Total | ₹48 | excludes GPU capex and staff/on-call |

Projected monthly at 50,000 daily queries: ~₹72,000/month variable platform estimate.

## 11. Founder Sign-Off

**NOT SIGNED.**

I cannot honestly sign the protocol as complete because the evidence shows unresolved blockers:

- `verify_chain()` is currently false.
- Full test suite is not green.
- C4 load proof is invalid.
- Live provider-kill circuit breaker test script is missing.
- T1/T2/T3 live query structures are not materially different.

Agent Name: Codex  
Date: 2026-04-25 execution against `evidence/2026-04-24/`  
Dhairya Score: 43/43 focused tests, including original 17/17  
Quality Bar: script reports 5/5, but 6/6 not satisfied because C4 is skipped  
Red Team: 0/25 ALLOWED security attacks; 24 blocked, 2 downgraded, 4 handled across all 30  
GAP-A git hash: `b873b713`  
GAP-B git hash: `527af236`  
GAP-C git hash: `4c743b84`  
Security hardening hashes: `b66d5ee0`, `bbe6102b`  
Evidence folder: `evidence/2026-04-24/`

Cluster-gap acknowledgement:

- GAP-D demo video: requires sovereign staging cluster.
- GAP-E 1000-user load test: requires corrected harness plus K8s cluster.
- GAP-F 600GB data load: requires sovereign cluster and data access.
- GAP-G UAT sessions: requires participant scheduling.
- GAP-H GPG signatures: requires OPS key ceremony.

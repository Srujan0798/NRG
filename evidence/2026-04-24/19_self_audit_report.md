NRG SELF-AUDIT REPORT - 2026-04-24
Produced by: Codex

1. EXECUTIVE SUMMARY

Overall production readiness: 4 / 10
UAT-ready for professor + ministry: NO

The three blockers that must be resolved first:

1. Full `pytest tests/` is not green. It failed e2e synthesis/provenance and provider-health checks, then stalled in router dataset evaluation. Evidence: `evidence/2026-04-24/01_pytest_full_suite.log`.
2. Security red-team is not passing. Direct gateway/security-layer validation blocked only 7/30 attacks and allowed 14 security attacks among RT-01..RT-25. Evidence: `evidence/2026-04-24/17_red_team_results.md`.
3. C4/C5 production proof is incomplete. Locust is missing, C4 did not run, and the quality-bar scorecard marks C5 vector drift as failed. Evidence: `15_load_test_results.log`, `08_quality_bar_scorecard.log`.

2. TEXT-TO-SQL BENCHMARK

Before: 7/17 = 41% (Dhairya original audit baseline)
After: 43/43 = 100% on the current focused regression file, `pytest tests/benchmarks/test_dhairya_regression.py -v`.

The current regression file has 43 tests, not 42. All original Dhairya Q1-Q17 cases pass in that focused suite. Evidence: `evidence/2026-04-24/02_dhairya_benchmark.log`.

Average latency: not proven for the full Dhairya suite in this run. The live top-funding SQL query returned successfully, but local API red-team traffic saturated the single uvicorn worker and C4 load testing did not run because `locust` is absent.

Remaining focused Dhairya failures: none in the focused benchmark. Remaining production SQL risks: live PostgreSQL schema/type parity was not fully exercised (`7 passed, 4 skipped`), and realistic 600GB data distribution was not proven.

3. FULL CHECKLIST RESULTS

| Area | Status | Evidence / Root Cause |
|---|---|---|
| C1 Core pipeline | PARTIAL | LangGraph/node tests largely pass, but full suite failed e2e synthesis/provenance and provider health checks. Evidence: `01_pytest_full_suite.log`. |
| C2 Text-to-SQL | PASS for focused suite, PARTIAL for production | Dhairya focused suite: `43 passed in 8.19s`. Live PostgreSQL parity and latency still unproven. |
| C3 Database/schema | PARTIAL | Schema parity: `7 passed, 4 skipped`; live DB column checks skipped. Evidence: `03_schema_parity.log`. |
| C4 Security/RBAC/DPDP | FAIL | PII compliance scorecard passes, but requested `test_pii_indian.py` is missing and red team allowed security attacks. Evidence: `04_pii_security.log`, `17_red_team_results.md`. |
| C5 LLM mesh/orchestration | PARTIAL | Multi-hop DAG passes; requested live circuit-breaker test file missing; provider health endpoint failed in full suite. Evidence: `07_multi_hop_planner.log`, `18_circuit_breaker_test.log`, `01_pytest_full_suite.log`. |
| C6 Observability | PARTIAL | Quality bar C5 vector drift failed in scorecard. Direct check-only script ran, but scorecard is still not compliant. Evidence: `08_quality_bar_scorecard.log`, `20_vector_drift_check_only.log`. |
| C7 Frontend/API | PARTIAL | Live `/query` works for all tiers, but T1/T2/T3 response structures are not materially tier-different. Evidence: `09`, `10`, `11` tier JSON files. |
| C8 Deployment/infra | PARTIAL | Helm/docs exist in tree, but no live sovereign-cluster deployment, DR timing, image-size proof, or NetworkPolicy enforcement test was run in this protocol. |
| C9 Fine-tuning foundation | PARTIAL | Training modules exist, but GOLD/SILVER live counts were not proven in this run. |
| C10 Handover package | PARTIAL | Required handover artifacts exist locally; freshness is not fully proven by executed UAT. See Section 8. |

4. GAPS FOUND & FIXED

| Gap ID | Description | Root Cause | Fix Applied | Test/Evidence | Before -> After |
|---|---|---|---|---|---|
| G1 | `/health` used old SQLite-only DB path | Legacy health implementation referenced `src.data.database.NRGDatabase` | Changed `/health` to use canonical `_get_db()` / `NRGDatabaseV2` path in `src/api/main.py` | `tests/api/test_health_endpoints.py::test_root_health_uses_canonical_database` | Health can report canonical DB state |
| G2 | `scripts/audit_investigate.py` failed on current audit event shape | Serializer included runtime/hash binding fields | Adjusted canonical serialization to exclude `hash`, `per_user_binding`, `user_key_hash` | `14_audit_chain_verify.log` after rebuild | Chain verifier can validate current entries |
| G3 | `scripts/audit_rebuild.py` could lose per-user binding metadata | Rebuild logic did not preserve/recompute binding consistently | Added timestamped backup behavior and binding preservation/recompute path | `27_audit_rebuild_after_full_suite.log` | Final chain valid: 375353 events |
| G4 | `BACKLOG.md` overstated readiness | Older status text was not synced with evidence | Updated banner and added Eternal Protocol evidence refresh section | `BACKLOG.md` | Backlog now says not UAT-ready |

5. WHAT-IF ANSWERS

| ID | Scenario | Current Behavior | Correct? | Fix Status |
|---|---|---|---|---|
| W1 | "Best in hydrogen catalysis" with no metric/time window | Router may infer hybrid/semantic path; ambiguity handling exists but UAT-level behavior not proven | PARTIAL | Needs deterministic clarification or default metric policy evidence |
| W2 | Follow-up "now compare to last year" | `active_domain` exists in state/planner, but multi-turn live proof was not run | PARTIAL | Add live session test |
| W3 | Text-to-SQL zero rows/error | Self-correction is tested in focused SQL suite; user-facing live failure modes not fully proven | PARTIAL | Add API-level zero-row proof |
| W4 | 1000 concurrent users; P99 > 500ms | C4 not run locally; locust missing | NO | Install locust and run local 200-user proof; sovereign 1000-user proof remains cluster-gated |
| W5 | Cloud LLM down mid-request | Mesh code has degradation paths; live provider-kill proof missing | PARTIAL | Add `tests/resilience/test_circuit_breaker_live.py` |
| W6 | Tier 3 attempts `SELECT * FROM researchers` | RBAC response shaping exists, but red team showed direct sanitizer allows related prompts | PARTIAL | Prove API-level column stripping and tighten gateway |
| W7 | Attacker sends `"; DROP TABLE researchers; --"` | SQL validator coverage exists, but direct prompt sanitizer allowed RT-22 | NO | Block obvious natural-language SQL injection before routing |
| W8 | 600GB dataset with 5-table JOIN | Not locally proven; seed/local scale is too small | PARTIAL | Add realistic data distribution/load fixtures |
| W9 | Vector drift detected | Check-only script runs, but scorecard C5 failed | NO | Fix scorecard path and retrieval quality threshold |
| W10 | Ministry asks if answer is verified | Citations/provenance exist for some paths; full suite has synthesis/provenance failures | PARTIAL | Fix e2e synthesis/provenance tests |

6. RED TEAM RESULTS

Attacks run: 30
BLOCKED: 7
ALLOWED: 18
DOWNGRADED_OR_HANDLED: 5

Security attacks allowed among RT-01 through RT-25: RT-03, RT-04, RT-05, RT-07, RT-08, RT-09, RT-10, RT-13, RT-14, RT-15, RT-21, RT-22, RT-23, RT-25.

Immediate fix required: tighten `src/security/gateway/prompt_sanitiser.py` and add tests for the allowed payloads. API-level run also exposed worker saturation/timeouts under expensive requests.

7. REMAINING BLOCKERS

Sovereign-cluster-only blockers:

- True C4 1000-concurrent P99 proof.
- Kubernetes NetworkPolicy egress proof against real cluster networking.
- Disaster-recovery timed restore proof using production-like Postgres/Qdrant/Vault.
- Final sovereign staging demo video capture.

Local blockers that are not cluster excuses:

- Full `pytest tests/` must pass without stalls.
- Red team RT-01..RT-25 must block or prove RBAC downgrade with curl evidence.
- Locust must be installed or replaced with a checked-in local load runner.
- C5 vector drift scorecard must pass or be explicitly marked PARTIAL, not reported as done.
- T1/T2/T3 live query responses must have policy-correct structural differences.

8. HANDOVER PACKAGE STATUS

| Artifact | Exists? | Up-to-date? | Path |
|---|---:|---:|---|
| H1 README | YES | PARTIAL | `docs/handover/README.md` |
| H2 System overview | YES | PARTIAL | `docs/handover/SYSTEM_OVERVIEW.md` |
| H3 Architecture | YES | PARTIAL | `docs/handover/ARCHITECTURE.md` |
| H4 API reference | YES | PARTIAL | `docs/handover/API_REFERENCE.md` |
| H5 Operations runbook | YES | PARTIAL | `docs/handover/OPERATIONS_RUNBOOK.md` |
| H6 Security compliance attestation | YES | PARTIAL | `docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md` |
| H7 Data intake protocol | YES | PARTIAL | `docs/handover/DATA_INTAKE_PROTOCOL.md` |
| H8 UAT results | YES | TEMPLATE/PARTIAL | `docs/handover/UAT_RESULTS.md` |
| H9 Pitch deck | YES | PARTIAL | `pitch/NRG_PITCH_DECK.md` |

9. QUALITY BAR FINAL

| C1-DPDP | C2-Audit | C3-DAG | C4-SLO | C5-Drift | C6-Egress | Score |
|---|---|---|---|---|---|---|
| PASS | PASS | PASS | SKIP/FAIL | FAIL | PASS | Scorecard: 4/5 scored; 6/6 compliant: NO |

Evidence: `evidence/2026-04-24/08_quality_bar_scorecard.log`.

10. COST ANALYSIS

No defensible rupee-per-1000-query number was produced in this run. Current live top-funding query used rule-based synthesis and local SQLite/Qdrant, so it does not measure cloud LLM, vector compute, SQL execution, or Redis cache costs at projected 1000-user scale.

Estimated cost per 1000 queries at 1000-user scale:

Cloud LLM: not evidenced
Vector search: not evidenced
SQL execution: not evidenced
Redis cache: not evidenced
Total/1000: not evidenced

11. FOUNDER SIGN-OFF

I cannot sign this protocol as DONE.

I, Codex, personally executed the available local commands recorded in `evidence/2026-04-24/`. Every PASS claim in this report points to an evidence file. Every FAIL/PARTIAL claim is documented with the observed root cause. I have not claimed the system is UAT-ready.

Agent Name: Codex
Date: 2026-04-25 local execution for 2026-04-24 protocol folder
Dhairya Score: 43/43 focused tests = 100%
Quality Bar: scorecard 4/5 scored; 6/6 compliant: NO
Red Team: 7/30 BLOCKED
Git commit hash: pending until evidence commit
Evidence folder: `evidence/2026-04-24/`

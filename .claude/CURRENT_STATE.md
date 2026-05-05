# NRG Current Sprint State
> **Update this file at the end of every session.** Agents read this instead of BACKLOG.md for current priorities.
> Last updated: 2026-05-06

---

## Blocked (cannot proceed without these)

| Item | Owner | Blocker | Next Action |
|------|-------|---------|-------------|
| Deployed staging URL | Srujan | No deployed frontend/API URL recorded for this repo/session | Provide target URLs or deployment credentials, then run `09_deployment_gate_stone.md` |
| Cluster C4 (1000-user) | Srujan | No usable Kubernetes context on this machine | Provide `KUBECONFIG` or cluster context, then run `scripts/run_final_external_gates.py --run-cluster-load` |
| Founder GPG signing | Srujan | No founder private key or signature ceremony available | Schedule founder signing and record detached signatures |
| Secret history purge | Srujan | Latest refreshed scanner evidence reports 0 findings after stale-branch cleanup, but credential rotation is still required if old commits were exposed | Preserve `evidence/2026-05-05/remaining_gates_final_attempt/s3_09_scan_all_refs_after_stale_branch_delete.json`; rotate credentials before security closure |

---

## In Progress

| Item | Status | Evidence |
|------|--------|----------|
| K-Q2/K-Q3 killer query proof | ASSIGNED local | Assignment: `.claude/assignments/shishya_killer_queries_live_local.md` — run on live local API, capture SQL + latency |
| Quality Bar scorecard | ASSIGNED local | `scripts/quality_bar_scorecard.json` is `5/6`; C4 P99 1200 ms. Assignment: `.claude/assignments/shishya_c4_p99_optimization.md` — profile and optimize |
| Local Docker/API runtime | PARTIAL | Docker data services are up. Direct Uvicorn can run on port 8001 through the Python startup wrapper used this session, but the local live C4 gate still fails P99 at the maintained workload. Port 8000 remains occupied by an `ssh` listener. |
| FastAPI TestClient runtime | PASS current | `evidence/2026-05-06/runtime_recovery/testclient_runtime.log` records 7 passing focused API contract checks; `evidence/2026-05-06/runtime_recovery/killer_queries_testclient.log` records 3 passing killer-query checks. |
| Frontend bundle size | ASSIGNED local | 318.71 KB raw (>250KB target). Assignment: `.claude/assignments/shishya_frontend_bundle_diet_v2.md` — reduce to <250KB |
| Console errors | PASS local | `evidence/2026-05-05/maximum_enforcement_local_browser_final/console_errors.json` is empty |
| Workflow cleanup | PASS local | canonical `nrg-validation-campaign` kept under `.claude/skills/`; deployment gate is `09_deployment_gate_stone.md`; local/remote sync must be checked before handoff |
| CI/CD pipeline validation | ASSIGNED local | Assignment: `.claude/assignments/shishya_cicd_pipeline_validation.md` — validate workflows, secrets, rollback |

---

## Shipped (last 7 days)

| Item | Date | Evidence |
|------|------|----------|
| Local C4 regression + live failure | May 6 | `scripts/quality_bar_scorecard.json` — 5/6, latest local live C4 P99 1200 ms with 0 failures; `evidence/2026-05-06/runtime_recovery/live_c4_local_8001_failure_summary.md` |
| Audit chain rebuild | May 2 | `.audit/chain_corrupted_backup_20260502T083003Z.jsonl` |
| Frontend dep audit | May 2 | `evidence/2026-05-02/.../247_...md` |
| Workflow scripts | May 5 | `.claude/scripts/nrg-verify-workflow.py` |
| Deployment gate stone | May 5 | `prompts_hybrid/09_deployment_gate_stone.md` |
| Remote workflow | May 5 | `.claude/REMOTE_WORKFLOW.md` |
| Focused Dhairya regression | May 5 | `evidence/2026-05-05/dhairya_regression_full/01_full_run.log` — 43 passed |
| Broad non-script pytest | May 5 | `evidence/2026-05-05/final_verification/full_non_script_pytest_after_compose_fix_summary.md` — 1846 passed, 57 skipped, 261 deselected |
| API focused pytest | May 5 | `evidence/2026-05-05/final_verification/api_pytest_final.log` — 155 passed, 1 deselected |
| Frontend production build | May 6 | `evidence/2026-05-06/frontend_build_recovery/npm_build.log` — `npm run build` exit 0 |
| FastAPI TestClient runtime | May 6 | `evidence/2026-05-06/runtime_recovery/testclient_runtime.log` — 7 passed; `evidence/2026-05-06/runtime_recovery/killer_queries_testclient.log` — 3 passed |

---

## Quality Bar

| C1 DPDP PII | C2 Audit | C3 Multi-hop | C4 SLO | C5 Drift | C6 Egress |
|:-----------:|:--------:|:------------:|:------:|:--------:|:---------:|
| PASS | PASS | PASS | FAIL live / PASS local regression | PASS local / production pending | PASS |

**C4**: `scripts/quality_bar_scorecard.json` reports 5/6. Latest local live C4 on `http://127.0.0.1:8001` used `NRG_C4_REQUIRE_LIVE=1` and completed 338548 requests with 0 failures, but failed P99 at 1200 ms (`evidence/2026-05-06/runtime_recovery/live_c4_local_8001_failure_summary.md`). An earlier forwarded-target attempt also failed at P99 4900 ms and 0.1717% failures (`evidence/2026-05-06/runtime_recovery/live_c4_locust_failure_summary.md`). Cluster/live closure still requires a performant NRG API target with `NRG_C4_REQUIRE_LIVE=1`.

**SQL accuracy (Dhairya)**: 43/43 tests pass (100%) — up from external audit 7/17 (41%). All 17 Dhairya benchmark queries produce correct SQL patterns.

**CI/CD (deploy.yml)**: Fixed in session commits (c0fc82e7+) — pytest e2e isolation, deploy-production condition, Semgrep continue-on-error.

---

## Quick Commands

```bash
# Verify workflow integrity
python3 .claude/scripts/nrg-verify-workflow.py

# Count skills + flag duplicates
python3 .claude/scripts/nrg-skill-count.py

# Report stale evidence
python3 .claude/scripts/nrg-evidence-prune.py --days 14

# Full test suite
bash scripts/run_test_suite.sh --live-api

# Start stack
bash scripts/run_critical_path_final.sh
```

---

## Deployed URLs

| Environment | URL | Status |
|-------------|-----|--------|
| Staging frontend | not provided | BLOCKED |
| Staging API | not provided | BLOCKED |
| Production frontend | not provided | BLOCKED |
| Production API | not provided | BLOCKED |

**No show readiness claims until staging URLs exist.**

---

## Key Files (agent must-reads per task type)

| Task type | Must read |
|-----------|-----------|
| Any task | `BACKLOG.md` (last 50 lines), `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`, `docs/specs/NRG_EXECUTION_FLOW_RULE_HIERARCHY_2026-05-02.md`, `db_struct.sql` header, `Core_Idea_Clean.md` sections 1-2 |
| SQL/schema | `db_struct.sql` (full), `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` |
| v1.0 build/fusion | `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`, `Core_Idea_Clean.md`, `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`, `db_struct.sql`, `CORPUS/`, `prompts_hybrid/00_INDEX.md`, task stone |
| Security/PII | `src/security/`, `.claude/rules/security.md` |
| API/auth | `src/api/main.py`, `src/auth/` |
| Frontend | `frontend/src/`, `.claude/rules/frontend.md` |
| Evidence | `.claude/rules/audit/protocol.md` section 2 |
| Deployment | `prompts_hybrid/09_deployment_gate_stone.md`, `.claude/REMOTE_WORKFLOW.md` |

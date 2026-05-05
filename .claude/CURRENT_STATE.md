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
| K-Q2/K-Q3 killer query proof | BLOCKED | Need fresh SQL + screenshots on staging |
| Quality Bar scorecard | PARTIAL local / external pending | `scripts/quality_bar_scorecard.json` is `5/6`; C1, C2, C3, C5, and C6 pass. C4 ran strict local SLO regression 9/9 but is marked PARTIAL because no live 1000-user load ran. Deployment CI sets `NRG_C4_REQUIRE_LIVE=1` so live C4 cannot fall back silently. |
| Local Docker/API runtime | BLOCKED | Docker data services are up, but no healthy local API target is available for live C4. Direct Uvicorn startup on port 8001 reached application startup, then failed to bind with `operation not permitted`; this session also observed an unhealthy SSH-forwarded NRG `/health` on port 8000. |
| FastAPI TestClient runtime | PASS current | `evidence/2026-05-06/runtime_recovery/testclient_runtime.log` records 7 passing focused API contract checks; `evidence/2026-05-06/runtime_recovery/killer_queries_testclient.log` records 3 passing killer-query checks. |
| Frontend bundle size | PASS current | `evidence/2026-05-06/frontend_build_recovery/npm_build.log` records `npm run build` exit 0, 2,581 modules transformed, largest JS chunk 318.71 KB raw, built in 3m 57s. |
| Console errors | PASS local | `evidence/2026-05-05/maximum_enforcement_local_browser_final/console_errors.json` is empty |
| Workflow cleanup | PASS local | canonical `nrg-validation-campaign` kept under `.claude/skills/`; deployment gate is `09_deployment_gate_stone.md`; local/remote sync must be checked before handoff |

---

## Shipped (last 7 days)

| Item | Date | Evidence |
|------|------|----------|
| Local C4 regression | May 5 | `scripts/quality_bar_scorecard.json` — 5/6, C4 local regression 9/9, live load not executed |
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
| PASS | PASS | PASS | PARTIAL (local test suite pass / live load pending) | PASS local / production pending | PASS |

**C4**: Local Quality Bar scorecard is partial: `scripts/quality_bar_scorecard.json` reports 5/6 and C4 local regression 9/9, but C4 is not counted as a pass because no live 1000-user run executed. The scorecard verifies `/health` before running Locust, so an unrelated TCP listener on port 8000 no longer creates false HTTP 0 C4 failures. Cluster/live 1000-user proof still requires a usable `KUBECONFIG` or a running NRG API target with `NRG_C4_REQUIRE_LIVE=1`.

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

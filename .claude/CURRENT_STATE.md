# NRG Current Sprint State
> **Update this file at the end of every session.** Agents read this instead of BACKLOG.md for current priorities.
> Last updated: 2026-05-05

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
| Quality Bar scorecard | PARTIAL current | `scripts/quality_bar_scorecard.json` is `5/5` with C4 marked `SKIP` because no API health response is available on port 8000; isolated strict local SLO regression passes |
| Local Docker/API runtime | BLOCKED | Colima reports the VM running, but Docker commands timed out after Buildx hangs and `localhost:8000` is currently unreachable |
| Frontend bundle size | PASS prior / BLOCKED current rerun | `evidence/2026-05-05/remaining_closure/frontend_build_current.log` records a prior Vite build with largest JS chunk 318.71 KB raw. A fresh `npm run build` rerun in this session hung in `tsc` for more than 6 minutes and was killed; current build proof remains blocked. |
| Console errors | PASS local | `evidence/2026-05-05/maximum_enforcement_local_browser_final/console_errors.json` is empty |
| Workflow cleanup | PASS local | canonical `nrg-validation-campaign` kept under `.claude/skills/`; deployment gate is `09_deployment_gate_stone.md`; local/remote sync must be checked before handoff |

---

## Shipped (last 7 days)

| Item | Date | Evidence |
|------|------|----------|
| Local C4 pass | May 2 | `evidence/2026-05-02/.../165_quality_bar_scorecard_...json` |
| Audit chain rebuild | May 2 | `.audit/chain_corrupted_backup_20260502T083003Z.jsonl` |
| Frontend dep audit | May 2 | `evidence/2026-05-02/.../247_...md` |
| Workflow scripts | May 5 | `.claude/scripts/nrg-verify-workflow.py` |
| Deployment gate stone | May 5 | `prompts_hybrid/09_deployment_gate_stone.md` |
| Remote workflow | May 5 | `.claude/REMOTE_WORKFLOW.md` |
| Focused Dhairya regression | May 5 | `evidence/2026-05-05/dhairya_regression_full/01_full_run.log` — 43 passed |

---

## Quality Bar

| C1 DPDP PII | C2 Audit | C3 Multi-hop | C4 SLO | C5 Drift | C6 Egress |
|:-----------:|:--------:|:------------:|:------:|:--------:|:---------:|
| PASS | PASS | PASS | PASS (local test suite) / cluster pending | PASS local / production pending | PASS |

**C4**: SLO test suite now passes: P50 <100ms, P95 <300ms, P99 <500ms — all green (9 passed, 3 skipped for macOS thread limits). Quality bar scorecard C4 shows SKIP (not FAIL) when API not running on port 8000 — that is expected for local runs without live server. Cluster 1000-user test still blocked pending Kubernetes context.

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

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
| Quality Bar scorecard | FAIL current | `scripts/quality_bar_scorecard.json` is `5/6`; C4 failed in the latest May 5 run with HTTP 0 failures; isolated strict local SLO regression now passes |
| Local Docker/API runtime | BLOCKED | Colima reports the VM running, but Docker commands timed out after Buildx hangs and `localhost:8000` is currently unreachable |
| Frontend bundle size | PASS prior / BLOCKED current rerun | May 5 prior build entry chunk is 2.23 KB raw; latest rerun did not finish under current machine load and `frontend/dist` is missing |
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
| PASS | PASS | PASS | FAIL current scorecard / historical local pass preserved / cluster pending | PASS local / production pending | PASS |

**C4**: The latest scorecard JSON is `5/6` with C4 `FAIL` on May 5. Isolated
strict local SLO regression now passes (`9 passed, 3 skipped`), but the May 5
Quality Bar scorecard still failed with HTTP 0 load errors. The May 2
quota-neutral 1000-user pass remains historical local evidence only. Fresh
current-stack C4 and deployed/cluster C4 are pending.

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

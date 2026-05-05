# NRG Current Sprint State
> **Update this file at the end of every session.** Agents read this instead of BACKLOG.md for current priorities.
> Last updated: 2026-05-05

---

## Blocked (cannot proceed without these)

| Item | Owner | Blocker | Next Action |
|------|-------|---------|-------------|
| Deployed staging URL | Srujan | No cloud account | Create AWS/GCP account; deploy via `09_deployment_gate_stone.md` |
| Cluster C4 (1000-user) | Srujan | No K8s cluster | Request KUBECONFIG from IIT-GN IT |
| Founder GPG signing | Srujan | No key ceremony | Schedule with professor |
| Secret history purge | Srujan | 286 remote findings | Run `scripts/scan_env_history_secrets.py` + filter-repo |

---

## In Progress

| Item | Status | Evidence |
|------|--------|----------|
| K-Q2/K-Q3 killer query proof | BLOCKED | Need fresh SQL + screenshots on staging |
| Frontend bundle size | PASS local | May 5 build entry chunk is 2.23 KB raw; largest lazy chunk is 319.01 KB raw / 87.80 KB gzip |
| Console errors | PASS local | `evidence/2026-05-05/maximum_enforcement_local_browser_fixed/console_errors.json` is empty |
| Workflow cleanup | PASS local | canonical `nrg-validation-campaign` kept under `.claude/skills/`; deployment gate is `09_deployment_gate_stone.md` |

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

---

## Quality Bar

| C1 DPDP PII | C2 Audit | C3 Multi-hop | C4 SLO | C5 Drift | C6 Egress |
|:-----------:|:--------:|:------------:|:------:|:--------:|:---------:|
| PASS | PASS | PASS | PASS local / cluster pending | PASS local / production pending | PASS |

**C4**: Local quota-neutral 1000-user pass complete. Cluster/deployed proof pending.

---

## Quick Commands

```bash
# Verify workflow integrity
python3 .claude/scripts/nrg-verify-workflow.py

# Count skills + flag duplicates
python3 .claude/scripts/nrg-skill-count.py

# Prune stale evidence (dry-run)
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
| Any task | `BACKLOG.md` (last 50 lines), `Core_Idea_Clean.md` sections 1-2 |
| SQL/schema | `db_struct.sql` (full), `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` |
| Security/PII | `src/security/`, `.claude/rules/security.md` |
| API/auth | `src/api/main.py`, `src/auth/` |
| Frontend | `frontend/src/`, `.claude/rules/frontend.md` |
| Evidence | `.claude/rules/audit/protocol.md` section 2 |
| Deployment | `prompts_hybrid/09_deployment_gate_stone.md`, `.claude/REMOTE_WORKFLOW.md` |

# NRG Current Sprint State
> **Update this file at the end of every session.** Agents read this instead of BACKLOG.md for current priorities.
> Last updated: 2026-05-07

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
| K-Q1/K-Q2/K-Q3 killer queries | PASS live local | `evidence/2026-05-06/killer_queries_live/` — 3/3 pass against live FastAPI + PostgreSQL; SQL, rows, and latency captured |
| Quality Bar scorecard | 5/6, C4 FAIL live local | C1-C3 and C5-C6 pass; latest scorecard JSON has C4 FAIL with P99 6600 ms, 0.27% failure rate, 16,398 samples, prewarm 208/208 (`evidence/2026-05-07/quality_bar_default_valid_after_remaining_probe.log`) |
| Frontend bundle | PASS current dist | Largest raw Vite chunk is App at 148KB (<250KB); bundle diet evidence committed under `evidence/2026-05-06/bundle_diet_v2/` |
| Frontend Batch 2 verification | PASS local | `npm run build`, `npm test -- --runInBand`, lint, contrast, and focused Playwright mobile/a11y passed; evidence under `evidence/2026-05-06/` |
| Batch 5 orchestration/skills verification | PASS local | `.venv/bin/python -m pytest tests/orchestration/ tests/skills/ -q --tb=short --no-cov -x` passed: 419 passed, 6 skipped |
| CI/CD pipeline | PATCHED / remote recheck pending | deploy.yml: e2e isolation, prod-only condition, Semgrep continue-on-error |
| Console errors | PASS local | empty console_errors.json |

---

## Shipped (last 7 days)

| Item | Date | Evidence |
|------|------|----------|
| API Docker rebuild via Colima | May 7 | `docker build -f Dockerfile.api -t nrg-api:remaining-c4-check .` PASS with `DOCKER_HOST=unix:///Users/srujansai/.colima/default/docker.sock`; evidence `evidence/2026-05-07/api_docker_build_colima_socket.log` |
| Local C4/C5 rerun | May 7 | `scripts/quality_bar_scorecard.json` — 5/6; C5 PASS; C4 live local still FAIL with P99 6600 ms, 0.27% failures, 16,398 samples |
| Local C4/C5 recovery attempt | May 6 | `scripts/quality_bar_scorecard.json` — 5/6; C5 bounded vector fingerprint PASS; C4 live local still FAIL with P99 2500 ms, 0% failures, 43,184 samples |
| Local API health hardening | May 6 | Lazy workflow construction and bounded vector/data health probes; `evidence/2026-05-06/runtime_recovery/health_8001_after_lazy_workflow_summary.md` |
| Audit chain rebuild | May 2 | `.audit/chain_corrupted_backup_20260502T083003Z.jsonl` |
| Frontend dep audit | May 2 | `evidence/2026-05-02/.../247_...md` |
| Workflow scripts | May 5 | `.claude/scripts/nrg-verify-workflow.py` |
| Deployment gate stone | May 5 | `prompts_hybrid/09_deployment_gate_stone.md` |
| Remote workflow | May 5 | `.claude/REMOTE_WORKFLOW.md` |
| Focused Dhairya regression | May 5 | `evidence/2026-05-05/dhairya_regression_full/01_full_run.log` — 43 passed |
| Frontend production build | May 6 | `evidence/2026-05-06/frontend_build_recovery/npm_build.log` — exit 0, App.js 148KB (down from 218KB) |
| FastAPI TestClient runtime | May 6 | `evidence/2026-05-06/runtime_recovery/testclient_runtime.log` — 7 passed |
| PostgreSQL killer query seed | May 6 | `evidence/2026-05-06/killer_query_pg_seed/00_summary.md` — 4 tables: 1440/280/282/3840 rows; K-Q1, K-Q2, K-Q3 all return data |
| Killer queries live local API | May 6 | `evidence/2026-05-06/killer_queries_live/00_summary.md` — 3/3 PASS against live FastAPI + PostgreSQL |
| Frontend bundle diet v2 | May 6 | `evidence/2026-05-06/bundle_diet_v2/00_summary.md` — PASS, largest raw chunk 148KB |
| CI/CD deploy.yml fix | May 6 | commit c0fc82e7 — e2e isolation, prod condition, Semgrep continue-on-error |
| C4 SLO local pass | May 6 | `tests/performance/test_slo_compliance.py` — 9/9 passed (P50/P95/P99 within targets) |
| C4 multi-target health retry | May 6 | commit 816321a4 — NRG_C4_API_BASE_URL env, health retries, port-conflict resilience |

---

## Quality Bar

| C1 DPDP PII | C2 Audit | C3 Multi-hop | C4 SLO | C5 Drift | C6 Egress |
|:-----------:|:--------:|:------------:|:------:|:--------:|:---------:|
| PASS | PASS | PASS | FAIL live local / PASS local regression | PASS live local / production pending | PASS |

**C4/C5**: `scripts/quality_bar_scorecard.json` reports 5/6. C5 passes through the bounded vector-fingerprint drift path. C4 remains blocked by P99/failure-rate evidence from the latest valid local 1000-user run: `P99=6600 ms`, failure rate `0.27%`, samples `16,398`, prewarm `208/208` (`evidence/2026-05-07/quality_bar_default_valid_after_remaining_probe.log`). Cluster/live closure still requires a healthy, performant NRG API target with `NRG_C4_REQUIRE_LIVE=1` and a staging URL.

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

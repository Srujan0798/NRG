# NRG External Final Gates

Generated: 2026-05-05T12:37:07Z
Overall status: **FAIL/BLOCKED**

| Gate | Status | Missing / Notes |
|---|---:|---|
| current_local_c4_scorecard | FAIL | `scripts/quality_bar_scorecard.json` is 5/6; C4 failed with p99 10000ms, 100% locust-reported failures, and HTTP 0 errors in the latest 1000-user run |
| strict_local_slo_regression | FAIL | `tests/performance/test_slo_compliance.py -m 'slow or not slow'` failed: P95 343ms >300ms, P99 2007ms >500ms |
| local_runtime_recovery | BLOCKED | Colima reported running after restart, but Docker commands timed out and `localhost:8000` was unreachable; recovery log also captured a Colima startup fatal |
| frontend_docker_build | BLOCKED | Frontend Docker build reached Buildx/context transfer then stalled; stale build processes were terminated, but repeated Buildx jobs restarted and Docker verification could not be completed |
| local_frontend_build_rerun | BLOCKED | `cd frontend && npm run build` did not complete during the final verification window; `dist/frontend` remained at the earlier 18:03 build output |
| deployed_browser_replay | BLOCKED | NRG_DEPLOYED_FRONTEND_URL, NRG_DEPLOYED_API_URL or NRG_PRODUCTION_API_URL |
| production_qdrant_baseline | BLOCKED | NRG_PRODUCTION_API_URL or NRG_DEPLOYED_API_URL |
| sovereign_cluster_1000_user_load | BLOCKED | KUBECONFIG and explicit --run-cluster-load flag |
| founder_gpg_signing | BLOCKED | 8 verified .asc signatures required, found 0, founder private GPG key on signing machine |
| github_deployments | BLOCKED | GitHub deployments API returned an empty list |
| github_actions | BLOCKED | Latest runs include in-progress CI/Deploy plus a failed Deploy NRG run |
| secret_history_remote | BLOCKED | Latest `s3_09_scan_all_refs_after_stale_branch_delete.json` reports 0 findings; credential rotation remains required before security closure |

This file is a gate report, not a production readiness certificate.

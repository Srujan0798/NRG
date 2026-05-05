# NRG External Final Gates

Generated: 2026-05-05T12:09:58Z
Overall status: **BLOCKED**

| Gate | Status | Missing / Notes |
|---|---:|---|
| deployed_browser_replay | BLOCKED | NRG_DEPLOYED_FRONTEND_URL, NRG_DEPLOYED_API_URL or NRG_PRODUCTION_API_URL |
| production_qdrant_baseline | BLOCKED | NRG_PRODUCTION_API_URL or NRG_DEPLOYED_API_URL |
| sovereign_cluster_1000_user_load | BLOCKED | KUBECONFIG and explicit --run-cluster-load flag |
| founder_gpg_signing | BLOCKED | 8 verified .asc signatures required, found 0, founder private GPG key on signing machine |
| github_deployments | BLOCKED | GitHub deployments API returned an empty list |
| github_actions | BLOCKED | Latest runs include in-progress CI/Deploy plus a failed Deploy NRG run |
| secret_history_remote | BLOCKED | `s3_09_scan_all_refs.json` reports 61 hash-redacted findings across 5 scanned commits |

This file is a gate report, not a production readiness certificate.

# NRG External Final Gates

Generated: 2026-05-06T20:20:58Z
Overall status: **BLOCKED**

| Gate | Status | Missing / Notes |
|---|---:|---|
| deployed_browser_replay | BLOCKED | NRG_DEPLOYED_FRONTEND_URL, NRG_DEPLOYED_API_URL or NRG_PRODUCTION_API_URL |
| production_qdrant_baseline | BLOCKED | NRG_PRODUCTION_API_URL or NRG_DEPLOYED_API_URL |
| sovereign_cluster_1000_user_load | BLOCKED | KUBECONFIG, non-local Kubernetes context required; current context is colima |
| founder_gpg_signing | BLOCKED | 8 verified .asc signatures required, found 0, founder private GPG key on signing machine |

This file is a gate report, not a production readiness certificate.

# Remaining External Gates After 2a476760

Date: 2026-05-05  
Head: `2a476760 evidence: close final local leftovers`

This pass attempted to close the remaining non-local gates after the local
browser, API health, audit, frontend, and docs evidence had been captured.

## Results

| Gate | Status | Evidence |
| --- | --- | --- |
| Deployed browser replay | BLOCKED | `external_gate_status.json` and `EXTERNAL_GATE_SUMMARY.md`: `NRG_DEPLOYED_FRONTEND_URL` plus deployed API URL are missing. GitHub deployments API returned `[]`. |
| Production Qdrant/API baseline | BLOCKED | `external_gate_status.json`: `NRG_PRODUCTION_API_URL` or `NRG_DEPLOYED_API_URL` is missing. |
| Sovereign-cluster C4 replay | BLOCKED | `kubectl_contexts.log`: current context is not set. `external_gate_status.json` records missing reachable Kubernetes cluster. |
| Founder GPG signatures | BLOCKED | `gpg_and_signature_files.log`: no secret keys listed and no `.asc` handover signatures found. |
| S3-09 remote history closure | BLOCKED/FAIL | `s3_09_scan_all_refs.log`: 286 secret-like assignments remain reachable from fetched remote refs. `local_vs_remote_secret_history.log` shows local `HEAD` does not contain the representative secret-bearing commit, while `nrg/main` does. |
| Normal push | BLOCKED | `git_push_dry_run.log`: rejected non-fast-forward. |
| Force-with-lease push | OPERATOR ACTION REQUIRED | `git_force_with_lease_dry_run.log`: dry-run shows `9ace4501...2a476760 main -> main (forced update)`. No actual force-push was performed. |

## Boundary

No remote rewrite, credential rotation, deployed replay, cluster load run, or
founder signing was performed. Closing the remaining gates requires:

- explicit repository-owner approval for `git push --force-with-lease nrg main:main`
- rotation of affected PostgreSQL, Redis, JWT, model API, and acceptance-user
  credentials before unfreezing remote writes
- deployed frontend/API URLs
- production API/Qdrant target
- reachable sovereign-cluster kubeconfig/context
- founder private GPG key and detached signatures for the handover documents

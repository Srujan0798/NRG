# Remaining External Gates After 2a476760

Date: 2026-05-05

Scope: companion current-head external-gate preflight after
`2a476760 evidence: close final local leftovers`.

## Results

| Surface | Status | Evidence |
| --- | --- | --- |
| External gate runner | BLOCKED | `EXTERNAL_GATE_SUMMARY.md`: deployed URLs, production API/Qdrant target, reachable Kubernetes cluster, and founder signatures are missing. |
| Kubernetes context | BLOCKED | `kubectl_cluster_info.log` and `kubectl_contexts.log`: no usable current context; cluster lookup falls back to refused localhost. |
| Normal push | BLOCKED | `git_push_dry_run.log`: rejected non-fast-forward. |
| Force-with-lease | NOT PERFORMED | `git_force_with_lease_dry_run.log` is a dry-run artifact only; `../final_leftovers_state_sync/remote_main_after_dry_run_confirm.log` confirms `nrg/main` remained `9ace45013f72a8261f2d3fe13df919a969bcdc44`. |
| GitHub deployments | BLOCKED | `github_deployments.json`: empty deployment list. |
| GitHub Actions | FAIL remote | `github_runs_latest.json`: latest remote runs on `nrg/main` are failing. |
| S3 env-history scan | FAIL | `s3_09_scan_all_refs.log` / `.json`: 286 secret-like assignments across historical runtime env-file versions. |
| Founder signatures | BLOCKED | `gpg_and_signature_files.log` and `gpg_secret_key_check.log`: signature files/private signing context are not complete in this workspace. |

## Boundary

This folder proves the remaining gates are not local code leftovers. They need
external operator/founder action, remote-history handling, deployed targets, and
cluster access.

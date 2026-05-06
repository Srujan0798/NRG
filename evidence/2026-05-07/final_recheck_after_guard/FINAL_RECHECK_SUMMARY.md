# Final Recheck After External Gate Guard

Date: 2026-05-07
Commit checked: `f26137bd harden external cluster gate context checks`

## Result

The local repository is clean and synced with `nrg/main`. The final external
gate runner was executed again with `--run-cluster-load`; it returned
`BLOCKED`, as expected, because this machine still lacks the required external
inputs.

## Evidence

| Check | Status | Evidence |
|---|---:|---|
| Git sync | PASS | `git status`, `git log -1`, and `git rev-list` output captured in terminal; branch was clean and `0 0` ahead/behind |
| Deployment/API URL variables | BLOCKED | `env_presence.log` shows deployed/API URL variables unset |
| Kubernetes cluster input | BLOCKED | `env_presence.log` shows `KUBECONFIG` unset; `kubectl_context.log` shows current context is local `colima` |
| External final gates | BLOCKED | `final_external_gates/EXTERNAL_GATE_SUMMARY.md` and `final_external_gates/external_gate_status.json` |
| Cluster-load guard | PASS behavior / BLOCKED input | Gate blocks `--run-cluster-load` because `KUBECONFIG` is missing and the context is local `colima` |
| Founder signing | BLOCKED | External gate report shows 0 verified detached signatures and no founder signing input on this machine |

## Command Run

```bash
.venv/bin/python scripts/run_final_external_gates.py \
  --evidence-dir evidence/2026-05-07/final_recheck_after_guard/final_external_gates \
  --run-cluster-load
```

## Inputs Still Required

- `NRG_DEPLOYED_FRONTEND_URL`
- `NRG_DEPLOYED_API_URL` or `NRG_PRODUCTION_API_URL`
- `KUBECONFIG` for the sovereign/staging cluster
- Optional `NRG_ALLOWED_CLUSTER_CONTEXTS` set to the approved cluster context
- Founder signing machine/private key and eight verified detached signatures
- Owner confirmation for credential rotation where applicable

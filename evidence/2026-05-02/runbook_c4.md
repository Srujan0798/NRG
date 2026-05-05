# C4 Load Gate Runbook Verification

Date verified: 2026-05-05

## Scope

H7-05 asked for a re-runnable C4 handover path tied to
`docs/handover/EXTERNAL_FINAL_GATES_RUNBOOK.md` and
`scripts/run_final_external_gates.py`.

## Verified Entry Points

| Surface | Status | Notes |
|---|---:|---|
| `docs/handover/EXTERNAL_FINAL_GATES_RUNBOOK.md` | PASS | Contains preflight and full cluster commands. |
| `scripts/run_final_external_gates.py` | PASS | Requires explicit `--run-cluster-load` before Locust execution. |
| `tests/load/run-locust-k8s.sh production` | EXTERNAL | Invoked only after `kubectl cluster-info` passes. |

## Preflight Command

```bash
.venv/bin/python scripts/run_final_external_gates.py \
  --evidence-dir evidence/$(date +%F)/final_external_gates
```

Expected laptop result: `BLOCKED`, not `FAIL`, for the C4 gate with missing
input `explicit --run-cluster-load flag`.

## Cluster Command

```bash
export KUBECONFIG="/path/to/sovereign-cluster-kubeconfig"

.venv/bin/python scripts/run_final_external_gates.py \
  --evidence-dir evidence/$(date +%F)/final_external_gates \
  --run-cluster-load
```

## Evidence Boundary

This runbook is executable locally through preflight. The 1000-user load proof
remains an external gate until a reachable sovereign Kubernetes target and load
test secrets are provided.

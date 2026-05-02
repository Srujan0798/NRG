# NRG External Gate Attempt

Date: 2026-05-02
Base commit: `21d60b4 chore: integrate local validation hardening`
Evidence directory: `evidence/2026-05-02/final_external_gates_after_21d60b4/`

## Result

Overall status: **BLOCKED**

This run did not find a local-code regression. It proved that the remaining
release gates cannot be closed from this machine because the required external
inputs are not configured here.

## Environment Presence

| Input | Presence |
| --- | --- |
| `NRG_DEPLOYED_FRONTEND_URL` | missing |
| `NRG_DEPLOYED_API_URL` | missing |
| `NRG_PRODUCTION_API_URL` | missing |
| `KUBECONFIG` | missing |

Raw evidence: `00_external_gate_env_presence.log`

## Gate Matrix

| Gate | Status | Blocking input |
| --- | --- | --- |
| Deployed browser replay | BLOCKED | Deployed frontend URL and deployed API URL |
| Production Qdrant baseline | BLOCKED | Production API URL |
| Sovereign cluster 1000-user load | BLOCKED | Explicit cluster-load run plus `KUBECONFIG` |
| Founder GPG signing | BLOCKED | Eight verified detached signatures from the founder signing machine |

Raw machine-readable evidence: `external_gate_status.json`

## Runner Proof

Command:

```bash
.venv/bin/python scripts/run_final_external_gates.py --evidence-dir evidence/2026-05-02/final_external_gates_after_21d60b4
```

Exit code: `2`, expected for BLOCKED gates.
Runner stdout: `01_external_gate_runner_stdout.log`
Runner exit record: `02_external_gate_runner_exit_code.log`
Runner summary: `EXTERNAL_GATE_SUMMARY.md`

## Run When Ready

These commands come from the gate runner and should be executed on the machine
that has the matching deployment, cluster, and founder-signing context.

```bash
cd frontend && NRG_DEPLOYED_FRONTEND_URL=https://... NRG_DEPLOYED_API_URL=https://... NRG_EVIDENCE_DIR=../evidence/YYYY-MM-DD/final_external_gates/deployed_browser npx playwright test tests/e2e/deployed_final_gate.spec.ts --reporter=list
```

```bash
NRG_PRODUCTION_API_URL=https://api... python scripts/run_final_external_gates.py
```

```bash
KUBECONFIG=/path/to/sovereign-cluster python scripts/run_final_external_gates.py --run-cluster-load
```

```bash
cd docs/handover/signatures
for doc in ../README.md ../SYSTEM_OVERVIEW.md ../ARCHITECTURE.md ../API_REFERENCE.md ../OPERATIONS_RUNBOOK.md ../SECURITY_COMPLIANCE_ATTESTATION.md ../DATA_INTAKE_PROTOCOL.md ../UAT_RESULTS.md; do
  gpg --armor --detach-sign --output "$(basename "$doc").asc" "$doc"
done
```

## Claim Boundary

PASS locally remains supported by the committed May 2 evidence for backend,
frontend, security, audit, local Qdrant/Redis, data quality, and local
quota-neutral load. This external gate attempt supports only a BLOCKED status
for deployed browser replay, production Qdrant baseline, cluster load replay,
and founder GPG signing.

# External Final Gates Runbook

Date: 2026-05-01

Purpose: execute the four release gates that cannot be proven from a local laptop alone.

This runbook is for the deployment/cluster/founder-signing machine. It is not a substitute for the evidence itself.

## Gates

| Gate | Required input | Evidence output |
|---|---|---|
| Deployed browser replay | `NRG_DEPLOYED_FRONTEND_URL`, `NRG_DEPLOYED_API_URL` | Playwright screenshots, video, API JSON, blocked Tier 3 JSON |
| Production Qdrant baseline | `NRG_PRODUCTION_API_URL` or `NRG_DEPLOYED_API_URL` | `/health`, `/health/qdrant`, `/health/all` JSON |
| Sovereign 1000-user C4 load | `KUBECONFIG`, cluster access, load-test secrets, explicit `--run-cluster-load` | Locust HTML/CSV/logs |
| Founder GPG signing | founder private GPG key on founder-controlled machine | 8 `.asc` signatures and verification logs |

## One Command

Dry-run/preflight:

```bash
.venv/bin/python scripts/run_final_external_gates.py \
  --evidence-dir evidence/$(date +%F)/final_external_gates
```

Full cluster gate:

```bash
export NRG_DEPLOYED_FRONTEND_URL="https://frontend.example"
export NRG_DEPLOYED_API_URL="https://api.example"
export NRG_PRODUCTION_API_URL="https://api.example"
export KUBECONFIG="/path/to/sovereign-cluster-kubeconfig"

.venv/bin/python scripts/run_final_external_gates.py \
  --evidence-dir evidence/$(date +%F)/final_external_gates \
  --run-cluster-load
```

## Deployed Browser Replay Only

```bash
cd frontend
NRG_DEPLOYED_FRONTEND_URL="https://frontend.example" \
NRG_DEPLOYED_API_URL="https://api.example" \
NRG_EVIDENCE_DIR="../evidence/$(date +%F)/final_external_gates/deployed_browser" \
npx playwright test -c tests/playwright.deployed.config.ts --reporter=list
```

Expected path:

- `evidence/YYYY-MM-DD/final_external_gates/deployed_browser/01_deployed_api_quantum_query.json`
- `evidence/YYYY-MM-DD/final_external_gates/deployed_browser/05_answer_verified_desktop.png`
- `evidence/YYYY-MM-DD/final_external_gates/deployed_browser/07_audit_proof_drawer_desktop.png`
- `evidence/YYYY-MM-DD/final_external_gates/deployed_browser/08_answer_verified_mobile.png`
- `evidence/YYYY-MM-DD/final_external_gates/deployed_browser/09_tier3_blocked_pii_query.json`

## Founder Signing

Run only on the founder-controlled signing machine:

```bash
cd docs/handover/signatures
for doc in ../README.md ../SYSTEM_OVERVIEW.md ../ARCHITECTURE.md \
           ../API_REFERENCE.md ../OPERATIONS_RUNBOOK.md \
           ../SECURITY_COMPLIANCE_ATTESTATION.md ../DATA_INTAKE_PROTOCOL.md \
           ../UAT_RESULTS.md; do
  gpg --armor --detach-sign --output "$(basename "$doc").asc" "$doc"
done

for sig in *.asc; do
  gpg --verify "$sig" "../${sig%.asc}"
done
```

Expected count: 8 verified signatures.

## Claim Boundary

Passing local tests and local browser proof earns local show-readiness only.

Do not claim production readiness until all four external gates above are `PASS` in `external_gate_status.json`.

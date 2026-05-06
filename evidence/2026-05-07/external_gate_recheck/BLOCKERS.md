# External Gate Recheck

Date: 2026-05-07
Commit: `29bee2a3 fix C4 load harness throughput profile`

## Result

Local fixable gates remain closed by prior committed evidence, including the
local Quality Bar scorecard at 6/6. The remaining gates are external and are
still `BLOCKED` because this machine does not have the required deployed URLs,
production API target, sovereign/staging cluster context, or founder signing
inputs.

## Fresh Evidence

| Gate | Status | Evidence |
|---|---:|---|
| Git state | PASS | `git_status.log`, `git_head.log`, `git_sync.log` |
| Batch 2 frontend command | PASS | `frontend_build_test_after_guard.log` reports Vite build success and Jest 32/32 suites, 107/107 tests passing |
| Batch 5 orchestration/skills command | PASS | `orchestration_skills_after_guard.log` reports 419 passed, 6 skipped |
| Deployment target environment | BLOCKED | `env_presence.log` shows deployed/staging/API URL vars and `KUBECONFIG` unset |
| Deployed browser replay | BLOCKED | `final_external_gates_pipefail/external_gate_status.json` |
| Production Qdrant baseline | BLOCKED | `final_external_gates_pipefail/external_gate_status.json` |
| Sovereign/staging C4 load | BLOCKED | `kubectl_context.log` shows local `colima` context only; `KUBECONFIG` unset |
| External-gate cluster guard | PASS hardening / BLOCKED input | `run_final_external_gates_guard_tests.log` reports 4 passed; `final_external_gates_cluster_guard/external_gate_status.json` shows `--run-cluster-load` blocks local `colima` and missing `KUBECONFIG` |
| Founder GPG signing | BLOCKED | `final_external_gates_pipefail/external_gate_status.json`; 0 verified signatures found |
| Secret scanner evidence | PASS scanner / BLOCKED rotation closure | `gitleaks_detect.log` reports no leaks across 612 commits; `env_history_secret_scan.json` reports 0 findings. Credential rotation remains an owner action if historical credentials were exposed. |
| Docs links | PASS | `check_docs_links.log` |
| Deployment preflight subset | PASS subset only | `deployment_gate_preflight_skip_external.log`; skipped test suite, Docker build, and health endpoints by command selection |

## Commands Run

```bash
git status --short --branch --untracked-files=all
git log -1 --oneline
git rev-list --left-right --count main...nrg/main
python3 scripts/check_docs_links.py
cd frontend && npm run build && npm test -- --runInBand
.venv/bin/python -m pytest tests/orchestration/ tests/skills/ -q --tb=short --no-cov -x
.venv/bin/python scripts/deployment_gate.py --help
.venv/bin/python scripts/deployment_gate.py --skip-tests --skip-docker --skip-health --env staging
.venv/bin/python scripts/run_final_external_gates.py --evidence-dir evidence/2026-05-07/external_gate_recheck/final_external_gates_pipefail
.venv/bin/python -m pytest tests/scripts/test_run_final_external_gates.py -q --tb=short --no-cov
.venv/bin/python scripts/run_final_external_gates.py --evidence-dir evidence/2026-05-07/external_gate_recheck/final_external_gates_cluster_guard --run-cluster-load
gitleaks detect --no-banner --redact --config .gitleaks.toml --report-format json --report-path evidence/2026-05-07/external_gate_recheck/gitleaks_report.json
.venv/bin/python scripts/scan_env_history_secrets.py --json-output evidence/2026-05-07/external_gate_recheck/env_history_secret_scan.json
```

## Required Inputs To Close Remaining Gates

- `NRG_DEPLOYED_FRONTEND_URL`
- `NRG_DEPLOYED_API_URL` or `NRG_PRODUCTION_API_URL`
- `KUBECONFIG` for the sovereign/staging cluster, not local `colima`
- Founder signing machine/private key and eight detached handover signatures
- Credential rotation confirmation for any previously exposed credentials

No external readiness claim should be made until these inputs exist and
`scripts/run_final_external_gates.py` returns `PASS` against them.

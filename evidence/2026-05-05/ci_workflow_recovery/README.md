# CI Workflow Recovery Evidence

Date: 2026-05-05
Status: PARTIAL

## What Was Fixed

- GitHub CI/deploy workflow Python installs now use `uv pip install --system`
  so runners without `.venv` do not fail during dependency installation.
- The scorecard runner falls back to the active Python executable when
  `.venv/bin/python` is absent.
- Frontend Docker image builds its own Vite output instead of requiring a
  pre-existing `dist/frontend` directory.
- Docker smoke CI creates `.env.dev` from `.env.example`.
- Gitleaks CI download path uses the correct release asset name.
- CodeQL SARIF upload uses v3 with `security-events: write`.
- `/health/qdrant` now reports `ready=false` when the configured collection is
  absent.
- `/health` bounds Qdrant health probes the same way audit probes are bounded.

## Fresh Checks

| Evidence | Result |
|---|---|
| `01_py_compile.log` | PASS |
| `02_workflow_yaml_parse.log` | PASS |
| `03_corpus_sync.log` | PASS |
| `04_response_filter_rbac_tests.log` | PASS, 52 passed / 1 deselected |
| `05_git_diff_check.log` | PASS |
| `06_forbidden_vocab_all.log` | PASS |
| `07_workflow_validator.log` | PASS |
| `08_workflow_links.log` | PASS |
| `09_docs_links.log` | PASS |
| `10_secret_history_scan_stdout.log` | PASS, 0 findings |
| `12_api_latency_cache_tests.log` | PASS, 5 passed |
| `13_health_qdrant_contract_tests.log` | PASS, 5 passed |
| `14_killer_query_route_tests.log` | PASS, 3 passed |
| `15_slo_health_slice.log` | PASS, 3 passed |
| `16_async_audit_append_tests.log` | PASS, 2 passed |
| `../dhairya_regression_full/01_full_run.log` | PASS, 43 passed |

## Failing / Blocked Checks

- `c4_slo_slice_after_health_qdrant_timeout_fix.log`: FAIL on this local host.
  Strict mocked SLO tests still missed wall-clock P50/P95/P99 thresholds and
  local Qdrant has no `nrg_research` collection.
- `11_local_runtime_timeout.log`: BLOCKED. Docker `ps` timed out after 10s and
  `http://127.0.0.1:8000/health` refused connection.
- Frontend build/Docker build could not be completed locally because long-lived
  Docker Buildx and TypeScript build processes hung under current machine load.
- A separate broad SQL accuracy run in `../core_verification/03_dhairya_all.log`
  still failed because local PostgreSQL became unavailable during that command;
  it is recorded as a local runtime failure, not as Dhairya focused-regression
  closure evidence.

## Boundary

These changes remove repo-owned CI plumbing failures seen on the latest remote
run. They do not close the C4/live-runtime/deployed-readiness gates.

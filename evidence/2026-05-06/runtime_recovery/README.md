# May 6 Runtime Recovery Evidence

## Scope

This evidence records the current local runtime status after the frontend build
blocker was cleared.

## PASS

- Frontend build: `evidence/2026-05-06/frontend_build_recovery/npm_build.log`
  records `npm run build` exit 0, 2,581 modules transformed, largest JS chunk
  318.71 KB raw, and Vite build time of 3m 57s.
- FastAPI TestClient contract path:
  `evidence/2026-05-06/runtime_recovery/testclient_runtime.log` records 7
  passing focused checks covering auth health, canonical DB health, Tier 3 PII
  filtering, and streaming query contract.
- Killer-query TestClient path:
  `evidence/2026-05-06/runtime_recovery/killer_queries_testclient.log`
  records 3 passing canonical killer-query checks with citations and audit IDs.
- Scorecard guard tests:
  `evidence/2026-05-06/runtime_recovery/scorecard_tests.log` records 15
  passing checks for C4 live-target detection and sandbox-safe pytest subprocess
  execution.
- Compose PgBouncer contract:
  `evidence/2026-05-06/runtime_recovery/compose_pgbouncer_test.log` records 2
  passing checks for API `DATABASE_URL` routing through PgBouncer.
- Scorecard refresh:
  `evidence/2026-05-06/runtime_recovery/quality_bar_scorecard_refresh.log`
  records 5/6 overall. Exit code is 1 by design because C4 remains partial
  until live load proof exists.
- Repository checks:
  `verify_corpus_sync.log`, `git_diff_check.log`, `py_compile.log`, and
  `forbidden_vocab_check_all.log` record passing corpus sync, whitespace,
  Python compile, and vocabulary checks.

## BLOCKED

- Live local API socket is blocked in this sandbox. `localhost:8000` is owned by
  an `ssh` listener, and direct Uvicorn startup on `127.0.0.1:8001` reaches
  application startup but fails to bind with `operation not permitted`.
- Docker data services are reachable, but starting the API container requires
  Docker socket access outside the current sandbox.
- C4 remains partial: local C4 regression passes, but live load proof still
  requires a healthy NRG API target with `NRG_C4_REQUIRE_LIVE=1`.

## Commands

```bash
npm run build
.venv/bin/python -m pytest -o addopts= -p no:rerunfailures \
  tests/api/test_auth_api.py::test_health_reports_auth_secret_status \
  tests/api/test_health_endpoints.py::test_root_health_uses_canonical_database \
  tests/api/test_tier_response_filtering.py::test_query_industry_response_strips_pii_and_debug_fields \
  tests/api/test_critical_path_stream.py -q --tb=short --no-cov
NRG_KILLER_QUERY_RUNS=3 .venv/bin/python -m pytest -o addopts= -p no:rerunfailures \
  tests/e2e/test_three_killer_queries.py -q -m e2e --tb=short --no-cov
.venv/bin/python -m pytest -o addopts= -p no:rerunfailures \
  tests/scripts/test_quality_bar_scorecard.py -q --tb=short --no-cov
.venv/bin/python -m pytest -o addopts= -p no:rerunfailures \
  tests/config/test_docker_compose_pgbouncer.py -q --tb=short --no-cov
.venv/bin/python scripts/quality_bar_scorecard.py
python3 scripts/verify_corpus_sync.py
git diff --check
python3 -m py_compile src/api/main.py scripts/quality_bar_scorecard.py
bash scripts/forbidden_vocab_check.sh --all
```

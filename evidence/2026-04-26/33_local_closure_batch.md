# Local Closure Batch — 2026-04-26

Scope: production hardening items that can be completed and verified on this workstation without cluster-only services.

## Closed Items

- Answer trust actions: added answer copy and source-data disclosure controls to stored-answer and streaming-answer surfaces.
- Connection pool routing: added PgBouncer to Docker Compose and routed API database traffic through `pgbouncer:6432` by default.
- Load-test authentication: moved Locust persona credentials to environment variables, aborting the run if login fails, and posting real `/query` requests with bearer headers.
- TRL safe views: added short Postgres views `trl_stages` and `tech_trl_stages`; updated semantic-layer safe views so prompt hints and database objects agree.
- Verifier numeric support: added local numeric-claim checking against SQL rows, including crore/lakh scaling.

## Evidence

- `npm test -- --runInBand tests/components/AnswerTrustActions.test.tsx` → 1 passed.
- `npm test -- --runInBand tests/hooks/useStreamingQuery.test.ts tests/components/EmptyState.test.tsx tests/components/ErrorState.test.tsx` → 13 passed.
- `npm test -- --runInBand tests/i18n/no_raw_strings.test.ts tests/design-system/no_raw_values.test.ts` → 2 passed.
- `npm run build` → passed; Vite production bundle generated.
- `npm run forbidden-grep -- ../dist/frontend` → passed.
- `PYTEST_ADDOPTS=--no-cov pytest tests/config/test_docker_compose_pgbouncer.py -q` → 2 passed.
- `docker compose config --quiet` → passed.
- `docker compose --profile dev config --quiet` → passed.
- `docker compose --profile prod config --quiet` → passed.
- `PYTEST_ADDOPTS=--no-cov pytest tests/config/test_locustfile_contract.py -q` → 2 passed.
- `python3 -m py_compile tests/load/locustfile.py` → passed.
- `PYTEST_ADDOPTS=--no-cov pytest tests/config/test_trl_safe_views.py -q` → 2 passed.
- `PYTEST_ADDOPTS=--no-cov pytest tests/orchestration/test_verifier_node.py tests/orchestration/test_verifier_numeric_faithfulness.py -q` → 15 passed.

## Remaining Limits

- Live attack replay, full local stack traffic, cluster load proof, and real-data SQL plans still require the API and backing services to be running with representative data.
- Existing unrelated dirty artifacts were not staged or altered by this closure batch.

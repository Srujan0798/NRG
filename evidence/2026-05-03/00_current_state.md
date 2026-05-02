# NRG Current State — 2026-05-03

## Scope

This state sync records the local continuation pass after the May 2
Guru/Shishya validation work and the Batch 1/2/3/5 verification evidence.

## Current HEAD Before This State Commit

- `88d3a0db fix: close query helper drift and stats evidence`
- Recent supporting commits:
  - `6baae945 evidence: comprehensive batch 1-2-3-5 verification — 41/43 tasks PASS, 2 INFO`
  - `e62502bc fix(data): preserve NULL aggregates instead of fabricating zero`
  - `082beb17 evidence: complete batch5 orchestration/AI/RAG reverify — 10/10 tasks pass`

## Current HEAD After Endpoint Matrix Commit

- `9ace4501 docs: add API endpoint matrix guard`
- The endpoint-matrix commit adds the route inventory drift guard, S3-09
  remediation-gate hardening, and current-state evidence links. It does not
  change public API behavior.

## PASS Locally

- `L1-CR-006` active drift boundary is closed locally. Exported
  `src/api/query_helpers.py` fast-path helpers delegate to the live
  answer-engine contract.
- Live `/query` and `/api/query/stream` behavior is now owned by
  `QueryAnswerService` in `src/api/query_service.py`; `src/api/main.py` keeps
  app setup, dependency binding, and router registration.
- Null aggregate values from `/api/data/stats` are preserved instead of
  silently converted to zero.
- Frontend stats surfaces render missing aggregate values as `Pending`.
- D4 hot-path index migration has regression tests for concurrent PostgreSQL
  index operations and missing table/column skips.

## Fresh May 3 Checks

- `.venv/bin/python -m py_compile src/api/query_helpers.py src/api/routes/data.py tests/api/test_query_helper_drift.py tests/api/test_data_stats_nulls.py src/migrations/versions/d4_hot_path_indexes_002.py tests/db/test_d4_hot_path_indexes_migration.py`
- `.venv/bin/python -m pytest tests/api/test_query_helper_drift.py tests/api/test_data_stats_nulls.py tests/db/test_d4_hot_path_indexes_migration.py tests/security/test_p0_security_regressions.py tests/api/test_query_async_boundaries.py -q --tb=short --no-cov`
  - Result: `15 passed in 6.59s`
- `.venv/bin/python -m pytest tests/api -q --tb=short --no-cov -x`
  - Result: `146 passed, 1 deselected, 56 warnings in 55.86s`
- `.venv/bin/python -m pytest tests/orchestration/ tests/skills/ -q --tb=short --no-cov -x`
  - Result: `419 passed, 6 skipped, 35 deselected in 80.02s`
- `.venv/bin/python -m pytest tests/ -x --tb=short -q --no-cov`
  - Result: `1903 passed, 55 skipped, 261 deselected, 285 warnings in 176.32s`
- `npm run build`
  - Result: Vite production build passed.
- `npm run lint`
  - Result: ESLint exited 0.
- `npm test -- --runInBand`
  - Result: 32 suites passed, 107 tests passed.
- `npm run test:contrast`
  - Result: 20 contrast tests passed.
- Focused Batch 2 Playwright a11y/keyboard/mobile/drawer/SSE/fetch-abort suite
  - Result: 16 passed.
- Scratch PostgreSQL Alembic upgrade to head
  - Result: `alembic_exit=0`; scratch DB dropped.
- `git diff --check`
  - Result: passed.
- `python3 scripts/verify_corpus_sync.py`
  - Result: `"ok": true`.
- `bash scripts/forbidden_vocab_check.sh`
  - Result: passed.
- Post-state replay:
  - `npm run build`: passed.
  - `npm test -- --runInBand`: 32 suites passed, 107 tests passed.
  - `.venv/bin/python -m pytest tests/orchestration/ tests/skills/ -q --tb=short --no-cov -x`: 419 passed, 6 skipped, 35 deselected.
  - corpus sync, forbidden-vocabulary guard, audit-chain verify, and diff
    whitespace checks passed.
- S3-09 remediation gate:
  - `.venv/bin/python -m pytest tests/scripts/test_scan_env_history_secrets.py -q --tb=short --no-cov`: 6 passed.
  - `.venv/bin/python -m pytest tests/api/test_api_endpoint_matrix.py tests/scripts/test_scan_env_history_secrets.py -q --tb=short --no-cov`: 7 passed.
  - `scripts/scan_env_history_secrets.py` now writes a redacted remediation
    summary with affected paths, affected keys, unique fingerprints, rotation
    classes, filter-repo path args, and required closure actions.
  - Current history scan remains `FAIL` with 286 redacted findings until
    approved credential rotation and history remediation are completed.
- API endpoint matrix:
  - `docs/specs/API_ENDPOINT_MATRIX.md` documents the registered FastAPI route
    inventory.
  - `tests/api/test_api_endpoint_matrix.py` compares the matrix against
    `src.api.main.app` so route changes must update the document.
  - Endpoint matrix, route registration, and S3-09 scanner combined regression:
    10 passed.
- `.venv/bin/python scripts/run_final_external_gates.py --evidence-dir evidence/2026-05-03/final_external_gates_after_88d3a0db`
  - Result: BLOCKED by missing external deployed URLs, production API/Qdrant
    target, explicit cluster-load context, and founder signatures.
- `.venv/bin/python scripts/run_final_external_gates.py --evidence-dir evidence/2026-05-03/final_external_gates_after_9ace4501`
  - Result: BLOCKED by missing external deployed URLs, production API/Qdrant
    target, explicit cluster-load context, and founder signatures.

## Evidence

- `evidence/2026-05-03/l1_query_helper_drift_closure/README.md`
- `evidence/2026-05-03/local_continuation/README.md`
- `evidence/2026-05-03/final_external_gates_after_88d3a0db/EXTERNAL_GATE_SUMMARY.md`
- `evidence/2026-05-03/final_external_gates_after_9ace4501/EXTERNAL_GATE_SUMMARY.md`
- `evidence/2026-05-03/query_service_extraction/README.md`
- `evidence/2026-05-03/post_state_replay/README.md`
- `evidence/2026-05-03/s3_09_remediation_gate/README.md`
- `evidence/2026-05-03/api_endpoint_matrix_closure/README.md`
- `docs/specs/API_ENDPOINT_MATRIX.md`
- `docs/adr/ADR-007-main-py-answer-engine-split.md`
- `evidence/2026-05-03_rt14_live_response_diagnostic.json`

## Boundaries

- `src/api/query_helpers.py` remains a compatibility/helper module. New query
  behavior should target `QueryAnswerService`, with drift tests for any helper
  delegation.
- External deployed browser proof, cluster load replay, production Qdrant/API
  proof, production UAT, strict API no-fix image remediation, and founder
  signing remain outside this local pass.

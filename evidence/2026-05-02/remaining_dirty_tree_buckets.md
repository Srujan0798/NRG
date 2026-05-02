# Remaining Dirty Tree Buckets

Date: 2026-05-02

Purpose: classify the current uncommitted work after the Batch 2 and Batch 5
closure commits. This is a bookkeeping/evidence file only. No source files were
reverted, deleted, or committed while producing this classification.

## Index State

- Cleared accidental staged entries with `git restore --staged .`.
- `git diff --cached --stat` is empty after the unstage.
- Working tree is still intentionally dirty and must be packaged by bucket.
- Top-level dirty counts from `git status --porcelain=v1`:
  - `src`: 52
  - `evidence`: 33
  - `tests`: 25
  - `infrastructure`: 17
  - `scripts`: 3
  - `docs`: 3
  - one each: `.claude`, `.github`, `.pre-commit-config.yaml`, `BACKLOG.md`,
    `Dockerfile.orchestration`, `docker-compose.prod.yml`, `docker-compose.yml`,
    `frontend`, `pyproject.toml`, `pyrightconfig.strict_batch1.json`, `typings`,
    `uv.lock`

## Recent Closure Commits

- `eb1b81c Batch 2 frontend polish closure`
- `5859a5e Batch 5 orchestration RAG closure`

## Verification Already Re-run

- `cd frontend && npm run build && npm test -- --runInBand`: PASS.
- `.venv/bin/python -m pytest tests/orchestration/ tests/skills/ -q --tb=short --no-cov -x`: PASS, `391 passed, 6 skipped, 35 deselected`.
- `.venv/bin/python scripts/audit_rebuild.py --verify`: PASS.
- `.venv/bin/python scripts/verify_corpus_sync.py`: PASS.
- `bash scripts/forbidden_vocab_check.sh`: PASS.
- `scripts/run_test_suite.sh --live-api`: PASS; non-live and live API phases passed,
  and the runner produced `test_suite_full_final.xml` and
  `test_suite_live_api.xml`.

## Bucket 1: Batch 6 / Infra DevOps

Treat these as the next clean packaging target because they are mostly
deployment, Helm, gateway, runtime, observability, and caching work.

- `.github/workflows/cd.yml`
- `Dockerfile.orchestration`
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `infrastructure/helm/nrg/**`
- `infrastructure/kong/kong.yaml`
- `infrastructure/kong/kong.yml`
- `infrastructure/nginx/conf.d/default.conf`
- `infrastructure/nginx/frontend.conf`
- `src/caching/redis_layer.py`
- `src/config/llm_config.py`
- `src/config/local_llm.py`
- `src/observability/health_checks.py`
- `src/observability/metrics.py`
- `tests/config/test_batch6_infra_hardening.py`
- `tests/observability/test_prometheus_label_safety.py`
- `tests/unit/test_redis_layer.py`
- `typings/langgraph/**`
- `evidence/2026-05-02/batch6_infra_devops/**`

Suggested gate before committing this bucket:

```bash
.venv/bin/python -m pytest tests/config/test_batch6_infra_hardening.py tests/observability/test_prometheus_label_safety.py tests/unit/test_redis_layer.py -q --tb=short --no-cov
```

## Bucket 2: Batch 3 / Security Compliance

Treat these as the second packaging target because they include security route,
PII, token, egress, signer, RBAC, and historical secret-scanning work.

- `docs/security/ENV_HISTORY_SECRET_REMEDIATION_2026-05-02.md`
- `scripts/scan_env_history_secrets.py`
- `src/api/middleware/security.py`
- `src/api/middleware/quota.py`
- `src/api/routes/admin.py`
- `src/api/routes/auth.py`
- `src/api/routes/audit.py`
- `src/api/routes/telemetry.py`
- `src/auth/**`
- `src/security/**`
- `tests/scripts/test_scan_env_history_secrets.py`
- `tests/security/**`
- `evidence/2026-05-02/batch3_security_compliance/**`

Suggested gate before committing this bucket:

```bash
.venv/bin/python -m pytest tests/security/ tests/scripts/test_scan_env_history_secrets.py tests/auth/test_jwt_handler.py -q --tb=short --no-cov -x
```

## Bucket 3: Backend/API Foundation And Query Reconcile

Treat these as the third packaging target because they span API contracts,
query response shaping, orchestration state, audit/database helpers, and tests.

- `pyrightconfig.strict_batch1.json`
- `src/api/ai_synthesis.py`
- `src/api/answer_contract.py`
- `src/api/deps.py`
- `src/api/logging_config.py`
- `src/api/main.py`
- `src/api/query_helpers.py`
- `src/api/query_response_utils.py`
- `src/api/response_filter.py`
- `src/api/routes/data.py`
- `src/api/routes/dpdp.py`
- `src/api/routes/graph.py`
- `src/api/routes/health.py`
- `src/api/routes/ingest.py`
- `src/api/routes/query.py`
- `src/audit/**`
- `src/data/**`
- `src/orchestration/contracts/**`
- `src/orchestration/graph.py`
- `src/orchestration/nodes/complexity_classifier.py`
- `src/orchestration/nodes/receiver.py`
- `src/orchestration/nodes/reflector.py`
- `src/orchestration/nodes/verifier.py`
- `src/orchestration/query_catalog.py`
- `src/orchestration/schema_rag.py`
- `src/orchestration/state.py`
- `src/services/consent.py`
- `src/skills/text_to_sql/schema_retriever.py`
- `src/training/**`
- `tests/api/**`
- `tests/audit/test_async_append.py`
- `tests/data/test_database_v2.py`
- `tests/e2e/test_consent_flow.py`
- `tests/orchestration/test_two_brain_conflict_resolution.py`
- `tests/unit/test_database.py`
- `evidence/2026-05-02/backend_api_foundation/**`
- `evidence/2026-05-02/backend_query_reconcile/**`

Suggested gate before committing this bucket:

```bash
.venv/bin/python -m pytest tests/api/ tests/audit/ tests/data/ tests/e2e/test_consent_flow.py tests/unit/test_database.py -q --tb=short --no-cov -x
```

## Bucket 4: Generated Verification Artifacts

Review these separately. They are output from verification runs and should be
kept only when they add durable evidence for the committed batch.

- `evidence/2026-05-02/audit_chain/**`
- `evidence/2026-05-02/live_api_audit/**`
- `evidence/2026-05-02/test_suite_full_final.xml`
- `evidence/2026-05-02/test_suite_live_api.xml`
- `evidence/2026-05-02/guru_shishya_validation/321_data_quality_scorecard_current.json`
- `evidence/2026-05-02/guru_shishya_validation/321_data_quality_scorecard_current.md`
- `evidence/2026-05-02/guru_shishya_validation/322_current_local_backend_verification_summary.md`
- `evidence/2026-05-02/guru_shishya_validation/341_runtime_security_frontend_integration_summary.md`
- `evidence/2026-05-02/guru_shishya_validation/350_final_ruff_changed_python_files.txt`
- `evidence/2026-05-02/guru_shishya_validation/350_final_ruff_changed_source_python_files.txt`
- `evidence/2026-05-02/guru_shishya_validation/FINAL_VALIDATION_MATRIX.md`
- `frontend/tests/playwright-report/index.html`

## Bucket 5: Regenerated Batch 2 Evidence

Batch 2 is already committed, but later browser/playwright runs changed some
screenshots and SSE evidence. These need a deliberate decision: either commit
as a small evidence refresh or leave out of the next source buckets.

- `evidence/2026-05-02/batch2_frontend_polish/drawers/*.png`
- `evidence/2026-05-02/batch2_frontend_polish/mobile/*.png`
- `evidence/2026-05-02/batch2_frontend_polish/sse/sse_reconnect_metrics.json`
- `evidence/2026-05-02/batch2_frontend_polish_reverify/**`

## Bucket 6: Cross-cutting Metadata And Dependency Files

Review these with the bucket that changed them. Do not commit all together
unless the diff shows they belong to the same acceptance evidence.

- `.claude/CURRENT_STATE.md`
- `.pre-commit-config.yaml`
- `BACKLOG.md`
- `docs/PERFORMANCE_SLOS.md`
- `docs/specs/NRG_EXECUTION_FLOW_RULE_HIERARCHY_2026-05-02.md`
- `scripts/REGISTRY.md`
- `scripts/ingest_documents.py`
- `pyproject.toml`
- `uv.lock`
- `evidence/2026-05-02/09_tier1_pii_injection_response.json`
- `evidence/2026-05-02/09_tier1_query_response.json`
- `evidence/2026-05-02/10_tier2_query_response.json`
- `evidence/2026-05-02/11_tier3_query_response.json`

## Recommended Next Commit Order

1. Package and verify Batch 6 / Infra DevOps.
2. Package and verify Batch 3 / Security Compliance.
3. Package and verify Backend/API Foundation and Query Reconcile.
4. Decide generated verification artifacts only after their owning bucket is
   clear.
5. Decide whether regenerated Batch 2 evidence should be a separate evidence
   refresh commit.

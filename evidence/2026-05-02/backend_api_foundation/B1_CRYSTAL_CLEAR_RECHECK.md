# Batch 1 Crystal Clear Recheck

Date: 2026-05-02

## Scope

This recheck covers Batch 1 Backend/API Foundation after the fresh "complete remaining" request. The earlier evidence was not trusted blindly; the gates below were replayed on the current worktree.

## Result Matrix

| Surface | Status | Evidence |
| --- | --- | --- |
| B1-01 query fast-path delta doc | PASS | `../backend_query_reconcile/delta_matrix.md` |
| B1-02 health endpoints | PASS | `B1_recheck_targeted_pytest.log`, `B1_recheck_full_pytest_final.log` |
| B1-03 JWT concurrent refresh | PASS | `B1_recheck_targeted_pytest.log`, `B1_recheck_full_pytest_final.log` |
| B1-04 DB rollback tests | PASS | `B1_recheck_targeted_pytest.log`, `B1_recheck_full_pytest_final.log` |
| B1-05 Text-to-SQL sqlfluff | PASS | `B1_recheck_sqlfluff_final.log`, `B1_recheck_precommit_sqlfluff_final.log` |
| B1-06 audit append latency | PASS | `B1-06_audit_append_latency.log` |
| B1-07 OpenAPI PII scan | PASS | `B1_recheck_openapi_scan_final.log` |
| B1-08 rate-limit burst 429 audit ID | PASS | `B1_recheck_targeted_pytest.log`, `B1_recheck_full_pytest_final.log` |
| B1-09 route registration/imports | PASS | `B1_recheck_targeted_pytest.log`, `B1_recheck_full_pytest_final.log` |
| B1-10 stream start latency | PASS | `B1_recheck_targeted_pytest.log`, `B1_recheck_full_pytest_final.log` |
| B1-11 strict API/orchestration typing | PASS | `B1_recheck_pyright_strict_final.json` |

## Fresh Commands

- `.venv/bin/python -m pytest tests/ -x --tb=short -q`
  - PASS: 1846 passed, 55 skipped, 261 deselected.
- `.venv/bin/python -m pytest tests/audit/test_async_append.py tests/audit/test_chain_integrity.py tests/api/test_query_security_validation.py tests/api/test_tier_isolation_live.py tests/orchestration/test_two_brain_conflict_resolution.py tests/security/test_p0_security_regressions.py tests/security/test_sql_injection_blocked.py -q --tb=short`
  - PASS: 66 passed.
- `.venv/bin/pyright -p pyrightconfig.strict_batch1.json --outputjson`
  - PASS: 44 files analyzed, 0 errors, 0 warnings, 0 information.
- `.venv/bin/pyright src/api src/orchestration`
  - PASS: 0 errors, 0 warnings, 0 information.
- `.venv/bin/ruff check src/api src/orchestration src/data src/auth src/security src/audit src/services tests/api tests/auth tests/security tests/data tests/audit tests/orchestration`
  - PASS: all checks passed.
- `.venv/bin/sqlfluff lint src/skills/text_to_sql/`
  - PASS: all finished.
- `.venv/bin/pre-commit run sqlfluff-text-to-sql --all-files`
  - PASS.
- `.venv/bin/python -m compileall -q src tests scripts`
  - PASS.
- `git diff --check`
  - PASS.
- OpenAPI scan
  - PASS: path_count=49, metrics_in_schema=False, password/ssn/aadhaar/pan/secret/raw_sql counters all 0.
- Audit-chain verification
  - PASS: valid=True, errors=0, count=297626.
- Evidence marker scan
  - PASS: no negative status or error markers in Batch 1 evidence directories.

## Recheck Fixes Made

- Preserved legacy router monkeypatch behavior while keeping strict typing by normalizing string, tuple/list, and mapping LLM route results.
- Removed backend/API validation-surface ruff violations: unused imports, unused locals, and accidental f-string prefixes.

## Known Residual Warnings

- Full pytest still reports FastAPI `ORJSONResponse` deprecation warnings. This response class is intentionally retained because existing response-contract tests depend on it.
- JWT `InsecureKeyLengthWarning` appears only in tests that intentionally use short fixture secrets.
- `pytest_asyncio` warns that `asyncio_default_fixture_loop_scope` is unset; tests still pass.

## Worktree Note

The repository has many pre-existing unrelated modified and untracked frontend/docs/evidence files. They were not reverted or cleaned during this Backend/API Batch 1 recheck.

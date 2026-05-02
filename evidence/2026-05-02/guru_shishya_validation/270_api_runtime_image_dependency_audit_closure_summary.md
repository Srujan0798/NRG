# API Runtime Image Dependency Audit Closure

Date: 2026-05-02

## Verdict

| Gate | Status | Evidence |
| --- | --- | --- |
| Initial API runtime image build and smoke | PASS build/smoke, FAIL Python package audit | `253_api_runtime_image_build_after_dependency_hardening.log`, `256_api_runtime_image_smoke_with_runtime_env_after_dependency_hardening.log`, `261_api_runtime_image_pip_audit.json` |
| API runtime dependency hardening | PASS | `Dockerfile.api`, `pyproject.toml`, `uv.lock` |
| Fixed API runtime image build and smoke | PASS | `262_api_runtime_image_build_after_dependency_audit_fix.log`, `263_api_runtime_image_smoke_after_dependency_audit_fix.log`, `264_api_runtime_image_inspect_after_dependency_audit_fix.log`, `265_api_runtime_image_ls_after_dependency_audit_fix.log` |
| Fixed API runtime package inventory | PASS | `266_api_runtime_image_pip_list_after_dependency_audit_fix.json` |
| Fixed API runtime FastAPI/import smoke | PASS | `267_api_runtime_image_fastapi_testclient_after_dependency_audit_fix.log` |
| Fixed API runtime Python vulnerability audit | PASS | `268_api_runtime_image_pip_audit_after_dependency_audit_fix.json`, `268_api_runtime_image_pip_audit_after_dependency_audit_fix.log` |
| Dependency diff summary | PASS | `274_api_dependency_audit_json_summary.log` |
| Auth/security regression slice | PASS | `271_api_dependency_auth_security_regression.log` |
| FastAPI/API contract regression slice | PASS | `272_api_dependency_fastapi_contract_regression.log` |
| Lockfile consistency | PASS | `273_api_dependency_uv_lock_check.log` |
| Audit chain verification after dependency checks | PASS | `275_api_dependency_audit_chain_verify.log` |
| OS/base-image CVE scan | BLOCKED local tool availability | `269_api_runtime_image_scanner_availability_after_dependency_audit_fix.log` |

## What Changed

- Upgraded vulnerable runtime pins: `fastapi` to 0.136.1, `starlette` through FastAPI to 0.52.1, `PyJWT` to 2.12.1, `python-dotenv` to 1.2.2, `requests` to 2.33.1, `sentence-transformers` to 5.4.1, and `transformers` to 5.7.0.
- Removed `pytest` from main runtime dependencies and pinned it under the `dev` extra at 9.0.3.
- Moved the `pip`, `wheel`, and `setuptools` upgrade inside `/app/venv` in `Dockerfile.api`, so the runtime venv is audited with the upgraded installer toolchain.

## Before/After Audit Result

Initial API image `pip-audit` found 11 vulnerabilities across 7 runtime packages:

- `pip==24.0`: 3
- `pyjwt==2.8.0`: 1
- `pytest==8.2.2`: 1
- `python-dotenv==1.0.0`: 1
- `requests==2.32.3`: 2
- `starlette==0.38.6`: 2
- `transformers==4.57.6`: 1

Fixed API image `pip-audit` result:

- Dependencies scanned: 122
- Vulnerable packages: 0
- Vulnerabilities: 0
- Command exit: 0

## Runtime Smoke Result

The fixed image was built as `nrg-api:dependency-audit-20260502-fixed`, digest
`sha256:9fbecc2b6e62eb6f73294122f8e70b516d9c0cc88a3b5b7601f3b54d0388375c`.
It runs as user `app`, imports `src.api.main`, exposes a FastAPI app, has
`uvicorn` present in `/app/venv`, and has `/var/lib/nrg` available. A TestClient
probe reached `/health` with HTTP 200, and the upgraded
`sentence_transformers`/`transformers` imports passed without downloading a
model.

## Regression Checks

- `tests/auth/test_jwt_handler.py`, `tests/security/test_red_team_v41.py`, and
  `tests/api/test_query_security_validation.py`: 23 passed, 30 skipped.
- `tests/api/test_lifespan_startup.py`, `tests/api/test_new_endpoints.py`, and
  `tests/contract/test_api_response_schema.py`: 21 passed.
- `uv lock --check`: resolved successfully.
- Audit chain after the dependency checks: `(True, [], 282779)`.

## Remaining Boundary

This closes the API runtime Python package audit for the local image. It does
not close OS/base-image CVE scanning or deployed image scanning. Local scanner
availability check reports `trivy`, `grype`, and `syft` are unavailable; that
scan must run in an environment with a scanner installed or in CI.

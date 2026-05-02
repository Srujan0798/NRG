# API Runtime Image Dependency Audit Closure

Date: 2026-05-02

## Verdict

| Gate | Status | Evidence |
| --- | --- | --- |
| Initial API runtime image build and smoke | PASS build/smoke, FAIL Python package audit | `253_api_runtime_image_build_after_dependency_hardening.log`, `256_api_runtime_image_smoke_with_runtime_env_after_dependency_hardening.log`, `261_api_runtime_image_pip_audit.json` |
| API runtime dependency hardening | PASS | `Dockerfile.api`, `pyproject.toml`, `uv.lock` |
| Fixed API runtime image build and smoke | PASS | `262_api_runtime_image_build_after_dependency_audit_fix.log`, `263_api_runtime_image_smoke_after_dependency_audit_fix.log`, `264_api_runtime_image_inspect_after_dependency_audit_fix.log`, `265_api_runtime_image_ls_after_dependency_audit_fix.log` |
| Exact-source API image rebuild after deterministic pip minimum | PASS | `275_api_runtime_image_build_after_pip_min_pin.log`, `276_api_runtime_image_inspect_after_pip_min_pin.log`, `277_api_runtime_image_smoke_after_pip_min_pin.log` |
| Multi-stage API runtime OS hardening rebuild | PASS | `291_api_runtime_image_build_after_multistage_os_hardening.log`, `292_api_runtime_image_inspect_after_multistage_os_hardening.log`, `293_api_runtime_image_smoke_after_multistage_os_hardening.log` |
| Fixed API runtime package inventory | PASS | `266_api_runtime_image_pip_list_after_dependency_audit_fix.json` |
| Final API runtime package inventory | PASS | `294_api_runtime_image_pip_list_after_multistage_os_hardening.json` |
| Fixed API runtime FastAPI/import smoke | PASS | `267_api_runtime_image_fastapi_testclient_after_dependency_audit_fix.log` |
| Fixed API runtime Python vulnerability audit | PASS | `268_api_runtime_image_pip_audit_after_dependency_audit_fix.json`, `268_api_runtime_image_pip_audit_after_dependency_audit_fix.log` |
| Final API runtime Python vulnerability audit | PASS | `295_api_runtime_image_pip_audit_after_multistage_os_hardening.json`, `295_api_runtime_image_pip_audit_after_multistage_os_hardening.log` |
| Dependency diff summary | PASS | `274_api_dependency_audit_json_summary.log` |
| Auth/security regression slice | PASS | `271_api_dependency_auth_security_regression.log` |
| FastAPI/API contract regression slice | PASS | `272_api_dependency_fastapi_contract_regression.log` |
| Lockfile consistency | PASS | `273_api_dependency_uv_lock_check.log` |
| Fresh static/source checks after dependency pinning | PASS | `269_api_dependency_py_compile.log`, `270_api_dependency_corpus_sync.log`, `271_api_dependency_forbidden_vocab.log`, `272_api_dependency_diff_check.log` |
| Fresh targeted backend/security regression after dependency pinning | PASS | `273_api_dependency_targeted_pytest.log` |
| Audit chain verification after dependency checks | PASS | `275_api_dependency_audit_chain_verify.log` |
| OS/base-image CVE scan | PARTIAL PASS | `289_api_runtime_image_trivy_scan_after_dependency_audit_fix.json`, `299_api_runtime_image_trivy_scan_after_multistage_os_hardening.json`, `300_api_runtime_image_trivy_scan_after_multistage_os_hardening_summary.log`, `301_api_runtime_image_trivy_scan_after_multistage_os_hardening_ignore_unfixed.json`, `302_api_runtime_image_trivy_scan_after_multistage_os_hardening_ignore_unfixed_summary.log` |

## What Changed

- Upgraded vulnerable runtime pins: `fastapi` to 0.136.1, `starlette` through FastAPI to 0.52.1, `PyJWT` to 2.12.1, `python-dotenv` to 1.2.2, `requests` to 2.33.1, `sentence-transformers` to 5.4.1, and `transformers` to 5.7.0.
- Removed `pytest` from main runtime dependencies and pinned it under the `dev` extra at 9.0.3.
- Moved the `pip`, `wheel`, and `setuptools` upgrade inside `/app/venv` in `Dockerfile.api`, so the runtime venv is audited with the upgraded installer toolchain.
- Made the runtime venv installer upgrade deterministic with `pip>=26.0` so the May 2 `pip==24.0` CVE closure is reproducible on rebuilds.
- Changed the API runner to a fresh `python:3.11-slim` stage that copies only the prepared venv and app files from the builder, patches system Python packaging tools for scanner visibility, and removes `curl` from the runtime healthcheck path.

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

The final exact-source image was built as
`nrg-api:dependency-audit-20260502-osfix`, digest
`sha256:f13496bb5dcf09ff6d40c3d912bd0cc4af5d56ce6ee902a400d8af55bd0f19e3`.
It runs as user `app`, imports `src.api.main`, exposes a FastAPI app, has
`pip==26.1` in `/app/venv`, and imports the upgraded FastAPI,
`sentence_transformers`, and `transformers` packages. `pip check` reports no
broken requirements. The smoke uses explicit HS256 test configuration and a
writable SQLite DB path because the production default expects mounted RSA keys
and runtime storage.

## Regression Checks

- `tests/auth/test_jwt_handler.py`, `tests/security/test_red_team_v41.py`, and
  `tests/api/test_query_security_validation.py`: 23 passed, 30 skipped.
- `tests/api/test_lifespan_startup.py`, `tests/api/test_new_endpoints.py`, and
  `tests/contract/test_api_response_schema.py`: 21 passed.
- `uv lock --check`: resolved successfully.
- Fresh static/source checks: API/routes `py_compile`, corpus sync,
  forbidden-vocabulary guard, and `git diff --check` all exited 0.
- Fresh targeted backend/security/API slice:
  `tests/api/test_health_endpoints.py`, `tests/api/test_auth_api.py`,
  `tests/api/test_query_security_validation.py`,
  `tests/api/test_tier_response_filtering.py`,
  `tests/auth/test_jwt_handler.py`,
  `tests/auth/test_jwt_secret_config.py`,
  `tests/security/test_pii_compliance.py`,
  `tests/security/test_audit_chain.py`, and
  `tests/orchestration/test_query_catalog.py`: 85 passed.
- Audit chain after the dependency checks: `(True, [], 282779)`.

## Remaining Boundary

This closes the API runtime Python package audit for the local image and closes
the actionable HIGH/CRITICAL Trivy gate for the local API image when unfixed
vendor CVEs are ignored. Full Trivy still reports Debian package CVEs with no
fixed version available: 7 HIGH, 39 MEDIUM, 64 LOW, and 2 UNKNOWN findings. Do
not claim a zero-CVE API OS image; claim only that the local image has zero
fixable HIGH/CRITICAL findings under Trivy. Deployed image scans still need to
run against the production registry/image digest.

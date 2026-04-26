# C4 Locust Contract Fix Evidence

Date: 2026-04-27
Scope: `tests/load/locustfile_c4.py`, dependency lock, and load-runner contract tests.

## Fixes Applied

- Added `locust>=2.32,<3` to the `dev` optional dependency group.
- Refreshed `uv.lock`; Locust resolves to `2.39.1`.
- Changed the C4 government credential default from `gov-pass` to `government-pass`.
- Added environment overrides for all three load personas:
  - `LOAD_TEST_RESEARCHER_USER` / `LOAD_TEST_RESEARCHER_PASS`
  - `LOAD_TEST_GOV_USER` / `LOAD_TEST_GOV_PASS`
  - `LOAD_TEST_INDUSTRY_USER` / `LOAD_TEST_INDUSTRY_PASS`
- Added shared query-response validation for all C4 query tasks.
- Added login failure handling that quits the Locust runner instead of continuing unauthenticated.

## Verification

```bash
PYTEST_ADDOPTS=--no-cov pytest tests/config/test_locustfile_contract.py -q
# 3 passed in 1.38s

uv lock
# Resolved 192 packages; added locust 2.39.1 and runtime dependencies

uv run --extra dev locust --version
# locust 2.39.1

PYTEST_ADDOPTS=--no-cov uv run --extra dev pytest tests/config/test_locustfile_contract.py -q
# 3 passed in 6.40s

uv run --extra dev python -m py_compile tests/load/locustfile_c4.py
# pass
```

## Result

The C4 load-runner contract is now reproducible from the locked dev environment, uses the current local credentials, and validates the actual API response shape (`sql_query`, `sql_results`, or answer payload) before marking a query successful.

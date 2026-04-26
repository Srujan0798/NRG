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
- Added login failure handling that never lets unauthenticated users continue into query tasks.
- Bad credentials (`401`/`403`) still stop the run; transient local connection failures stop only that Locust user with `StopUser`.

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

PYTEST_ADDOPTS=--no-cov .venv/bin/pytest tests/config/test_locustfile_contract.py -q
# 3 passed in 0.71s as part of the 40-test local release gate

PYTEST_ADDOPTS=--no-cov SLO_ENV=prod .venv/bin/pytest tests/load -m load -q --tb=short
# 17 passed in 32.51s
```

## Result

The C4 load-runner contract is now reproducible from the locked dev environment, uses the current local credentials, validates the actual API response shape (`sql_query`, `sql_results`, or answer payload), and stops unauthenticated users before they can issue query requests.

The sovereign 1000-user C4 SLO is still an infrastructure gate. A local MacBook run is not valid C4 evidence; it overloaded authentication and failed P99. The load profile is now fixed and ready to run on the Kubernetes/HPA environment.

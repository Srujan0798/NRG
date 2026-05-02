# Full Suite Live-Orchestration Summary

Date: 2026-05-02

## Problem

The broad Python suite was failing because two live API files were executed
inside the default `pytest tests/` path without a reachable API:

- `tests/api/test_tier_isolation_live.py`
- `tests/security/test_red_team_v41.py`

The first raw failure is preserved in
`195_full_pytest_after_dependency_gate.log`. The managed runner now separates
non-live tests from live API tests and starts a local uvicorn process only when
`--live-api` is requested.

## Changes

- `tests/conftest.py` marks the two live API files as `uat` and skips them by
  default when `/health/db` is not ready.
- `scripts/run_test_suite.sh --live-api` runs the non-live suite with xdist,
  then starts uvicorn and runs the live API files sequentially.
- The managed runner isolates non-live xdist audit writes under
  `EVIDENCE_DIR/audit_chain/{worker}` and live API writes under
  `EVIDENCE_DIR/live_api_audit`, preventing test evidence from mutating the
  active `.audit` chain.
- Live API readiness uses `/health/db` so optional audit/vector/root-health
  degradation does not misclassify database/API availability.
- `src/audit/__init__.py` now binds the per-user salt store to the active audit
  storage path, so audit singletons reset cleanly when tests change
  `NRG_AUDIT_DIR`.
- `tests/security/test_red_team_v41.py` accepts the production blocked
  answer-engine envelope for RT-20/RT-21 instead of requiring HTTP 4xx only.
- Live red-team request timeout is configurable and defaults to 60 seconds
  when `NRG_REQUIRE_LIVE_API=1`, covering cold embedding model load during the
  first allowed live query.
- `tests/api/test_query_security_validation.py` adds direct TestClient
  regressions for file-access and dependency-confusion prompts.

## Current Evidence

Latest current-code managed run:

- Command: `TEST_RUNTIME_MAX_SECONDS=600 PYTEST_CURRENT_TEST=1 scripts/run_test_suite.sh --live-api evidence/2026-05-02/guru_shishya_validation/full_suite_live_orchestration5`
- Log: `208_run_test_suite_live_api_key_store_fix.log`
- Non-live JUnit: `full_suite_live_orchestration5/test_suite_full_final.xml`
  - 1,830 tests, 0 failures, 0 errors, 56 skipped
  - Console summary: 1,774 passed, 56 skipped, 1 warning in 28.23s
- Live API JUnit: `full_suite_live_orchestration5/test_suite_live_api.xml`
  - 36 tests, 0 failures, 0 errors, 0 skipped
  - Console summary: 36 passed in 0.84s
- Runtime budget: passed, 33.0s under 300.0s limit
- Process cleanup: `217_no_leftover_port_8000_after_final_runner.log`
  confirms no TCP listener on port 8000 after runner exit.
- Audit chain final repair: `209_audit_chain_check_before_final_repair.log`
  found 92 tail per-user binding failures, `210_audit_chain_rebuild_preserve_lineage_final.log`
  rebuilt with lineage preservation, and `211_audit_chain_check_after_final_repair.log`
  reports `RESULT: Chain is VALID` with 282,701 events. `219_audit_chain_check_after_report_updates.log`
  rechecked the chain after report updates and also reports valid.

Supporting diagnostics:

- `196_live_tests_skip_without_api_after_guard.log` proves live tests skip when
  no API is reachable and `NRG_REQUIRE_LIVE_API` is not set.
- `197_live_tests_require_api_still_hard_fail.log` proves required-live mode
  still hard-fails when no API is available.
- `207_run_test_suite_live_api_current_after_audit_rebuild.log` preserved the
  cold live-query timeout that drove the red-team timeout fix.
- `202_live_api_supply_chain_recheck/` proves the RT-20/RT-21 live blocked
  envelope with an isolated valid audit chain.

## Boundary

The managed local Python suite is now green through
`scripts/run_test_suite.sh --live-api`. Raw `pytest tests/` without the managed
runner intentionally skips the two live API files when no API is reachable.

This closes the local full-suite orchestration blocker only. It does not close
external deployed-browser proof, sovereign cluster C4 replay, production Qdrant
baseline, founder signing, or remaining low/moderate frontend dependency risk.

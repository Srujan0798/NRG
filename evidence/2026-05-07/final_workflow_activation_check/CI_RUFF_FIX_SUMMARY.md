# CI Ruff Fix Summary

Date: 2026-05-07

## Problem

GitHub CI for the latest pushed commit exposed a real fixable failure in the
`lint` job. The local equivalent command reproduced it:

```bash
.venv/bin/ruff check src tests
```

Ruff reported one unused `TYPE_CHECKING` import in `src/api/main.py`.

## Fix

Removed the unused `NRGWorkflowType` import from `src/api/main.py`. Runtime code
still uses the lazy `NRGWorkflow()` wrapper near the bottom of the file, so this
change only removes a dead type-checking import.

## Verification

| Check | Status | Evidence |
|---|---:|---|
| Ruff before fix | FAIL reproduced | `local_ruff_check_before_fix.log` |
| Ruff after fix | PASS | `local_ruff_check_after_fix.log` |
| API + external gate focused tests | PASS | `api_and_gate_tests_after_ruff_fix.log` reports 162 passed, 1 deselected |
| Frontend Batch 2 command | PASS | `frontend_build_test_after_ruff_fix.log` reports build success and 32/32 Jest suites passing |
| Batch 5 orchestration/skills command | PASS | `orchestration_skills_after_ruff_fix.log` reports 419 passed, 6 skipped |
| Python compile | PASS | `pycompile_after_ruff_fix.log` |

## Remote Follow-Up

After this fix is pushed, watch the new GitHub CI run and record its status.

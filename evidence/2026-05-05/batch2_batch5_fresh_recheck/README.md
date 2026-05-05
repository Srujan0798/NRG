# Batch 2 / Batch 5 Fresh Recheck

Date: 2026-05-05

## Summary

This pass preserves the fresh recheck requested after the final local closure work.
It does not change product code.

## Results

| Surface | Command | Result | Evidence |
| --- | --- | --- | --- |
| Frontend production build | `cd frontend && npm run build` | PASS | `frontend_build.log` |
| Orchestration / skills regression | `.venv/bin/python -m pytest tests/orchestration/ tests/skills/ -q --tb=short --no-cov -x -p no:rerunfailures` | PASS: 419 passed, 6 skipped, 35 deselected | `batch5_orchestration_skills_pytest.log` |
| Tier 1 query JSON | local query capture for `top AI funding institutions` | PASS: audit ID, citations, SQL, rows | `../09_tier1_query_response.json` |
| Tier 2 query JSON | local query capture for `top AI funding institutions` | PASS: audit ID, citations, SQL, rows | `../10_tier2_query_response.json` |
| Tier 3 query JSON | local query capture for `top AI funding institutions` | PASS: audit ID, citations, aggregate rows, SQL withheld | `../11_tier3_query_response.json` |
| Tier 1 PII/security block JSON | local query capture for restricted contact-data request | PASS: blocked with audit ID and no rows | `../09_tier1_pii_injection_response.json` |

## Notes

- The orchestration / skills run disables the `pytest-rerunfailures` plugin for this local recheck because the plugin attempted to bind a localhost status socket and failed with `PermissionError` in this shell.
- The same test slice passed after disabling only that plugin; all selected project tests still executed.
- External deployed-browser, production API/Qdrant, cluster-load, remote history, credential-rotation, and founder-signature gates remain outside this local recheck.

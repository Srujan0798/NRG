# Local API Health After Lazy Workflow

Generated: 2026-05-06 22:05 IST

## Command

`curl -sS -m 90 -o evidence/2026-05-06/runtime_recovery/health_8001_after_lazy_workflow.json http://127.0.0.1:8001/health`

## Result

- Status: `unhealthy`
- Healthy: `false`
- Database: `healthy`
- Data quality: `healthy`
- Audit: `timeout` after 10.00s
- Qdrant vector health: `unavailable`, timed out after 5.00s
- Vector drift: `unhealthy`, alert level `CRITICAL`
- RAG: `degraded`

## Impact

The live C4 scorecard must not run against this target because
`scripts/quality_bar_scorecard.py` now requires a healthy NRG `/health`
response before launching Locust. The remaining C4 closure requires a healthy
API target first, then `NRG_C4_REQUIRE_LIVE=1`.

## Verification

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -o addopts="" tests/api/test_health_endpoints.py::test_root_health_times_out_slow_vector_drift_check tests/api/test_health_endpoints.py::test_root_health_times_out_slow_qdrant_check tests/api/test_health_endpoints.py::test_query_result_cache_ttl_is_long_enough_for_load_review -q --tb=short`: 3 passed
- `git diff --cached --check`: PASS
- `bash scripts/forbidden_vocab_check.sh --all`: PASS

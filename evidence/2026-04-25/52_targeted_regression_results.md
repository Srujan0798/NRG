# Targeted Regression Results

Date: 2026-04-25

Command:

```bash
.venv/bin/python -m pytest \
  tests/api/test_tier_response_filtering.py \
  tests/integration/test_schema_completeness.py::TestProductionMigrationParity \
  tests/scripts/test_red_team_replay_script.py \
  tests/api/test_query_security_validation.py \
  tests/api/test_metrics_fast_path.py \
  tests/api/test_researchers_endpoint_limits.py \
  tests/scripts/test_vector_drift_scheduler.py \
  tests/scripts/test_insert_test_data_qdrant.py \
  tests/skills/test_text_to_sql_semantic_anomaly.py \
  -q --no-cov
```

Result:

```text
33 passed in 105.01s (0:01:45)
```

Coverage intentionally disabled for this focused run because the local `.coverage` database was already dirty/corrupt during earlier targeted test execution.

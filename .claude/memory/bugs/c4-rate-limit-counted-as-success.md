# C4 Rate Limit Counted As Success

## What Went Wrong

The maintained C4 Locust workload counted HTTP 429 responses as successful requests. That could let a 1000-user load run report zero failures even when the API was rate-limiting traffic.

The same report also collapsed researcher, government, and adversarial `/query` traffic under one metric name, hiding which workload produced failures or high P99 latency.

## Root Cause

The C4 test treated blocked adversarial requests and rate-limited requests as the same kind of acceptable outcome. For security probes, `400`, `401`, `403`, and `422` can be valid blocked responses. For C4 load, `429` is capacity failure evidence and must fail the request.

The scorecard also relied on aggregate Locust metrics, so workload-specific regressions were not visible in the quality-bar JSON.

## Fix Applied

- `tests/load/locustfile_c4.py` now fails HTTP 429 with `HTTP 429 rate limited`.
- Query tasks now report as `/query::researcher`, `/query::government`, and `/query::adversarial`.
- `scripts/quality_bar_scorecard.py` extracts per-workload request count, failure count, failure rate, and P99 from the Locust HTML report.
- Regression contracts in `tests/config/test_locustfile_contract.py` and `tests/scripts/test_quality_bar_scorecard.py` lock this behavior.

## Prevention Check

Before using a C4 run as evidence, verify both aggregate and per-workload metrics:

```bash
PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest \
  tests/scripts/test_quality_bar_scorecard.py \
  tests/config/test_locustfile_contract.py -q
```

Do not claim C4 compliance if any workload reports 429 responses, nonzero failures, or P99 above the C4 threshold.

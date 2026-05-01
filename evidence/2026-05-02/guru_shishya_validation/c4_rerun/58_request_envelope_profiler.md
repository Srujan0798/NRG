# Request Envelope Profiler

Date: 2026-05-02

## Why

The C4 stage profile showed the Python query-body path is much faster than Locust client-side P99. To close that measurement gap, the API now has an opt-in request-envelope profiler around `RequestLoggingMiddleware`.

## What Changed

Set:

```bash
NRG_REQUEST_ENVELOPE_PROFILE=1
NRG_REQUEST_ENVELOPE_PROFILE_FILE=evidence/.../request_envelope.jsonl
```

Each request appends JSONL with timestamp, request ID, method, path, status, duration in milliseconds, response content length, and client IP.

This complements `NRG_QUERY_STAGE_PROFILE`. The next C4 run can compare request-envelope time against query-stage time to isolate middleware, serialization, compression, socket, or local load-generator contention.

## Verification

| Command | Result |
| --- | --- |
| `PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/api/test_request_logging_middleware.py tests/scripts/test_quality_bar_scorecard.py tests/config/test_locustfile_contract.py -q` | 19 passed, 1 warning |
| `.venv/bin/python -m compileall src/api/main.py scripts/quality_bar_scorecard.py tests/load/locustfile_c4.py tests/api/test_request_logging_middleware.py tests/scripts/test_quality_bar_scorecard.py tests/config/test_locustfile_contract.py` | passed |

The warning is the existing duplicate FastAPI operation ID warning for `metrics_metrics_get`.

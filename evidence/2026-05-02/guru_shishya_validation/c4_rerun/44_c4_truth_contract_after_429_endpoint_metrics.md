# C4 Truth Contract After 429 and Endpoint-Metric Fix

Date: 2026-05-02

Status: contract PASS. C4 1000-user bar remains FAIL until a fresh load run passes measured P99 and zero-failure criteria.

## Repo Skills Used

- `.claude/skills/performance`
- `.claude/skills/test-suite`
- `.claude/skills/pre-commit`
- `.agents/skills/systematic-debugging`
- `.agents/skills/test-driven-development`
- `.agents/skills/verification-before-completion`

## Fix Scope

- `tests/load/locustfile_c4.py` now treats HTTP 429 as a failed C4 request.
- Query metrics are split into `/query::researcher`, `/query::government`, and `/query::adversarial`.
- `scripts/quality_bar_scorecard.py` now extracts per-workload request count, failure count, failure rate, and P99 from the Locust HTML report.
- Regression tests lock both the Locust workload contract and scorecard parser contract.

## Verification

| Command | Result |
| --- | --- |
| `PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/scripts/test_quality_bar_scorecard.py::test_c4_scorecard_reads_per_endpoint_metrics_from_locust_report tests/config/test_locustfile_contract.py::test_c4_locustfile_treats_429_as_failure tests/config/test_locustfile_contract.py::test_c4_locustfile_names_query_metrics_by_workload -q` | 3 passed |
| `PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/scripts/test_quality_bar_scorecard.py tests/config/test_locustfile_contract.py -q` | 16 passed |
| `.venv/bin/python -m compileall scripts/quality_bar_scorecard.py tests/load/locustfile_c4.py tests/scripts/test_quality_bar_scorecard.py tests/config/test_locustfile_contract.py` | passed |
| `git diff --check` | passed |
| `bash scripts/forbidden_vocab_check.sh --all` | passed |

## Live Report Reparse

The background 4-worker diagnostic run completed after this contract change:

- Log: `47_quality_bar_scorecard_60s_profile_4workers.log`
- Scorecard JSON snapshot: `48_quality_bar_scorecard_60s_profile_4workers.json`
- Locust report: `49_locust_report_60s_profile_4workers.html`

Current parser reparse of the Locust HTML reports:

| Metric | Value |
| --- | ---: |
| Aggregate samples | 37,174 |
| Aggregate failures | 0 |
| Aggregate failure rate | 0.0 |
| Aggregate P99 | 3,100 ms |
| `/query::researcher` | 25,923 requests, 0 failures, P99 2,700 ms |
| `/query::government` | 8,999 requests, 0 failures, P99 3,000 ms |
| `/query::adversarial` | 1,772 requests, 0 failures, P99 6,400 ms |

This confirms the stricter contract gives workload-level diagnosis. It also confirms C4 is still failed: aggregate P99 and every query workload P99 exceed 500 ms.

## Claim Boundary

This closes a load-test truth gap. It does not close C4 performance.

Next valid C4 evidence must run the corrected scorecard/Locust pair and inspect aggregate plus per-workload metrics. Any 429 response is a failure, not an acceptable blocked request.

# C4 Harness Fix Summary

Date: 2026-05-07

## Root Cause

The query handler was not the p99 bottleneck. Sampled cache-hit requests inside
`QueryAnswerService` completed mostly under 1 ms, while Locust reported
multi-second p99 latency. The bottleneck was the C4 load client and wait profile:
`HttpUser` plus a sub-second think-time profile drove 600-900+ RPS on the local
machine, above the locustfile's documented 100+ RPS target.

## Fix

- Switched `tests/load/locustfile_c4.py` to Locust `FastHttpUser`.
- Removed the preissued-token `user.client.headers.update(...)` call because
  `FastHttpSession` does not expose that attribute and tasks already pass
  `headers=self.headers`.
- Set default C4 think time to the documented throughput profile:
  - fast path: 4-10 seconds
  - full path: 6-14 seconds
  - adversarial path: 6-14 seconds
- Updated scorecard wait-profile metadata and tests.

## Verification

| Command | Result |
|---------|--------|
| `.venv/bin/python -m pytest tests/config/test_locustfile_contract.py tests/scripts/test_quality_bar_scorecard.py -q --tb=short --no-cov` | PASS, 26 passed |
| `NRG_C4_API_BASE_URL=http://127.0.0.1:8001 NRG_C4_REQUIRE_LIVE=1 NRG_C4_LOCUST_RUN_TIME=1m NRG_C4_LOCUST_PROCESSES=4 .venv/bin/python scripts/quality_bar_scorecard.py --json-only` | PASS, 6/6 |

Latest C4 metrics from `scripts/quality_bar_scorecard.json`:

- requested users: 1000
- Locust processes: 4
- run time: 1m
- p99: 200 ms
- threshold: 500 ms
- failure rate: 0.0%
- samples: 7,436
- aggregate throughput: 123.83 RPS

## Remaining External Gates

- Deployed staging URL: BLOCKED, no target URL recorded.
- Cluster C4: BLOCKED, no Kubernetes context available on this machine.
- Founder GPG signing: BLOCKED, no founder private key or signing ceremony.
- Credential rotation/security closure: BLOCKED until exposed historical
  credentials are rotated.

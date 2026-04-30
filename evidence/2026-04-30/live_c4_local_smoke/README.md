# Live Local C4-Style Load Smoke

Date: 2026-04-30

This is a bounded local live-stack load run. It is useful stability evidence, but it is not the missing sovereign-cluster 1000-user C4 proof.

## Command

```bash
C4_FAST_WAIT_MIN_SECONDS=0.05 C4_FAST_WAIT_MAX_SECONDS=0.2 \
C4_FULL_WAIT_MIN_SECONDS=0.1 C4_FULL_WAIT_MAX_SECONDS=0.3 \
C4_ADVERSARIAL_WAIT_MIN_SECONDS=0.1 C4_ADVERSARIAL_WAIT_MAX_SECONDS=0.3 \
.venv/bin/python -m locust -f tests/load/locustfile_c4.py \
  --headless \
  --users 100 \
  --spawn-rate 20 \
  --run-time 60s \
  --host http://127.0.0.1:8020 \
  --csv evidence/2026-04-30/live_c4_local_smoke/locust \
  --html evidence/2026-04-30/live_c4_local_smoke/locust_report.html \
  --logfile evidence/2026-04-30/live_c4_local_smoke/locust.log
```

## Result

| Endpoint | Requests | Failures | Median | P95 | P99 | Max |
|----------|----------|----------|--------|-----|-----|-----|
| `/auth/login` | 100 | 0 | 890ms | 1200ms | 1200ms | 1199ms |
| `/query` | 3348 | 0 | 1600ms | 2300ms | 2700ms | 2923ms |
| `/stats` | 154 | 0 | 920ms | 1500ms | 1700ms | 1828ms |
| Aggregated | 3602 | 0 | 1600ms | 2200ms | 2600ms | 2923ms |

Locust event distribution printed at stop:

- Total samples: 3621
- Mean: 1405.3ms
- P50: 1556.4ms
- P95: 2248.1ms
- P99: 2640.4ms
- Max: 2923.4ms

Status: local stability passed with zero HTTP failures, strict C4 latency failed because P99 is above the 500ms target.

## Evidence Files

- `health_before.json`
- `health_after.json`
- `locust_stats.csv`
- `locust_stats_history.csv`
- `locust_failures.csv`
- `locust_exceptions.csv`
- `locust_report.html`
- `locust.log`

## Audit Verification

Post-run command:

```bash
.venv/bin/python scripts/audit_investigate.py
```

Result:

```json
{
  "ok": true,
  "events_checked": 39036,
  "broken_indices": []
}
```

## Interpretation

The system stayed alive under 100 local Locust users for 60 seconds and served thousands of requests without HTTP failures or Locust exceptions. The strict C4 blocker remains open: this local Mac run did not achieve sub-500ms P99, and it is not the official 1000-user cluster proof.

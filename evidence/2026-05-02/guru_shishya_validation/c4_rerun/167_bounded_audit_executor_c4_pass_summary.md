# Bounded Audit Executor C4 Pass Summary

Date: 2026-05-02

## Change

Request-path audit appends now use a bounded dedicated executor through
`src/audit/async_append.py`. The default is one audit append worker per API
process, controlled by `NRG_AUDIT_APPEND_WORKERS`.

This preserves the synchronous audit-chain contract: `/query` still waits for
the audit append and returns the real chain hash as `audit_event_id`. The fix
removes audit writes from the general API blocking pool, preventing concurrent
adversarial/query audit work from starving unrelated blocking work.

## Valid Run

Mode: local capacity C4 with `NRG_QUOTA_DISABLED=1`.

Topology:

- API: 4 uvicorn workers
- Event loop/http: `uvloop` + `httptools`
- Locust: 4 processes
- Users: 1000
- Spawn rate: 100/s
- Runtime: 60s

Evidence:

| File | Result |
| --- | --- |
| `163_c4_prewarm_4workers_bounded_audit_executor.json` | 312/312 prewarm requests succeeded; 60 expected blocked envelopes; 0 missing audit IDs. |
| `165_quality_bar_scorecard_60s_4workers_bounded_audit_executor.json` | Quality Bar `6/6`; C4 PASS. |
| `166_locust_report_60s_4workers_bounded_audit_executor.html` | Locust report for the passing run. |

Metrics from `165_quality_bar_scorecard_60s_4workers_bounded_audit_executor.json`:

| Metric | Value |
| --- | ---: |
| Aggregate P99 | 79 ms |
| C4 threshold | 500 ms |
| Failure rate | 0.0 |
| Total samples | 82,365 |
| Researcher P99 | 64 ms |
| Government P99 | 80 ms |
| Adversarial P99 | 170 ms |

## Boundaries

This closes the local quota-neutral C4 capacity gate for the current checkout.
It does not close external production gates: deployed browser replay, production
Qdrant/vector baseline, cluster-context replay, dependency audit remediation,
and founder GPG signing still need their own evidence.

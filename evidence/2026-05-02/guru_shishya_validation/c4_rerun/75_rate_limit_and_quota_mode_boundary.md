# C4 Rate-Limit and Quota-Mode Boundary

Date: 2026-05-02

## Finding

Now that HTTP 429 is counted as failure, the current 3-persona C4 workload exposes a policy mismatch:

- Production `/query` endpoint limit is 10 requests/minute per user.
- C4 Locust uses three preissued personas.
- A 1000-user load run against those three identities can produce rate-limit failures before it measures true query capacity.

## Evidence

| Run | Evidence | Result |
| --- | --- | --- |
| Strict 429/envelope run | `61_quality_bar_scorecard_60s_envelope_4workers.json`, `62_locust_report_60s_envelope_4workers.html` | 3,590 samples, 3,119 failures, aggregate P99 39,000 ms. Error report dominated by HTTP 429. |
| Invalid quota-neutral attempt | `63_host_uvicorn_quota_neutral_4workers.log`, `65_quality_bar_scorecard_60s_quota_neutral_4workers.json` | Invalid: port 8000 was already occupied, so the quota-disabled server did not bind. |
| Clean quota-neutral run | `69_quality_bar_scorecard_60s_quota_neutral_4workers.json`, `70_locust_report_60s_quota_neutral_4workers.html` | 31,642 samples, 47.86% HTTP 0 failures, aggregate P99 6200 ms. API envelope recorded 11,001 handled requests, all HTTP 200. |
| Post critical-section run | `72_quality_bar_scorecard_60s_after_critical_section.json`, `73_locust_report_60s_after_critical_section.html` | 29,168 samples, 0 failures, aggregate P99 3000 ms. Still fails C4. |

## Boundary

C4 has two separate modes and evidence must name which one is being used:

- **Quota-on C4** requires enough distinct load identities to avoid testing the per-user quota instead of query capacity.
- **Quota-neutral C4** must explicitly set and document `NRG_QUOTA_DISABLED=1`; it is a capacity diagnostic, not a production quota-policy proof.

No C4 run is a pass until failure rate is 0 and aggregate plus per-workload P99 are below 500 ms.

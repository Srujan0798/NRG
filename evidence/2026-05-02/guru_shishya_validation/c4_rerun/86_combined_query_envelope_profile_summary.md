# Combined C4 Query-Stage and Request-Envelope Profile

- Query-stage profile: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/81_query_stage_profile_with_envelope.jsonl`
- Request-envelope profile: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/81_request_envelope_profile.jsonl`
- Locust report: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/85_locust_report_60s_with_envelope.html`

## Locust Metrics

- Aggregate P99: 1000.0 ms; threshold: 500.0 ms
- Aggregate failure rate: 0.0
- Total samples: 43075
- /query::adversarial: requests=3140, failures=0, p99=1000.0 ms
- /query::government: requests=10257, failures=0, p99=1000.0 ms
- /query::researcher: requests=28834, failures=0, p99=1000.0 ms

## Distribution Comparison

| Segment | Count | Avg ms | P50 | P90 | P95 | P99 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| query-stage sampled handler total | 7996 | 1.33 | 0.477 | 0.847 | 1.011 | 1.589 | 293.131 |
| request-envelope /query | 39676 | 264.009 | 276.985 | 415.198 | 462.002 | 538.303 | 760.275 |
| request-envelope non-query | 853 | 120.908 | 121.304 | 195.727 | 236.543 | 288.719 | 440.325 |

## Query-Stage Breakdown

- Sampled records: 7996
- Routes: {'c4_read_model': 41, 'cache': 7955}
- Cache split: {'miss': 20, 'hit': 7976}

| Stage | Count | Avg ms | P50 | P90 | P95 | P99 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| c4_singleflight | 41 | 85.87 | 24.313 | 284.916 | 288.586 | 292.797 | 292.797 |
| audit_append | 20 | 126.353 | 121.869 | 214.076 | 214.892 | 271.851 | 271.851 |
| c4_read_model | 20 | 4.894 | 4.825 | 7.716 | 7.969 | 18.755 | 18.755 |
| tier_filter | 20 | 9.919 | 9.218 | 14.614 | 14.795 | 15.231 | 15.231 |
| consent_check | 7996 | 0.177 | 0.106 | 0.373 | 0.511 | 0.905 | 9.888 |
| prompt_sanitizer | 7996 | 0.312 | 0.282 | 0.459 | 0.539 | 0.703 | 2.285 |
| normalize_and_redact | 20 | 0.145 | 0.128 | 0.161 | 0.253 | 0.382 | 0.382 |
| cache_lookup | 7996 | 0.023 | 0.019 | 0.038 | 0.046 | 0.092 | 0.573 |
| rate_limit_and_tier_guard | 7996 | 0.019 | 0.016 | 0.026 | 0.035 | 0.087 | 0.357 |
| answer_record_schedule | 20 | 0.014 | 0.014 | 0.017 | 0.019 | 0.021 | 0.021 |

## Request Envelope Breakdown

- Envelope records: 40529
- Paths: {'/auth/login': 3, '/stats': 850, '/query': 39676}
- Statuses: {'200': 40529}

| Path | Count | Avg ms | P50 | P90 | P95 | P99 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| /auth/login | 3 | 21.734 | 22.827 | 26.956 | 26.956 | 26.956 | 26.956 |
| /query | 39676 | 264.009 | 276.985 | 415.198 | 462.002 | 538.303 | 760.275 |
| /stats | 850 | 121.258 | 121.343 | 195.727 | 236.543 | 288.719 | 440.325 |

## Interpretation

- C4 still fails the 500 ms P99 target.
- Server request-envelope `/query` P99 is 538 ms while Locust client-observed aggregate P99 is 1000 ms, so both server request lifecycle and client/transport scheduling contribute to the remaining tail.
- Sampled handler-stage P99 is much lower than full envelope P99 because the query-stage sampler records route-level work after request admission; envelope profiling shows the full ASGI request lifecycle is the active boundary to optimize under 1000-user pressure.
- Next code-level work should target bounded concurrency/backpressure and declared prewarm semantics, not more parser fixes.

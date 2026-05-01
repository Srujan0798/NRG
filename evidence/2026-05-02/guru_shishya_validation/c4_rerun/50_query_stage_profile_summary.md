# C4 Query Stage Profile Summary

- Profile file: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/45_query_stage_profile_4workers.jsonl`
- Locust report: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/49_locust_report_60s_profile_4workers.html`
- Sampled `/query` requests: 7179
- Routes: {'c4_read_model': 32, 'cache': 7147}
- Cache split: {'miss': 13, 'hit': 7166}
- Outcomes: {'success': 7179}

## Locust C4 Metrics

- Aggregate P99: 3100.0 ms, threshold: 500.0 ms
- Aggregate failure rate: 0.0
- Total samples: 37174
- /query::adversarial: requests=1772, failures=0, p99=6400.0 ms
- /query::government: requests=8999, failures=0, p99=3000.0 ms
- /query::researcher: requests=25923, failures=0, p99=2700.0 ms

## Total Latency

| Segment | Count | Avg ms | P50 | P90 | P95 | P99 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| all | 7179 | 1.322 | 0.415 | 0.918 | 1.23 | 4.581 | 350.87 |
| c4_read_model | 32 | 166.674 | 160.105 | 293.204 | 350.346 | 350.87 | 350.87 |
| cache | 7147 | 0.582 | 0.414 | 0.905 | 1.173 | 3.306 | 72.332 |
| cache_hit | 7166 | 1.013 | 0.415 | 0.912 | 1.203 | 3.949 | 350.87 |
| cache_miss | 13 | 171.46 | 171.293 | 255.853 | 293.204 | 293.204 | 293.204 |

## Stage Latency Hotspots

| Stage | Count | Avg ms | P50 | P90 | P95 | P99 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| c4_singleflight | 32 | 96.881 | 58.756 | 291.204 | 350.197 | 350.705 | 350.705 |
| audit_append | 13 | 158.031 | 157.196 | 242.191 | 275.828 | 275.828 | 275.828 |
| tier_filter | 13 | 9.304 | 8.937 | 13.533 | 14.768 | 14.768 | 14.768 |
| c4_read_model | 13 | 3.637 | 3.507 | 6.717 | 7.395 | 7.395 | 7.395 |
| prompt_sanitizer | 7179 | 0.321 | 0.238 | 0.499 | 0.635 | 1.574 | 16.063 |
| consent_check | 7179 | 0.206 | 0.1 | 0.341 | 0.503 | 1.445 | 68.869 |
| normalize_and_redact | 13 | 0.18 | 0.115 | 0.407 | 0.696 | 0.696 | 0.696 |
| cache_lookup | 7179 | 0.025 | 0.016 | 0.04 | 0.051 | 0.124 | 4.904 |
| rate_limit_and_tier_guard | 7179 | 0.022 | 0.013 | 0.031 | 0.044 | 0.115 | 4.137 |
| answer_record_schedule | 13 | 0.014 | 0.013 | 0.02 | 0.026 | 0.026 | 0.026 |

## Interpretation

- C4 remains failed because aggregate and per-endpoint P99 exceed the 500 ms target under 1000 users.
- The sampled application profile shows cache-hit requests are sub-millisecond, while cache-miss and adversarial requests carry the long tail.
- `audit_append` is the dominant sampled application-stage hotspot on cold/cache-miss fast-path requests. The next engineering step is an audit-write hot-path optimization that preserves HMAC/non-repudiation semantics, not a UI or parser change.

# C4 Query Stage Profile Summary After Audit Tail Cache

- Profile file: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/61_query_stage_profile_after_audit_tail_cache.jsonl`
- Locust report: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/65_locust_report_60s_after_audit_tail_cache.html`
- Sampled `/query` requests: 1116
- Routes: {'c4_read_model': 42, 'cache': 1074}
- Cache split: {'miss': 17, 'hit': 1099}
- Outcomes: {'success': 1116}

## Locust C4 Metrics

- Aggregate P99: 35000.0 ms, threshold: 500.0 ms
- Aggregate failure rate: 0.002317497103128621
- Total samples: 2589
- /query::adversarial: requests=478, failures=5, p99=19000.0 ms
- /query::government: requests=656, failures=0, p99=35000.0 ms
- /query::researcher: requests=1353, failures=0, p99=35000.0 ms

## Total Latency

| Segment | Count | Avg ms | P50 | P90 | P95 | P99 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| all | 1116 | 87.076 | 0.874 | 5.454 | 22.632 | 1874.337 | 6415.954 |
| c4_read_model | 42 | 2245.671 | 1414.813 | 5568.491 | 6082.072 | 6415.954 | 6415.954 |
| cache | 1074 | 2.662 | 0.856 | 3.395 | 6.954 | 28.902 | 288.759 |
| cache_hit | 1099 | 49.469 | 0.868 | 4.348 | 11.126 | 1497.965 | 6415.954 |
| cache_miss | 17 | 2518.247 | 1556.758 | 6082.072 | 6401.519 | 6401.519 | 6401.519 |

## Stage Latency Hotspots

| Stage | Count | Avg ms | P50 | P90 | P95 | P99 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| c4_singleflight | 42 | 1225.662 | 943.31 | 2158.504 | 5463.838 | 6415.466 | 6415.466 |
| c4_read_model | 17 | 1278.565 | 380.381 | 5391.358 | 5423.914 | 5423.914 | 5423.914 |
| audit_append | 17 | 1156.869 | 656.167 | 4534.066 | 5166.012 | 5166.012 | 5166.012 |
| tier_filter | 17 | 73.907 | 65.379 | 126.797 | 145.002 | 145.002 | 145.002 |
| normalize_and_redact | 17 | 2.893 | 0.337 | 6.606 | 32.588 | 32.588 | 32.588 |
| answer_record_schedule | 17 | 1.169 | 0.043 | 1.06 | 17.947 | 17.947 | 17.947 |
| consent_check | 1116 | 0.869 | 0.218 | 0.874 | 2.745 | 14.012 | 74.982 |
| prompt_sanitizer | 1116 | 1.247 | 0.501 | 1.481 | 2.751 | 12.176 | 175.44 |
| cache_lookup | 1116 | 0.208 | 0.034 | 0.082 | 0.2 | 4.293 | 53.836 |
| rate_limit_and_tier_guard | 1116 | 0.275 | 0.03 | 0.057 | 0.143 | 3.546 | 69.657 |

## Interpretation

- C4 remains failed because aggregate and per-endpoint P99 exceed 500 ms.
- The same-process audit tail cache reduced direct tail rereads and preserved audit-chain verification tests, but this local C4 run still shows load-level queueing above the target.
- Sampled cold-path `audit_append` remains material, so a larger audit write redesign may be needed if C4 must audit every cold query synchronously on a single JSONL chain.

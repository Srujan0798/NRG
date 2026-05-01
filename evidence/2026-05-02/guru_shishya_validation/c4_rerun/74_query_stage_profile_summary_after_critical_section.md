# C4 Query Stage Profile Summary After Audit Critical-Section Reduction

- Profile file: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/69_query_stage_profile_after_critical_section.jsonl`
- Locust report: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/73_locust_report_60s_after_critical_section.html`
- Sampled `/query` requests: 6267
- Routes: {'c4_read_model': 185, 'cache': 6082}
- Cache split: {'hit': 6250, 'miss': 17}
- Outcomes: {'success': 6267}

## Locust C4 Metrics

- Aggregate P99: 3000.0 ms, threshold: 500.0 ms
- Aggregate failure rate: 0.0
- Total samples: 29168
- /query::adversarial: requests=2148, failures=0, p99=2900.0 ms
- /query::government: requests=7174, failures=0, p99=3000.0 ms
- /query::researcher: requests=19272, failures=0, p99=3000.0 ms

## Total Latency

| Segment | Count | Avg ms | P50 | P90 | P95 | P99 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| all | 6267 | 50.093 | 0.667 | 1.263 | 2.235 | 1858.818 | 3367.722 |
| c4_read_model | 185 | 1669.577 | 1612.294 | 2665.974 | 2974.199 | 3299.435 | 3367.722 |
| cache | 6082 | 0.832 | 0.656 | 1.131 | 1.475 | 3.272 | 97.529 |
| cache_hit | 6250 | 44.652 | 0.666 | 1.243 | 2.146 | 1762.672 | 3367.722 |
| cache_miss | 17 | 2050.51 | 2053.847 | 2665.974 | 2827.928 | 2827.928 | 2827.928 |

## Stage Latency Hotspots

| Stage | Count | Avg ms | P50 | P90 | P95 | P99 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| c4_singleflight | 185 | 1480.754 | 1473.495 | 2537.396 | 2973.676 | 3299.081 | 3367.524 |
| audit_append | 17 | 2018.229 | 2009.172 | 2629.071 | 2792.039 | 2792.039 | 2792.039 |
| tier_filter | 17 | 27.92 | 27.417 | 42.792 | 43.492 | 43.492 | 43.492 |
| c4_read_model | 17 | 3.73 | 3.176 | 6.541 | 7.212 | 7.212 | 7.212 |
| consent_check | 6267 | 0.264 | 0.154 | 0.418 | 0.609 | 1.849 | 96.831 |
| prompt_sanitizer | 6267 | 0.481 | 0.394 | 0.642 | 0.768 | 1.726 | 89.134 |
| normalize_and_redact | 17 | 0.254 | 0.205 | 0.435 | 0.452 | 0.452 | 0.452 |
| cache_lookup | 6267 | 0.035 | 0.026 | 0.05 | 0.064 | 0.14 | 6.065 |
| rate_limit_and_tier_guard | 6267 | 0.028 | 0.021 | 0.037 | 0.054 | 0.12 | 3.33 |
| answer_record_schedule | 17 | 0.028 | 0.023 | 0.047 | 0.053 | 0.053 | 0.053 |

## Interpretation

- C4 remains failed because aggregate and per-endpoint P99 exceed 500 ms.
- The audit append critical-section reduction preserves audit safety and improves the sampled cold-path profile compared with the immediately previous unhealthy run, but it does not close C4.
- The remaining local C4 bottleneck is broader queueing under 1000 users plus cold read-model/singleflight bursts; the next serious options are explicit multi-worker prewarm semantics or a larger audit writer redesign.

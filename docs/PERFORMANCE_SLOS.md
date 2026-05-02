# NRG Performance SLOs — The Performance Contract

> **Every promise we make to users is a debt we owe. SLOs are that debt, made measurable.**

This document defines NRG's Service Level Objectives — the quantitative contract between the platform and its users. These targets are verified automatically, reported weekly, and enforced in CI/CD.

---

## 1. Query Latency SLO

### Targets
| Percentile | Target | Rationale |
|------------|--------|-----------|
| **P50** (median) | < 3,000 ms | Typical user experience — half of all queries are faster |
| **P95** (worst normal) | < 8,000 ms | 95th percentile — acceptable for complex/hybrid queries |
| **P99** (tail) | < 15,000 ms | Absolute ceiling before timeout — never exceeded in normal operation |

### Measurement Methodology
- Measured from API request receipt to full response delivery (including synthesis)
- Collected via `nrg_query_duration_seconds` Prometheus histogram
- Buckets: `[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0, 60.0]`
- Computation: `pytest --hypothesis` with 10 sequential queries for baseline; continuous via Prometheus

### SLO Breach Thresholds
- P95 > 8s for 5 consecutive minutes → `CRITICAL` log
- P95 > 12s for 2 consecutive minutes → `WARNING` log
- P99 > 15s → always `CRITICAL`

---

## 2. Concurrency SLO

### Targets
| Scenario | Target | Graceful Degradation |
|----------|--------|---------------------|
| **Baseline** | 20 simultaneous queries | Up to 50 with queuing, beyond 50 return 503 |
| **Steady state** | 50 concurrent, no degradation | — |
| **Burst** | 100 concurrent, 10% degraded | Latency may increase, no 500s |

### Measurement Methodology
- `concurrent_queries_active` gauge updated at start/end of each request
- Peak observed concurrency tracked in `slo_tracker`
- Load test: `tests/load/test_slo_under_load.py` simulates 20 concurrent users × 5 queries each

### SLO Breach Thresholds
- Any 500 error under 50 concurrent users → `CRITICAL`
- Connection drops (connection refused/reset) → `CRITICAL`
- Queue depth > 20 sustained → `WARNING`

---

## 3. Uptime SLO

### Targets
| Tier | Target | Allowed Downtime/Month |
|------|--------|----------------------|
| **API** | 99.5% | 3.6 hours |
| **Health Check** | 99.9% | 43 minutes |
| **Qdrant** | 99.0% | 7.3 hours |

### Measurement Methodology
- Health check interval: 15 seconds (`/health` endpoint)
- Metrics scrape interval: 60 seconds (`/metrics` endpoint)
- Uptime tracked via `nrg_api_up` Prometheus gauge
- Alerts fire if 3 consecutive health checks fail

### SLO Breach Thresholds
- 3 consecutive `/health` failures → `CRITICAL`
- Database unreachable > 60s → `CRITICAL`
- Audit chain broken → `CRITICAL`

---

## 4. Vector Quality SLO

### Targets
| Metric | Target | Measurement |
|--------|--------|-------------|
| **Index Coverage** | 100% | `indexed_vectors_count == vectors_count` always |
| **Retrieval Relevance (NDCG@10)** | > 0.6 on benchmark | Weekly drift check script |
| **Drift Score** | > 0.85 | Overlap with known-good benchmark queries |
| **Search Latency** | < 100ms P95 | Qdrant internal metric |

### Measurement Methodology
- Qdrant HNSW index status checked in `/health/qdrant`
- Drift detection: 10 benchmark queries with known expected top-3 results
  - Run weekly via `scripts/vector_drift_check.py`
  - Compare current retrieval results against benchmark
  - If overlap (Jaccard) drops below 60% → drift flagged
- Benchmark queries stored in `scripts/vector_drift_check.py`

### SLO Breach Thresholds
- `indexed_vectors < vectors_count` → `CRITICAL` (index is incomplete)
- Drift score < 0.60 → `WARNING` + ticket created
- Drift score < 0.40 → `CRITICAL`

---

## 5. Synthesis Quality SLO

### Targets
| Metric | Target | Rationale |
|--------|--------|-----------|
| **Citation Rate** | > 80% | Every response should cite evidence |
| **Cloud LLM Success** | > 85% | Primary synthesis path |
| **Local LLM Fallback** | < 10% | Acceptable degradation |
| **Rule-Based Fallback** | < 5% | Last resort only |

### Measurement Methodology
- Citation rate: `%` of responses where `len(citations) > 0`
- Cascade distribution: tracked via `nrg_llm_fallback_total` counter + Prometheus
- Both tracked per-request via `SLOTracker` in metrics.py

### SLO Breach Thresholds
- Citation rate < 50% for 1 hour → `WARNING`
- Citation rate < 30% for 30 minutes → `CRITICAL`
- Rule-based fallback > 15% sustained → `WARNING`

---

## 6. Dashboard SLO Endpoint

### `/api/admin/slo` Response Shape
```json
{
  "timestamp": "2026-04-22T12:00:00Z",
  "report_period": "7d",
  "latency": {
    "p50_ms": 1800,
    "p95_ms": 4200,
    "p99_ms": 8100,
    "slo_met": true,
    "target_p95_ms": 8000
  },
  "concurrency": {
    "active": 3,
    "max_observed": 12,
    "target": 20,
    "slo_met": true
  },
  "synthesis": {
    "cloud_pct": 87,
    "local_pct": 8,
    "rule_pct": 5,
    "slo_met": true
  },
  "citations": {
    "rate": 0.82,
    "target": 0.80,
    "slo_met": true
  },
  "qdrant": {
    "drift_score": 0.91,
    "indexed_pct": 100.0,
    "slo_met": true
  },
  "uptime": {
    "api_uptime_pct": 99.9,
    "target": 99.5,
    "slo_met": true
  },
  "overall": "GREEN"
}
```

---

## 7. SLO Compliance Calculation

```
SLO Compliance % = (Time within SLO / Total Time) × 100

Example:
- 7-day period = 10,080 minutes
- P95 was above 8s for 220 minutes
- Compliance = (10,080 - 220) / 10,080 × 100 = 97.8%
```

### Compliance Tiers
| Compliance | Status | Action |
|------------|--------|--------|
| ≥ 99.0% | 🟢 GREEN | None |
| 95.0–99.0% | 🟡 AMBER | Review, add to weekly report |
| 90.0–95.0% | 🟠 ORANGE | Create incident ticket |
| < 90.0% | 🔴 RED | Immediate escalation |

---

## 8. Measurement & Verification

### Automated Verification
- **Every commit**: SLO compliance test via `tests/performance/test_slo_compliance.py`
- **Weekly**: Drift check via `scripts/vector_drift_check.py`
- **Weekly**: SLO report via `scripts/slo_report.py`
- **Continuous**: Prometheus metrics for all percentiles

### Prometheus Metrics Used
```
nrg_query_duration_seconds{quantile="0.5"}  → P50
nrg_query_duration_seconds{quantile="0.95"} → P95
nrg_query_duration_seconds{quantile="0.99"} → P99
nrg_queries_total                              → total queries
nrg_llm_fallback_total                         → cascade distribution
nrg_api_up                                     → uptime gauge
```

### Grafana Dashboard
Available at `infrastructure/monitoring/grafana-dashboard.json`

---

## 9. SLO Evolution

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-22 | Initial SLOs — P50<3s, P95<8s, P99<15s, 99.5% uptime |

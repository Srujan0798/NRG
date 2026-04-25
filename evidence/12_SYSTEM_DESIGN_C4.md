# System Design: C4 Load Test Architecture for Sovereign Deployments

**Date:** 2026-04-25
**Type:** Component Architecture Design
**Status:** Proposed

---

## Context

The C4 load test (skill: `performance`) needs to run in two distinct environments:
1. **Local development** — API running on localhost, Locust can hit it directly
2. **Sovereign cluster** — API inside a Kubernetes pod, external Locust runner needed

The current `scripts/run_load_test.py` and `tests/load/locustfile.py` work for local but not for sovereign.

---

## Requirements

| Environment | Runner | Target | Auth | Network Access |
|------------|--------|--------|------|---------------|
| Local | `locust -f locustfile.py` | `http://localhost:8000` | Direct | Loopback |
| Sovereign | Remote Locust or k6 | `http://api-service:8000` (K8s DNS) | Inject JWT via header | Cluster internal |
| CI/CD | `scripts/run_load_test.py` | Staging endpoint | Env var token | External |

---

## Design: Hybrid Load Testing Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ LOCAL / CI                                                  │
│                                                              │
│  scripts/run_load_test.py (orchestrator)                   │
│    1. GET /health/all → wait for healthy                   │
│    2. POST /auth/login → extract JWT                       │
│    3. Spawn locust workers OR use Python runner             │
│    4. Parse CSV → assert P99 < 2000ms                      │
│    5. Write evidence/XX_C4_LOAD_TEST.json                  │
└──────────────────────┬─────────────────────────────────────┘
                       │ (if sovereign mode)
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ SOVEREIGN CLUSTER (air-gapped)                             │
│                                                              │
│  Option A: k6 operator (preferred)                          │
│    k6 CRD runs load test as a Kubernetes Job                │
│    k6 --out csv → metrics written to PVC                   │
│    k6 operator parses results → writes to evidence PVC     │
│                                                              │
│  Option B: Pre-seeded JWT via env                          │
│    scripts/run_load_test.py injects token into configmap   │
│    Load test uses fixed JWT (from K8s secret)              │
│    Results streamed via SSE to external observer           │
└──────────────────────────────────────────────────────────────┘
```

---

## Architecture Decision: k6 vs Locust for Sovereign

| Criteria | Locust | k6 | Decision |
|----------|--------|----|----------|
| K8s native | No (needs Python) | Yes (Go binary) | k6 wins |
| Sovereign-compatible | Yes (Python runtime) | Yes (static binary) | Tie |
| CSV output | Yes | Yes (`--out csv`) | Tie |
| JWT injection | Via headers | Via environment | Tie |
| Learning curve | Lower | Medium | Locust wins (current codebase) |

**Decision:** Keep Locust for local/CI. Add k6 CRD for sovereign.

---

## Load Test Configurations

### C4.1: Steady State (100 concurrent users, 10 RPS, 5 min)
```
locust -f tests/load/locustfile.py \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --host http://localhost:8000 \
  --csv /tmp/c4_steady \
  --html /tmp/c4_report.html
```

### C4.2: Spike (500 concurrent users, instant spawn)
```
--users 500 --spawn-rate 500 --run-time 2m
```

### C4.3: Soak (50 concurrent, 60 min sustained)
```
--users 50 --spawn-rate 5 --run-time 60m
```

---

## P99 Assertion Logic

```python
def assert_p99_latency(csv_path: str, threshold_ms: float = 2000.0) -> dict:
    """
    Parse Locust CSV and assert P99 < threshold.
    Returns {p50, p95, p99, pass: bool}
    """
    import csv
    latencies = []
    with open(csv_path + "_stats.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Type"] == "GET" and row["Name"] == "/api/query/stream":
                latencies.append(float(row["Response Time"]))
    latencies.sort()
    n = len(latencies)
    p50 = latencies[int(n * 0.50)]
    p95 = latencies[int(n * 0.95)]
    p99 = latencies[int(n * 0.99)]
    return {
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "threshold_ms": threshold_ms,
        "pass": p99 < threshold_ms
    }
```

---

## Trade-offs

1. **Locust for local, k6 for sovereign** — Two tools to maintain. Upside: each is optimal for its environment.
2. **Fixed JWT in sovereign** — Token expires. Upside: no auth complexity. Downside: must rotate before expiry.
3. **CSV evidence in PVC** — Data never leaves cluster. Upside: sovereign integrity. Downside: manual retrieval.

---

## Action Items

- [ ] Implement `assert_p99_latency()` in `scripts/run_load_test.py`
- [ ] Add k6 CRD definition in `infrastructure/k8s/load-test-crd.yaml`
- [ ] Create `scripts/sovereign_load_test.sh` using k6
- [ ] Add `C4_SOVEREIGN_THRESHOLD_P99` env var
- [ ] Document in `docs/architecture/OPERATIONS_RUNBOOK.md`

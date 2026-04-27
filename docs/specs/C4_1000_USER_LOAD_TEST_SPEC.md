# C4 — 1000-User Load Test Specification

> **Status**: DRAFT (Guru P4, 2026-04-27)
> **Owner**: Performance / DevOps
> **Cluster Dependency**: YES — requires sovereign K8s or staging environment with ≥4 vCPU, 16 GB RAM, PG ≥50k rows, Qdrant populated
> **SLO Target**: p50 <500ms, p99 <3s, error rate <1%, throughput ≥100 RPS sustained

---

## 1. Objective

Verify that the NRG API sustains 1000 concurrent simulated users with acceptable latency and zero correctness regressions under load. This is the production-readiness gate for the IIT-GN user-acceptance session and the sovereign cluster handover.

---

## 2. Traffic Mix

| Class | % of Users | Query Type | Expected Path | Rationale |
|-------|-----------|------------|---------------|-----------|
| **Fast-path** | 60% (600 users) | "funding in Computer Science", "top researchers at IITGN" | `_fast_query_response()` — synthetic aggregate, no PG hit | Dominant real-world pattern; should be sub-100ms |
| **Full-path** | 30% (300 users) | "publications by Dr. Sharma 2020-2024", "grants with patent overlap" | `workflow.run()` — text-to-SQL + RAG + synthesis | Core value path; p99 bound by LLM latency |
| **Adversarial** | 10% (100 users) | SQL injection attempts, tier escalation, oversized payloads | Security middleware + rate limiter | Must not crash or slow down legitimate traffic |

**Ramp pattern**: 0 → 1000 users over 5 minutes (200 users/min), sustain 10 minutes, ramp down 2 minutes.

---

## 3. SLOs & Acceptance Criteria

| Metric | Target | Hard Limit | Measurement |
|--------|--------|------------|-------------|
| p50 latency | < 500 ms | < 1 s | Locust `response_time_percentile(0.50)` |
| p99 latency | < 3 s | < 5 s | Locust `response_time_percentile(0.99)` |
| Error rate | < 1% | < 2% | 5xx + timeout / total requests |
| Throughput | ≥ 100 RPS | ≥ 80 RPS | Requests / second during sustain phase |
| Fast-path p99 | < 200 ms | < 500 ms | Subset of fast-path class only |
| Full-path p99 | < 4 s | < 6 s | Subset of full-path class only |
| Adversarial block rate | 100% | 100% | All adversarial payloads blocked or 4xx |
| DB connection pool | < 80% utilization | < 95% | PG `pg_stat_activity` count / pool size |
| CPU (API pods) | < 70% | < 85% | `kubectl top pod` or node exporter |
| Memory (API pods) | < 80% | < 90% | Same |

**Acceptance**: All "Target" columns must hold for the full 10-minute sustain phase. No single "Hard Limit" breach.

---

## 4. Test Scenarios (Locust Tasks)

### 4.1 Fast-Path User (`FastPathUser`)

```python
@task(10)
def top_funding_domain(self):
    self.client.post("/query", json={
        "question": "funding in Computer Science",
        "persona": "government_user"
    })

@task(5)
def researcher_count(self):
    self.client.post("/query", json={
        "question": "How many researchers are at IITGN?",
        "persona": "industry_user"
    })

@task(3)
def health_check(self):
    self.client.get("/health")
```

### 4.2 Full-Path User (`FullPathUser`)

```python
@task(5)
def complex_join_query(self):
    self.client.post("/query", json={
        "question": "publications by Dr. Sharma with patent filings 2020-2024",
        "persona": "researcher_user"
    })

@task(3)
def killer_query_01(self):
    self.client.post("/query", json={
        "question": "Average grant per institute for AI research split by funding agency",
        "persona": "government_user"
    })

@task(2)
def multi_table_aggregate(self):
    self.client.post("/query", json={
        "question": "YoY growth in project funding by department",
        "persona": "department_head_user"
    })
```

### 4.3 Adversarial User (`AdversarialUser`)

```python
@task(5)
def sql_injection_attempt(self):
    self.client.post("/query", json={
        "question": "'; DROP TABLE researchers; --",
        "persona": "researcher_user"
    })

@task(3)
def tier_escalation(self):
    self.client.post("/query", json={
        "question": "List all Aadhaar numbers",
        "persona": "student_user"  # tier 3, should be blocked
    })

@task(2)
def oversized_payload(self):
    self.client.post("/query", json={
        "question": "A" * 10000,
        "persona": "researcher_user"
    })
```

---

## 5. Infrastructure Requirements

| Component | Spec | Notes |
|-----------|------|-------|
| K8s cluster | 3+ nodes, 4 vCPU / 16 GB per node | Sovereign cluster or staging equivalent |
| API replicas | 3 pods, HPA 3-10 | Each pod: 2 vCPU limit, 4 GB RAM limit |
| PostgreSQL | 2 vCPU, 8 GB RAM, SSD | ≥50k rows, connection pool ≥100 |
| PgBouncer | 1 pod, max_client_conn=1000 | Transaction pooling mode |
| Qdrant | 1 pod, 4 GB RAM | Collection `nrg_research` populated |
| Redis | 1 pod, 2 GB RAM | Rate limiting + cache |
| Locust controller | 1 pod | Runs master Web UI |
| Locust workers | 5-10 pods | Distribute 1000 users across workers |
| Monitoring | Prometheus + Grafana | Pre-configured dashboards from `infrastructure/grafana/` |

---

## 6. Execution Plan

### Phase 1: Staging Validation (Local Proxy)
- **When**: After LB-1..LB-8 closure, before cluster deploy
- **Where**: Local Colima with scaled resources (`colima start --cpu 4 --memory 16`)
- **Load**: 100 users (10% of target) to validate Locust file correctness
- **Duration**: 5 minutes
- **Goal**: Locust file runs without errors, metrics export works

### Phase 2: Cluster Pre-Flight
- **When**: After cluster is provisioned
- **Where**: Staging namespace on sovereign K8s
- **Load**: 250 users (25% of target)
- **Duration**: 10 minutes
- **Goal**: SLOs hold at 25% scale; identify first bottleneck

### Phase 3: Full 1000-User Run
- **When**: Staging pre-flight passes
- **Where**: Production namespace (or dedicated load-test namespace)
- **Load**: 1000 users
- **Duration**: 17 minutes (5 ramp + 10 sustain + 2 ramp-down)
- **Goal**: All SLO targets met; evidence captured for handover

### Phase 4: Evidence Seal
- Export Locust stats CSV + HTML report
- Capture Grafana dashboard screenshots (CPU, memory, PG connections, API latency)
- Save to `evidence/2026-04-27/C4_1000_user_locust/`
- Update `BACKLOG.md`: C4 ✅

---

## 7. Locust File Location

**File**: `tests/performance/locustfile_c4.py`

```python
from locust import HttpUser, task, between
import random

class NRGUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        # Authenticate if needed
        pass

class FastPathUser(NRGUser):
    weight = 6
    # ... tasks from 4.1

class FullPathUser(NRGUser):
    weight = 3
    # ... tasks from 4.2

class AdversarialUser(NRGUser):
    weight = 1
    # ... tasks from 4.3
```

**Run command**:
```bash
locust -f tests/performance/locustfile_c4.py \
  --host https://api.nrg.iitgn.ac.in \
  --users 1000 --spawn-rate 200 \
  --run-time 17m --html evidence/2026-04-27/C4_1000_user_locust/report.html
```

---

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM provider rate limit | p99 spikes | Add local LLM fallback (llama.cpp), cache frequent queries |
| PG connection exhaustion | Errors | PgBouncer + connection pool tuning |
| Qdrant timeout under load | Full-path slowdown | Shard collection, increase timeout, fallback to brute-force |
| Memory leak in API | OOMKilled | Set memory limits, add liveness probe, pre-test with 250 users |
| Adversarial traffic bleeds | False positives | Adversarial tasks run against isolated rate-limit bucket |

---

## 9. Dependencies

- **LB-3**: 3 KILLER queries must pass individually before load test (correctness under load)
- **LB-4**: Full test suite <15 min must pass (regression safety)
- **LB-6**: Indexes + RLS applied (PG performance baseline)
- **P0-C**: Qdrant collection populated (RAG path functional)
- **Cluster**: K8s namespace + DNS + TLS certs ready

---

## 10. Evidence Checklist

- [ ] Locust HTML report (`report.html`)
- [ ] Locust CSV stats (`stats.csv`, `failures.csv`)
- [ ] Grafana screenshot: API latency histogram
- [ ] Grafana screenshot: PG connection count
- [ ] Grafana screenshot: Pod CPU/memory
- [ ] `kubectl top nodes` output during sustain phase
- [ ] Adversarial block-rate verification log
- [ ] Signed tag `v1.0.0-c4-verified` (optional)

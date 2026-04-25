# Build Dashboard Evidence — NRG System Dashboards

**Skill**: build-dashboard
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/27_BUILD_DASHBOARD.md`

---

## Dashboard Design: NRG System Health

### Dashboard 1: Executive Summary (NRG Command Center)

**Audience**: Leadership / CTO
**Purpose**: High-level system health at a glance
**Refresh**: Real-time

#### Top-Line Metrics

| Metric | Visualization | Comparison | Alert Threshold |
|--------|--------------|-----------|-----------------|
| Chain Length | Big number + trend | vs 7 days ago | < 0 growth = 🔴 |
| Chain Validity | Status indicator | Current state | Invalid = 🔴 |
| Active Users (24h) | Big number | vs yesterday | -20% = 🔴 |
| Query Success Rate | Percentage | vs SLO (3s) | < 60% = 🟡 |
| API Health | Up/Down indicator | Current state | Down = 🔴 |

#### Secondary Metrics

| Metric | Visualization | Drill-Down |
|--------|--------------|------------|
| Queries by Tier | Pie chart | Tier 1/2/3 breakdown |
| Average Response Time | Sparkline (7d) | Per-tier trend |
| Error Rate by Type | Bar chart | SQL/Auth/RAG/Other |
| Consent覆盖率 | Gauge | By tier |

#### Layout

```
┌─────────────────────────────────────────────────────┐
│  HEADER: NRG Command Center — [Last Updated]       │
├───────────┬───────────┬───────────┬─────────────────┤
│ Chain     │ Active    │ Query     │ API             │
│ Length    │ Users     │ Success   │ Status          │
│ 382,653   │ 1,247     │ 73%       │ ✅ UP           │
├───────────┴───────────┴───────────┴─────────────────┤
│  Response Time Sparkline (7d)     │  Error Breakdown│
│  ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇█▇▆▅▄▃   │  SQL: 12%       │
│                                  │  Auth: 5%       │
│                                  │  RAG: 8%        │
├──────────────────────────────────┴─────────────────┤
│  Tier Distribution  │  Consent Coverage  │  Alerts  │
│  [PIE CHART]        │  [GAUGE]          │  [LIST]  │
└─────────────────────────────────────────────────────┘
```

---

### Dashboard 2: Operations Dashboard

**Audience**: DevOps / SRE
**Purpose**: Infrastructure health and incident response
**Refresh**: Real-time

#### Top-Line Metrics

| Metric | Visualization | Comparison | Alert Threshold |
|--------|--------------|-----------|-----------------|
| API Uptime | Percentage | 30-day trend | < 99.9% = 🔴 |
| DB Query Latency (p50) | Big number | SLO: 3.5ms | > 10ms = 🔴 |
| Redis Cache Hit Rate | Percentage | 24h trend | < 80% = 🟡 |
| Qdrant Vector Latency | Big number | Baseline | > 100ms = 🟡 |
| Error Rate | Percentage | vs baseline | > 1% = 🔴 |

#### Secondary Metrics

| Metric | Visualization | Drill-Down |
|--------|--------------|------------|
| Container Health | Table | PG/Redis/Qdrant status |
| Audit Chain Growth | Line chart | Daily event count |
| Rate Limit Hits | Bar chart | By tier |
| JWT Revocations | Counter | 24h count |
| Audit Cosign Lag | Time delta | Current delay |

#### Layout

```
┌─────────────────────────────────────────────────────┐
│  OPS DASHBOARD — [Alerts: 2] — [Refresh: 5s]        │
├───────────┬───────────┬───────────┬─────────────────┤
│ API Uptime│ DB p50    │ Cache Hit │ Qdrant Latency  │
│ 99.97% 🟡 │ 2.1ms ✅  │ 87% ✅    │ 45ms ✅         │
├───────────┴───────────┴───────────┴─────────────────┤
│  Container Health                                  │
│  ┌──────────┬────────┬──────────┐                   │
│  │PostgreSQL│ Redis  │ Qdrant   │                   │
│  │  ✅ UP   │  ✅ UP │  ❌ DOWN │  ← CRITICAL       │
│  └──────────┴────────┴──────────┘                   │
├─────────────────────────────────────────────────────┤
│  Audit Chain Growth (24h)  │  Rate Limit Hits      │
│  ▅▆▇█▇▆▅▇█▆▅▃▂▃▅▆▇█▇▆▅▃  │  Tier1: 234  🟡       │
│                             │  Tier2: 89           │
│                             │  Tier3: 12           │
└─────────────────────────────────────────────────────┘
```

---

### Dashboard 3: Text-to-SQL Performance

**Audience**: ML Engineering / Product
**Purpose**: Track AI query accuracy and speed
**Refresh**: Daily

#### Top-Line Metrics

| Metric | Visualization | Comparison | Target |
|--------|--------------|-----------|--------|
| Query Accuracy | Percentage | vs last sprint | > 75% |
| Avg Response Time | Big number | SLO: 3s | < 3s |
| Queries Processed | Counter | vs last week | Growing |
| Error Rate | Percentage | vs last sprint | < 10% |

#### Secondary Metrics

| Metric | Visualization | Drill-Down |
|--------|--------------|------------|
| Accuracy by Query Type | Bar chart | Lookup/Join/Aggregation |
| Response Time Distribution | Histogram | < 3s / 3-5s / > 5s |
| Failure Modes | Table | SQL/RAG/Auth/Timeout |
| Dev vs Prod Accuracy | Comparison | Gap analysis |

#### Layout

```
┌─────────────────────────────────────────────────────┐
│  TEXT-TO-SQL PERFORMANCE — [Last: Apr 25 2026]     │
├───────────┬───────────┬───────────┬─────────────────┤
│ Accuracy  │ Avg Time  │ Processed │ Error Rate      │
│ 73% 🟡    │ 7.2s 🔴   │ 12,847    │ 18% 🟡          │
│ (target>75%)    (SLO:3s)    (this month) (target<10%)│
├───────────┴───────────┴───────────┴─────────────────┤
│  Accuracy by Query Type         │ Response Dist.    │
│  Lookup: ████████████░░ 82%    │ <3s: ████░░ 45%   │
│  Join:   ██████░░░░░░░░ 41%    │ 3-5s: ███░░░ 35%  │
│  Aggreg: ██████████░░░░ 67%    │ >5s:  ██░░░░ 20%   │
├─────────────────────────────────┴──────────────────┤
│  Recent Failures — 17 queries evaluated             │
│  Q4: Error (000) — Table not in dev schema        │
│  Q6: Error (000) — Table not in dev schema        │
│  Q7: Wrong (zzz) — JOIN on missing table          │
└─────────────────────────────────────────────────────┘
```

---

### Dashboard 4: Security & Compliance

**Audience**: Security / Legal
**Purpose**: DPDP-2023 compliance and threat monitoring
**Refresh**: Real-time

#### Top-Line Metrics

| Metric | Visualization | Comparison | Target |
|--------|--------------|-----------|--------|
| Consent Coverage | Percentage | By tier | > 95% |
| Audit Chain Valid | Status | Current | ✅ Valid |
| Failed Auth (24h) | Counter | vs baseline | < 100 |
| SQL Injection Blocked | Counter | vs last week | < trend |
| PII Detections | Counter | 24h | Any = 🔴 |

#### Secondary Metrics

| Metric | Visualization | Drill-Down |
|--------|--------------|------------|
| Consent by Tier | Stacked bar | Tier 1/2/3 |
| JWT Revocation List | Size | Growth |
| Rate Limit Hits | Heatmap | By hour |
| Audit Events | Line chart | Daily volume |
| Tamper Alerts | Counter | Any = 🔴 |

---

## Data Sources

| Dashboard | Source | Table | Refresh |
|-----------|--------|-------|---------|
| Executive | API metrics | `system_events`, `queries` | Real-time |
| Operations | Docker/DB | `pg_stat_activity`, `INFO` | Real-time |
| Text-to-SQL | Benchmark | `benchmark_queries` | Daily |
| Security | Audit | `audit_events`, `user_consents` | Real-time |

---

## Alerts Configuration

| Condition | Dashboard | Severity | Owner |
|-----------|-----------|----------|-------|
| Chain invalid | Executive | 🔴 CRITICAL | Security |
| Qdrant down | Operations | 🔴 CRITICAL | DevOps |
| DB p50 > 10ms | Operations | 🔴 CRITICAL | DevOps |
| Accuracy < 60% | Text-to-SQL | 🟡 WARNING | ML Eng |
| Response > 10s | Text-to-SQL | 🟡 WARNING | ML Eng |
| Consent < 90% | Security | 🟡 WARNING | Legal |
| Any PII detected | Security | 🔴 CRITICAL | Security |

---

## Skill Deliverable

**Status**: COMPLETED

4 dashboards designed for NRG:
1. **Executive Summary** — Chain health, API status, user activity
2. **Operations** — Infrastructure, DB, containers, audit chain
3. **Text-to-SQL Performance** — Accuracy, response time, failure modes
4. **Security & Compliance** — DPDP-2023, consent, auth, audit

Key finding: No existing dashboards found in codebase. All 4 must be built.

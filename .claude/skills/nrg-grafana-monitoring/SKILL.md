# NRG Grafana Monitoring Skill

Monitoring, alerting, and dashboard design for the National Research Graph (NRG) sovereign AI platform.

## When to Use

Use this skill when:
- Building or reviewing Grafana dashboards for NRG services
- Configuring alerts for SLO breaches, drift, or audit anomalies
- Setting up monitoring for the sovereign Indian-soil stack
- Diagnosing performance regressions from metrics
- Designing runbooks from metric patterns

## NRG Monitoring Stack

```
Grafana → Prometheus (metrics) + Loki (logs) + Alertmanager
         ↓
    Postgres (pg_stat_statements, slow queries)
    Qdrant (vector ops, drift)
    Redis (cache hit/miss, memory)
    Kong (request rates, latencies, errors)
    Nginx (connections, SSL handshakes)
```

## Core Dashboards

### 1. API Health Dashboard

| Panel | Query | Threshold |
|-------|-------|-----------|
| Request Rate | `rate(http_requests_total[5m])` | Baseline: ~100 rpm |
| p50 Latency | `histogram_quantile(0.5, rate(http_request_duration_seconds_bucket[5m]))` | SLO: <500ms |
| p99 Latency | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` | SLO: <3s |
| Error Rate | `rate(http_requests_total{status=~"5.."}[5m])` | Alert: >0.1% |
| Active Connections | `nginx_connections_active` | Alert: >80% of pool |

### 2. Tier Isolation Dashboard

Track per-tier query volume and rejection rates:

```promql
# Query count by tier
sum(rate(nrg_queries_total[5m])) by (tier)

# Rejection rate by tier
rate(nrg_queries_rejected_total[5m]) / rate(nrg_queries_total[5m])

# PII access attempts (should be 0 for non-government)
rate(nrg_pii_access_attempts_total{tier!="government"}[5m])
```

### 3. Vector Drift Dashboard

Panels from the C5 drift detection spec:

| Panel | Metric | Alert |
|-------|--------|-------|
| Cosine Drift | `nrg_vector_drift_cosine` | >0.15 |
| Coverage Gap | `nrg_vector_coverage_gap_pct` | >10% |
| Language Bias | `nrg_vector_language_bias_ratio` | >2.0 |
| Model Fingerprint | `nrg_embedding_model_hash` | Change = WARN |

### 4. Audit Chain Dashboard

```promql
# Events per minute
rate(nrg_audit_events_total[5m])

# Chain verification failures (MUST be 0)
nrg_audit_verification_failures_total

# Co-signature lag
nrg_audit_cosign_lag_seconds
```

**Golden signal:** `nrg_audit_verification_failures_total` must always be 0. Any non-zero value triggers P1 incident.

### 5. Database Dashboard

```promql
# Active connections
pg_stat_activity_count{state="active"}

# Slow queries (>1s)
rate(pg_stat_statements_calls{mean_time>1000}[5m])

# Table bloat
pg_stat_user_tables{n_live_tup / n_dead_tup < 0.8}

# Replication lag (if streaming replica)
pg_replication_lag_seconds
```

## Alert Rules

### P1 — Page Immediately

```yaml
- alert: AuditChainTampered
  expr: nrg_audit_verification_failures_total > 0
  for: 0s
  annotations:
    summary: "Audit chain verification failed"
    runbook_url: "docs/runbooks/P1_AUDIT_CHAIN_FAILURE.md"

- alert: DBPrimaryDown
  expr: pg_up{role="primary"} == 0
  for: 0s

- alert: SovereignDataExfil
  expr: rate(nrg_data_exfil_bytes_total[5m]) > 1048576  # 1MB/s
  for: 1m
```

### P2 — Alert Within 15 min

```yaml
- alert: VectorDriftHigh
  expr: nrg_vector_drift_cosine > 0.15
  for: 5m

- alert: p99LatencySLOBreach
  expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 3
  for: 5m

- alert: RedisMemoryHigh
  expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.85
  for: 5m
```

### P3 — Alert Within 1 hour

```yaml
- alert: CacheHitRateLow
  expr: rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) < 0.70
  for: 15m

- alert: QdrantCollectionLag
  expr: time() - nrg_qdrant_last_index_timestamp > 3600
  for: 15m
```

## SLO Definitions (from C4 spec)

| SLO | Target | Measurement Window |
|-----|--------|-------------------|
| Availability | 99.9% | 30 days |
| p50 Latency | <500ms | 7 days |
| p99 Latency | <3s | 7 days |
| Error Rate | <0.1% | 7 days |
| Audit Chain Integrity | 100% | Forever |

## Log-Based Panels (Loki)

```logql
# ERROR logs from API
{app="nrg-api"} |= "ERROR"

# Slow SQL queries
{app="nrg-api"} |~ "duration: [1-9][0-9]+\\.[0-9]+ms"

# Auth failures by tier
{app="nrg-api"} |= "AUTH_FAILURE" | json | line_format "{{.tier}} — {{.reason}}"

# Audit chain anomalies
{app="nrg-audit"} |= "HMAC_MISMATCH" or `CORRUPTED`
```

## Dashboard JSON Conventions

- Use `datasource: "${datasource}"` for portability
- Tag all NRG dashboards: `tags: ["nrg", "sovereign", "{service}"]`
- Set `refresh: "30s"` for live dashboards, `"5m"` for trend dashboards
- Use consistent color mapping: green = healthy, yellow = warning, red = critical

## Runbook Link Pattern

Every alert annotation must link to a runbook:
```
docs/runbooks/{SEVERITY}_{SHORT_NAME}.md
```

Example: `docs/runbooks/P1_AUDIT_CHAIN_FAILURE.md`

## Sovereign Constraint

All metrics, logs, and dashboards must remain on Indian soil. No telemetry leaves the sovereign boundary. Grafana Cloud is prohibited; use self-hosted Grafana only.

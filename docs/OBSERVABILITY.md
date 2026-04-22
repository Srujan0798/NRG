# NRG Observability Stack — Complete Implementation Guide

## Current State

**Observability Maturity: 2.5 / 5**

| Dimension | Score | Evidence |
|-----------|-------|---------|
| Tracing | 3/5 | Langfuse active on 4/5 nodes; captures latency/errors, NOT token usage |
| Metrics | 2/5 | Rich definitions exist; Prometheus endpoint NOW wired; no metrics ever recorded |
| Alerting | 3/5 | 8 Prometheus alert rules defined; alerts not yet connected to channels |
| Health Checks | 4/5 | `/health`, `/health/llm`, `/health/db`, `/health/qdrant`, `/health/all` |
| Audit | 3/5 | HMAC audit chain active; no observability correlation |

---

## 1. Langfuse Distributed Tracing

### 1.1 All 5 Nodes — Tracing Status

| Node | File | Tracing | Token Counts | Cost | Fallback Tracking |
|------|------|---------|-------------|------|-------------------|
| **Router** | `src/orchestration/nodes/router.py` | ❌ NONE | ❌ | ❌ | ❌ |
| **Planner** | `src/orchestration/nodes/planner.py` | ✅ `@trace_llm_call` | ❌ | ❌ | ❌ |
| **Executor** | `src/orchestration/nodes/executor.py` | ✅ `@trace_llm_call` | ❌ | ❌ | ❌ |
| **Verifier** | `src/orchestration/nodes/verifier.py` | ✅ `@trace_llm_call` | ❌ | ❌ | ❌ |
| **Synthesizer** | `src/orchestration/nodes/synthesizer.py` | ✅ `@trace_llm_call` | ❌ | ❌ | ❌ |

### 1.2 Add Router Tracing

**File:** `src/orchestration/nodes/router.py`

The router uses heuristic pattern matching — no LLM call. However, it should emit routing decisions to Langfuse for audit and analysis:

```python
from src.observability.langfuse_tracer import trace_routing_decision

@trace_routing_decision
def route_query(query: str, user_tier: int) -> Dict[str, Any]:
    """Route query to appropriate workflow path."""
    # ... existing routing logic
    return {
        "intent": intent,
        "path": path,
        "confidence": confidence,
        "user_tier": user_tier,
    }
```

**New tracer file:** `src/observability/langfuse_tracer.py` add:

```python
def trace_routing_decision(func):
    """Decorator to trace routing decisions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        client = _init_langfuse()
        if not client:
            return func(*args, **kwargs)

        trace = client.trace(name="nrg.router")
        span = trace.span(name="route_decision")
        start = time.time()

        try:
            result = func(*args, **kwargs)
            latency_ms = (time.time() - start) * 1000
            span.update(
                metadata={
                    "latency_ms": latency_ms,
                    "intent": result.get("intent"),
                    "path": result.get("path"),
                    "confidence": result.get("confidence"),
                    "user_tier": result.get("user_tier"),
                }
            )
            trace.update(
                metadata={
                    "routing_intent": result.get("intent"),
                    "user_tier": result.get("user_tier"),
                }
            )
            return result
        except Exception as exc:
            span.update(status="error", output=str(exc))
            raise
        finally:
            span.end()

    return wrapper
```

### 1.3 Capture Token Counts from LLM Responses

The `count_llm_tokens()` helper in `metrics.py` is **defined but never called**. The LLM client responses contain `usage` dict with `prompt_tokens`, `completion_tokens`, `total_tokens`. These must be extracted.

**Every LLM call site should call:**

```python
from src.observability.metrics import count_llm_tokens

def extract_token_counts(response: Any, provider: str, model: str) -> Dict[str, int]:
    """Extract token counts from LLM response based on provider format."""
    usage = getattr(response, 'usage', None) or {}
    if isinstance(usage, dict):
        prompt_tokens = usage.get('prompt_tokens', 0) or usage.get('input_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0) or usage.get('output_tokens', 0)
        total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
    else:
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "provider": provider,
        "model": model,
    }
```

**Add to synthesizer after each LLM call:**

```python
# After successful LLM generation:
token_data = extract_token_counts(response, provider, model)
count_llm_tokens(
    role="synthesizer",
    provider=token_data["provider"],
    model=token_data["model"],
    tokens=token_data["total_tokens"],
)
nrg_llm_latency_seconds.labels(
    role="synthesizer",
    provider=token_data["provider"],
).observe(latency_seconds)
```

---

## 2. Custom Metrics — All Available

### 2.1 Metric Definitions

All defined in `src/observability/metrics.py`:

```python
# ── Query Metrics ──────────────────────────────────────────────
nrg_queries_total          Counter  [tier, intent, status]
nrg_query_latency_seconds  Histogram [tier, intent]  p50/p95/p99

# ── LLM Metrics ───────────────────────────────────────────────
nrg_llm_tokens_total       Counter  [role, provider, model]
nrg_llm_latency_seconds    Histogram [role, provider]  p50/p95/p99

# ── Cache Metrics ──────────────────────────────────────────────
nrg_cache_hits_total       Counter  []
nrg_cache_misses_total     Counter  []
nrg_cache_lookup_total     Counter  []

# ── Skill Metrics ─────────────────────────────────────────────
nrg_skill_latency_seconds  Histogram [skill_name]  p50/p95
nrg_skill_errors_total     Counter  [skill_name, error_type]

# ── Security Metrics ──────────────────────────────────────────
nrg_pii_block_total        Counter  [entity_type]
nrg_injection_block_total  Counter  []
nrg_egress_block_total     Counter  []

# ── Audit Metrics ─────────────────────────────────────────────
nrg_audit_chain_ok         Gauge    []  (1=ok, 0=broken)
nrg_audit_events_total     Counter  [action]

# ── Rate Limiting ──────────────────────────────────────────────
nrg_rate_limited_total     Counter  [user_tier]

# ── Database ──────────────────────────────────────────────────
nrg_db_connections_active  Gauge    []
nrg_db_query_latency_seconds Histogram [query_type]
```

### 2.2 Record Metrics at Query Boundary

**File:** `src/api/main.py` — `/query` endpoint

The query endpoint should record metrics on every request:

```python
from src.observability.metrics import (
    count_query, nrg_query_latency_seconds, count_cache_hit,
    count_llm_tokens, nrg_llm_latency_seconds,
)
import time

@app.post("/query")
async def query_with_langgraph(request: QueryRequest, token_payload: dict = Depends(get_current_user)):
    start_time = time.time()
    user_tier = token_payload.get("tier", 1)

    try:
        # ... existing logic ...

        # Record success metric
        latency = time.time() - start_time
        nrg_query_latency_seconds.labels(
            tier=str(user_tier),
            intent=result.get("intent", "unknown"),
        ).observe(latency)
        count_query(
            tier=str(user_tier),
            intent=result.get("intent", "unknown"),
            status="success",
        )

        # Record cache hit
        if result.get("cached"):
            count_cache_hit()

        # Record token usage if available
        if result.get("llm_usage"):
            count_llm_tokens(
                role="synthesizer",
                provider=result["llm_usage"]["provider"],
                model=result["llm_usage"]["model"],
                tokens=result["llm_usage"]["total_tokens"],
            )

        return response_payload

    except HTTPException:
        count_query(tier=str(user_tier), intent="unknown", status="error")
        raise
```

### 2.3 LLM Fallback Rate Tracking

When the LLM cascade activates (NVIDIA → local → rule-based), record this:

```python
# In metrics.py, add new counter:
nrg_llm_fallback_total = Counter(
    'nrg_llm_fallback_total',
    'LLM fallback activations',
    ['from_provider', 'to_provider']
)

def count_llm_fallback(from_provider: str, to_provider: str):
    """Record when LLM fallback activates."""
    nrg_llm_fallback_total.labels(
        from_provider=from_provider,
        to_provider=to_provider,
    ).inc()
```

**Wire into `src/config/llm_config.py`** when fallback activates:

```python
# When primary LLM fails and fallback is triggered:
from src.observability.metrics import count_llm_fallback
count_llm_fallback("nvidia", "local")
# or when local also fails:
count_llm_fallback("local", "rule_based")
```

---

## 3. Alert Rules

### 3.1 Fixed Prometheus Alerts

**File:** `infrastructure/prometheus/alerts.yaml`

Fix metric names to match actual Prometheus metrics and add new critical alerts:

```yaml
groups:
  - name: nrg_critical
    rules:

      - alert: AuditChainBroken
        expr: nrg_audit_chain_ok == 0
        for: 1m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Audit chain integrity compromised"
          description: "HMAC audit chain broken. Immediate investigation required."
          runbook_url: "https://wiki.internal/nrg/runbooks/audit-chain-broken"

      - alert: QdrantDown
        expr: up{job="nrg-qdrant"} == 0
        for: 5m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Qdrant vector database unreachable"
          description: "RAG functionality degraded. Queries will use text-only fallback."
          runbook_url: "https://wiki.internal/nrg/runbooks/qdrant-down"

      - alert: PostgresDown
        expr: up{job="nrg-api"} == 0
        for: 2m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "NRG API pod is down"
          description: "All API endpoints unreachable. No new queries can be processed."
          runbook_url: "https://wiki.internal/nrg/runbooks/postgres-down"

      - alert: EgressViolation
        expr: increase(nrg_egress_block_total[5m]) > 0
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Data sovereignty violation blocked"
          description: "Research data attempted to leave VPC. Egress guard blocked the request."
          runbook_url: "https://wiki.internal/nrg/runbooks/egress-violation"

      - alert: HighLLMErrorRate
        expr: |
          (
            sum(rate(nrg_skill_errors_total{error_type="llm_failure"}[10m]))
            /
            sum(rate(nrg_queries_total[10m]))
          ) > 0.10
        for: 5m
        labels:
          severity: critical
          team: ml-platform
        annotations:
          summary: "LLM error rate > 10%"
          description: "LLM is failing for >10% of queries. Check NVIDIA API key quota and local LLM health."
          runbook_url: "https://wiki.internal/nrg/runbooks/llm-high-error-rate"

      - alert: PromptInjectionSpike
        expr: increase(nrg_injection_block_total[5m]) > 10
        for: 2m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Prompt injection attack detected"
          description: "{{ $value }} injection attempts blocked in last 5 minutes."
          runbook_url: "https://wiki.internal/nrg/runbooks/prompt-injection"

  - name: nrg_warning
    rules:

      - alert: QueryLatencyHigh
        expr: histogram_quantile(0.95, rate(nrg_query_latency_seconds_bucket[5m])) > 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Query p95 latency > 30s"
          description: "95th percentile query latency is {{ $value | humanizeDuration }}. Check RAG retrieval and LLM latency."
          runbook_url: "https://wiki.internal/nrg/runbooks/query-latency-high"

      - alert: LLMFallbackRateHigh
        expr: |
          (
            sum(rate(nrg_llm_fallback_total[15m]))
            /
            sum(rate(nrg_queries_total[15m]))
          ) > 0.20
        for: 10m
        labels:
          severity: warning
          team: ml-platform
        annotations:
          summary: "LLM fallback rate > 20%"
          description: "Cloud LLM is failing for >20% of queries. Check NVIDIA API status and quota."
          runbook_url: "https://wiki.internal/nrg/runbooks/llm-fallback-rate"

      - alert: CacheHitRateLow
        expr: |
          (
            rate(nrg_cache_hits_total[10m])
            /
            (rate(nrg_cache_hits_total[10m]) + rate(nrg_cache_misses_total[10m]))
          ) < 0.50
        for: 15m
        labels:
          severity: info
        annotations:
          summary: "Cache hit rate < 50%"
          description: "Low cache utilization. Consider warming cache with frequent queries."
          runbook_url: "https://wiki.internal/nrg/runbooks/cache-hit-rate"

      - alert: DBLatencyHigh
        expr: histogram_quantile(0.95, rate(nrg_db_query_latency_seconds_bucket[5m])) > 1.0
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "Database p95 query latency > 1s"
          description: "Slow database queries detected. Check connection pool and query plans."
          runbook_url: "https://wiki.internal/nrg/runbooks/db-latency"

      - alert: PIISpike
        expr: increase(nrg_pii_block_total[5m]) > 20
        for: 3m
        labels:
          severity: warning
          team: security
        annotations:
          summary: "PII query spike detected"
          description: "{{ $value }} PII-containing queries blocked in last 5 minutes."
          runbook_url: "https://wiki.internal/nrg/runbooks/pii-spike"

      - alert: RateLimitThrottling
        expr: increase(nrg_rate_limited_total[5m]) > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate-limit throttle rate"
          description: "{{ $value }} requests were rate-limited in the last 5 minutes."
          runbook_url: "https://wiki.internal/nrg/runbooks/rate-limiting"

      - alert: LocalLLMHealthFlapping
        expr: |
          changes(llama_cpp_health_status[10m]) > 5
        for: 2m
        labels:
          severity: warning
          team: ml-platform
        annotations:
          summary: "Local Llama.cpp health check is unstable"
          description: "Local LLM health is flapping. Synthesis quality may degrade."
          runbook_url: "https://wiki.internal/nrg/runbooks/local-llm-flapping"

      - alert: TierDistributionAnomaly
        expr: |
          (
            sum(rate(nrg_queries_total{tier="3"}[10m]))
            /
            sum(rate(nrg_queries_total[10m]))
          ) > 0.5
        for: 30m
        labels:
          severity: info
        annotations:
          summary: "Industry (Tier 3) queries > 50% of traffic"
          description: "Unusual tier distribution. Normally Government (Tier 2) should dominate."
          runbook_url: "https://wiki.internal/nrg/runbooks/tier-distribution"
```

---

## 4. Grafana Ops Dashboard

**File:** `infrastructure/grafana/dashboards/nrg-ops.json`

```json
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "collapsed": false,
      "gridPos": { "h": 1, "w": 24, "x": 0, "y": 0 },
      "id": 1,
      "title": "System Health",
      "type": "row"
    },
    {
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "thresholds" },
          "mappings": [
            { "options": { "0": { "color": "red", "text": "DOWN" } }, "type": "value" },
            { "options": { "1": { "color": "green", "text": "UP" } }, "type": "value" }
          ],
          "thresholds": { "mode": "absolute", "steps": [{ "color": "red", "value": null }, { "color": "green", "value": 1 }] }
        }
      },
      "gridPos": { "h": 4, "w": 6, "x": 0, "y": 1 },
      "id": 2,
      "options": { "colorMode": "background", "graphMode": "none", "justifyMode": "auto", "orientation": "auto", "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false }, "textMode": "auto" },
      "pluginVersion": "10.0.0",
      "targets": [{ "expr": "up{job='nrg-api'}", "legendFormat": "API", "refId": "A" }],
      "title": "API Status",
      "type": "stat"
    },
    {
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "thresholds" },
          "mappings": [{ "options": { "0": { "color": "red", "text": "DOWN" }, "1": { "color": "green", "text": "UP" } }, "type": "value" }],
          "thresholds": { "mode": "absolute", "steps": [{ "color": "red", "value": null }, { "color": "green", "value": 1 }] }
        }
      },
      "gridPos": { "h": 4, "w": 6, "x": 6, "y": 1 },
      "id": 3,
      "options": { "colorMode": "background", "graphMode": "none", "justifyMode": "auto", "orientation": "auto", "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false }, "textMode": "auto" },
      "targets": [{ "expr": "up{job='nrg-qdrant'}", "legendFormat": "Qdrant", "refId": "A" }],
      "title": "Qdrant Status",
      "type": "stat"
    },
    {
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "thresholds" },
          "mappings": [{ "options": { "0": { "color": "red", "text": "BROKEN" }, "1": { "color": "green", "text": "OK" } }, "type": "value" }],
          "thresholds": { "mode": "absolute", "steps": [{ "color": "red", "value": null }, { "color": "green", "value": 1 }] }
        }
      },
      "gridPos": { "h": 4, "w": 6, "x": 12, "y": 1 },
      "id": 4,
      "options": { "colorMode": "background", "graphMode": "none", "justifyMode": "auto", "orientation": "auto", "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false }, "textMode": "auto" },
      "targets": [{ "expr": "nrg_audit_chain_ok", "legendFormat": "Audit Chain", "refId": "A" }],
      "title": "Audit Chain Integrity",
      "type": "stat"
    },
    {
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "palette-classic" },
          "custom": { "axisCenteredZero": false, "axisColorMode": "text", "axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 20, "gradientMode": "none", "hideFrom": { "legend": false, "tooltip": false, "viz": false }, "lineInterpolation": "smooth", "lineWidth": 2, "pointSize": 5, "scaleDistribution": { "type": "linear" }, "showPoints": "never", "spanNulls": true, "stacking": { "group": "A", "mode": "none" }, "thresholdsStyle": { "mode": "line" } },
          "mappings": [],
          "thresholds": { "mode": "absolute", "steps": [{ "color": "green", "value": null }, { "color": "red", "value": 30 }] },
          "unit": "s"
        }
      },
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 5 },
      "id": 5,
      "options": { "legend": { "calcs": ["mean", "max"], "displayMode": "table", "placement": "bottom", "showLegend": true }, "tooltip": { "mode": "multi", "sort": "none" } },
      "targets": [
        { "expr": "histogram_quantile(0.50, rate(nrg_query_latency_seconds_bucket[5m]))", "legendFormat": "p50", "refId": "A" },
        { "expr": "histogram_quantile(0.95, rate(nrg_query_latency_seconds_bucket[5m]))", "legendFormat": "p95", "refId": "B" },
        { "expr": "histogram_quantile(0.99, rate(nrg_query_latency_seconds_bucket[5m]))", "legendFormat": "p99", "refId": "C" }
      ],
      "title": "Query Latency (p50 / p95 / p99)",
      "type": "timeseries"
    },
    {
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "palette-classic" },
          "custom": { "drawStyle": "line", "fillOpacity": 30, "lineWidth": 2, "pointSize": 5, "showPoints": "never", "spanNulls": true },
          "mappings": [],
          "thresholds": { "mode": "absolute", "steps": [{ "color": "green", "value": null }] },
          "unit": "reqps"
        }
      },
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 5 },
      "id": 6,
      "options": { "legend": { "calcs": ["mean", "max"], "displayMode": "table", "placement": "bottom", "showLegend": true }, "tooltip": { "mode": "multi", "sort": "none" } },
      "targets": [
        { "expr": "sum(rate(nrg_queries_total{status='success'}[5m]))", "legendFormat": "Success QPS", "refId": "A" },
        { "expr": "sum(rate(nrg_queries_total{status='error'}[5m]))", "legendFormat": "Error QPS", "refId": "B" }
      ],
      "title": "Query Throughput (Success vs Error QPS)",
      "type": "timeseries"
    },
    {
      "collapsed": false,
      "gridPos": { "h": 1, "w": 24, "x": 0, "y": 13 },
      "id": 7,
      "title": "LLM & Cost Analytics",
      "type": "row"
    },
    {
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "palette-classic" },
          "custom": { "drawStyle": "line", "fillOpacity": 20, "lineWidth": 2, "pointSize": 5, "showPoints": "never", "spanNulls": true },
          "mappings": [],
          "unit": "s"
        }
      },
      "gridPos": { "h": 8, "w": 8, "x": 0, "y": 14 },
      "id": 8,
      "options": { "legend": { "calcs": ["mean", "max"], "displayMode": "table", "placement": "bottom", "showLegend": true }, "tooltip": { "mode": "multi", "sort": "none" } },
      "targets": [
        { "expr": "histogram_quantile(0.50, rate(nrg_llm_latency_seconds_bucket[5m]))", "legendFormat": "LLM p50", "refId": "A" },
        { "expr": "histogram_quantile(0.95, rate(nrg_llm_latency_seconds_bucket[5m]))", "legendFormat": "LLM p95", "refId": "B" }
      ],
      "title": "LLM Response Latency",
      "type": "timeseries"
    },
    {
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "palette-classic" },
          "custom": { "drawStyle": "bars", "fillOpacity": 80, "lineWidth": 0, "pointSize": 5, "showPoints": "never", "spanNulls": true },
          "mappings": [],
          "unit": "short"
        }
      },
      "gridPos": { "h": 8, "w": 8, "x": 8, "y": 14 },
      "id": 9,
      "options": { "legend": { "calcs": ["sum"], "displayMode": "table", "placement": "bottom", "showLegend": true }, "tooltip": { "mode": "multi", "sort": "none" } },
      "targets": [
        { "expr": "sum by (provider, model) (rate(nrg_llm_tokens_total[1h]))", "legendFormat": "{{provider}}:{{model}}", "refId": "A" }
      ],
      "title": "Token Usage by Provider/Model (tokens/hr)",
      "type": "timeseries"
    },
    {
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "thresholds" },
          "mappings": [],
          "max": 1,
          "min": 0,
          "thresholds": { "mode": "absolute", "steps": [{ "color": "red", "value": null }, { "color": "yellow", "value": 0.5 }, { "color": "green", "value": 0.8 }] },
          "unit": "percentunit"
        }
      },
      "gridPos": { "h": 8, "w": 8, "x": 16, "y": 14 },
      "id": 10,
      "options": { "orientation": "auto", "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false }, "showThresholdLabels": false, "showThresholdMarkers": true },
      "targets": [
        { "expr": "rate(nrg_cache_hits_total[10m]) / (rate(nrg_cache_hits_total[10m]) + rate(nrg_cache_misses_total[10m]))", "legendFormat": "Cache Hit Rate", "refId": "A" }
      ],
      "title": "Cache Hit Rate",
      "type": "gauge"
    },
    {
      "collapsed": false,
      "gridPos": { "h": 1, "w": 24, "x": 0, "y": 22 },
      "id": 11,
      "title": "Security & Audit",
      "type": "row"
    },
    {
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "palette-classic" },
          "custom": { "drawStyle": "line", "fillOpacity": 20, "lineWidth": 2, "pointSize": 5, "showPoints": "never", "spanNulls": true },
          "mappings": [],
          "thresholds": { "mode": "absolute", "steps": [{ "color": "green", "value": null }] },
          "unit": "short"
        }
      },
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 23 },
      "id": 12,
      "options": { "legend": { "calcs": ["sum", "max"], "displayMode": "table", "placement": "bottom", "showLegend": true }, "tooltip": { "mode": "multi", "sort": "none" } },
      "targets": [
        { "expr": "rate(nrg_pii_block_total[5m])", "legendFormat": "PII Blocks", "refId": "A" },
        { "expr": "rate(nrg_injection_block_total[5m])", "legendFormat": "Injection Blocks", "refId": "B" },
        { "expr": "rate(nrg_egress_block_total[5m])", "legendFormat": "Egress Violations", "refId": "C" }
      ],
      "title": "Security Events (PII / Injection / Egress)",
      "type": "timeseries"
    },
    {
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "palette-classic" },
          "custom": { "drawStyle": "pie", "fillOpacity": 80, "legendDisplayMode": "table", "pieType": "donut", "pointSize": 5, "reduceOptions": { "calcs": ["sum"], "fields": "", "values": false }, "strokeWidth": 2 },
          "mappings": [],
          "unit": "short"
        }
      },
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 23 },
      "id": 13,
      "options": { "legend": { "displayMode": "table", "placement": "right", "showLegend": true, "values": ["value", "percent"] }, "tooltip": { "mode": "single", "sort": "none" } },
      "targets": [
        { "expr": "sum by (tier) (increase(nrg_queries_total[24h]))", "legendFormat": "Tier {{tier}}", "refId": "A" }
      ],
      "title": "Query Distribution by Tier (24h)",
      "type": "piechart"
    },
    {
      "collapsed": false,
      "gridPos": { "h": 1, "w": 24, "x": 0, "y": 31 },
      "id": 14,
      "title": "Query Analytics",
      "type": "row"
    },
    {
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "palette-classic" },
          "custom": { "axisCenteredZero": false, "drawStyle": "bars", "fillOpacity": 80, "lineWidth": 0, "pointSize": 5, "showPoints": "never", "spanNulls": true },
          "mappings": [],
          "thresholds": { "mode": "absolute", "steps": [{ "color": "green", "value": null }] },
          "unit": "short"
        }
      },
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 32 },
      "id": 15,
      "options": { "barRadius": 0, "barWidth": 0.8, "groupWidth": 0.7, "legendDisplayMode": "table", "legendPlacement": "bottom", "showLegend": true, "stacking": "none", "tooltip": { "mode": "multi", "sort": "none" }, "xTickLabelRotation": 0, "xTickLabelSpacing": 0 },
      "targets": [
        { "expr": "sum by (intent) (increase(nrg_queries_total[24h]))", "legendFormat": "{{intent}}", "refId": "A" }
      ],
      "title": "Queries by Intent (24h)",
      "type": "barchart"
    },
    {
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "palette-classic" },
          "custom": { "axisCenteredZero": false, "drawStyle": "line", "fillOpacity": 20, "gradientMode": "none", "lineInterpolation": "smooth", "lineWidth": 2, "pointSize": 5, "showPoints": "never", "spanNulls": true },
          "mappings": [],
          "thresholds": { "mode": "absolute", "steps": [{ "color": "green", "value": null }] },
          "unit": "reqps"
        }
      },
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 32 },
      "id": 16,
      "options": { "legend": { "calcs": ["mean", "max"], "displayMode": "table", "placement": "bottom", "showLegend": true }, "tooltip": { "mode": "multi", "sort": "none" } },
      "targets": [
        { "expr": "sum by (hour) (rate(nrg_queries_total[5m]))", "legendFormat": "{{hour}}:00", "refId": "A" }
      ],
      "title": "Queries by Hour of Day (QPS)",
      "type": "timeseries"
    }
  ],
  "refresh": "30s",
  "schemaVersion": 38,
  "style": "dark",
  "tags": ["nrg", "observability", "ops"],
  "templating": { "list": [{ "current": {}, "hide": 0, "includeAll": false, "label": "Prometheus", "name": "DS_PROMETHEUS", "options": [], "query": "prometheus", "refresh": 1, "regex": "", "skipUrlSync": false, "type": "datasource" }] },
  "time": { "from": "now-6h", "to": "now" },
  "timepicker": {},
  "timezone": "browser",
  "title": "NRG — Operations Dashboard",
  "uid": "nrg-ops",
  "version": 1,
  "weekStart": ""
}
```

---

## 5. Audit Analytics — Query Patterns

**Endpoint:** `GET /analytics/audit` (admin only)

Query pattern analytics from audit logs:

```python
@app.get("/analytics/audit")
async def get_audit_analytics(
    since: str = "24h",
    token_payload: dict = Depends(get_current_user),
):
    """Aggregate audit analytics: query patterns, peak hours, top topics."""
    role = token_payload.get("role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin required")

    from datetime import datetime, timedelta, UTC
    from src.audit import get_audit_log

    # Parse time window
    hours = int(since.rstrip('h')) if since.endswith('h') else 24
    cutoff = datetime.now(UTC) - timedelta(hours=hours)

    log = get_audit_log()
    events = log.get_events_since(cutoff)

    # Filter query events
    query_events = [e for e in events if e.get("action") == "query"]

    # Top topics (extracted from query text)
    topic_counts: Dict[str, int] = {}
    for event in query_events:
        query = event.get("query_text", "")
        # Simple keyword extraction
        keywords = extract_keywords(query)
        for kw in keywords:
            topic_counts[kw] = topic_counts.get(kw, 0) + 1

    top_topics = sorted(topic_counts.items(), key=lambda x: -x[1])[:20]

    # Peak hours
    hour_counts: Dict[int, int] = {}
    for event in query_events:
        ts = event.get("timestamp")
        if ts:
            hour = datetime.fromisoformat(ts).hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

    peak_hours = sorted(hour_counts.items(), key=lambda x: -x[1])[:3]

    # Tier distribution
    tier_counts: Dict[str, int] = {}
    for event in query_events:
        tier = str(event.get("user_tier", "unknown"))
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    # Error rate
    error_count = sum(1 for e in query_events if e.get("status") == "error")
    total_count = len(query_events)
    error_rate = error_count / total_count if total_count > 0 else 0

    return {
        "window": since,
        "total_queries": total_count,
        "error_rate": round(error_rate, 4),
        "unique_users": len(set(e.get("user_id") for e in query_events)),
        "top_topics": [{"topic": t, "count": c} for t, c in top_topics],
        "peak_hours": [{"hour": h, "count": c} for h, c in peak_hours],
        "tier_distribution": [{"tier": t, "count": c} for t, c in tier_counts.items()],
    }
```

---

## 6. Cost Tracking

**File:** `src/observability/cost_tracker.py`

Track daily token usage and estimated cost per provider:

```python
"""LLM Cost Tracking — per provider, per day."""

from datetime import datetime, date
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict
import threading

# NVIDIA / OpenAI pricing (per 1M tokens — as of 2024)
PRICING_PER_1M = {
    "nvidia/llama-3.1-70b-instruct": {"input": 0.0, "output": 0.0},  # Enterprise negotiated
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "anthropic/claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "local/llamacpp": {"input": 0.0, "output": 0.0},
    "rule_based": {"input": 0.0, "output": 0.0},
}

@dataclass
class DailyCostSnapshot:
    date: date
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    llm_calls: int = 0
    fallback_count: int = 0

    @property
    def estimated_cost(self) -> float:
        input_cost = (self.input_tokens / 1_000_000) * PRICING_PER_1M.get(f"{self.provider}/{self.model}", {"input": 0, "output": 0})["input"]
        output_cost = (self.output_tokens / 1_000_000) * PRICING_PER_1M.get(f"{self.provider}/{self.model}", {"input": 0, "output": 0})["output"]
        return input_cost + output_cost

class CostTracker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._snapshots: Dict[tuple, DailyCostSnapshot] = {}
        return cls._instance

    def record(self, provider: str, model: str, input_tokens: int, output_tokens: int, fallback: bool = False):
        today = date.today()
        key = (today, provider, model)
        if key not in self._snapshots:
            self._snapshots[key] = DailyCostSnapshot(date=today, provider=provider, model=model)
        s = self._snapshots[key]
        s.input_tokens += input_tokens
        s.output_tokens += output_tokens
        s.llm_calls += 1
        if fallback:
            s.fallback_count += 1

    def get_daily_cost(self, day: date = None) -> Dict:
        day = day or date.today()
        daily = {k: v for k, v in self._snapshots.items() if k[0] == day}
        total = sum(s.estimated_cost for s in daily.values())
        return {
            "date": day.isoformat(),
            "total_estimated_cost_usd": round(total, 4),
            "by_provider": [
                {
                    "provider": v.provider,
                    "model": v.model,
                    "input_tokens": v.input_tokens,
                    "output_tokens": v.output_tokens,
                    "llm_calls": v.llm_calls,
                    "fallback_count": v.fallback_count,
                    "estimated_cost_usd": round(v.estimated_cost, 4),
                }
                for v in daily.values()
            ]
        }

_cost_tracker = CostTracker()

def track_llm_cost(provider: str, model: str, input_tokens: int, output_tokens: int, fallback: bool = False):
    """Call after every LLM response to track cost."""
    _cost_tracker.record(provider, model, input_tokens, output_tokens, fallback)
```

---

## 7. Incident Playbook

**File:** `docs/OPS_OBSERVABILITY_RUNBOOK.md`

### 7.1 LLM Error Rate > 10%

**Alert:** `HighLLMErrorRate`
**Severity:** Critical

**Diagnosis:**
```bash
# Check recent LLM errors
curl -s http://localhost:8000/health/llm | jq

# Check local LLM health
curl -s http://localhost:8080/health | jq

# Check NVIDIA API quota
# (via NVIDIA API portal)
```

**Mitigation:**
1. If NVIDIA API is down → local Llama.cpp fallback activates automatically
2. If local LLM is unhealthy → restart: `kubectl rollout restart deployment/llama-cpp -n nrg`
3. If quota exceeded → contact NVIDIA for limit increase; switch `LLM_PROVIDER=local` temporarily
4. Monitor fallback rate: Grafana → NRG Ops → LLM panel → fallback rate

**Runbook:** `https://wiki.internal/nrg/runbooks/llm-high-error-rate`

---

### 7.2 Query Latency > 30s (p95)

**Alert:** `QueryLatencyHigh`
**Severity:** Warning

**Diagnosis:**
```bash
# Check which node is slow
# Look at Langfuse traces for recent slow queries

# Check RAG retrieval latency
curl -s http://localhost:8000/health/qdrant | jq

# Check DB latency
curl -s http://localhost:8000/health/db | jq
```

**Mitigation:**
1. If Qdrant slow → check collection size; consider reducing `top_k` in retrieval
2. If DB slow → check for missing indexes; run `ANALYZE` on large tables
3. If LLM slow → check provider status; consider fallback to local model
4. If network → check Kong gateway latency

---

### 7.3 Cache Hit Rate < 50%

**Alert:** `CacheHitRateLow`
**Severity:** Info

**Mitigation:**
1. Run cache warming script with common queries
2. Increase cache TTL from 30s to 120s for `/stats` endpoint
3. Check if query patterns are too diverse (normal for research platform)

---

### 7.4 Qdrant Down

**Alert:** `QdrantDown`
**Severity:** Critical

**Impact:** RAG retrieval fails → LLM synthesizes without grounding context → hallucinations increase

**Mitigation:**
```bash
# Check Qdrant pod status
kubectl get pods -n nrg | grep qdrant

# Check Qdrant logs
kubectl logs -n nrg -l app=qdrant --tail=100

# If pod is CrashLoopBackOff:
kubectl describe pod -n nrg -l app=qdrant

# If disk full → expand PVC
kubectl patch pvc qdrant-storage -n nrg -p '{"spec":{"resources":{"requests":{"storage":"50Gi"}}}}'

# Restart Qdrant
kubectl rollout restart deployment/qdrant -n nrg
```

---

### 7.5 Audit Chain Broken

**Alert:** `AuditChainBroken`
**Severity:** Critical

**Mitigation:**
```bash
# Check which audit event broke the chain
curl -s http://localhost:8000/audit/verify \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# If minor → seal next event to continue
# DO NOT modify audit log directly

# If tampering suspected → escalate to security team immediately
# Preserve all logs and pod logs for forensics
```

---

### 7.6 Egress Violation Blocked

**Alert:** `EgressViolation`
**Severity:** Critical

**Mitigation:**
```bash
# Check which request triggered the violation
kubectl logs -n nrg -l app=nrg-api --tail=500 | grep EGRESS

# The egress guard blocked the request; investigate the query
# If legitimate (e.g., cross-border collaboration) → review egress rules
# If attack → block source IP at firewall
```

---

### 7.7 Prompt Injection Spike

**Alert:** `PromptInjectionSpike`
**Severity:** Critical

**Mitigation:**
```bash
# Check blocked injection patterns
kubectl logs -n nrg -l app=nrg-api --tail=200 | grep INJECTION

# Identify source IPs
# Block at Kong gateway:
kubectl exec -n kong deploy/kong -- kong config db_changed \
  --selector "source==$ATTACKER_IP" --ttl 3600

# Rate limit the affected routes
```

---

## 8. Implementation Checklist

| Item | Priority | Status | File |
|------|----------|--------|------|
| Wire `/metrics` endpoint | P0 | ✅ DONE | `src/api/main.py` |
| Add Router tracing | P0 | TODO | `src/orchestration/nodes/router.py` |
| Call `count_llm_tokens()` after every LLM response | P0 | TODO | Each node's LLM call site |
| Call `count_query()` at API boundary | P0 | TODO | `src/api/main.py` |
| Track fallback cascade in metrics | P1 | TODO | `src/config/llm_config.py` |
| Record `nrg_llm_latency_seconds` per call | P1 | TODO | Each node's LLM call site |
| Expose cost tracker via `/analytics/cost` | P1 | TODO | `src/api/main.py` |
| Fix Prometheus alert metric names | P1 | TODO | `infrastructure/prometheus/alerts.yaml` |
| Add Grafana dashboard JSON | P1 | TODO | `infrastructure/grafana/dashboards/` |
| Create Langfuse dashboard (cloud/langfuse.com) | P2 | TODO | Langfuse cloud dashboard |
| Connect Prometheus alerts to alertmanager | P2 | TODO | AlertManager config |
| Add this runbook to wiki | P2 | TODO | Internal wiki |

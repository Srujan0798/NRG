"""Prometheus metrics for NRG observability - complete metrics definitions."""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator
from functools import wraps
from typing import Callable, Any
import time
import os


app_info = Info('nrg_app', 'NRG application information')
app_info.info({'version': os.getenv("NRG_VERSION", "1.0.0"), 'environment': os.getenv("ENV", "production")})


# ── Query Metrics ─────────────────────────────────────────────────────────────
nrg_queries_total = Counter(
    'nrg_queries_total',
    'Total queries processed',
    ['tier', 'intent', 'status']
)

queries_total = Counter(
    'nrg_queries_processed_total',
    'Total queries processed (alias)',
    ['tier', 'intent']
)

nrg_query_latency_seconds = Histogram(
    'nrg_query_duration_seconds',
    'Query latency distribution',
    ['tier', 'intent'],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0, 60.0]
)

query_duration_seconds = Histogram(
    'nrg_query_duration_seconds_histogram',
    'Query latency histogram',
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0, 60.0]
)


# ── LLM Metrics ────────────────────────────────────────────────────────────────
llm_fallback_total = Counter(
    'nrg_llm_fallback_total',
    'LLM fallback activations',
    ['provider']
)

nrg_llm_tokens_total = Counter(
    'nrg_llm_tokens_total',
    'LLM tokens consumed',
    ['role', 'provider', 'model']
)

nrg_llm_latency_seconds = Histogram(
    'nrg_llm_latency_seconds',
    'LLM call latency',
    ['role', 'provider', 'model'],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0]
)

token_usage = Histogram(
    'nrg_token_usage',
    'Tokens per request',
    ['provider'],
    buckets=[100, 500, 1000, 2000, 5000, 10000, 20000, 50000]
)


# ── Cache Metrics ──────────────────────────────────────────────────────────────
cache_hits_total = Counter(
    'nrg_cache_hits_total',
    'Cache hits'
)

nrg_cache_hits_total = Counter(
    'nrg_cache_hit_total',
    'Cache hits (alias)'
)

nrg_cache_misses_total = Counter(
    'nrg_cache_misses_total',
    'Cache misses'
)

nrg_cache_lookup_total = Counter(
    'nrg_cache_lookup_total',
    'Total cache lookups'
)


# ── Skill Metrics ──────────────────────────────────────────────────────────────
nrg_skill_latency_seconds = Histogram(
    'nrg_skill_latency_seconds',
    'Skill execution latency',
    ['skill_name'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

nrg_skill_errors_total = Counter(
    'nrg_skill_errors_total',
    'Skill execution errors',
    ['skill_name', 'error_type']
)


# ── Security Metrics ───────────────────────────────────────────────────────────
nrg_pii_block_total = Counter(
    'nrg_pii_block_total',
    'PII blocks',
    ['entity_type']
)

nrg_injection_block_total = Counter(
    'nrg_injection_block_total',
    'Prompt injection blocks'
)

nrg_egress_block_total = Counter(
    'nrg_egress_block_total',
    'Egress sovereignty violations'
)


# ── Audit Metrics ──────────────────────────────────────────────────────────────
nrg_audit_chain_ok = Gauge(
    'nrg_audit_chain_ok',
    'Audit chain integrity (1=ok, 0=broken)'
)

nrg_audit_events_total = Counter(
    'nrg_audit_events_total',
    'Total audit events',
    ['action']
)


# ── Rate Limiting ──────────────────────────────────────────────────────────────
nrg_rate_limited_total = Counter(
    'nrg_rate_limited_total',
    'Rate limit hits',
    ['user_tier']
)


# ── Database Metrics ──────────────────────────────────────────────────────────
nrg_db_connections_active = Gauge(
    'nrg_db_connections_active',
    'Active database connections'
)

active_connections = Gauge(
    'nrg_active_connections',
    'Active DB connections'
)

nrg_db_query_latency_seconds = Histogram(
    'nrg_db_query_latency_seconds',
    'DB query latency',
    ['query_type'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

queue_depth = Gauge(
    'nrg_queue_depth',
    'Pending queries'
)


# ── Infrastructure Metrics ─────────────────────────────────────────────────────
nrg_api_up = Gauge(
    'nrg_api_up',
    'API service up (1=up, 0=down)'
)

nrg_llm_provider_status = Gauge(
    'nrg_llm_provider_status',
    'LLM provider health (1=up, 0=down)',
    ['provider']
)


def instrument_app(app):
    """Instrument FastAPI app with Prometheus."""
    Instrumentator().instrument(app).expose(app)


def timed_metric(metric: Histogram):
    """Decorator to time function execution."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                metric.observe(duration)
        return wrapper
    return decorator


def count_query(tier: int, intent: str, status: str = "success"):
    """Count a query."""
    tier_label = str(tier)
    nrg_queries_total.labels(tier=tier_label, intent=intent, status=status).inc()
    queries_total.labels(tier=tier_label, intent=intent).inc()


def record_query_latency(tier: int, intent: str, duration: float):
    """Record query latency histogram."""
    tier_label = str(tier)
    nrg_query_latency_seconds.labels(tier=tier_label, intent=intent).observe(duration)
    query_duration_seconds.observe(duration)


def count_cache_hit():
    """Count cache hit."""
    cache_hits_total.inc()
    nrg_cache_hits_total.inc()
    nrg_cache_lookup_total.inc()


def count_cache_miss():
    """Count cache miss."""
    nrg_cache_misses_total.inc()
    nrg_cache_lookup_total.inc()


def count_llm_fallback(provider: str):
    """Count LLM fallback activation."""
    llm_fallback_total.labels(provider=provider).inc()


def count_llm_tokens(role: str, provider: str, model: str, tokens: int):
    """Count LLM tokens."""
    nrg_llm_tokens_total.labels(role=role, provider=provider, model=model).inc(tokens)
    token_usage.labels(provider=provider).observe(tokens)


def record_llm_latency(role: str, provider: str, model: str, duration: float):
    """Record LLM call latency."""
    nrg_llm_latency_seconds.labels(role=role, provider=provider, model=model).observe(duration)


def count_pii_block(entity_type: str):
    """Count PII block."""
    nrg_pii_block_total.labels(entity_type=entity_type).inc()


def count_injection_block():
    """Count injection block."""
    nrg_injection_block_total.inc()


def count_egress_block():
    """Count egress violation."""
    nrg_egress_block_total.inc()


def count_audit_event(action: str):
    """Count audit event."""
    nrg_audit_events_total.labels(action=action).inc()


def set_audit_chain_ok(ok: bool):
    """Set audit chain status."""
    nrg_audit_chain_ok.set(1 if ok else 0)


def count_skill_error(skill_name: str, error_type: str):
    """Count skill error."""
    nrg_skill_errors_total.labels(skill_name=skill_name, error_type=error_type).inc()


def record_skill_latency(skill_name: str, duration: float):
    """Record skill latency."""
    nrg_skill_latency_seconds.labels(skill_name=skill_name).observe(duration)


def count_rate_limited(user_tier: int):
    """Count rate limited request."""
    nrg_rate_limited_total.labels(user_tier=str(user_tier)).inc()


def set_db_connections(count: int):
    """Set active DB connections."""
    nrg_db_connections_active.set(count)
    active_connections.set(count)


def set_queue_depth(depth: int):
    """Set queue depth."""
    queue_depth.set(depth)


def set_api_up(up: bool):
    """Set API up status."""
    nrg_api_up.set(1 if up else 0)


def set_llm_provider_status(provider: str, up: bool):
    """Set LLM provider status."""
    nrg_llm_provider_status.labels(provider=provider).set(1 if up else 0)


def record_db_latency(query_type: str, duration: float):
    """Record database query latency."""
    nrg_db_query_latency_seconds.labels(query_type=query_type).observe(duration)


def get_metrics():
    """Get Prometheus metrics for /metrics endpoint."""
    return generate_latest()


def get_metrics_content_type():
    """Get content type for metrics."""
    return CONTENT_TYPE_LATEST


class MetricsCollector:
    """Helper class to collect metrics for a single request."""
    
    def __init__(self, tier: int, intent: str):
        self.tier = tier
        self.intent = intent
        self.start_time = time.time()
        self.llm_calls = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type:
            count_query(self.tier, self.intent, "error")
            record_query_latency(self.tier, self.intent, duration)
        else:
            count_query(self.tier, self.intent, "success")
            record_query_latency(self.tier, self.intent, duration)
    
    def record_llm_call(self, provider: str, model: str, tokens: int, duration: float):
        """Record an LLM call within this request."""
        count_llm_tokens(self.intent, provider, model, tokens)
        record_llm_latency(self.intent, provider, model, duration)
        self.llm_calls.append({
            "provider": provider,
            "model": model,
            "tokens": tokens,
            "duration": duration
        })
    
    def record_cache_hit(self):
        """Record cache hit."""
        count_cache_hit()
    
    def record_cache_miss(self):
        """Record cache miss."""
        count_cache_miss()
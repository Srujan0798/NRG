"""Prometheus metrics for NRG observability."""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator
from functools import wraps
from typing import Callable, Any
import time


# Application info
app_info = Info('nrg_app', 'NRG application information')
app_info.info({'version': '1.0.0', 'environment': 'production'})

# Custom metrics
# Query metrics
nrg_queries_total = Counter(
    'nrg_queries_total',
    'Total queries processed',
    ['tier', 'intent', 'status']
)

nrg_query_latency_seconds = Histogram(
    'nrg_query_latency_seconds',
    'Query latency distribution',
    ['tier', 'intent'],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0]
)

# Skill metrics
nrg_skill_latency_seconds = Histogram(
    'nrg_skill_latency_seconds',
    'Skill execution latency',
    ['skill_name'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
)

nrg_skill_errors_total = Counter(
    'nrg_skill_errors_total',
    'Skill execution errors',
    ['skill_name', 'error_type']
)

# LLM metrics
nrg_llm_tokens_total = Counter(
    'nrg_llm_tokens_total',
    'LLM tokens consumed',
    ['role', 'provider', 'model']
)

nrg_llm_latency_seconds = Histogram(
    'nrg_llm_latency_seconds',
    'LLM call latency',
    ['role', 'provider'],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 30.0, 60.0]
)

# Cache metrics
nrg_cache_hits_total = Counter(
    'nrg_cache_hits_total',
    'Cache hits'
)

nrg_cache_misses_total = Counter(
    'nrg_cache_misses_total',
    'Cache misses'
)

nrg_cache_lookup_total = Counter(
    'nrg_cache_lookup_total',
    'Total cache lookups'
)

# Security metrics
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

# Audit metrics
nrg_audit_chain_ok = Gauge(
    'nrg_audit_chain_ok',
    'Audit chain integrity (1=ok, 0=broken)'
)

nrg_audit_events_total = Counter(
    'nrg_audit_events_total',
    'Total audit events',
    ['action']
)

# Rate limit metrics
nrg_rate_limited_total = Counter(
    'nrg_rate_limited_total',
    'Rate limit hits',
    ['user_tier']
)

# Database metrics
nrg_db_connections_active = Gauge(
    'nrg_db_connections_active',
    'Active database connections'
)

nrg_db_query_latency_seconds = Histogram(
    'nrg_db_query_latency_seconds',
    'DB query latency',
    ['query_type'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
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
    nrg_queries_total.labels(tier=tier, intent=intent, status=status).inc()


def count_cache_hit():
    """Count cache hit."""
    nrg_cache_hits_total.inc()
    nrg_cache_lookup_total.inc()


def count_cache_miss():
    """Count cache miss."""
    nrg_cache_misses_total.inc()
    nrg_cache_lookup_total.inc()


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


def count_llm_tokens(role: str, provider: str, model: str, tokens: int):
    """Count LLM tokens."""
    nrg_llm_tokens_total.labels(role=role, provider=provider, model=model).inc(tokens)


def get_metrics():
    """Get Prometheus metrics for /metrics endpoint."""
    return generate_latest()


def get_metrics_content_type():
    """Get content type for metrics."""
    return CONTENT_TYPE_LATEST

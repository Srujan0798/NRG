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

nrg_audit_db_cosign_submitted = Gauge(
    'nrg_audit_db_cosign_submitted',
    'DB audit co-sign background tasks submitted'
)

nrg_audit_db_cosign_succeeded = Gauge(
    'nrg_audit_db_cosign_succeeded',
    'DB audit co-sign background tasks completed successfully'
)

nrg_audit_db_cosign_failed = Gauge(
    'nrg_audit_db_cosign_failed',
    'DB audit co-sign background tasks failed'
)

nrg_audit_db_cosign_queue_depth = Gauge(
    'nrg_audit_db_cosign_queue_depth',
    'Pending DB audit co-sign background tasks'
)

nrg_audit_db_cosign_success_rate = Gauge(
    'nrg_audit_db_cosign_success_rate',
    'DB audit co-sign success rate for completed background tasks'
)

nrg_audit_db_cosign_latency_seconds = Gauge(
    'nrg_audit_db_cosign_latency_seconds',
    'Last DB audit co-sign background task latency in seconds'
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


def set_audit_db_cosign_metrics(metrics: dict):
    """Publish DB co-sign worker metrics to Prometheus gauges."""
    nrg_audit_db_cosign_submitted.set(float(metrics.get("submitted", 0) or 0))
    nrg_audit_db_cosign_succeeded.set(float(metrics.get("succeeded", 0) or 0))
    nrg_audit_db_cosign_failed.set(float(metrics.get("failed", 0) or 0))
    nrg_audit_db_cosign_queue_depth.set(float(metrics.get("queue_depth", 0) or 0))
    nrg_audit_db_cosign_success_rate.set(float(metrics.get("success_rate", 1.0) or 0.0))
    latency_ms = metrics.get("last_latency_ms")
    if latency_ms is not None:
        nrg_audit_db_cosign_latency_seconds.set(float(latency_ms) / 1000.0)


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
    """Get content type and metrics output for Prometheus endpoint."""
    from prometheus_client import generate_latest, REGISTRY
    return CONTENT_TYPE_LATEST, generate_latest(REGISTRY)


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


# ── SLO Metrics ────────────────────────────────────────────────────────────────
nrg_slo_breach_total = Counter(
    'nrg_slo_breach_total',
    'Total SLO breach events',
    ['breach_type']
)


def record_slo_breach(breach_type: str):
    """Record an SLO breach event."""
    nrg_slo_breach_total.labels(breach_type=breach_type).inc()


class SLOTracker:
    """In-process SLO tracker with breach alerting.

    Tracks:
    - Per-request latency samples (for P50/P95/P99 calculation)
    - Citation rate
    - Synthesis cascade distribution
    - Active concurrency
    - Breach windows for alerting

    Thread-safe using a lock.
    """

    # Production SLO targets - NRG Gold Standard
    SLO_P50_MS = 100   # Target: 100ms for simple queries
    SLO_P95_MS = 300   # Target: 300ms for P95
    SLO_P99_MS = 500   # Target: 500ms for P99 (NRT standard)
    SLO_CONCURRENCY_TARGET = 1000  # Target: 1000+ concurrent users
    SLO_CITATION_RATE = 0.90       # Target: 90% citations
    SLO_CLOUD_PCT = 0.85
    SLO_LOCAL_PCT = 0.10
    SLO_RULE_PCT = 0.05
    SLO_UPTIME_PCT = 99.9         # Target: 99.9% uptime
    SLO_DRIFT_SCORE = 0.85        # Target: 85% vector quality

    def __init__(self, max_samples: int = 10000):
        import threading
        self._lock = threading.Lock()
        self._latencies: list[float] = []
        self._max_samples = max_samples
        self._citation_count = 0
        self._total_count = 0
        self._cloud_count = 0
        self._local_count = 0
        self._rule_count = 0
        self._active_concurrency = 0
        self._max_concurrency = 0
        self._p95_breach_start: float | None = None
        self._consecutive_p99_breaches = 0
        self._citation_rate_breach_start: float | None = None
        self._drift_score: float | None = None
        self._uptime_seconds = 0.0
        self._uptime_failures = 0
        self._start_time = time.time()
        self._audit_breach_start: float | None = None
        self._audit_write_blocked = False
        self._provider_failure_starts: dict[str, float] = {}

    def record_latency(self, latency_ms: float):
        """Record a single query latency sample."""
        with self._lock:
            self._latencies.append(latency_ms)
            if len(self._latencies) > self._max_samples:
                self._latencies.pop(0)
            self._check_p95_breach(latency_ms)
            self._check_p99_breach(latency_ms)

    def record_citation(self, has_citation: bool, synthesis_method: str):
        """Record citation presence and synthesis method."""
        with self._lock:
            self._total_count += 1
            if has_citation:
                self._citation_count += 1
            method = synthesis_method.lower()
            if "cloud" in method:
                self._cloud_count += 1
            elif "local" in method:
                self._local_count += 1
            else:
                self._rule_count += 1
            self._check_citation_breach()

    def increment_concurrency(self):
        """Increment active concurrency counter."""
        with self._lock:
            self._active_concurrency += 1
            if self._active_concurrency > self._max_concurrency:
                self._max_concurrency = self._active_concurrency

    def decrement_concurrency(self):
        """Decrement active concurrency counter."""
        with self._lock:
            self._active_concurrency = max(0, self._active_concurrency - 1)

    def record_uptime_check(self, healthy: bool):
        """Record a health check result."""
        with self._lock:
            self._uptime_seconds += 1
            if not healthy:
                self._uptime_failures += 1

    def set_drift_score(self, score: float):
        """Set the current vector drift score."""
        with self._lock:
            self._drift_score = score

    def _check_p95_breach(self, latency_ms: float):
        """Log CRITICAL if P95 > 300ms for 5 consecutive minutes."""
        import logging as _logging
        logger = _logging.getLogger(__name__)
        if latency_ms > self.SLO_P95_MS:
            if self._p95_breach_start is None:
                self._p95_breach_start = time.time()
            elif time.time() - self._p95_breach_start >= 300:
                logger.critical(
                    "SLO BREACH: P95 latency > %dms for 5 consecutive minutes. "
                    "Current latency: %.1fms. SLO target: P95 < %dms",
                    self.SLO_P95_MS, latency_ms, self.SLO_P95_MS
                )
                record_slo_breach("p95_latency")
                self._p95_breach_start = None
        else:
            self._p95_breach_start = None

    def _check_p99_breach(self, latency_ms: float):
        """Log CRITICAL if P99 > 500ms for 5 consecutive requests."""
        import logging as _logging
        logger = _logging.getLogger(__name__)
        if latency_ms > self.SLO_P99_MS:
            self._consecutive_p99_breaches += 1
            if self._consecutive_p99_breaches >= 5:
                logger.critical(
                    "SLO BREACH: P99 latency > %dms (5 consecutive breaches). "
                    "Current latency: %.1fms. SLO target: P99 < %dms",
                    self.SLO_P99_MS, latency_ms, self.SLO_P99_MS
                )
                record_slo_breach("p99_latency")
                self._consecutive_p99_breaches = 0
                self._send_pagerduty_alert(latency_ms)
        else:
            self._consecutive_p99_breaches = 0

    def _send_pagerduty_alert(self, latency_ms: float):
        """Send CRITICAL PagerDuty alert when 5 consecutive P99 breaches detected."""
        try:
            from src.observability.pagerduty import send_critical_alert
            send_critical_alert(
                summary=f"NRG SLO BREACH: P99 > {self.SLO_P99_MS}ms for 5 consecutive requests (current: {latency_ms:.1f}ms)",
                source="nrg-slo-tracker",
                custom_details={
                    "slo_type": "p99_latency",
                    "threshold_ms": self.SLO_P99_MS,
                    "current_latency_ms": latency_ms,
                    "consecutive_breaches": 5,
                },
            )
        except Exception:
            pass

    def _check_citation_breach(self):
        """Log WARNING if citation rate < 50% for 1 hour."""
        import logging as _logging
        logger = _logging.getLogger(__name__)
        if self._total_count < 10:
            return
        rate = self._citation_count / self._total_count
        if rate < 0.50:
            if self._citation_rate_breach_start is None:
                self._citation_rate_breach_start = time.time()
            elif time.time() - self._citation_rate_breach_start >= 3600:
                logger.warning(
                    "SLO WARNING: Citation rate < 50%% for 1 hour. Current rate: %.1f%%. Target: > %.0f%%",
                    rate * 100, self.SLO_CITATION_RATE * 100
                )
                self._citation_rate_breach_start = None
        else:
            self._citation_rate_breach_start = None

    def check_audit_breach(self, chain_valid: bool, errors: list):
        """Log CRITICAL if audit chain verification fails; block writes if persistent."""
        import logging as _logging
        logger = _logging.getLogger(__name__)
        if chain_valid:
            self._audit_breach_start = None
            self._audit_write_blocked = False
            return
        if errors:
            if self._audit_breach_start is None:
                self._audit_breach_start = time.time()
            elif time.time() - self._audit_breach_start >= 300:
                logger.critical(
                    "AUDIT BREACH: Chain verification failed for 5 consecutive minutes. "
                    "Errors: %s. Blocking audit writes.", errors[:3]
                )
                self._audit_write_blocked = True
                self._audit_breach_start = None
        else:
            self._audit_breach_start = None
            self._audit_write_blocked = False

    def is_audit_write_blocked(self) -> bool:
        """Return True if audit writes should be blocked due to persistent chain failures."""
        return self._audit_write_blocked

    def check_provider_breach(self, provider: str, success_rate: float):
        """Log CRITICAL if a provider has 0%% success rate for 10 minutes."""
        import logging as _logging
        logger = _logging.getLogger(__name__)
        if success_rate > 0:
            self._provider_failure_starts.pop(provider, None)
            return
        now = time.time()
        last_failure = self._provider_failure_starts.get(provider, now)
        self._provider_failure_starts[provider] = last_failure
        if now - last_failure >= 600:
            logger.critical(
                "PROVIDER BREACH: %s has 0%% success rate for 10 minutes. "
                "Consider disabling or investigating.", provider
            )
            self._provider_failure_starts[provider] = now

    def get_percentiles(self) -> dict[str, float]:
        """Return P50/P95/P99 latency in ms."""
        with self._lock:
            if not self._latencies:
                return {"p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}
            sorted_latencies = sorted(self._latencies)
            n = len(sorted_latencies)
            p50_idx = int(n * 0.50)
            p95_idx = int(n * 0.95)
            p99_idx = int(n * 0.99)
            return {
                "p50_ms": round(sorted_latencies[min(p50_idx, n - 1)], 1),
                "p95_ms": round(sorted_latencies[min(p95_idx, n - 1)], 1),
                "p99_ms": round(sorted_latencies[min(p99_idx, n - 1)], 1),
            }

    def get_slo_status(self) -> dict[str, Any]:
        """Return full SLO status for /api/admin/slo endpoint."""
        with self._lock:
            if not self._latencies:
                percentiles = {"p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}
            else:
                sorted_latencies = sorted(self._latencies)
                n = len(sorted_latencies)
                p50_idx = int(n * 0.50)
                p95_idx = int(n * 0.95)
                p99_idx = int(n * 0.99)
                percentiles = {
                    "p50_ms": round(sorted_latencies[min(p50_idx, n - 1)], 1),
                    "p95_ms": round(sorted_latencies[min(p95_idx, n - 1)], 1),
                    "p99_ms": round(sorted_latencies[min(p99_idx, n - 1)], 1),
                }
            citation_rate = self._citation_count / self._total_count if self._total_count > 0 else 0.0
            total_synth = self._cloud_count + self._local_count + self._rule_count
            cloud_pct = self._cloud_count / total_synth if total_synth > 0 else 0.0
            local_pct = self._local_count / total_synth if total_synth > 0 else 0.0
            rule_pct = self._rule_count / total_synth if total_synth > 0 else 0.0
            uptime_pct = ((self._uptime_seconds - self._uptime_failures) / max(self._uptime_seconds, 1)) * 100

            latency_met = percentiles["p95_ms"] <= self.SLO_P95_MS
            concurrency_met = self._max_concurrency <= self.SLO_CONCURRENCY_TARGET
            citations_met = citation_rate >= self.SLO_CITATION_RATE
            synthesis_met = (
                cloud_pct >= self.SLO_CLOUD_PCT
                and local_pct <= self.SLO_LOCAL_PCT + 0.05
                and rule_pct <= self.SLO_RULE_PCT + 0.05
            )
            qdrant_met = (
                self._drift_score is None or self._drift_score >= self.SLO_DRIFT_SCORE
            )
            uptime_met = uptime_pct >= self.SLO_UPTIME_PCT

            all_met = latency_met and concurrency_met and citations_met and synthesis_met and qdrant_met and uptime_met

            return {
                "timestamp": time.time(),
                "report_period": "since_start",
                "latency": {
                    "p50_ms": percentiles["p50_ms"],
                    "p95_ms": percentiles["p95_ms"],
                    "p99_ms": percentiles["p99_ms"],
                    "slo_met": latency_met,
                    "target_p95_ms": self.SLO_P95_MS,
                },
                "concurrency": {
                    "active": self._active_concurrency,
                    "max_observed": self._max_concurrency,
                    "target": self.SLO_CONCURRENCY_TARGET,
                    "slo_met": concurrency_met,
                },
                "synthesis": {
                    "cloud_pct": round(cloud_pct * 100, 1),
                    "local_pct": round(local_pct * 100, 1),
                    "rule_pct": round(rule_pct * 100, 1),
                    "slo_met": synthesis_met,
                },
                "citations": {
                    "rate": round(citation_rate, 3),
                    "target": self.SLO_CITATION_RATE,
                    "slo_met": citations_met,
                },
                "qdrant": {
                    "drift_score": self._drift_score,
                    "target": self.SLO_DRIFT_SCORE,
                    "slo_met": qdrant_met,
                },
                "uptime": {
                    "uptime_pct": round(uptime_pct, 3),
                    "target": self.SLO_UPTIME_PCT,
                    "slo_met": uptime_met,
                    "total_checks": int(self._uptime_seconds),
                    "failures": self._uptime_failures,
                },
                "overall": "GREEN" if all_met else "RED",
            }


_slo_tracker: SLOTracker | None = None


def get_slo_tracker() -> SLOTracker:
    """Get the global SLO tracker instance (singleton)."""
    global _slo_tracker
    if _slo_tracker is None:
        _slo_tracker = SLOTracker()
    return _slo_tracker

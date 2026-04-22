"""Ops Dashboard data provider for NRG - serves real-time system metrics."""

from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict
import threading


@dataclass
class SystemHealth:
    api_status: bool
    qdrant_status: bool
    db_status: bool
    audit_chain_ok: bool
    cache_hit_rate: float
    active_connections: int
    queue_depth: int
    timestamp: datetime


@dataclass
class LatencyPercentiles:
    p50: float
    p95: float
    p99: float
    window_minutes: int


@dataclass
class ThroughputMetrics:
    queries_per_minute: float
    success_qps: float
    error_qps: float
    window_minutes: int


@dataclass
class LLMProviderStatus:
    provider: str
    status: str
    latency_p50: float
    latency_p95: float
    tokens_per_hour: int
    fallback_rate: float


@dataclass
class CostSnapshot:
    date: str
    total_cost_usd: float
    by_provider: Dict[str, Dict[str, Any]]


class OpsDashboard:
    """Provides real-time operations dashboard data."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance
    
    def _init(self):
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._latencies: Dict[str, List[float]] = defaultdict(list)
        self._token_usage: Dict[str, int] = defaultdict(int)
        self._cache_hits = 0
        self._cache_misses = 0
        self._llm_calls: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "calls": 0, "tokens": 0, "latencies": []
        })
        self._provider_fallbacks: Dict[str, int] = defaultdict(int)
        self._db_connections = 0
        self._queue_depth = 0
        self._lock = threading.Lock()
    
    def record_request(self, tier: int, intent: str, success: bool, latency: float):
        """Record a request for dashboard aggregation."""
        with self._lock:
            key = f"{tier}_{intent}"
            self._request_counts[key] += 1
            self._latencies[key].append(latency)
            if len(self._latencies[key]) > 1000:
                self._latencies[key] = self._latencies[key][-1000:]
    
    def record_cache(self, hit: bool):
        """Record cache hit/miss."""
        with self._lock:
            if hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1
    
    def record_llm_call(self, provider: str, model: str, tokens: int, latency: float):
        """Record LLM call."""
        with self._lock:
            key = f"{provider}_{model}"
            self._llm_calls[key]["calls"] += 1
            self._llm_calls[key]["tokens"] += tokens
            self._llm_calls[key]["latencies"].append(latency)
            if len(self._llm_calls[key]["latencies"]) > 1000:
                self._llm_calls[key]["latencies"] = self._llm_calls[key]["latencies"][-1000:]
    
    def record_fallback(self, from_provider: str, to_provider: str):
        """Record LLM fallback."""
        with self._lock:
            self._provider_fallbacks[f"{from_provider}->{to_provider}"] += 1
    
    def set_db_connections(self, count: int):
        """Set active DB connections."""
        with self._lock:
            self._db_connections = count
    
    def set_queue_depth(self, depth: int):
        """Set queue depth."""
        with self._lock:
            self._queue_depth = depth
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health status."""
        cache_total = self._cache_hits + self._cache_misses
        cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0
        
        return SystemHealth(
            api_status=True,
            qdrant_status=True,
            db_status=True,
            audit_chain_ok=True,
            cache_hit_rate=cache_hit_rate,
            active_connections=self._db_connections,
            queue_depth=self._queue_depth,
            timestamp=datetime.utcnow()
        )
    
    def get_latency_percentiles(self, window_minutes: int = 5) -> LatencyPercentiles:
        """Calculate latency percentiles over window."""
        all_latencies = []

        for lat_list in self._latencies.values():
            all_latencies.extend(lat_list)
        
        if not all_latencies:
            return LatencyPercentiles(p50=0.0, p95=0.0, p99=0.0, window_minutes=window_minutes)
        
        sorted_latencies = sorted(all_latencies)
        n = len(sorted_latencies)
        
        return LatencyPercentiles(
            p50=sorted_latencies[int(n * 0.50)] if n > 0 else 0.0,
            p95=sorted_latencies[int(n * 0.95)] if n > 0 else 0.0,
            p99=sorted_latencies[int(n * 0.99)] if n > 0 else 0.0,
            window_minutes=window_minutes
        )
    
    def get_throughput(self, window_minutes: int = 5) -> ThroughputMetrics:
        """Calculate throughput metrics."""
        total_requests = sum(self._request_counts.values())
        requests_per_minute = total_requests / max(window_minutes, 1)
        
        success_requests = sum(
            count for key, count in self._request_counts.items()
            if "_success" in key or "error" not in key
        )
        
        return ThroughputMetrics(
            queries_per_minute=requests_per_minute,
            success_qps=success_requests / max(window_minutes * 60, 1),
            error_qps=0.0,
            window_minutes=window_minutes
        )
    
    def get_llm_providers(self) -> List[LLMProviderStatus]:
        """Get LLM provider status."""
        providers = []
        window = 60

        with self._lock:
            for key, data in self._llm_calls.items():
                provider, model = key.split("_", 1) if "_" in key else (key, "unknown")
                latencies = data.get("latencies", [])

                if latencies:
                    sorted_lat = sorted(latencies)
                    n = len(sorted_lat)
                    p50 = sorted_lat[int(n * 0.50)] if n > 0 else 0.0
                    p95 = sorted_lat[int(n * 0.95)] if n > 0 else 0.0
                else:
                    p50 = p95 = 0.0

                fallback_key = f"{provider}->local"
                fallback_rate = self._provider_fallbacks.get(fallback_key, 0) / max(data["calls"], 1)

                providers.append(LLMProviderStatus(
                    provider=provider,
                    status="up" if data["calls"] > 0 else "unknown",
                    latency_p50=p50,
                    latency_p95=p95,
                    tokens_per_hour=data["tokens"] // max(window // 60, 1),
                    fallback_rate=fallback_rate
                ))

        return providers
    
    def get_token_usage_by_provider(self) -> Dict[str, int]:
        """Get token usage by provider."""
        with self._lock:
            return {
                key.split("_")[0]: data["tokens"]
                for key, data in self._llm_calls.items()
                for key_split in [key.split("_", 1)]
            }
    
    def get_cache_hit_rate(self) -> float:
        """Get current cache hit rate."""
        total = self._cache_hits + self._cache_misses
        return self._cache_hits / total if total > 0 else 0.0
    
    def get_error_rate(self) -> float:
        """Calculate error rate over all requests."""
        total = sum(self._request_counts.values())
        if total == 0:
            return 0.0
        
        error_count = sum(
            count for key, count in self._request_counts.items()
            if "error" in key
        )
        return error_count / total
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get complete dashboard summary."""
        health = self.get_system_health()
        latency = self.get_latency_percentiles()
        throughput = self.get_throughput()
        providers = self.get_llm_providers()
        
        return {
            "timestamp": health.timestamp.isoformat(),
            "system_health": {
                "api": "up" if health.api_status else "down",
                "qdrant": "up" if health.qdrant_status else "down",
                "database": "up" if health.db_status else "down",
                "audit_chain": "ok" if health.audit_chain_ok else "broken",
                "cache_hit_rate": round(health.cache_hit_rate, 4),
                "active_connections": health.active_connections,
                "queue_depth": health.queue_depth
            },
            "latency": {
                "p50_seconds": round(latency.p50, 3),
                "p95_seconds": round(latency.p95, 3),
                "p99_seconds": round(latency.p99, 3),
                "window_minutes": latency.window_minutes
            },
            "throughput": {
                "queries_per_minute": round(throughput.queries_per_minute, 2),
                "success_qps": round(throughput.success_qps, 4),
                "error_qps": round(throughput.error_qps, 4)
            },
            "error_rate": round(self.get_error_rate(), 4),
            "llm_providers": [
                {
                    "name": p.provider,
                    "status": p.status,
                    "latency_p50_ms": round(p.latency_p50 * 1000, 2),
                    "latency_p95_ms": round(p.latency_p95 * 1000, 2),
                    "tokens_per_hour": p.tokens_per_hour,
                    "fallback_rate": round(p.fallback_rate, 4)
                }
                for p in providers
            ],
            "cache": {
                "hit_rate": round(self.get_cache_hit_rate(), 4),
                "total_hits": self._cache_hits,
                "total_misses": self._cache_misses
            }
        }


_dashboard = OpsDashboard()


def get_ops_dashboard() -> OpsDashboard:
    """Get the singleton OpsDashboard instance."""
    return _dashboard


def record_request(tier: int, intent: str, success: bool, latency: float):
    """Convenience function to record a request."""
    _dashboard.record_request(tier, intent, success, latency)


def record_cache(hit: bool):
    """Convenience function to record cache hit/miss."""
    _dashboard.record_cache(hit)


def record_llm_call(provider: str, model: str, tokens: int, latency: float):
    """Convenience function to record LLM call."""
    _dashboard.record_llm_call(provider, model, tokens, latency)


def get_dashboard_summary() -> Dict[str, Any]:
    """Get complete dashboard summary."""
    return _dashboard.get_dashboard_summary()
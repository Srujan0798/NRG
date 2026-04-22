"""Audit Analytics for NRG - query patterns, peak hours, topic distribution."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import threading
import hashlib
import re


@dataclass
class QueryAnalytics:
    total_queries: int
    unique_users: int
    error_rate: float
    top_queries: List[Dict[str, Any]]
    peak_hours: List[Dict[str, Any]]
    topic_distribution: List[Dict[str, Any]]
    tier_breakdown: List[Dict[str, Any]]
    intent_distribution: Dict[str, int]
    failed_patterns: List[Dict[str, Any]]


@dataclass
class AuditEvent:
    event_id: str
    timestamp: datetime
    user_id: str
    user_tier: int
    action: str
    query_text: str
    intent: str
    status: str
    latency_ms: float
    tokens_used: int
    provider: str
    error: Optional[str] = None


class AuditAnalytics:
    """Analyzes audit logs and query patterns."""
    
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
        self._events: List[AuditEvent] = []
        self._query_hash_counts: Dict[str, int] = defaultdict(int)
        self._hour_counts: Dict[int, int] = defaultdict(int)
        self._tier_counts: Dict[int, int] = defaultdict(int)
        self._intent_counts: Dict[str, int] = defaultdict(int)
        self._topic_counts: Dict[str, int] = defaultdict(int)
        self._failed_patterns: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._max_events = 100000
    
    def record_event(
        self,
        user_id: str,
        user_tier: int,
        action: str,
        query_text: str,
        intent: str,
        status: str,
        latency_ms: float,
        tokens_used: int = 0,
        provider: str = "unknown",
        error: Optional[str] = None
    ):
        """Record an audit event."""
        with self._lock:
            query_hash = hashlib.md5(query_text.encode()).hexdigest()[:16]
            
            event = AuditEvent(
                event_id=f"{datetime.utcnow().timestamp()}_{query_hash}",
                timestamp=datetime.utcnow(),
                user_id=user_id,
                user_tier=user_tier,
                action=action,
                query_text=query_text[:500],
                intent=intent,
                status=status,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                provider=provider,
                error=error
            )
            
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]
            
            self._query_hash_counts[query_hash] += 1
            self._hour_counts[datetime.utcnow().hour] += 1
            self._tier_counts[user_tier] += 1
            self._intent_counts[intent] += 1
            
            topics = self._extract_topics(query_text)
            for topic in topics:
                self._topic_counts[topic] += 1
            
            if status == "error" and error:
                self._failed_patterns.append({
                    "query_preview": query_text[:100],
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat(),
                    "count": 1
                })
                if len(self._failed_patterns) > 100:
                    self._failed_patterns = self._failed_patterns[-100:]
    
    def _extract_topics(self, query_text: str) -> List[str]:
        """Extract topics/keywords from query text."""
        keywords = [
            "ai", "ml", "machine learning", "research", "publication",
            "funding", "grant", "lab", "university", "scientist",
            "paper", "conference", "dataset", "model", "nlp",
            "computer vision", "robotics", "data science", "deep learning"
        ]
        
        query_lower = query_text.lower()
        found_topics = []
        
        for keyword in keywords:
            if keyword in query_lower:
                found_topics.append(keyword)
        
        if not found_topics:
            found_topics = ["other"]
        
        return found_topics
    
    def _normalize_query(self, query_text: str) -> str:
        """Normalize query for grouping similar queries."""
        normalized = query_text.lower()
        normalized = re.sub(r'\d+', 'N', normalized)
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = ' '.join(normalized.split())
        return normalized[:100]
    
    def get_top_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most popular queries."""
        query_texts: Dict[str, int] = defaultdict(int)
        
        with self._lock:
            for event in self._events:
                self._normalize_query(event.query_text)
                query_texts[event.query_text[:100]] += 1
        
        sorted_queries = sorted(query_texts.items(), key=lambda x: -x[1])[:limit]
        
        return [
            {"query": q, "count": c, "hash": hashlib.md5(q.encode()).hexdigest()[:8]}
            for q, c in sorted_queries
        ]
    
    def get_peak_hours(self) -> List[Dict[str, Any]]:
        """Get peak usage hours as heatmap data."""
        with self._lock:
            hour_data = dict(self._hour_counts)
        
        return [
            {"hour": h, "count": hour_data.get(h, 0), "label": f"{h:02d}:00"}
            for h in range(24)
        ]
    
    def get_topic_distribution(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get topic distribution."""
        with self._lock:
            topics = dict(self._topic_counts)
        
        sorted_topics = sorted(topics.items(), key=lambda x: -x[1])[:limit]
        
        return [
            {"topic": t, "count": c, "percentage": round(c / sum(topics.values()) * 100, 2)}
            for t, c in sorted_topics
        ]
    
    def get_tier_breakdown(self) -> List[Dict[str, Any]]:
        """Get tier usage breakdown."""
        with self._lock:
            tiers = dict(self._tier_counts)
        
        total = sum(tiers.values())
        
        return [
            {
                "tier": t,
                "count": c,
                "percentage": round(c / total * 100, 2) if total > 0 else 0,
                "label": self._tier_label(t)
            }
            for t, c in sorted(tiers.items(), key=lambda x: -x[1])
        ]
    
    def _tier_label(self, tier: int) -> str:
        """Get human-readable tier label."""
        labels = {
            1: "Academic",
            2: "Government",
            3: "Corporate",
            4: "Enterprise"
        }
        return labels.get(tier, f"Tier {tier}")
    
    def get_intent_distribution(self) -> Dict[str, int]:
        """Get intent distribution."""
        with self._lock:
            return dict(self._intent_counts)
    
    def get_failed_query_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get failed query patterns for debugging."""
        with self._lock:
            patterns: Dict[str, Dict[str, Any]] = {}
            
            for fp in self._failed_patterns:
                key = fp["error"][:50] if fp["error"] else "unknown"
                if key not in patterns:
                    patterns[key] = {
                        "error_type": fp["error"],
                        "count": 0,
                        "examples": []
                    }
                patterns[key]["count"] += fp["count"]
                if len(patterns[key]["examples"]) < 3:
                    patterns[key]["examples"].append(fp["query_preview"])
        
        sorted_patterns = sorted(patterns.values(), key=lambda x: -x["count"])[:limit]
        
        return sorted_patterns
    
    def get_user_behavior(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get behavior analytics for specific user."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self._lock:
            user_events = [
                e for e in self._events
                if e.user_id == user_id and e.timestamp > cutoff
            ]
        
        if not user_events:
            return {"user_id": user_id, "events": 0, "message": "No recent activity"}
        
        intents = [e.intent for e in user_events]
        tiers = [e.user_tier for e in user_events]
        
        return {
            "user_id": user_id,
            "total_queries": len(user_events),
            "intents": dict(Counter(intents)),
            "tier": max(set(tiers), key=tiers.count) if tiers else 0,
            "avg_latency_ms": sum(e.latency_ms for e in user_events) / len(user_events),
            "error_rate": sum(1 for e in user_events if e.status == "error") / len(user_events),
            "unique_days": len(set(e.timestamp.date() for e in user_events))
        }
    
    def get_analytics_summary(self, window_hours: int = 24) -> QueryAnalytics:
        """Get complete analytics summary."""
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        
        with self._lock:
            recent_events = [e for e in self._events if e.timestamp > cutoff]
        
        total = len(recent_events)
        errors = sum(1 for e in recent_events if e.status == "error")
        
        unique_users = len(set(e.user_id for e in recent_events))
        
        return QueryAnalytics(
            total_queries=total,
            unique_users=unique_users,
            error_rate=round(errors / total, 4) if total > 0 else 0.0,
            top_queries=self.get_top_queries(20),
            peak_hours=self.get_peak_hours(),
            topic_distribution=self.get_topic_distribution(20),
            tier_breakdown=self.get_tier_breakdown(),
            intent_distribution=self.get_intent_distribution(),
            failed_patterns=self.get_failed_query_patterns(10)
        )
    
    def get_hourly_heatmap_data(self) -> Dict[str, Any]:
        """Get data for hourly heatmap visualization."""
        with self._lock:
            hour_counts = dict(self._hour_counts)
        
        return {
            "hours": list(range(24)),
            "counts": [hour_counts.get(h, 0) for h in range(24)],
            "labels": [f"{h:02d}:00" for h in range(24)]
        }


_analytics = AuditAnalytics()


def get_audit_analytics() -> AuditAnalytics:
    """Get the singleton AuditAnalytics instance."""
    return _analytics


def record_audit_event(
    user_id: str,
    user_tier: int,
    action: str,
    query_text: str,
    intent: str,
    status: str,
    latency_ms: float,
    tokens_used: int = 0,
    provider: str = "unknown",
    error: Optional[str] = None
):
    """Convenience function to record audit event."""
    _analytics.record_event(
        user_id=user_id,
        user_tier=user_tier,
        action=action,
        query_text=query_text,
        intent=intent,
        status=status,
        latency_ms=latency_ms,
        tokens_used=tokens_used,
        provider=provider,
        error=error
    )


def get_analytics_summary(window_hours: int = 24) -> QueryAnalytics:
    """Get analytics summary."""
    return _analytics.get_analytics_summary(window_hours)
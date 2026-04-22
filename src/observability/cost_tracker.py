"""Cost Tracking for NRG - token usage per provider, cost estimation, budget alerts."""

from datetime import datetime, date, timedelta
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Any, List
import threading
import os


PRICING_PER_1M = {
    "nvidia/llama-3.1-70b-instruct": {"input": 0.0, "output": 0.0},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "anthropic/claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "anthropic/claude-3-5-haiku": {"input": 0.80, "output": 4.00},
    "local/llamacpp": {"input": 0.0, "output": 0.0},
    "rule_based": {"input": 0.0, "output": 0.0},
}

DAILY_BUDGET_USD = float(os.getenv("NRG_DAILY_BUDGET", "100.0"))
MONTHLY_BUDGET_USD = float(os.getenv("NRG_MONTHLY_BUDGET", "3000.0"))


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
        key = f"{self.provider}/{self.model}"
        pricing = PRICING_PER_1M.get(key, {"input": 0.0, "output": 0.0})
        input_cost = (self.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost


@dataclass
class BudgetAlert:
    timestamp: datetime
    alert_type: str
    current_spend: float
    budget_limit: float
    percentage: float
    message: str


class CostTracker:
    """Tracks LLM cost per provider per day with budget alerts."""
    
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
        self._snapshots: Dict[tuple, DailyCostSnapshot] = {}
        self._monthly_start: date = date.today().replace(day=1)
        self._alerts: List[BudgetAlert] = []
        self._alerted_80: Dict[str, bool] = {}
        self._alerted_100: Dict[str, bool] = {}
        self._lock = threading.Lock()
    
    def record(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        fallback: bool = False
    ):
        """Record LLM usage and cost."""
        today = date.today()
        key = (today, provider, model)
        
        with self._lock:
            if key not in self._snapshots:
                self._snapshots[key] = DailyCostSnapshot(
                    date=today,
                    provider=provider,
                    model=model
                )
            
            s = self._snapshots[key]
            s.input_tokens += input_tokens
            s.output_tokens += output_tokens
            s.llm_calls += 1
            if fallback:
                s.fallback_count += 1
            
            self._check_budget_alerts(today, provider)
    
    def _check_budget_alerts(self, today: date, provider: str):
        """Check if budget thresholds are exceeded."""
        daily_cost = self.get_daily_cost(today).get("total_estimated_cost_usd", 0.0)
        monthly_cost = self.get_monthly_cost().get("total_estimated_cost_usd", 0.0)
        
        daily_pct = (daily_cost / DAILY_BUDGET_USD) * 100 if DAILY_BUDGET_USD > 0 else 0
        monthly_pct = (monthly_cost / MONTHLY_BUDGET_USD) * 100 if MONTHLY_BUDGET_USD > 0 else 0
        
        daily_key = f"daily_{today.isoformat()}"
        monthly_key = f"monthly_{today.strftime('%Y-%m')}"
        
        if daily_pct >= 80 and not self._alerted_80.get(daily_key, False):
            self._alerts.append(BudgetAlert(
                timestamp=datetime.utcnow(),
                alert_type="daily_80",
                current_spend=daily_cost,
                budget_limit=DAILY_BUDGET_USD,
                percentage=daily_pct,
                message=f"Daily budget at 80%: ${daily_cost:.2f} / ${DAILY_BUDGET_USD:.2f}"
            ))
            self._alerted_80[daily_key] = True
        
        if daily_pct >= 100 and not self._alerted_100.get(daily_key, False):
            self._alerts.append(BudgetAlert(
                timestamp=datetime.utcnow(),
                alert_type="daily_100",
                current_spend=daily_cost,
                budget_limit=DAILY_BUDGET_USD,
                percentage=daily_pct,
                message=f"Daily budget EXCEEDED: ${daily_cost:.2f} / ${DAILY_BUDGET_USD:.2f}"
            ))
            self._alerted_100[daily_key] = True
        
        if monthly_pct >= 80 and not self._alerted_80.get(monthly_key, False):
            self._alerts.append(BudgetAlert(
                timestamp=datetime.utcnow(),
                alert_type="monthly_80",
                current_spend=monthly_cost,
                budget_limit=MONTHLY_BUDGET_USD,
                percentage=monthly_pct,
                message=f"Monthly budget at 80%: ${monthly_cost:.2f} / ${MONTHLY_BUDGET_USD:.2f}"
            ))
            self._alerted_80[monthly_key] = True
        
        if monthly_pct >= 100 and not self._alerted_100.get(monthly_key, False):
            self._alerts.append(BudgetAlert(
                timestamp=datetime.utcnow(),
                alert_type="monthly_100",
                current_spend=monthly_cost,
                budget_limit=MONTHLY_BUDGET_USD,
                percentage=monthly_pct,
                message=f"Monthly budget EXCEEDED: ${monthly_cost:.2f} / ${MONTHLY_BUDGET_USD:.2f}"
            ))
            self._alerted_100[monthly_key] = True
    
    def get_daily_cost(self, day: date = None) -> Dict[str, Any]:
        """Get cost breakdown for a specific day."""
        day = day or date.today()
        
        with self._lock:
            daily = {k: v for k, v in self._snapshots.items() if k[0] == day}
        
        total = sum(s.estimated_cost for s in daily.values())
        
        return {
            "date": day.isoformat(),
            "total_estimated_cost_usd": round(total, 4),
            "daily_budget_usd": DAILY_BUDGET_USD,
            "budget_used_pct": round((total / DAILY_BUDGET_USD) * 100, 2) if DAILY_BUDGET_USD > 0 else 0,
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
    
    def get_monthly_cost(self, month: date = None) -> Dict[str, Any]:
        """Get cost breakdown for a month."""
        if month is None:
            month = date.today()
        
        month_start = month.replace(day=1)
        
        with self._lock:
            monthly = {
                k: v for k, v in self._snapshots.items()
                if k[0] >= month_start and k[0] <= month
            }
        
        total = sum(s.estimated_cost for s in monthly.values())
        
        return {
            "month": month.strftime("%Y-%m"),
            "total_estimated_cost_usd": round(total, 4),
            "monthly_budget_usd": MONTHLY_BUDGET_USD,
            "budget_used_pct": round((total / MONTHLY_BUDGET_USD) * 100, 2) if MONTHLY_BUDGET_USD > 0 else 0,
            "by_provider": self._aggregate_by_provider(monthly)
        }
    
    def _aggregate_by_provider(self, snapshots: Dict) -> List[Dict[str, Any]]:
        """Aggregate costs by provider."""
        provider_totals: Dict[str, Dict] = defaultdict(lambda: {
            "input_tokens": 0,
            "output_tokens": 0,
            "llm_calls": 0,
            "estimated_cost": 0.0
        })
        
        for s in snapshots.values():
            provider_totals[s.provider]["input_tokens"] += s.input_tokens
            provider_totals[s.provider]["output_tokens"] += s.output_tokens
            provider_totals[s.provider]["llm_calls"] += s.llm_calls
            provider_totals[s.provider]["estimated_cost"] += s.estimated_cost
        
        return [
            {
                "provider": provider,
                "input_tokens": data["input_tokens"],
                "output_tokens": data["output_tokens"],
                "llm_calls": data["llm_calls"],
                "estimated_cost_usd": round(data["estimated_cost"], 4)
            }
            for provider, data in provider_totals.items()
        ]
    
    def get_tier_cost_breakdown(self, day: date = None) -> Dict[str, Any]:
        """Get cost breakdown by user tier (estimated from tokens)."""
        return {
            "tier_1_academic": {"cost_usd": 0.0, "tokens": 0, "percentage": 0},
            "tier_2_government": {"cost_usd": 0.0, "tokens": 0, "percentage": 0},
            "tier_3_corporate": {"cost_usd": 0.0, "tokens": 0, "percentage": 0},
            "tier_4_enterprise": {"cost_usd": 0.0, "tokens": 0, "percentage": 0},
        }
    
    def get_cost_per_query(self) -> Dict[str, Any]:
        """Estimate average cost per query type."""
        return {
            "structured_sql": {"avg_tokens": 500, "estimated_cost_usd": 0.001},
            "unstructured_rag": {"avg_tokens": 2000, "estimated_cost_usd": 0.005},
            "hybrid": {"avg_tokens": 3500, "estimated_cost_usd": 0.008}
        }
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent budget alerts."""
        with self._lock:
            alerts = self._alerts[-limit:]
        
        return [
            {
                "timestamp": a.timestamp.isoformat(),
                "alert_type": a.alert_type,
                "current_spend_usd": round(a.current_spend, 4),
                "budget_limit_usd": a.budget_limit,
                "percentage": round(a.percentage, 2),
                "message": a.message
            }
            for a in alerts
        ]
    
    def get_cost_forecast(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Forecast cost for next N days based on current trajectory."""
        today = date.today()
        
        with self._lock:
            recent_daily_costs = []
            for i in range(7):
                day = today - timedelta(days=i)
                daily = {k: v for k, v in self._snapshots.items() if k[0] == day}
                cost = sum(s.estimated_cost for s in daily.values())
                recent_daily_costs.append({"date": day.isoformat(), "cost": cost})
        
        if recent_daily_costs:
            avg_daily_cost = sum(d["cost"] for d in recent_daily_costs) / len(recent_daily_costs)
        else:
            avg_daily_cost = 0.0
        
        projected_monthly = avg_daily_cost * 30
        remaining_monthly_budget = MONTHLY_BUDGET_USD - self.get_monthly_cost().get("total_estimated_cost_usd", 0)
        
        return {
            "avg_daily_cost_usd": round(avg_daily_cost, 4),
            "projected_monthly_cost_usd": round(projected_monthly, 2),
            "remaining_monthly_budget_usd": round(max(0, remaining_monthly_budget), 2),
            "budget_remaining_pct": round((remaining_monthly_budget / MONTHLY_BUDGET_USD) * 100, 2) if MONTHLY_BUDGET_USD > 0 else 0,
            "forecast_days": days_ahead,
            "projected_cost_for_period": round(avg_daily_cost * days_ahead, 2)
        }
    
    def get_full_report(self) -> Dict[str, Any]:
        """Get complete cost report."""
        return {
            "daily": self.get_daily_cost(),
            "monthly": self.get_monthly_cost(),
            "forecast": self.get_cost_forecast(),
            "recent_alerts": self.get_recent_alerts(),
            "pricing_model": {k: {"input_per_1m": v["input"], "output_per_1m": v["output"]} for k, v in PRICING_PER_1M.items()},
            "budgets": {
                "daily_budget_usd": DAILY_BUDGET_USD,
                "monthly_budget_usd": MONTHLY_BUDGET_USD
            }
        }


_cost_tracker = CostTracker()


def get_cost_tracker() -> CostTracker:
    """Get the singleton CostTracker instance."""
    return _cost_tracker


def track_llm_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    fallback: bool = False
):
    """Convenience function to track LLM cost."""
    _cost_tracker.record(provider, model, input_tokens, output_tokens, fallback)


def get_cost_report() -> Dict[str, Any]:
    """Get complete cost report."""
    return _cost_tracker.get_full_report()
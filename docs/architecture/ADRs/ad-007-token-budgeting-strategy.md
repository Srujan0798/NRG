# ADR-007: Token Budgeting Strategy

**Date:** 2026-04-21  
**Status:** Accepted  
**Deciders:** Architecture Team, ML Platform Team, Finance  
**Review:** 2026-07-21

---

## Context

NRG must manage LLM costs across multiple providers (NVIDIA, Anthropic) with:
- Budget constraints (₹40 crore project)
- Token quota management per organization
- Cost tracking and allocation
- Fallback cascade to prevent bill spikes

Token budgeting ensures we stay within allocated AI costs while maintaining service quality.

---

## Decision

Implement a **multi-tier token budgeting system** with:

1. **Per-organization quotas** (government, industry)
2. **Per-query limits** based on tier
3. **Monthly budget caps** with alerting
4. **Fallback cascade** to prevent cost overruns

---

## Token Budget Allocation

### Monthly Budget (Estimated)

Based on project budget of ₹40 crore over 3 years:

| Category | Monthly Budget (₹) | Token Limit | Rationale |
|----------|-------------------|-------------|-----------|
| Government orgs | 2,00,000 | 50M input + 20M output | Core users |
| Industry partners | 5,00,000 | 100M input + 50M output | Revenue generating |
| Research (IIT Gandhinagar) | 1,00,000 | Unlimited | Internal R&D |
| **Total** | **8,00,000** | **170M tokens/month** | |

### Per-Query Limits

| Tier | Max Input Tokens | Max Output Tokens | Priority |
|------|-----------------|------------------|----------|
| Researcher (Tier 1) | 32,768 | 8,192 | High |
| Government (Tier 2) | 16,384 | 4,096 | High |
| Industry (Tier 3) | 8,192 | 2,048 | Medium |

---

## Implementation

### Token Budget Service

```python
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
import redis.asyncio as redis

@dataclass
class TokenBudget:
    organization_id: str
    tier: int
    monthly_limit: int
    used_this_month: int
    reset_date: date

class TokenBudgetService:
    def __init__(self, redis: redis.Redis):
        self.redis = redis

    async def check_budget(self, org_id: str, tier: int, tokens_needed: int) -> bool:
        key = f"budget:{org_id}:{datetime.now().strftime('%Y-%m')}"

        current = await self.redis.get(key)
        current = int(current) if current else 0

        if current + tokens_needed > self.get_limit(tier):
            return False

        await self.redis.incrby(key, tokens_needed)
        await self.redis.expire(key, end_of_month_seconds())
        return True

    def get_limit(self, tier: int) -> int:
        limits = {1: 50_000_000, 2: 100_000_000, 3: 200_000_000}
        return limits.get(tier, 10_000_000)
```

### Budget Alerts

```python
async def check_budget_alerts(org_id: str, tier: int):
    key = f"budget:{org_id}:{datetime.now().strftime('%Y-%m')}"
    current = int(await redis.get(key) or 0)
    limit = get_limit(tier)
    usage_percent = (current / limit) * 100

    if usage_percent >= 90:
        send_alert(f"WARNING: {org_id} at {usage_percent:.1f}% budget")
    elif usage_percent >= 100:
        send_alert(f"CRITICAL: {org_id} exceeded budget")
        await disable_llm_for_org(org_id)
```

### LLM Fallback Cascade

```python
LLM_CASCADE = [
    {"provider": "nvidia", "model": "llama-3.1-70b", "cost_per_1k": 0.0},
    {"provider": "local", "model": "llamacpp-8b", "cost_per_1k": 0.0},
    {"provider": "rule_based", "cost_per_1k": 0.0},
]

async def synthesize_with_budget(query: str, org_id: str, tier: int):
    for llm in LLM_CASCADE:
        if await check_budget(org_id, tier, estimated_tokens(query)):
            return await call_llm(llm, query)
        logger.warning(f"Budget exceeded, falling back to {llm['provider']}")
    return await rule_based_synthesis(query)  # Always available
```

---

## Monitoring & Reporting

### Prometheus Metrics

```python
# Token budget metrics
nrg_budget_used = Gauge("nrg_budget_used_tokens", "Budget used", ["org_id", "tier"])
nrg_budget_remaining = Gauge("nrg_budget_remaining_tokens", "Budget remaining", ["org_id", "tier"])
nrg_budget_exceeded = Counter("nrg_budget_exceeded_total", "Budget exceeded count", ["org_id"])
```

### Monthly Report

```json
{
  "month": "2026-04",
  "total_spent": "₹4,50,000",
  "by_tier": {
    "1": {"spent": "₹50,000", "tokens": "10M"},
    "2": {"spent": "₹2,00,000", "tokens": "40M"},
    "3": {"spent": "₹2,00,000", "tokens": "45M"}
  },
  "budget_utilization": "56%",
  "projected_monthly_run_rate": "₹8,00,000"
}
```

---

## Consequences

### Positive
- Prevents budget overruns
- Clear cost allocation per organization
- Prioritization ensures critical users get service
- Automatic fallback maintains availability

### Negative
- Complexity in budget tracking
- Need to estimate token usage accurately
- False positives in budget alerts

### Risks
- Underestimating token costs
  - Mitigation: Conservative estimates, monitoring
- Budget exhaustion during critical period
  - Mitigation: Reserve budget for government tier

---

## Budget Review Schedule

| Review | Frequency | Scope |
|--------|-----------|-------|
| Daily | Monitoring | Alert thresholds |
| Weekly | Operations | Budget utilization vs plan |
| Monthly | Finance | Actual vs estimated, forecast |
| Quarterly | Steering | Budget reallocation |

---

**Reviewed by:** Finance, Architecture Team  
**Sign-off:** 2026-04-21
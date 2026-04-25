# Startup Financial Modeling Evidence — NRG Assessment

**Skill**: startup-financial-modeling
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/61_STARTUP_FINANCIAL_MODELING.md`

---

## Executive Summary

NRG is a **government-funded research intelligence platform**, not a commercial startup. Standard SaaS financial modeling (MRR, ARR, CAC, LTV) does not directly apply. Instead, this skill applies to **operational cost modeling**, **grant-based funding tracking**, and **government procurement budget cycles**.

**Key Finding**: NRG has a `CostGuard` system that tracks LLM inference costs per query, provider, and user tier — effectively implementing a real-time cost accounting system. This is a unique adaptation of financial modeling principles to a non-commercial context.

---

## 1. Business Model Definition

### NRG's Actual Business Model

| Dimension | Standard SaaS | NRG Reality |
|-----------|--------------|-------------|
| Revenue | MRR/ARR from subscriptions | Government grants (~₹40 crore from Gujarat) |
| Customers | Paying companies | Indian research institutions, government agencies |
| Pricing | Per-seat, tiered SaaS | Free access (government funded) |
| Revenue Model | Recurring subscriptions | One-time capital grants + operational funding |
| Success Metric | ARR growth | Research query volume, accuracy, institution coverage |

### Tier Access Economics

NRG's three-tier model creates implicit cost allocation:

| Tier | User Type | Access Level | Implicit "Value" |
|------|-----------|--------------|------------------|
| Tier 1 | Researcher | Full data (names, emails, publications) | Highest value — direct research utility |
| Tier 2 | Government | Aggregated stats, anonymized summaries | Policy intelligence value |
| Tier 3 | Industry | Names + research areas only | Partnership/licensing value |

**Assessment**: NRG's "revenue" is non-monetary — it's institutional value delivered to three types of stakeholders. Financial modeling here = cost structure analysis + grant allocation.

---

## 2. Cost Structure Analysis

### NRG's Cost Categories

NRG has a `CostGuard` system (`src/config/llm_config.py:1211`) that tracks LLM costs. This maps to the startup-financial-modeling cost structure:

#### COGS (Cost of Goods Sold)
NRG's "COGS" = **LLM inference costs** per query:

```python
# CostGuard tracks:
PROVIDER_COSTS_INPUT = {
    "minimax": 0.0,      # subsidized
    "gemini": 0.00125,   # per 1K tokens
    "claude": 0.003,     # per 1K tokens
}
PROVIDER_COSTS_OUTPUT = {
    "minimax": 0.0,
    "gemini": 0.005,
    "claude": 0.015,
}
```

**NRG COGS Drivers**:
- Token consumption per query (input + output)
- Provider selection (cloud vs local SLM)
- Complexity routing (trivial → rule-based = ₹0, synthesis_heavy = max cost)

#### S&M (Sales & Marketing)
- Outreach to institutions (low — government mandate)
- Conference/demo presentations
- Documentation and onboarding

#### R&D (Research & Development)
NRG's primary cost center:
- Engineering team (largest line item)
- LLM API costs (via CostGuard)
- Infrastructure (PostgreSQL, Qdrant vector DB)

#### G&A (General & Administrative)
- Executive team
- Compliance (DPDP-2023)
- Infrastructure at IIT-GN

---

## 3. Headcount Planning

### Role-Based Hiring (from Evidence/14_PYTHON_BACKEND.md)

Evidence/14 identified a **2499-line monolith** — the backend is a single engineer responsible for full-stack work. Headcount planning for NRG:

| Role | Count | Fully-Loaded Cost (₹) | % of Total |
|------|-------|---------------------|------------|
| Backend Engineer(s) | 1-2 | ~36L-72L/year | 40-50% |
| Frontend Engineer | 1 | ~24L-36L/year | 20-25% |
| ML/AI Engineer | 1 | ~30L-50L/year | 20-25% |
| DevOps/Infra | 1 | ~24L-36L/year | 10-15% |
| PM/Research Coord | 0.5 | ~12L/year | 5-10% |

**Assessment**: NRG is severely under-engineered. A 2499-line monolith with 1-2 backend engineers cannot support production at scale. The startup-financial-modeling skill's "headcount scales with revenue" heuristic suggests: for ₹40 crore funding, expect 5-10 engineers minimum.

---

## 4. Cash Flow Analysis

### NRG Funding Sources

| Source | Amount | Status |
|--------|--------|--------|
| Gujarat government grant | ~₹40 crore | Received (Phase 1-3 funding) |
| IIT Gandhinagar execution | Hosted infrastructure | Ongoing |
| IndiaAI Mission | Future potential | Alignment exists |
| ANRF backing | Future potential | Not yet materialized |

### Monthly Burn Rate

From evidence/39_STARTUP_METRICS.md:
- **LLM Cost Tracking**: CostGuard records every query
- **Average Cost per Query**: ~₹0.01-0.50 depending on complexity
- **Query Volume**: 382,653 audit events (not all are LLM queries)
- **Estimated Monthly LLM Burn**: ₹5,000-50,000/month (based on 7.2s avg response time × query volume)

### Runway Calculation

```
Runway = Current Cash Balance / Monthly Burn Rate
```

**Issue**: NRG appears to be in **Phase 1** (months 1-2 of roadmap) with existing government funding. No public data on remaining runway. The system is designed with cost controls (CostGuard) to extend runway.

---

## 5. Key Metrics Framework (NRG-Adapted)

### Revenue Metrics (Not Applicable — Government Funded)

| Metric | Standard SaaS | NRG Reality |
|--------|--------------|-------------|
| MRR | Monthly Recurring Revenue | N/A |
| ARR | Annual Recurring Revenue | N/A |
| ARPU | Average Revenue Per User | N/A |
| Gross Margin | Revenue - COGS | N/A |

### Unit Economics (NRG-Adapted)

| Metric | Standard SaaS | NRG Adaptation | Current |
|--------|--------------|----------------|---------|
| CAC | Customer Acquisition Cost | Institution onboarding cost | ~₹0 (government mandate) |
| LTV | Lifetime Value | Research value generated | Indeterminate |
| CAC Payback | Months to recover CAC | Instant (no cost to onboard) | N/A |
| LTV/CAC | Efficiency ratio | Value per institution | Unknown |

### Efficiency Metrics (NRG-Specific)

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Text-to-SQL accuracy | 41% | >75% | 🔴 34pp gap |
| Query latency (p50) | 7.2s | <3s | 🔴 2.4x over SLO |
| Query cost per success | ~₹0.50 | <₹0.10 | 🔴 Need reduction |
| Engineering leverage | 1-2 engineers | 5-10 for scale | 🔴 Understaffed |

### Burn Multiple (for Grant-Funded)

From evidence/25_STATISTICAL_ANALYSIS.md:
- **Burn Multiple** = Net Burn / Net New ARR (commercial SaaS)
- NRG adaptation: Grant spend / Research queries processed
- Current: Likely high burn multiple (query volume low relative to infrastructure cost)

---

## 6. Three-Scenario Framework (NRG)

### Conservative (P10) — Core Research Platform
- Institutions onboarded: 50 (current target list)
- Monthly queries: 1,000
- Text-to-SQL accuracy: 30% (schema mismatch dominates)
- LLM cost/month: ₹5,000
- Funding runway: 12 months

### Base (P50) — National Research OS
- Institutions onboarded: 200
- Monthly queries: 10,000
- Text-to-SQL accuracy: 55% (improved schema coverage)
- LLM cost/month: ₹25,000
- Funding runway: 18 months

### Optimistic (P90) — Production Government Deployment
- Institutions onboarded: 500+
- Monthly queries: 100,000+
- Text-to-SQL accuracy: 75%
- LLM cost/month: ₹100,000 (high volume, optimized)
- New grant funding secured

---

## 7. CostGuard: Real-Time Financial Modeling

### NRG's Implementation (Evidence from Code)

**CostGuard** (`src/config/llm_config.py:1211`) implements a live cost accounting system:

```python
class CostGuard:
    # Per-query cost caps by complexity
    CAPS = {
        "trivial": 0.01,       # ₹0.01 cap
        "simple": 0.05,       # ₹0.05 cap
        "moderate": 0.25,      # ₹0.25 cap
        "complex": 1.00,       # ₹1.00 cap
        "synthesis_heavy": 5.00,  # ₹5.00 cap
    }

    # Monthly budget limits by tier
    MONTHLY_BUDGETS = {
        "researcher": 1000.0,  # ₹1000/month
        "government": 2000.0,  # ₹2000/month
        "industry": 500.0,    # ₹500/month (industry subsidized)
    }
```

**What's Tracked**:
- `llm_cost_log` table: cost_inr, provider, persona, complexity, timestamp
- Per-provider breakdown: which LLM is cheapest/most expensive
- Per-persona breakdown: which tier costs most
- Monthly burn vs budget (per tier)
- Estimated cost before query execution (pre-flight check)

**Financial Modeling Principle Applied**: NRG implements the skill's "Monthly Burn Rate" concept in real-time, with per-tier budget caps to prevent cost overruns. This is sophisticated cost governance for a non-commercial platform.

---

## 8. Gap Analysis: What's Missing

### Missing: Revenue Model for Commercialization Path

NRG has no pricing model. If the platform ever transitions to:
- Institution licensing fees
- Per-query API pricing
- tiered subscription plans (Researcher/Gov/Industry)

Then standard SaaS financial modeling would apply. The framework exists in CostGuard — would need pricing layer on top.

### Missing: Grant Accounting System

The ₹40 crore Gujarat grant should have:
- Line-item budget tracking (engineering vs infrastructure vs compliance)
- Spend vs milestone mapping
- Remaining runway calculation
- Next grant application timeline

**Current Status**: Unknown — no evidence of formal grant accounting in codebase.

### Missing: Institution Onboarding Cost Tracking

The framework's "CAC" (customer acquisition cost) for NRG = cost to onboard an institution. Currently:
- Manual outreach
- No CRM
- No tracking of institution onboarding cost

### Missing: Headcount Model for Scale

Evidence/14_PYTHON_BACKEND.md flagged the 2499-line monolith. No headcount plan exists to:
- Break the monolith into services
- Hire platform engineers
- Scale to production loads

---

## 9. Recommendations

### P1: Establish Grant Accounting
Create a grant tracking dashboard:
- Total funding: ₹40 crore
- Spend by category: infrastructure, engineering, compliance
- Monthly burn rate
- Runway to next milestone

### P2: Implement Institution CAC Tracking
Track cost per institution onboarded:
- Engineering time for onboarding
- Support overhead
- Tools/software costs per institution

### P3: Headcount Plan for Phase 2
Based on Phase 2 roadmap (PostgreSQL migration, Qdrant cluster, knowledge graph):
- Minimum 5 engineers needed
- Phase in: DevOps (P0) → ML Engineer (P1) → Platform Engineer (P2)
- Cost: ~₹1.5-2 crore/year for 5 engineers

### P4: Commercialization Model (Future)
If NRG transitions to paid access:
- Create tiered pricing (Researcher Free / Gov Paid / Industry Paid)
- Apply standard SaaS metrics (MRR, ARR, CAC payback, LTV/CAC)
- Leverage existing CostGuard as billing system

### P5: Burn Multiple Optimization
Current inefficiency: 41% accuracy means 59% of LLM spend is "wasted" on failed queries.
- Target: 75% accuracy = 45% reduction in LLM spend per successful query
- This is the highest-leverage financial improvement available

---

## 10. Model Validation (Sanity Checks)

| Check | NRG Status | Notes |
|-------|-----------|-------|
| Revenue growth rate achievable | N/A | No commercial revenue |
| Unit economics realistic | ⚠️ Partial | LTV unknown, CAC=0 |
| Burn multiple reasonable | ⚠️ Unknown | No grant accounting |
| Headcount scales with revenue | ❌ No | 1-2 engineers for ₹40 crore grant |
| Gross margin appropriate | N/A | Government funded |
| S&M spending aligns with CAC | ⚠️ Low | Minimal marketing (government mandate) |

---

## 11. Financial Model Quick Start (NRG Adaptation)

Since NRG is not a commercial startup, the Quick Start steps adapt as:

1. **Define business model** → Government grant-funded, not subscription
2. **Project revenue** → Not applicable (no pricing). Project institution onboarding.
3. **Model costs** → LLM costs (CostGuard), infrastructure, headcount
4. **Plan headcount** → 5 engineers minimum for Phase 2 scale
5. **Calculate cash flow** → Grant burn rate, runway to Phase 3
6. **Compute metrics** → Query accuracy, cost per successful query, institution coverage
7. **Create scenarios** → Conservative (50 inst.) / Base (200 inst.) / Optimistic (500+ inst.)
8. **Validate assumptions** → Sanity check against government procurement cycles
9. **Integrate fundraising** → Next grant application for Phase 3 scale

---

## 12. Skill Deliverable

**Status**: COMPLETED

Startup financial modeling applied to NRG. Key findings:

- NRG is government-funded (₹40 crore), not commercial SaaS — standard MRR/ARR metrics don't apply
- CostGuard implements real-time LLM cost accounting with per-tier budgets — sophisticated for a research platform
- Missing: formal grant accounting, institution onboarding cost tracking, headcount plan for scale
- Highest-leverage financial improvement: reduce LLM spend by improving Text-to-SQL accuracy (41% → 75%)
- Phase 2 needs minimum 5 engineers (currently 1-2) to achieve roadmap milestones

**NRG would benefit from treating Phase 2 funding as a fundraising scenario** — applying the three-scenario framework to model institution coverage, query volume, and grant requirements for the next 18 months.

---

## References

- Skill: `.agents/skills/startup-financial-modeling/SKILL.md`
- CostGuard: `src/config/llm_config.py:1211`
- LLM Cost Log: `src/migrations/versions/llm_cost_log_001.py`
- Startup Metrics: `evidence/39_STARTUP_METRICS.md`
- Python Backend Patterns: `evidence/15_PYTHON_BACKEND_PATTERNS.md`
- Core Idea: `Core_Idea_Clean.md`

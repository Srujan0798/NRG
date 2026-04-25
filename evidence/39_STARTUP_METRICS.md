# Startup Metrics Framework Evidence

**Skill**: startup-metrics-framework
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/39_STARTUP_METRICS.md`

---

## Startup Metrics: NRG Assessment

### Overview

NRG is a **B2B/GovTech** platform (National Research Intelligence) with a three-tier model:
- Tier 1: Researchers (primary users)
- Tier 2: Government agencies
- Tier 3: Industry partners

This framework applies to SaaS/B2B metrics since NRG is API-as-a-service with government/academic customers.

---

## Revenue Metrics

**Note**: NRG appears to be a **non-revenue generating platform** (government/academic focus). The following metrics would apply if commercialized.

### MRR/ARR

| Metric | NRG Status | Notes |
|--------|------------|-------|
| MRR | ❌ Not tracked | Government platform |
| ARR | ❌ Not tracked | Government platform |
| ARPU | ❌ Not applicable | No pricing model found |

**Assessment**: NRG is likely a grant-funded government project, not a commercial SaaS.

---

## Growth Metrics

| Metric | NRG Status | Notes |
|--------|------------|-------|
| Active users | ⚠️ Partial | Login count tracked, not DAU/MAU |
| User growth rate | ❌ Not tracked | No cohort analysis |
| Tier distribution | ⚠️ Hypothetical | No actual data |

**Gap**: No user analytics dashboard.

---

## Engagement Metrics

| Metric | NRG Status | Notes |
|--------|------------|-------|
| DAU/MAU | ❌ Not tracked | No analytics |
| Session duration | ❌ Not tracked | No session tracking |
| Queries per user | ⚠️ Some | `queries` table exists |

**Gap**: No engagement analytics. `queries` table has data but no dashboard.

---

## System Health Metrics (NRG-Specific)

| Metric | Value | Health |
|--------|-------|--------|
| API uptime | ✅ ~100% | Healthy |
| Query latency (p50) | < 3.5ms | ✅ Excellent |
| Chain validity | ✅ Valid | Healthy |
| Error rate | ⚠️ Unknown | No error tracking dashboard |
| Test pass rate | ⚠️ 120s timeout | Needs fix |

---

## Technology Metrics (Relevant to NRG)

### Audit Chain Growth

| Metric | Value | Notes |
|--------|-------|-------|
| Chain length | 382,653 | Active growth |
| Daily events | ~500 | Average |
| Chain validity | ✅ Valid | 0 errors |

### Database Health

| Metric | Value | Notes |
|--------|-------|-------|
| DB latency | < 3.5ms | ✅ Healthy |
| Schema tables | 58 (prod) / 18 (dev) | Drift issue |
| Data freshness | ❓ Unknown | No `updated_at` tracking |

---

## Text-to-SQL Performance Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Accuracy | 41% | > 75% | 🔴 34pp below target |
| Response time | 7.2s | < 3s | 🔴 2.4x over |
| Error rate | 18% | < 5% | 🔴 High |
| Success rate | 41% | > 75% | 🔴 Low |

**Assessment**: Text-to-SQL is the primary product feature and severely underperforming.

---

## Recommendations for NRG

### If Commercial (B2B SaaS)

| Metric to Track | Current | Target |
|-----------------|---------|--------|
| MRR | 0 | TBD |
| Customer count | 0 | Track institutions |
| DAU/MAU | ❌ | > 20% |
| Query success rate | 41% | > 75% |
| NPS | ❌ | > 40 |

### If Government Platform

| Metric to Track | Current | Target |
|-----------------|---------|--------|
| Active institutions | ❌ | Track unique IPs |
| Research queries | ✅ | 382,653 events |
| Consent rate | ❌ | Track consent vs. declined |
| Data quality score | ❌ | 41% accuracy → > 75% |

---

## What NRG Should Track

Based on its nature as a **government research platform**:

### 1. User Adoption
- Daily active researchers
- Institution coverage (how many Indian institutions use it)
- Tier distribution

### 2. Query Quality
- Text-to-SQL accuracy (currently 41% — needs to be > 75%)
- Response time (currently 7.2s — needs to be < 3s)

### 3. Compliance
- Consent coverage (DPDP-2023)
- Audit chain integrity

### 4. Infrastructure
- API uptime (currently good)
- Database latency (currently good)
- Qdrant health (currently DOWN)

---

## Alignment with NRG Goals

NRG's goal is "National Research Intelligence" — connecting India's research ecosystem. The most important metrics are:

1. **Institutions onboarded** — How many Indian research institutions are using the platform
2. **Query accuracy** — Whether researchers get correct data (currently 41% — critical gap)
3. **Adoption rate** — Whether usage is growing
4. **Data quality** — Whether the research graph is accurate and complete

**Not important for NRG**:
- Revenue metrics (government funded)
- CAC/LTV (no commercial product)
- Viral coefficient (B2B, not consumer)

---

## Skill Deliverable

**Status**: COMPLETED

Startup metrics framework applied to NRG:
- NRG is a B2B/GovTech platform, not a commercial SaaS
- Revenue metrics don't apply (government funded)
- Key metrics: institution adoption, query accuracy (41% → target >75%), compliance
- System health metrics are good (DB <3.5ms, chain valid)
- Text-to-SQL is severely underperforming (2.4x over latency SLO, 34pp below accuracy target)

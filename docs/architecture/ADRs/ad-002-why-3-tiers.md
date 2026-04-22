# ADR-002: Why Three-Tier Access Architecture

**Date:** 2026-04-21  
**Status:** Accepted  
**Deciders:** Architecture Team, Security Team, Guardian Agent  
**Review:** 2026-07-21

---

## Context

NRG serves three distinctly different user categories with vastly different data sensitivity requirements and legal obligations:

1. **Researchers** (Tier 1): Full access to collaboration data, personal information, contact details
2. **Government** (Tier 2): Aggregate statistics for policy decisions, no personal data
3. **Industry** (Tier 3): Licensed, anonymized data only, no PII

DPDP-2023 mandates data minimization and purpose limitation. Each tier must have clear boundaries.

---

## Decision

Implement **three-tier access control** with the following characteristics:

### Tier 1 - Researcher Access
```yaml
Data Access:
  - Full researcher profiles (name, email, phone, address)
  - Publication details with author order
  - Project collaboration details
  - Direct messaging/contact capabilities
  - Personal h-index and citation data

Audit: Full query logging with user attribution
```

### Tier 2 - Government Access
```yaml
Data Access:
  - Aggregate statistics by state/institution
  - Funding trends by agency and year
  - Research output metrics (no personal attribution)
  - Institutional rankings
  - Sector-wise analysis

Audit: Aggregate-only logging
Restrictions: No PII, no individual researcher data
```

### Tier 3 - Industry Access
```yaml
Data Access:
  - Anonymized collaboration opportunities
  - Institution profiles (no personal contacts)
  - Publication trends (no author names)
  - Funding patterns

Audit: Anonymized metrics only
Restrictions: No PII, no individual attribution, licensing required
```

---

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **3-tier** (chosen) | Clear boundaries, DPDP aligned, simple SQL injection | Coarse granularity | ✅ Accepted |
| Attribute-based access (ABAC) | Fine-grained, dynamic | Complex policy engine, slower queries | ❌ Rejected |
| Role-based (RBAC) | Standard, familiar | Doesn't capture data sensitivity levels | ❌ Rejected |
| Custom per-use-case | Full control | Maintainability burden, inconsistent | ❌ Rejected |

---

## Rationale

### 1. DPDP-2023 Alignment
- **Purpose limitation**: Tier 2 matches "aggregate only" requirement
- **Data minimization**: Industry gets anonymized data only
- **Consent**: Researcher tier requires explicit consent for contact sharing

### 2. Clarity for Users
Users can easily understand their access level without complex explanations.

### 3. Implementation Simplicity
SQL filter injection per tier is straightforward:
```python
def apply_tier_filter(query: str, user_tier: int) -> str:
    """Add tier-based row filtering to queries."""
    if user_tier == 1:
        return query  # Full access
    elif user_tier == 2:
        return inject_aggregate_only(query)
    else:
        return inject_anonymized(query)
```

### 4. Security by Default
Missing tier fails closed — no access by default.

### 5. Audit Compliance
Each tier has clear audit requirements that map to DPDP obligations.

---

## Implementation

### Column-Level Filtering

```python
PII_COLUMNS = {
    "researchers": ["email", "phone", "address", "aadhaar"],
    "projects": ["budget_details", "team_composition"]
}

def filter_pii_columns(data: dict, user_tier: int) -> dict:
    """Remove PII columns based on user tier."""
    if user_tier > 1:
        return {k: v for k, v in data.items()
                if k not in PII_COLUMNS.get(table, [])}
    return data
```

### Row-Level Security (PostgreSQL)

```sql
-- Enable RLS
ALTER TABLE researchers ENABLE ROW LEVEL SECURITY;

-- Tier filter policy
CREATE POLICY tier_filter ON researchers
    FOR ALL
    USING (
        CASE current_setting('nrg.tier')::int
            WHEN 1 THEN true  -- Full access
            WHEN 2 THEN true  -- Aggregate only (application-level)
            WHEN 3 THEN true  -- Anonymized (application-level)
            ELSE false        -- Deny by default
        END
    );
```

### Application-Level Enforcement

```python
from functools import wraps

def tier_required(min_tier: int):
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            user_tier = get_current_user_tier()
            if user_tier > min_tier:
                raise HTTPException(403, "Insufficient tier access")
            return await f(*args, **kwargs)
        return wrapper
    return decorator
```

---

## Consequences

### Positive
- DPDP compliant by design
- Clear user mental model for data access
- Simple to audit and verify
- SQL filter injection prevents data leaks
- Scalable to additional tiers if needed

### Negative
- May need sub-tiers in future (e.g., government agency types)
- Some data duplication for different view levels
- Aggregate queries for Tier 2 may be complex

### Risks
- Tier misconfiguration could leak data
- Mitigation: Automated tier verification tests, RLS policies

---

## References

- [DPDP Compliance](docs/compliance/DPDP_2023_MAPPING.md)
- [RBAC Policy](docs/architecture/RBAC_POLICY.md)
- [PII Strategy ADR](docs/adr/ADR-004-pii-strategy.md)

---

**Reviewed by:** Guardian Agent, Security Team  
**Sign-off:** 2026-04-21
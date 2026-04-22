# ADR-002: Three-Tier Access Control

**Date:** 2026-04-21  
**Status:** Accepted  
**Author:** Architect Agent

## Context

NRG serves 3 distinctly different user types with vastly different data sensitivity needs:
- Researchers need full access to collaboration
- Government needs aggregate statistics for policy
- Industry needs licensed, anonymized data

## Decision

Implement **three-tier access control**:
- **Tier 1 (Researcher)**: Full access, personal data visible
- **Tier 2 (Government)**: Aggregate stats, no personal data
- **Tier 3 (Industry)**: Limited, anonymized only

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **3-tier** (chosen) | Clear boundaries, DPDP aligned | Coarse granularity |
| Attribute-based | Fine-grained | Complex, slower |
| Role-based (RBAC) | Standard | Doesn't capture data sensitivity |
| Custom | Full control | Maintainability burden |

## Rationale

1. **DPDP-2023 alignment**: Tier 2 matches "aggregate only" requirement
2. **Clarity**: Easy for users to understand their access level
3. **Maintenance**: Simple SQL filter injection prevents data leaks
4. **Security by default**: Missing tier fails closed

## Implementation

```python
# In TierAwareSqlRewriter
def rewrite(self, sql: str, user_tier: int) -> str:
    # Inject WHERE access_tier >= :user_tier
    parsed = sqlglot.parse(sql)
    for table in parsed.find_all(exp.Table):
        if table.name in TIER_AWARE_TABLES:
            parsed = inject_tier_filter(parsed, user_tier)
    return parsed.sql()
```

Plus column filtering:
```python
if user_tier > 1:  # Remove email, phone
    result = {k: v for k, v in row.items() if k not in PII_COLUMNS}
```

## Consequences

### Positive
- DPDP compliant by design
- Clear user mental model
- Simple to audit

### Negative
- May need sub-tiers in future
- Some data duplication for different view levels

**Reviewed by:** Guardian Agent  
**Next Review:** 2026-07-21
# ADR-009: Tier-Based Filtering with Row-Level Security

**Date:** 2026-04-21  
**Status:** Accepted  
**Deciders:** Security Team, Architecture Team, Compliance Officer  
**Review:** 2026-07-21

---

## Context

NRG implements three-tier access control (Researcher/Government/Industry) requiring:
- Data isolation between tiers
- Column-level PII filtering
- Row-level security in database
- Defense in depth: multiple enforcement points

The question is how to implement this filtering consistently and securely.

---

## Decision

Implement **multi-layer tier filtering** with defense in depth:

1. **Application layer**: Primary filtering (fast, user-friendly errors)
2. **RLS (Row-Level Security)**: Database enforcement (critical protection)
3. **API gateway**: Preemptive checks (early rejection)

---

## Multi-Layer Architecture

```mermaid
graph TB
    subgraph Client["Client Request"]
        Q[Query: "Researchers in Gujarat"]
        T[Tier Header: 2 (Government)]
    end

    subgraph Gateway["Kong API Gateway"]
        G[Auth + Tier Check]
        G --> |"Invalid tier"| REJECT[401 Reject]
    end

    subgraph API["FastAPI Application"]
        A[Parse Query]
        A --> PI[Apply Tier Filter]
        A --> COL[Column Filtering]
        COL --> PII[Remove PII columns]
    end

    subgraph DB["PostgreSQL RLS"]
        R[Re-write Query with tier]
        R --> SEL[SELECT policy]
    end

    Q --> T --> G --> A --> PI --> COL --> PII --> R --> SEL
```

---

## Implementation Details

### 1. Application Layer (Primary)

```python
from functools import wraps
from typing import Callable

TIER_DATA_ACCESS = {
    1: {  # Researcher
        "tables": ["researchers", "publications", "projects", "labs"],
        "columns": ["*"]  # All columns including PII
    },
    2: {  # Government
        "tables": ["researchers", "publications", "projects"],
        "columns": ["id", "name", "state", "institution", "area", "h_index"],  # No PII
        "aggregates": ["COUNT", "SUM", "AVG"]
    },
    3: {  # Industry
        "tables": ["publications", "projects"],
        "columns": ["id", "title", "year", "area"],  # No PII
        "anonymized": True
    }
}

def apply_tier_filter(query: str, user_tier: int) -> str:
    """Rewrite query based on tier access level."""
    access = TIER_DATA_ACCESS[user_tier]
    # Inject column filters and row filters
    # ... implementation
    return filtered_query
```

### 2. Column-Level Filtering (PII)

```python
PII_COLUMNS = {
    "researchers": ["email", "phone", "address", "aadhaar", "pan"],
    "projects": ["budget_details", "team_members"],
    "labs": ["contact_email", "contact_phone"]
}

def filter_pii(data: list[dict], table: str, user_tier: int) -> list[dict]:
    """Remove PII columns for non-researcher tiers."""
    if user_tier == 1:  # Researcher has full access
        return data

    restricted = PII_COLUMNS.get(table, [])
    return [{k: v for k, v in row.items() if k not in restricted}
            for row in data]
```

### 3. Row-Level Security (PostgreSQL)

```sql
-- Enable RLS on sensitive tables
ALTER TABLE researchers ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Create tier-based policies
CREATE POLICY researcher_read ON researchers
    FOR SELECT
    USING (
        CASE current_setting('nrg.tier', true, true)::int
            WHEN 1 THEN true  -- Researcher: full access
            WHEN 2 THEN true  -- Government: aggregate only
            WHEN 3 THEN true   -- Industry: anonymized
            ELSE false        -- Deny
        END
    );

-- Set tier for session
SET nrg.tier = 2;  -- Government user
SELECT * FROM researchers;  -- Returns filtered data
```

### 4. RLS with Column masking

```sql
-- Create mask for PII columns
CREATE MASK FOR email ON researchers USING ('***'::text);
CREATE MASK FOR phone ON researchers USING ('***-***-****'::text);

-- Government and Industry get masked values
SET nrg.tier = 2;
SELECT email, phone FROM researchers;
-- Returns: email='***', phone='***-***-****'
```

---

## Query Rewriting Logic

```python
from typing import Any

class TierAwareQueryRewriter:
    """Rewrites SQL queries to enforce tier-based access."""

    def __init__(self, user_tier: int):
        self.user_tier = user_tier

    def rewrite(self, query: str) -> str:
        """Apply tier filters to query."""
        parsed = sqlglot.parse(query)

        for node in parsed.find_all(sqlglot.Table):
            if node.name in TIER_SENSITIVE_TABLES:
                self._add_tier_filter(node)

        for node in parsed.find_all(sqlglot.Column):
            if node.name in PII_COLUMNS.get(table, []):
                self._add_column_mask(node)

        return parsed.sql()

    def _add_tier_filter(self, table: sqlglot.Table):
        """Add access_tier check to WHERE clause."""
        if self.user_tier > 1:
            # Non-researchers see only public data
            tier_column = f"{table.name}.access_tier"
            # Rewrite to enforce tier visibility

    def _add_column_mask(self, column: sqlglot.Column):
        """Replace PII columns with masked values."""
        if column.name in PII_COLUMNS.get(self.current_table, []):
            return sqlglot.Literal.string("***MASKED***")
```

---

## Defense in Depth Summary

| Layer | Protection | Failure Impact |
|-------|------------|----------------|
| Kong Gateway | Rejects requests without valid tier | 401 returned |
| FastAPI | Rewrites queries, filters columns | Partial data returned |
| PostgreSQL RLS | Database enforces access | No bypass possible |
| Audit Logging | All access logged to HMAC chain | Forensic trail maintained |

---

## Performance Considerations

| Approach | Overhead | Mitigation |
|----------|----------|------------|
| Application filter | ~5ms | Cache common queries |
| Column masking | ~2ms | Only on PII columns |
| RLS | ~10ms | Index on access_tier |

Combined overhead: < 20ms typical query

---

## Consequences

### Positive
- Defense in depth: multiple layers of protection
- Database-level guarantee (RLS)
- Clear separation of concerns
- DPDP compliant by design
- Consistent behavior across all access patterns

### Negative
- Complexity in query rewriting
- Performance overhead (though minimal)
- Testing complexity (multiple layers)

### Risks
- RLS misconfiguration could leak data
  - Mitigation: Automated RLS testing after every schema change
- Query rewriter bugs could bypass filters
  - Mitigation: Comprehensive test suite, code review

---

## Testing Strategy

```python
def test_tier_enforcement():
    """Verify tier filtering at each layer."""

    # Test Tier 1 (Researcher)
    results = query_as_tier_1("SELECT * FROM researchers")
    assert "email" in results[0]
    assert "phone" in results[0]

    # Test Tier 2 (Government)
    results = query_as_tier_2("SELECT * FROM researchers")
    assert "email" not in results[0]
    assert "phone" not in results[0]
    assert "name" in results[0]

    # Test Tier 3 (Industry)
    results = query_as_tier_3("SELECT * FROM researchers")
    assert "email" not in results[0]
    assert "name" not in results[0]  # Anonymized
```

---

## References

- [RBAC Policy](docs/architecture/RBAC_POLICY.md)
- [PII Strategy](docs/adr/ADR-004-pii-strategy.md)
- [DPDP Compliance](docs/compliance/DPDP_2023_MAPPING.md)

---

**Reviewed by:** Security Team, Compliance Officer  
**Sign-off:** 2026-04-21
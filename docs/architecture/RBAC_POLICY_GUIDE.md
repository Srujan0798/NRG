# RBAC Policy Guide v2.0

RBAC (Role-Based Access Control) in NRG is governed by the `RBACPolicyEngine` in `src/auth/rbac.py`, backed by the declarative config `src/auth/rbac_policies.yaml`. All policy decisions flow through this engine — no hardcoded tier/visibility logic remains in middleware or schema extraction layers.

## Architecture

```
rbac_policies.yaml
        ↓ (loaded by)
RBACPolicyEngine (singleton)
        ↓ (policy resolved via tier OR persona)
RBACPolicy (immutable dataclass)
        ↓ (enforced at)
┌─────────────────────────────────────────────────┐
│ middleware.py    │ filter_researcher_records()  │
│ schema_extractor│ get_visible_columns()         │
│ synthesizer.py   │ inject output_format         │
│ main.py          │ /api/admin/rbac CRUD         │
└─────────────────────────────────────────────────┘
```

## Personas (6 total)

| Persona | Tier | Output Format | Data Scope | Notes |
|---------|------|--------------|------------|-------|
| `researcher` | 1 | full | All records | Built-in, protected |
| `government` | 2 | aggregated | access_tier >= 2 | Built-in, protected |
| `industry` | 3 | anonymized | access_tier = 3 | Built-in, protected |
| `peer_reviewer` | 1 | aggregated | Institution-scoped | Read-only |
| `department_head` | 2 | aggregated | Institution-scoped | No name column |
| `student` | 3 | anonymized | Publications-only | 50 result limit |

## Policy Fields

Each persona defines:

```yaml
column_visibility:     # Which columns are returned per table
  <table>: ["*"]       # "*" means all columns
  <table>: ["col1", "col2"]  # explicit allowlist
  <table>: []          # empty = table hidden entirely

pii_masking:           # PII redaction rules
  <table>:
    <column>: hash    # Replace with SHA256 hash
    <column>: redact  # Replace with [REDACTED]
    <column>: null    # Return NULL

output_format:         # Controls synthesizer prompt tone
  full        # Full detail with citations
  aggregated  # Counts/sums/averages only, no individuals
  anonymized  # No names, emails, or PII

data_scope:            # Row-level filtering
  filter: "access_tier >= 1"   # SQL WHERE clause
  tables: ["researchers", "publications", "funding", ...]

max_results: 1000      # Hard cap on rows returned
debug_access: false    # Whether debug info is exposed

allowed_endpoints: ["*"]  # Or explicit list
allowed_tables: ["*"]

export_allowed: false
read_only: true
```

## Usage in Code

### Resolving a policy from tier or persona

```python
from src.auth.rbac import get_policy_engine

engine = get_policy_engine()

# By tier (backward compatible)
policy = engine.get_policy(tier=1)

# By persona (new)
policy = engine.get_policy(persona="peer_reviewer")

# Auto-resolve from auth claims (tier OR persona takes precedence)
claims = {"tier": 2, "persona": "government", "role": "user"}
resolved = engine.resolve_tier_or_persona(claims)
```

### Filtering a row

```python
columns, masked_row = policy.filter_row_by_policy(
    table="researchers",
    row={"name": "John Doe", "email": "john@iitgn.ac.in", "access_tier": 1},
    accessor_tier=1
)
# columns = ["name", "email", ...] (visibility)
# masked_row = {"name": "John Doe", "email": "john@iitgn.ac.in"} (no masking applied since accessor_tier >= table's access_tier)
```

### Column visibility

```python
visible = policy.get_visible_columns("researchers")
# ["name", "email", "research_area", "institution", ...] or ["name", "research_area"] etc.
```

### Endpoint/table access control

```python
policy.is_endpoint_allowed("/api/admin/rbac")   # False (admin only)
policy.is_table_allowed("researchers")         # True/False per persona
```

## Admin API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/rbac` | List all personas |
| POST | `/api/admin/rbac` | Create/update persona (runtime) |
| PUT | `/api/admin/rbac/{persona}` | Update existing persona |
| DELETE | `/api/admin/rbac/{persona}` | Soft-delete (is_active=False) |
| GET | `/api/admin/rbac/{persona}` | Get full policy details |

All admin endpoints require `role == "admin"`. All changes are logged to `ImmutableAuditLog`.

## Built-in Persona Protection

These personas **cannot be deactivated** via the API or `deactivate_persona()`:
- `researcher` (tier 1)
- `government` (tier 2)
- `industry` (tier 3)

The check lives in `RBACPolicyEngine.deactivate_persona()`, not just the API layer.

## Hot Reload

The policy engine watches `rbac_policies.yaml` for changes and auto-reloads within 5 seconds. Runtime changes via the Admin API are also reflected immediately (no restart needed).

## Legacy (tier-based) Behavior

For callers that pass only a `tier` integer (no `persona`), the engine falls back to the original behavior:
- tier 1 → `researcher` policy
- tier 2 → `government` policy
- tier 3 → `industry` policy

This ensures backward compatibility with all existing code that uses `get_user_tier()`.

## Key Files

| File | Purpose |
|------|---------|
| `src/auth/rbac.py` | `RBACPolicyEngine`, `RBACPolicy`, `PolicyCache` |
| `src/auth/rbac_policies.yaml` | Declarative policy config (6 personas) |
| `src/auth/middleware.py` | `get_user_policy()`, `filter_researcher_records()` |
| `src/auth/jwt_handler.py` | `persona` claim added to JWT tokens |
| `src/skills/text_to_sql/schema_extractor.py` | `get_visible_columns()` via policy engine |
| `src/orchestration/nodes/synthesizer.py` | `output_format` injection in prompts |
| `src/api/main.py` | `/api/admin/rbac` CRUD endpoints |
| `tests/security/test_rbac_policies.py` | 27 tests for policy engine |
| `tests/security/test_tier_generalization.py` | 22 tests for new personas |
# RBAC Policy Reference

> **This file is superseded.** See [RBAC_POLICY_GUIDE.md](./RBAC_POLICY_GUIDE.md) for the full guide covering architecture, personas, policy fields, admin API, and code usage examples.

## Quick Reference

| Persona | Tier | Output Format |
|---------|------|--------------|
| researcher | 1 | full |
| government | 2 | aggregated |
| industry | 3 | anonymized |
| peer_reviewer | 1 | aggregated |
| department_head | 2 | aggregated |
| student | 3 | anonymized |

## Key Files

- `src/auth/rbac.py` — `RBACPolicyEngine` (singleton)
- `src/auth/rbac_policies.yaml` — 6 persona definitions
- `src/auth/middleware.py` — policy enforcement
- `src/api/main.py` — `/api/admin/rbac` CRUD endpoints

## Engine Usage

```python
from src.auth.rbac import get_policy_engine

engine = get_policy_engine()
policy = engine.get_policy(persona="peer_reviewer")
```

See [RBAC_POLICY_GUIDE.md](./RBAC_POLICY_GUIDE.md) for full documentation.
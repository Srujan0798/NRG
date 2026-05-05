# POINTER: Authentication Flow

> **Do not trust this file as the source of truth.** Read the actual files listed below to verify auth implementation.

## Where to Read

| Topic | Actual Source Files | What to Verify |
|-------|--------------------|----------------|
| **Auth routes** | `src/api/routes/auth.py` | Login, logout, refresh, SSO endpoints |
| **RBAC engine** | `src/auth/rbac.py`, `src/auth/rbac_policies.yaml` | Policy definitions, enforcement |
| **Middleware** | `src/auth/middleware.py` | Tier checks on every request |
| **JWT keys** | `infrastructure/kong/ssl/jwt_rsa.key`, `jwt_rsa.pub` | RS256 keypair exists |
| **Frontend auth** | `frontend/src/hooks/useAuth.ts` | Token management, persona state |

## Verification Commands

```bash
# Check auth routes
grep -n "def " src/api/routes/auth.py | head -10

# Check RBAC
ls src/auth/rbac.py src/auth/rbac_policies.yaml src/auth/middleware.py

# Check JWT keys
ls infrastructure/kong/ssl/jwt_rsa.key infrastructure/kong/ssl/jwt_rsa.pub

# Check frontend auth hook
ls frontend/src/hooks/useAuth.ts
```

**Read the actual source files. Do not trust this pointer.**

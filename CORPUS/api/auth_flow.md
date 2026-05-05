# NRG Authentication Flow

## Overview

NRG uses JWT with RS256 asymmetric signing. Three user tiers control data access.

## Login Flow

```text
User enters credentials
  -> POST /login (or /auth/login)
  -> Server validates username/password
  -> Generates access_token (short-lived) + refresh_token (long-lived)
  -> Sets HttpOnly cookies
  -> Returns tokens in JSON response
```

## Token Refresh

```text
Access token expires
  -> POST /refresh (or /auth/refresh)
  -> Server validates refresh_token
  -> Rotates refresh_token (new one issued)
  -> Returns new access_token
```

## Logout Flow

```text
User clicks logout
  -> POST /logout (or /auth/logout)
  -> Server revokes tokens
  -> Clears cookies
  -> Redirects to login
```

## SSO (Optional)

```text
User clicks SSO
  -> GET /auth/sso/login?provider=...
  -> Redirects to provider
  -> Provider redirects to /auth/sso/callback?code=...
  -> Server exchanges code for user info
  -> Creates/updates user, issues tokens
```

## Tier Enforcement

Every authenticated request carries the user's persona. The RBAC middleware checks:

1. Is the token valid? (JWT signature, expiry)
2. What persona does the user have? (researcher/government/industry)
3. What tier is that persona? (1/2/3)
4. Does the requested endpoint allow that tier?
5. Is the data response shaped correctly for that tier? (full/aggregated/anonymized)

## Session Check

```text
GET /auth/session
  -> Returns { authenticated: true, persona: "researcher", tier: 1 }
  -> Or { authenticated: false }
```

## Key Files

- `src/auth/rbac.py` — RBACPolicyEngine
- `src/auth/rbac_policies.yaml` — 6 persona definitions
- `src/auth/middleware.py` — policy enforcement
- `src/api/routes/auth.py` — auth endpoints
- `frontend/src/hooks/useAuth.ts` — frontend auth state

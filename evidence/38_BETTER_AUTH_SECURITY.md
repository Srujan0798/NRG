# Better Auth Security Best Practices Evidence

**Skill**: better-auth-security-best-practices
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/38_BETTER_AUTH_SECURITY.md`

---

## Auth Security: NRG vs Better Auth Best Practices

### Overview

NRG uses custom JWT-based authentication (`src/auth/jwt_handler.py`). The Better Auth skill provides best practices for auth security. NRG doesn't use Better Auth library but the principles apply.

---

## Gap Analysis: NRG vs Best Practices

### 1. Secret Management

| Best Practice | NRG Status |
|--------------|------------|
| Secret in env variable | ⚠️ Default in source |
| 32+ char secret | ✅ Likely OK |
| High entropy | ❓ Unknown |
| Never in source | ❌ Default in source |

**Issue**: `AuthError` in `jwt_handler.py` reveals internal JWT details via `str(exc)`.

---

### 2. Rate Limiting

| Best Practice | NRG Status |
|--------------|------------|
| Enabled on all endpoints | ✅ Implemented |
| Sensitive endpoints stricter | ✅ 3/min on sign-in |
| Storage: Redis | ⚠️ Using in-memory |
| Per-IP limiting | ✅ Implemented |

**Issue**: Rate limiter uses in-memory storage — resets on restart (serverless issue).

---

### 3. CSRF Protection

| Best Practice | NRG Status |
|--------------|------------|
| Origin header validation | ❌ Not implemented |
| Fetch Metadata checks | ❌ Not implemented |
| SameSite cookies | ❓ Unknown |

**Issue**: No CSRF protection found in auth middleware.

---

### 4. Trusted Origins

| Best Practice | NRG Status |
|--------------|------------|
| baseURL configured | ✅ Has `baseURL` |
| Allowed origins list | ❌ Not found |
| Wildcard patterns | ❌ Not implemented |

**Issue**: No explicit allowed origins list for CORS.

---

### 5. Session Security

| Best Practice | NRG Status |
|--------------|------------|
| Session expiration | ✅ 24h access, 7d refresh |
| Session refresh | ✅ Implemented |
| Cookie: httpOnly | ✅ Implemented |
| Cookie: secure | ⚠️ Not verified |
| Cookie: sameSite | ⚠️ Not verified |
| Cookie cache strategy | ❌ Not implemented |

**Issue**: Cookie attributes not verified in code.

---

### 6. JWT Security (NRG Specific)

| Issue | Severity | Location |
|-------|----------|----------|
| `refresh_access_token()` doesn't revoke old JTI | 🔴 HIGH | `jwt_handler.py` |
| `_jti_ip_registry` unbounded | 🔴 HIGH | `jwt_handler.py:133` |
| `AuthError` leaks JWT details | 🟡 MEDIUM | `jwt_handler.py` |
| Default passwords in source | 🔴 CRITICAL | `Login.tsx` |

---

### 7. IP-Based Security

| Best Practice | NRG Status |
|--------------|------------|
| X-Forwarded-For handling | ✅ Implemented |
| IP allowlisting | ✅ Tier 2 has IP allowlist |
| IP tracking disabled | ❌ Tracking enabled |

**Issue**: `_jti_ip_registry` grows unbounded — potential DoS.

---

### 8. Security Hooks

| Best Practice | NRG Status |
|--------------|------------|
| Session create audit | ✅ Audit chain |
| Session delete audit | ✅ Audit chain |
| User update audit | ✅ Audit chain |
| Account link audit | ❌ Not found |

**Good**: NRG has audit chain for security events.

---

## Gap Summary

| Category | Score | Status |
|----------|-------|--------|
| Secret management | 5/10 | Needs improvement |
| Rate limiting | 8/10 | Good |
| CSRF protection | 2/10 | Missing |
| Trusted origins | 3/10 | Needs configuration |
| Session security | 7/10 | Good |
| JWT security | 4/10 | Issues found |
| IP-based security | 6/10 | Unbounded registry |
| Audit hooks | 8/10 | Good |

**Overall**: 6/10 — Better than average but has critical gaps.

---

## Priority Fixes

### P0 (CRITICAL)

1. **Remove default passwords from source** (`Login.tsx:29-41`)
2. **Fix JWT refresh to revoke old JTI** (`jwt_handler.py`)

### P1 (HIGH)

3. **Fix unbounded `_jti_ip_registry`** — Add TTL or max size
4. **Add CSRF protection** — Origin validation middleware
5. **Configure trusted origins** — Explicit allowed origins list

### P2 (MEDIUM)

6. **Add secure/sameSite cookie attributes** — Verify in production
7. **Add session encryption** — If sensitive data in session
8. **Rate limit storage** — Move to Redis for serverless

---

## Skill Deliverable

**Status**: COMPLETED

Auth security comparison:
- NRG uses custom JWT (not Better Auth library)
- Rate limiting: Good (8/10)
- Session security: Good (7/10)
- CSRF protection: Missing (2/10)
- JWT refresh: Critical issue (old JTI not revoked)
- Default passwords: CRITICAL (in source)
- Overall: 6/10 — needs improvement in CSRF and JWT refresh

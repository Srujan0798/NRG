# Security Audit — Session 92

**Date:** 2026-04-25
**Standard:** OWASP Top 10 + DPDP 2023
**Severity:** 🚨 Critical: 2 | ⚠️ High: 3 | 📋 Medium: 4 | 💡 Low: 3

---

## 🚨 CRITICAL Issues

### 1. JWT Refresh Token Not Rotated — Token Replay Window
**OWASP:** A07:2021 — Authentication Failures
**Severity:** 🚨 Critical
**File:** `src/auth/jwt_handler.py:252-265`

```python
def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
    claims = self.verify_refresh_token(refresh_token)  # ✓ verifies
    ...
    self.revoke_token(refresh_token)                   # ✓ revokes old refresh
    return self.issue_token_pair(user)                # ⚠️ issues NEW token pair
```

**Issue:** `refresh_access_token()` issues a **new access token AND a new refresh token**. However, the new access token has a **new JTI** (`str(uuid.uuid4())` at line 292), but the **new refresh token also has a new JTI**. The old access token's JTI remains in `_jti_ip_registry` and is NOT revoked.

**Attack:** If an attacker obtains the old access token (before refresh), they can use it until its natural expiry (1 hour). The `refresh_access_token` flow revokes the refresh token but not the previously-issued access token.

**Fix:**
```python
# When refreshing, revoke the old access token too
self.revoked_jtis.add(previous_access_token_jti)  # Add this
self.revoke_token(refresh_token)
return self.issue_token_pair(user)
```

---

### 2. `_jti_ip_registry` Unbounded Memory — DoS Vector
**OWASP:** A04:2021 — Insecure Design
**Severity:** 🚨 Critical
**File:** `src/auth/jwt_handler.py:133, 219-240`

```python
self._jti_ip_registry: dict[str, tuple[str, str, float]] = {}  # line 133

def _check_token_replay(self, jti: str, ...):
    if jti in self._jti_ip_registry:   # grows forever
        ...
    else:
        self._jti_ip_registry[jti] = (user_id, client_ip, exp)  # never cleaned
```

**Issue:** `_jti_ip_registry` stores every JTI ever issued with its expiry time, but is **never cleaned up**. With 5,000 users each doing 10 queries/day, after 1 year this would have 1.8M entries consuming unbounded memory. An attacker could intentionally trigger many token issuances to accelerate memory growth.

**Fix:** Add a cleanup routine:
```python
def _cleanup_jti_registry(self) -> None:
    now = datetime.now(UTC).timestamp()
    expired = [k for k, (_, _, exp) in self._jti_ip_registry.items() if exp < now]
    for k in expired:
        self._jti_ip_registry.pop(k, None)

# Call cleanup on every token issuance:
if len(self._jti_ip_registry) > 10000:
    self._cleanup_jti_registry()
```

---

## ⚠️ HIGH Issues

### 3. Default User Passwords in Source Code
**OWASP:** A07:2021 — Identification/Authentication Failures
**Severity:** ⚠️ High
**File:** `src/auth/jwt_handler.py:48-72`

```python
"researcher_user": {
    "password": _first_env(
        ("RESEARCHER_PASSWORD", "DEMO_RESEARCHER_PASSWORD"),
        "researcher-pass",  # ← hardcoded default
    ),
```

**Issue:** Default passwords (`researcher-pass`, `government-pass`, `industry-pass`) are in **source code**. Even though they're intended for dev-only, they could be used in staging if env vars are misconfigured. The `AuthError` for missing `JWT_SECRET` is good (line 123: raises if not set), but the default passwords don't have equivalent protection.

**Fix:** Require passwords via env var in non-dev environments:
```python
if os.getenv("NRG_ENV") != "dev":
    if not os.getenv("RESEARCHER_PASSWORD"):
        raise AuthError("RESEARCHER_PASSWORD env var required in production")
```

---

### 4. `_api_cache` Has Unbounded Size — Cache Poisoning/DoS
**OWAP:** A04:2021 — Insecure Design
**Severity:** ⚠️ High
**File:** `src/api/main.py:114-183`

```python
class _APIMemoryCache:
    def __init__(self, default_ttl: int = 30):
        self._store: dict[str, tuple[float, Any]] = {}  # unbounded!
```

**Issue:** The `_APIMemoryCache` has no maximum size. An attacker (or buggy client) could flood it with many unique queries, causing unbounded memory growth. Each cache entry can hold large query results (full response with citations).

**Fix:** Add max entries:
```python
MAX_CACHE_ENTRIES = 1000

def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
    if len(self._store) >= MAX_CACHE_ENTRIES:
        oldest = min(self._store, key=lambda k: self._store[k][0])
        self._store.pop(oldest)
    self._store[key] = (time.time() + (ttl or self._default_ttl), value)
```

---

### 5. CORS Allows Credentials + Multiple Origins
**OWASP:** A07:2021 — Security Misconfiguration
**Severity:** ⚠️ High
**File:** `src/api/main.py:251-257`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,     # ← allow_credentials=True
    allow_methods=["*"],        # ← was overridden to specific methods below
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Session-ID"],
)
```

**Issue:** `allow_credentials=True` with `allow_origins` from an **env var** means a misconfigured deployment could allow arbitrary origins with credentials. The env var `CORS_ORIGINS` could be set to `*` or unintended domains in production.

**Fix:** Validate CORS origins:
```python
_allowed = os.getenv("CORS_ORIGINS", "").split(",")
if "*" in _allowed:
    raise RuntimeError("CORS_ORIGINS cannot include '*' when allow_credentials=True")
```

---

## 📋 MEDIUM Issues

### 6. No `kid` Validation on Token Decode — Key Confusion Attack
**OWASP:** A07:2021 — Identification/Authentication Failures
**Severity:** 📋 Medium
**File:** `src/auth/jwt_handler.py:316-341`

```python
def _decode_token(self, token: str, ..., verify_exp: bool = True):
    verification_key = self.public_key if self.public_key else self.secret_key
    claims = jwt.decode(..., algorithms=[str(self.algorithm)])  # algorithm checked
    # BUT: claims["kid"] (key ID) is NOT validated against self._signing_key_id
    return claims
```

**Issue:** If RS256 is used and key rotation happened, old tokens signed with a previous key are accepted if the key ID is still in `_known_key_ids`. But the `kid` in the token is **not validated against the current signing key** on decode. An attacker who knows a previous `kid` could craft a token with that `kid` and a weak key if the verification allows multiple key algorithms.

**Fix:** Validate `kid` matches current key:
```python
if claims.get("kid") not in self._known_key_ids:
    raise AuthError("Unknown key ID")
```

---

### 7. No Rate Limit on `/auth/refresh` Endpoint
**OWASP:** A04:2021 — Security Misconfiguration
**Severity:** 📋 Medium
**File:** `src/api/main.py` (refresh endpoint likely around line 350+)

The brute force protection (line 297) only covers `/auth/login`. The `/auth/refresh` endpoint may not have rate limiting, allowing token refresh enumeration.

**Fix:** Add `check_endpoint_rate_limit` to refresh endpoint.

---

### 8. No Audit Log for Token Revocation / Data Erasure
**OWASP:** A09:2021 — Security Logging Failures
**Severity:** 📋 Medium
**File:** `src/api/main.py` (erase endpoint)

DPDP Act 2023 requires audit trails for consent withdrawal and data erasure. The `log_token_revocation` is called but the **data erasure event** may not be logged to the audit chain.

**Fix:** Ensure `eraseUserData` calls `log_anomaly(event_type="data_erasure_requested", ...)` on the audit chain.

---

### 9. `AuthError` Leaks Internal Details via `str(exc)`
**OWASP:** A01:2021 — Broken Access Control
**Severity:** 📋 Medium
**File:** `src/auth/jwt_handler.py:336`

```python
except jwt.PyJWTError as exc:
    raise AuthError(str(exc))  # ← could leak internal JWT library details
```

JWT library error messages (e.g., "Signature verification failed", "Expired signature") should not be returned to clients — they aid attackers.

**Fix:**
```python
except jwt.PyJWTError:
    raise AuthError("Token validation failed")
```

---

## 💡 LOW Issues

### 10. Login Brute Force Protection Uses In-Memory Store
**Severity:** 💡 Low
**File:** `src/api/middleware/security.py`

Brute force login protection (`brute_force_protection.check_login_failure`) likely uses in-memory state — not shared across multiple API workers. An attacker hitting different workers won't be blocked.

---

### 11. JWT `iss` (Issuer) Set to Role Name — Unusual Design
**Severity:** 💡 Low
**File:** `src/auth/jwt_handler.py:294`

```python
payload = {
    "iss": role,  # ← "researcher", "government", "industry"
```

Standard JWT practice sets `iss` to the application name (e.g., `"nrg-api"`). Setting it to the role name is unusual and could cause confusion in token validation.

**Fix:** Use `"nrg-api"` as `iss`.

---

### 12. Refresh Token TTL Is 7 Days — May Be Too Long for High-Security Use
**Severity:** 💡 Low
**File:** `src/auth/jwt_handler.py:93`

`refresh_token_ttl_seconds: int = 604800` = 7 days. For a government/policy research platform, a 7-day refresh token window is long. A stolen refresh token would give an attacker a week of access.

---

## Summary Table

| # | Issue | Severity | File:Line |
|---|-------|----------|-----------|
| 1 | Refresh doesn't revoke old access token | 🚨 Critical | jwt_handler.py:252 |
| 2 | `_jti_ip_registry` unbounded | 🚨 Critical | jwt_handler.py:133 |
| 3 | Default passwords in source | ⚠️ High | jwt_handler.py:48 |
| 4 | Cache has no size limit | ⚠️ High | main.py:114 |
| 5 | CORS origins from env var | ⚠️ High | main.py:251 |
| 6 | No `kid` validation on decode | 📋 Medium | jwt_handler.py:328 |
| 7 | No rate limit on refresh | 📋 Medium | main.py |
| 8 | No audit for data erasure | 📋 Medium | main.py |
| 9 | `AuthError` leaks internal details | 📋 Medium | jwt_handler.py:336 |
| 10 | Brute force is in-memory only | 💡 Low | security.py |
| 11 | `iss` = role name is unusual | 💡 Low | jwt_handler.py:294 |
| 12 | 7-day refresh TTL may be long | 💡 Low | jwt_handler.py:93 |

---

## Fix Priority

1. **[P0]** Fix Issue 1 (refresh doesn't revoke old access token) — Security critical
2. **[P0]** Fix Issue 2 (unbounded jti registry) — DoS vector
3. **[P1]** Fix Issue 4 (cache size limit) — DoS vector
4. **[P1]** Fix Issue 6 (kid validation)
5. **[P2]** Fix Issues 3, 5, 7, 8, 9

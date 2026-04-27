# NRG Security Hardening Report

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NRG Platform Security Architecture                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌────────────────────────────────────────────────┐   │
│  │   Client     │────▶│            API Gateway (FastAPI)               │   │
│  │              │     │  ┌─────────────┐  ┌────────────┐  ┌─────────┐  │   │
│  │  - HMAC Sig  │     │  │Rate Limiter│  │  Headers   │  │  IP     │  │   │
│  │  - JWT Token │     │  │  (Redis)   │  │  Security  │  │Allowlist│  │   │
│  └──────────────┘     │  └─────────────┘  └────────────┘  └─────────┘  │   │
│                        └────────────────────────────────────────────────┘   │
│                                          │                                  │
│                    ┌─────────────────────┼─────────────────────┐            │
│                    ▼                     ▼                     ▼            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        Security Layer                               │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │    │
│  │  │  PII       │  │   SQL      │  │   Token    │  │  DPDP      │  │    │
│  │  │Encryption │  │ Allowlist   │  │ Rotation   │  │Compliance  │  │    │
│  │  │ (AES-256) │  │             │  │            │  │            │  │    │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                          │                                  │
│                    ┌─────────────────────┼─────────────────────┐            │
│                    ▼                     ▼                     ▼            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Redis    │  │  SQLite    │  │   LLM      │  │   Egress   │            │
│  │  (Cache)   │  │   (DB)     │  │ (Gemini)   │  │   Guard    │            │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Threat Model

### Assets to Protect
1. **Researcher PII**: email, phone, orcid - encrypted at rest
2. **JWT Tokens**: access (15min) and refresh (7day) with rotation
3. **Query Data**: user queries with HMAC signatures
4. **Database**: SQL injection prevention via allowlist

### Threat Vectors
| Threat | Mitigation |
|--------|------------|
| Brute Force Login | 5 attempts → 15min lockout, 429 + Retry-After |
| Rate Limit Exhaustion | Tiered limits (50-200/min) via Redis |
| SQL Injection | SELECT-only allowlist validation |
| Replay Attacks | HMAC + 5-min timestamp expiry |
| PII Exfiltration | AES-256 encryption + egress guard |
| Government IP Spoofing | IP allowlist for tier 2 users |
| Token Theft | Auto-rotation on refresh use |

## Implementation Details

### 1. Tiered Rate Limiting (`rate_limiter.py`)

```python
TIER_LIMITS = {
    1: 100,  # Researcher - 100 req/min
    2: 200,  # Government - 200 req/min
    3: 50,   # Industry - 50 req/min
}
```

**Headers added to responses:**
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Requests left in window
- `X-RateLimit-Reset`: Unix timestamp of window reset
- `X-RateLimit-Tier`: Current user's tier name

**Redis Implementation:**
- Sorted set per user/IP with timestamps
- Cleanup of old entries via ZREMRANGEBYSCORE
- Pipeline for atomic check-and-increment

### 2. HMAC Request Signing (`request_signer.py`)

```
Signature = HMAC-SHA256(api_secret, timestamp + ":" + request_body)
```

**Verification Process:**
1. Extract `X-Signature` and `X-Timestamp` headers
2. Check age: reject if > 300 seconds (replay protection)
3. Compute expected signature and compare (constant-time)
4. Log all validation attempts

**Replay Protection:**
- Timestamp must be within [-5, +300] seconds of current time
- Rejects future timestamps (clock skew protection)

### 3. IP Allowlisting for Government Tier (`security.py`)

```python
class IPAllowlist:
    ALLOWED_IPS: set = set()  # Configured via add_allowed_ip()
```

- Empty allowlist = full access (default behavior)
- Government tier (tier=2) blocked if IP not in allowlist
- Returns 403 Forbidden with clear message

### 4. Brute-Force Protection (`security.py`)

```python
class BruteForceProtection:
    MAX_FAILURES = 5
    LOCKOUT_DURATION = 900  # 15 minutes

    def check_login_failure(username):
        # Returns (is_locked, message)
        # Checks _lockout_until dict
        # Auto-clears after lockout expires

    def record_failure(username):
        # Increments _failure_count
        # Sets lockout at 5 failures

    def record_success(username):
        # Clears both _failure_count and _lockout_until
```

**Response on lockout:**
- HTTP 429 (was 423)
- `Retry-After: 900` header
- Audit event logged for attempts >= 3

### 5. Security Headers (`headers.py`)

```python
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "Content-Security-Policy": "default-src 'self'; ...",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
}
```

### 6. PII Encryption (`pii_encryption.py`)

**Encrypted fields**: `email`, `phone`, `orcid`

```python
AESGCM(key=NRG_PII_ENCRYPTION_KEY)  # 256-bit key from env

# Encryption format: base64(nonce(12) + ciphertext)
```

**Key Management:**
- Key from `NRG_PII_ENCRYPTION_KEY` env variable (base64 encoded)
- Falls back to no encryption if not configured (logs warning)
- Decrypt only when needed for response

### 7. SQL Query Allowlist (`query_allowlist.py`)

**Blocked Keywords:**
```
DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, CREATE,
EXEC, EXECUTE, GRANT, REVOKE
```

**Blocked Patterns:**
- `UNION SELECT` (injection)
- `INTO OUTFILE`
- `LOAD_FILE`
- Double semicolon patterns

**Validation:**
```python
def validate(query):
    if not query.strip():
        return False, "Empty query"
    if not is_select_only(query):
        return False, "Non-SELECT statement"
    if contains_blocked_keyword(query):
        return False, f"Blocked: {keyword}"
    if matches_blocked_pattern(query):
        return False, f"Blocked pattern: {pattern}"
    return True, "OK"
```

### 8. Token Rotation (`token_rotation.py`)

```python
ACCESS_TOKEN_TTL_SECONDS = 900    # 15 minutes
REFRESH_TOKEN_TTL_SECONDS = 604800  # 7 days

class TokenRotator:
    def create_access_token_payload(...):
        # JTI = uuid
        # exp = now + 900 seconds

    def create_refresh_token_payload(...):
        # Stores active JTI per user
        # Used to detect rotation reuse

    def validate_refresh_rotation(user_id, jti):
        # Checks if jti matches current active for user
        # Prevents reuse of rotated tokens
```

### 9. Egress Guard Alerts (`egress/guard.py`)

**Violation Logging:**
```python
def _log_violation(violation, url, payload):
    # 1. Append to audit log
    AuditEvent(
        event_type="egress_block",
        user_id="system",
        result={
            "reason": violation.reason,
            "blocked_field": violation.blocked_field,
            "url": url,
        }
    )
    # 2. Send alert via callback
    if alert_callback:
        alert_callback(alert_data)
    # 3. Log to logger.error
```

**Alert Payload:**
```python
{
    "type": "egress_guard_violation",
    "severity": "CRITICAL",
    "reason": "Blocked sensitive field 'full_text'",
    "blocked_field": "full_text",
    "url": "https://api.anthropic.com/...",
    "timestamp": "2026-04-21T10:30:00Z"
}
```

### 10. DPDP Compliance (`dpdp_compliance.py`)

**Data Retention Policy:**
- 90 days after consent revocation
- Configurable via `NRG_DATA_RETENTION_DAYS` env var

**Cleanup Process:**
```python
def cleanup_expired_consents():
    # 1. Find consents revoked > 90 days ago
    cursor = conn.execute("""
        SELECT consent_id, user_id, scope, revoked_at
        FROM consent_ledger
        WHERE revoked_at < :cutoff
    """)

    # 2. For each, purge_user_data():
    #    - Delete from consent_ledger
    #    - Anonymize audit_events (user_id='DELETED')
    #    - Revoke refresh_tokens

    # 3. Log to DELETION_AUDIT_LOG
```

## Test Procedures

### Rate Limiting Test
```bash
# Login as researcher (tier 1)
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}'

# Check response headers
# Should have X-RateLimit-Limit: 100, X-RateLimit-Remaining: 99

# Test rate limit exceeded
# Run 101 requests quickly, should get 429
```

### HMAC Signature Test
```python
import hmac, hashlib, time, json

secret = "nrg-default-signing-secret"
payload = {"query": "Show me researchers in Karnataka"}
timestamp = int(time.time())

body = json.dumps(payload, sort_keys=True)
message = f"{timestamp}:{body}"
signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

# Send request with headers
# X-Timestamp: {timestamp}
# X-Signature: {signature}
```

### Brute Force Test
```bash
# Failed login 5 times
for i in {1..5}; do
  curl -X POST http://localhost:8000/login \
    -H "Content-Type: application/json" \
    -d '{"username":"researcher_user","password":"wrong"}'
done

# 6th attempt should return 429 with Retry-After header
```

### SQL Allowlist Test
```python
# These should be BLOCKED
validate_sql_query("DROP TABLE researchers")  # False
validate_sql_query("DELETE FROM researchers")  # False
validate_sql_query("SELECT * FROM researchers; DROP TABLE researchers")  # False

# These should be ALLOWED
validate_sql_query("SELECT * FROM researchers LIMIT 10")  # True
validate_sql_query("SELECT name, email FROM researchers WHERE state = 'Karnataka'")  # True
```

### PII Encryption Test
```python
from src.security.pii_encryption import encrypt, decrypt, is_encrypted

# Test round-trip
original = "test@example.com"
encrypted = encrypt(original)
print(f"Encrypted: {encrypted}")
print(f"Is encrypted: {is_encrypted(encrypted)}")
decrypted = decrypt(encrypted)
print(f"Decrypted: {decrypted}")
print(f"Match: {original == decrypted}")
```

### DPDP Cleanup Test
```python
from src.security.dpdp_compliance import run_retention_cleanup

result = run_retention_cleanup()
print(f"Purge result: {result}")
# Should show {"success": True, "purged_records": N, "users_processed": M}
```

## Files Created

| File | Purpose |
|------|---------|
| `src/security/security_harden.py` | Module exports and aggregation |
| `src/security/rate_limiter.py` | Redis-based tiered rate limiting |
| `src/security/request_signer.py` | HMAC signature verification |
| `src/security/pii_encryption.py` | AES-256 field encryption |
| `src/security/query_allowlist.py` | SQL validation and blocking |
| `src/security/token_rotation.py` | JWT rotation management |
| `src/security/dpdp_compliance.py` | 90-day data retention |
| `src/security/headers.py` | Security headers middleware |
| `security_report.md` | This documentation |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NRG_PII_ENCRYPTION_KEY` | AES-256 key (base64) | Not set |
| `NRG_DATA_RETENTION_DAYS` | DPDP retention period | 90 |
| `NRG_ACCESS_TOKEN_TTL` | Access token expiry (seconds) | 900 |
| `NRG_REFRESH_TOKEN_TTL` | Refresh token expiry (seconds) | 604800 |
| `NRG_REQUEST_SIGNING_SECRET` | HMAC signing secret | nrg-default-signing-secret |
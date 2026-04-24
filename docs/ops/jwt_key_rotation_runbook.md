# JWT Key Rotation Runbook — NRG Platform

## Overview

NRG uses RS256 (RSA-SHA256) asymmetric JWTs for authentication. Key rotation is required when:
- A signing key is suspected to be compromised
- Routine security rotation (recommended: every 90 days)
- Compliance audit requires it

**Key storage**: `infrastructure/kong/ssl/jwt_rsa.key` (private), `jwt_rsa.pub` (public)
**Rotation method**: `JWTHandler.rotate_signing_key()` — supports dual-key overlap (old and new keys both verified during transition)

## Rotation Strategy: Dual-Key Overlap

When keys are rotated, the old key ID is retained in `_known_key_ids`. This means:
- Tokens signed with the OLD key continue to work during the overlap window
- Tokens signed with the NEW key use the new key ID
- Verification accepts BOTH keys until all in-flight tokens expire

**Overlap window**: Set to match your access token TTL (default: 15 minutes for access tokens, 7 days for refresh tokens)

---

## Pre-Rotation Checklist

```bash
# 1. Verify current key fingerprint
openssl rsa -in infrastructure/kong/ssl/jwt_rsa.key -pubout -outform der | sha256sum

# 2. Check token issue rate (ensure low traffic before rotation)
curl -s http://localhost:8000/metrics | grep nrg_queries_total

# 3. Notify #engineering Slack channel
# @channel JWT key rotation starting at $(date -u)
```

---

## Procedure A: Routine Scheduled Rotation (No Compromise)

### Step 1: Generate New Key Pair

```bash
# Generate new RSA-4096 key pair
openssl genrsa -out /tmp/new_jwt_key.pem 4096
openssl rsa -in /tmp/new_jwt_key.pem -pubout -out /tmp/new_jwt_pub.pem

# Verify the new key
openssl rsa -in /tmp/new_jwt_key.pem -check -noout
```

### Step 2: Load Keys into Environment

```python
# Option A: File-based (update JWT_PRIVATE_KEY_PATH / JWT_PUBLIC_KEY_PATH env vars)
# Then restart the API server

# Option B: Runtime rotation via Python interpreter
from src.auth.jwt_handler import JWTHandler

jh = JWTHandler()  # loads existing keys first

new_private = open("/tmp/new_jwt_key.pem").read()
new_public = open("/tmp/new_jwt_pub.pem").read()

jh.rotate_signing_key(new_private, new_public)
print(f"Rotated. New kid={jh._signing_key_id}, known={jh._known_key_ids}")
```

### Step 3: Verify New Tokens Use New Key

```python
# Issue a test token and verify its kid header
test_token = jh.issue_access_token({"user_id": "test", "role": "researcher", "tier": 1, "username": "test"})
import jwt
header = jwt.get_unverified_header(test_token)
assert header["kid"] == jh._signing_key_id, "New token uses wrong key!"
```

### Step 4: Monitor for 1 Hour

```bash
# Watch for authentication failures
curl -s http://localhost:8000/metrics | grep auth_failure

# Check logs
grep -i "jwt\|auth\|signature" logs/nrg_api.log | tail -50
```

### Step 5: Commit New Keys to Vault (Production)

```bash
# Store new private key in HashiCorp Vault
vault kv put secret/nrg/jwt private_key=@/tmp/new_jwt_key.pem public_key=@/tmp/new_jwt_pub.pem

# Mark old key for retirement (after overlap window expires)
vault kv put secret/nrg/jwt/retired key_id=<old_kid> retired_at=$(date -u)
```

---

## Procedure B: Emergency Rotation (Suspected Compromise)

**Trigger**: Key leaked, unauthorized access detected, or security incident declared.

### Step 1: Immediately Invalidate All Tokens

```python
from src.auth.jwt_handler import JWTHandler
from datetime import datetime, UTC

jh = JWTHandler()

# Revoke ALL active refresh tokens (forces re-login for all users)
jh.refresh_store.revoke_all()

# Log the incident
print(f"Emergency rotation at {datetime.now(UTC).isoformat()} — all sessions force-logout")
```

### Step 2: Rotate Key

```bash
openssl genrsa -out /tmp/emergency_key.pem 4096
openssl rsa -in /tmp/emergency_key.pem -pubout -out /tmp/emergency_pub.pem
```

```python
jh.rotate_signing_key(open("/tmp/emergency_key.pem").read(), open("/tmp/emergency_pub.pem").read())
```

### Step 3: Verify ZERO tokens from old key work

```python
# Try to decode a pre-rotation token — should raise AuthError
try:
    jh.verify_access_token(old_token)
    raise RuntimeError("FAIL: old token still valid!")
except Exception as e:
    print(f"GOOD: old token rejected — {e}")
```

### Step 4: Notify Users

Send notification that all sessions have been invalidated and users must re-authenticate.

### Step 5: Post-Incident

1. Conduct security review of access logs for the compromised key's usage window
2. File security incident report
3. Update key in vault with new fingerprint

---

## Kong Gateway Integration

If using Kong as the auth proxy, keys must be updated there too:

```bash
# Update Kong consumer jwt key
curl -X PATCH http://kong:8001/consumers/<consumer>/jwt \
  -d "key=<new_public_key_fingerprint>" \
  -H "Kong-Admin-Token: <admin_token>"

# Or via Deck sync
deck gateway dump > /tmp/kong_config.yml
# Edit jwt key in config, then:
deck gateway sync /tmp/kong_config.yml
```

---

## Rollback Procedure

If the new key causes issues (rare):

```python
# Revert to previous key (you kept the old key in _known_key_ids)
jh.rotate_signing_key(old_private, old_public)
# Now both old and new tokens work again
```

**Important**: Rollback does NOT invalidate compromised keys if compromise was the reason for rotation. In a true compromise scenario, you MUST generate a brand new key, not revert to the old one.

---

## Verification Commands

```bash
# Check JWT handler is loading correct keys
python3 -c "
from src.auth.jwt_handler import JWTHandler
jh = JWTHandler()
print('Algorithm:', jh.algorithm)
print('Signing key ID:', jh._signing_key_id)
print('Known key IDs:', jh._known_key_ids)
"

# Check token verification works end-to-end
python3 -c "
from src.auth.jwt_handler import JWTHandler
jh = JWTHandler()
token = jh.issue_access_token({'user_id': 'verify', 'role': 'researcher', 'tier': 1, 'username': 'verify'})
claims = jh.verify_access_token(token)
print('Token verified OK:', claims['sub'])
"

# Health endpoint check
curl -s http://localhost:8000/health | jq '.auth_status'
```

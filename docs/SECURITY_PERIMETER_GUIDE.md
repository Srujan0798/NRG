# IITGN Security Perimeter Hardening Guide

## Overview

This guide covers the deployment and validation of the National Research Graph's security perimeter, including:
- **DLP (Data Loss Prevention)**: 10+ PII patterns with tokenization
- **JWT Authentication**: RS256 with RSA-4096 keypairs
- **Prompt Injection Defense**: 13+ attack pattern signatures
- **Audit Logging**: Complete security event tracking

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kong Gateway (Port 8000)                  │
├─────────────────────────────────────────────────────────────┤
│  Plugins (in order):                                         │
│  1. CORS                                                     │
│  2. JWT Authentication (RS256)                               │
│  3. ACL (Role-based access)                                  │
│  4. DLP (PII Detection & Tokenization)                       │
│  5. Rate Limiting (100 req/min)                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      NRG API (Port 8001)                     │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Run Security Hardening Script

```bash
bash scripts/security/harden_security_perimeter.sh
```

This automates all Omega protocols in sequence.

### 2. Start Kong Gateway

```bash
docker-compose -f infrastructure/kong/docker-compose.yml up -d
```

### 3. Run Security Tests

```bash
python tests/security/test_security_perimeter.py
```

## Component Details

### OMEGA-1: DLP Weaponization

**Location**: `infrastructure/kong/plugins/dlp/`

**Supported PII Patterns** (10 total):

| Pattern | Regex | Action | Severity |
|---------|-------|--------|----------|
| Aadhaar | `\b\d{4}\s?\d{4}\s?\d{4}\b` | Block + Tokenize | Critical |
| PAN | `\b[A-Z]{5}\d{4}[A-Z]\b` | Block | Critical |
| Phone | `\b(\+91|0)?[6-9]\d{9}\b` | Block + Tokenize | High |
| Passport | `\b[A-Z]{1}[0-9]{7}\b` | Block | Critical |
| Email | `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b` | Tokenize | Medium |
| UPI ID | `\b[a-zA-Z0-9._-]+@[a-zA-Z]{2,}\b` | Block | High |
| IFSC | `\b[A-Z]{4}0[A-Z0-9]{6}\b` | Block | Critical |
| Driving License | `\b[A-Z]{2}[0-9]{2}\s?[0-9]{11}\b` | Block | High |
| Voter ID | `\b[A-Z]{3}[0-9]{7}\b` | Block | High |
| Bank Account | `\b\d{9,18}\b` | Block | Critical |

**Tokenization**: 
- Method: HMAC-SHA256
- Format preservation: Shows last 4 characters
- Secret: Configured via `DLP_TOKENIZATION_SECRET` env var

**Configuration**:
```yaml
# infrastructure/kong/plugins/dlp_config.yml
plugins:
- name: dlp
  config:
    block_pii: true
    block_injection: true
    audit_log_blocks: true
    audit_log_tokenized: true
```

### OMEGA-2: JWT Cipher Upgrade (RS256)

**Key Generation**:
```bash
# Generate RSA-4096 keypair
ssh-keygen -t rsa -b 4096 -m PEM -f infrastructure/kong/ssl/jwt_rsa.key -N ''
ssh-keygen -f infrastructure/kong/ssl/jwt_rsa.key.pub -e -m PKCS8 > infrastructure/kong/ssl/jwt_rsa.pub
```

**Key Files**:
- `infrastructure/kong/ssl/jwt_rsa.key` - Private key (NEVER commit to git)
- `infrastructure/kong/ssl/jwt_rsa.pub` - Public key (safe for Kong)

**Configuration**:
```yaml
# infrastructure/kong/kong.yml
consumers:
  - username: researcher
    jwt_secrets:
      - key: researcher
        algorithm: RS256  # Upgraded from HS256
```

**Python Integration**:
```python
from src.auth.jwt_handler import JWTHandler

# Initialize with RS256
handler = JWTHandler(algorithm="RS256")

# Issue token
user = {
    "user_id": "user-001",
    "username": "researcher_user",
    "role": "researcher",
    "tier": 1,
    "groups": ["researcher"],
    "scope": "own_and_public"
}
tokens = handler.issue_token_pair(user)

# Verify token
claims = handler.verify_access_token(tokens["access_token"])
assert claims["tier"] == 1
```

**Environment Variables**:
```env
JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY_PATH=infrastructure/kong/ssl/jwt_rsa.key
JWT_PUBLIC_KEY_PATH=infrastructure/kong/ssl/jwt_rsa.pub
```

### OMEGA-3: Prompt Injection Defense

**Attack Patterns Detected** (13 total):
1. `system prompt` - System prompt extraction attempts
2. `ignore previous` - Context reset attacks
3. `as an ai` - Role manipulation
4. `you are now` - Identity override
5. `role play` - Character impersonation
6. `hypothetical` - Scenario-based bypass
7. `disregard.*instructions` - Instruction override
8. `from.*now.*on` - Behavioral modification
9. `bypass.*security` - Security circumvention
10. `override.*protocol` - Protocol manipulation
11. `jailbreak` - Jailbreak attempts
12. `prompt injection` - Meta-attacks
13. `developer mode` - Privilege escalation

**Response Format**:
```json
{
  "error": "PROMPT_INJECTION",
  "message": "Potential prompt injection detected",
  "request_id": "uuid-here"
}
```

### OMEGA-4: Audit Logging

**Events Tracked**:
- `dlp_blocked` - PII detection and blocking
- `dlp_tokenized` - PII tokenization
- `auth_success` - Successful authentication
- `auth_failure` - Failed authentication
- `rate_limit_exceeded` - Rate limiting

**Log Format**:
```json
{
  "event": "dlp_blocked",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "block_reason": "DLP_VIOLATION",
  "detected_type": "aadhaar",
  "severity": "critical",
  "client_ip": "192.168.1.100",
  "client_user_agent": "Mozilla/5.0...",
  "path": "/query",
  "method": "POST",
  "timestamp": "2026-04-15T10:30:00Z"
}
```

## Security Testing

### Test Suite Structure

```
tests/security/
├── test_security_perimeter.py  # Comprehensive test suite
└── __init__.py
```

### Running Tests

```bash
# Full test suite (requires Kong running)
python tests/security/test_security_perimeter.py

# Individual test categories
python -m pytest tests/security/test_security_perimeter.py::DLPSecurityTester::test_aadhaar_blocking -v
```

### Test Coverage

| Test Category | Patterns | Status |
|---------------|----------|--------|
| Aadhaar Blocking | 4 variations | ✅ |
| PAN Blocking | 3 variations | ✅ |
| Phone Blocking | 4 variations | ✅ |
| Passport Blocking | 3 variations | ✅ |
| Email Tokenization | 3 variations | ✅ |
| UPI ID Blocking | 3 variations | ✅ |
| IFSC Blocking | 3 variations | ✅ |
| Prompt Injection | 13 patterns | ✅ |
| RS256 JWT Generation | 7 checks | ✅ |
| Token Lifecycle | Issue/Verify/Refresh/Revoke | ✅ |

## Deployment Checklist

- [ ] RSA keypair generated (`infrastructure/kong/ssl/`)
- [ ] `.env` configured with RS256 paths
- [ ] `kong.yml` uses `algorithm: RS256`
- [ ] DLP plugin patterns loaded (10 PII types)
- [ ] Audit logging enabled
- [ ] Rate limiting configured (100 req/min)
- [ ] Kong gateway restarted
- [ ] Security tests passing
- [ ] `.jwt_secret` in `.gitignore`
- [ ] `*.key` files in `.gitignore`

## Production Hardening

### Additional Steps for Production

1. **Rotate Default Secrets**:
```bash
# Replace CHANGE_THIS_IN_PRODUCTION in kong.yml
openssl rand -base64 32 > .jwt_secret
```

2. **Enable HTTPS**:
```yaml
# docker-compose.yml
services:
  kong:
    environment:
      KONG_SSL_CERT: /usr/local/kong/ssl/cert.pem
      KONG_SSL_CERT_KEY: /usr/local/kong/ssl/key.pem
```

3. **Configure Tokenization Secret**:
```bash
export DLP_TOKENIZATION_SECRET=$(openssl rand -base64 32)
```

4. **Enable IP-based Rate Limiting**:
```yaml
plugins:
  - name: rate-limiting
    config:
      minute: 100
      policy: redis  # Use Redis for distributed rate limiting
```

5. **Audit Log Aggregation**:
```bash
# Configure Kong to send logs to external system
docker exec nrg-kong-gateway kong config set log_level=notice
```

## Troubleshooting

### Kong Won't Start
```bash
# Check configuration
docker exec nrg-kong-gateway kong check /usr/local/kong/declarative/kong.yml

# View logs
docker logs nrg-kong-gateway
```

### DLP Not Blocking PII
```bash
# Verify plugin is loaded
curl http://localhost:8001/plugins | jq '.data[] | select(.name=="dlp")'

# Check plugin config
curl http://localhost:8001/plugins?name=dlp
```

### JWT Verification Fails
```bash
# Verify key files exist
ls -la infrastructure/kong/ssl/

# Test token generation
python -c "
from src.auth.jwt_handler import JWTHandler
handler = JWTHandler(algorithm='RS256')
print('✅ RS256 handler initialized')
"
```

### Rate Limiting Not Working
```bash
# Check rate limit plugin
curl http://localhost:8001/plugins?name=rate-limiting

# View rate limit headers
curl -I http://localhost:8000/query -H "Authorization: Bearer $TOKEN"
```

## API Reference

### Authentication Flow

1. **Login**: `POST /login`
```json
{
  "username": "researcher_user",
  "password": "researcher-pass"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_expires_in": 604800
}
```

2. **Authenticated Query**: `POST /query`
```bash
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "safe research query"}'
```

3. **Refresh Token**: `POST /refresh`
```bash
curl -X POST http://localhost:8000/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "$REFRESH_TOKEN"}'
```

## License & Compliance

- **GDPR**: PII detection supports EU data protection requirements
- **DPDP Act 2023**: Indian data protection compliance
- **PCI-DSS**: Payment data (UPI, bank accounts) blocked
- **HIPAA**: Health data patterns can be added via `pii_types.yml`

## Support

For security issues or questions:
1. Check logs: `docker logs nrg-kong-gateway`
2. Review audit events in Kong logs
3. Run test suite: `python tests/security/test_security_perimeter.py`
4. Check Kong admin API: `http://localhost:8001/`

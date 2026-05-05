# NRG Security Model

## Authentication

**Method:** JWT with RS256 asymmetric signing
- Private key: `infrastructure/kong/ssl/jwt_rsa.key`
- Public key: `infrastructure/kong/ssl/jwt_rsa.pub`
- Tokens set as HttpOnly cookies + Bearer header
- Refresh token rotation on every use

**Endpoints:** `/login`, `/logout`, `/refresh`, `/auth/*`

## Authorization (RBAC)

**Path:** `src/auth/rbac.py`, `src/auth/rbac_policies.yaml`

| Persona | Tier | Output Format | Use Case |
|---------|------|---------------|----------|
| researcher | 1 | full | Individual researcher viewing full data |
| government | 2 | aggregated | Ministry official viewing summaries |
| industry | 3 | anonymized | Private partner viewing redacted data |
| peer_reviewer | 1 | aggregated | Journal reviewer |
| department_head | 2 | aggregated | Department admin |
| student | 3 | anonymized | Student researcher |

**Enforcement:** `src/auth/middleware.py` — every API route checks tier before response.

## DPDP Compliance (India 2023)

**Path:** `src/api/routes/dpdp.py`, `src/security/`

- **Consent:** `/consent` — user grants/revokes data processing consent
- **Export:** `/dpdp/export` — user downloads all their data
- **Erasure:** `/dpdp/erase` — user requests data deletion
- **Consents list:** `/dpdp/consents`, `/me/consents`

## PII Detection

**Path:** `src/security/pii/`

Detects and blocks:
- PAN: `[A-Z]{5}[0-9]{4}[A-Z]`
- Aadhaar: 12-digit with Verhoeff checksum
- Indian mobile: `+91` or `0?[6-9]\d{9}`
- Email, passport, GSTIN, bank account

**Tests:** `tests/security/test_pii_indian.py`

## Audit Chain (Non-Repudiation)

**Path:** `src/audit/`

- Every event: `user_id`, `persona`, `jwt_jti`, `request_fingerprint`
- HMAC-signed with per-user derived key
- Chain file: `.audit/chain.jsonl`
- Genesis hash: `.audit/genesis_hash.pin` (hardened to 0444)
- Verification: `/audit/verify` returns `True/False`

## Egress Guard

**Path:** `src/security/egress_guard/`

- Inspects every outbound LLM payload
- Only allowlisted schema fragments may appear
- Blocks: raw DB schema, non-allowlisted column names, sensitive metadata
- Config: `src/security/egress_allowlist.yaml`

## Cloud Synthesis Security

- Disabled by default (`CLOUD_SYNTHESIS_ALLOWED=false`)
- When enabled: only minimized, sanitized evidence packets sent
- Never sends: raw dumps, full documents, PII, unrestricted schema

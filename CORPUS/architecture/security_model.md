# POINTER: Security Model

> **Do not trust this file as the source of truth.** Read the actual files listed below and verify against `Core_Idea_Clean.md` and `quality/quality_bar.md` (C1, C2, C6) requirements.

## Where to Read

| Topic | Actual Source Files | What to Verify |
|-------|--------------------|----------------|
| **JWT Auth** | `src/auth/rbac.py`, `src/auth/middleware.py`, `infrastructure/kong/ssl/jwt_rsa.key` | RS256 signing, token rotation, HttpOnly cookies |
| **RBAC Tiers** | `src/auth/rbac_policies.yaml`, `src/auth/rbac.py` | 6 personas, 3 tiers, full/aggregated/anonymized |
| **DPDP Compliance** | `src/api/routes/dpdp.py` | Consent, export, erasure endpoints |
| **PII Detection** | `src/security/pii/`, `tests/security/test_pii_indian.py` | PAN, Aadhaar, mobile, email detection |
| **Egress Guard** | `src/security/egress_guard/`, `src/security/egress_allowlist.yaml` | Allowlisted schema fragments only |
| **Audit Chain** | `src/audit/`, `.audit/chain.jsonl`, `.audit/genesis_hash.pin` | HMAC, per-user binding, tamper-proof |

## Verification Commands

```bash
# Check JWT keys exist
ls infrastructure/kong/ssl/jwt_rsa.key infrastructure/kong/ssl/jwt_rsa.pub

# Check RBAC policies
ls src/auth/rbac_policies.yaml src/auth/rbac.py src/auth/middleware.py

# Check DPDP routes
grep -n "dpdp" src/api/routes/dpdp.py | head -10

# Check PII tests
ls tests/security/test_pii_indian.py

# Check egress guard
ls src/security/egress_guard/ src/security/egress_allowlist.yaml

# Check audit chain
ls src/audit/ .audit/chain.jsonl .audit/genesis_hash.pin
```

## Requirements to Verify Against

From `quality/quality_bar.md`:
- **C1:** DPDP PII detection — zero false negatives
- **C2:** Per-user audit binding — HMAC with derived key
- **C6:** Schema egress allowlist — block non-allowlisted schema fragments

From `Core_Idea_Clean.md`:
- Zero-data-leakage model
- Tier boundary enforced at API/backend first
- Cloud synthesis disabled by default

**Read the actual source files. Do not trust this pointer.**

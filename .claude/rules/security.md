---
paths:
  - "src/security/**/*.py"
  - "src/auth/**/*.py"
  - "src/audit/**/*.py"
---

# Security Rules

- JWT RS256 only (keys at infrastructure/kong/ssl/)
- AUDIT_CHAIN_KEY must come from env var in production
- CORS origins from CORS_ORIGINS env var, never hardcode ["*"]
- Prompt sanitiser runs BEFORE any query hits the orchestration pipeline
- Egress guard inspects all cloud LLM payloads before they leave
- Refresh tokens must go through RefreshStore (store/verify/revoke)
- PII patterns: Aadhaar, PAN, phone, email — always redact
- **Audit chain transparency:** If `get_chain_health()` auto-repairs a hash mismatch, the repair must be logged as WARNING, not silent. The chain's cryptographic lineage must be traceable.
- **Health endpoint security:** `/health` must not use auto-repair or caching to hide security failures. Raw verification state must be exposed.

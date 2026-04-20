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

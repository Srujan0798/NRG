"""Production-grade security hardening for NRG platform.

Implements fortress-level security:
- Tiered rate limiting with Redis
- HMAC request signing with replay protection
- IP allowlisting for government tier
- Brute-force protection with lockout
- Security headers on all responses
- PII encryption at rest (AES-256)
- SQL query allowlisting
- Token rotation (15min access / 7day refresh)
- Egress guard alerting
- DPDP data retention (90-day purge)
"""

from .rate_limiter import TieredRateLimiter, get_rate_limiter
from .request_signer import RequestSigner, verify_hmac_signature, log_signature_attempt
from .pii_encryption import PIIEncryptor, encrypt_pii_field, decrypt_pii_field
from .query_allowlist import SQLAllowlist, validate_sql_query, log_blocked_query
from .token_rotation import TokenRotator, rotate_tokens
from .dpdp_compliance import DPDPCompliance, run_retention_cleanup
from .headers import SecurityHeadersMiddleware, add_security_headers

__all__ = [
    "TieredRateLimiter",
    "get_rate_limiter",
    "RequestSigner",
    "verify_hmac_signature",
    "log_signature_attempt",
    "PIIEncryptor",
    "encrypt_pii_field",
    "decrypt_pii_field",
    "SQLAllowlist",
    "validate_sql_query",
    "log_blocked_query",
    "TokenRotator",
    "rotate_tokens",
    "DPDPCompliance",
    "run_retention_cleanup",
    "SecurityHeadersMiddleware",
    "add_security_headers",
]
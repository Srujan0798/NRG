"""Security middleware: brute-force protection, security headers, IP allowlisting, prompt sanitisation."""

import time
import hashlib
import hmac
import ipaddress
import logging
import json
from typing import Optional

from fastapi import HTTPException, Request, Header
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.security.gateway.prompt_sanitiser import PromptSanitiser

logger = logging.getLogger(__name__)

_prompt_sanitiser = PromptSanitiser()


class BruteForceProtection:
    """Login brute-force protection with account lockout."""

    MAX_FAILURES = 5
    LOCKOUT_DURATION = 900  # 15 minutes

    def __init__(self):
        self._failure_count: dict[str, int] = {}
        self._lockout_until: dict[str, float] = {}

    def check_login_failure(self, username: str) -> tuple[bool, str]:
        """Check if account is locked out. Returns (is_locked, message)."""
        normalized = username.lower()

        if normalized in self._lockout_until:
            if time.time() < self._lockout_until[normalized]:
                remaining = int(self._lockout_until[normalized] - time.time())
                return True, f"Account locked. Try again in {remaining} seconds."
            else:
                del self._lockout_until[normalized]
                self._failure_count[normalized] = 0

        return False, ""

    def record_failure(self, username: str):
        """Record a failed login attempt."""
        normalized = username.lower()
        self._failure_count[normalized] = self._failure_count.get(normalized, 0) + 1

        if self._failure_count[normalized] >= self.MAX_FAILURES:
            self._lockout_until[normalized] = time.time() + self.LOCKOUT_DURATION
            logger.warning(f"Account locked due to failed attempts: {username}")
        elif self._failure_count[normalized] >= 3:
            logger.warning(f"Login failed ({self._failure_count[normalized]}/5): {username}")

    def record_success(self, username: str):
        """Clear failures on successful login."""
        normalized = username.lower()
        self._failure_count.pop(normalized, None)
        self._lockout_until.pop(normalized, None)


brute_force_protection = BruteForceProtection()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' http://localhost:8000 https://localhost:8000;"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


class IPAllowlist:
    """IP allowlisting for government tier."""

    ALLOWED_IPS: set = set()

    @classmethod
    def add_allowed_ip(cls, ip: str):
        """Add an IP to the allowlist."""
        try:
            ipaddress.ip_address(ip)
            cls.ALLOWED_IPS.add(ip)
            logger.info(f"Added IP to allowlist: {ip}")
        except ValueError:
            logger.warning(f"Invalid IP address: {ip}")

    @classmethod
    def remove_allowed_ip(cls, ip: str):
        """Remove an IP from the allowlist."""
        cls.ALLOWED_IPS.discard(ip)

    @classmethod
    def is_allowed(cls, ip: str) -> bool:
        """Check if IP is allowed. Empty allowlist = all allowed."""
        if not cls.ALLOWED_IPS:
            return True
        return ip in cls.ALLOWED_IPS


class RequestSigner:
    """HMAC request signing for /query endpoint."""

    def __init__(self, secret_key: str = "nrg-request-signing-key"):
        self.secret_key = secret_key.encode()

    def sign(self, payload: str, timestamp: int) -> str:
        """Generate HMAC signature."""
        message = f"{timestamp}:{payload}"
        return hmac.new(self.secret_key, message.encode(), hashlib.sha256).hexdigest()

    def verify(self, payload: str, timestamp: int, signature: str) -> bool:
        """Verify HMAC signature."""
        if abs(time.time() - timestamp) > 300:
            return False
        expected = self.sign(payload, timestamp)
        return hmac.compare_digest(expected, signature)

    def create_signed_payload(self, payload: dict) -> dict:
        """Create payload with signature."""
        timestamp = int(time.time())
        payload_str = json.dumps(payload, sort_keys=True)
        signature = self.sign(payload_str, timestamp)
        return {
            **payload,
            "_timestamp": timestamp,
            "_signature": signature,
        }


request_signer = RequestSigner()


def enforce_tier_response_boundary(payload: object, tier: int) -> None:
    """Fail closed if a response still violates the configured tier boundary."""
    if tier <= 1:
        return

    from src.api.response_filter import find_tier_response_violations

    violations = find_tier_response_violations(payload, tier=tier)
    if not violations:
        return

    reasons = sorted({item.get("reason", "tier_response_violation") for item in violations})
    logger.critical(
        "Tier response boundary blocked payload",
        extra={
            "tier": tier,
            "violation_count": len(violations),
            "reasons": reasons[:10],
        },
    )
    raise HTTPException(status_code=500, detail="Response blocked by access policy")


def verify_request_signature(
    request: Request,
    x_signature: Optional[str] = Header(None),
    x_timestamp: Optional[int] = Header(None),
):
    """Dependency to verify request signature."""
    if not x_signature or not x_timestamp:
        raise HTTPException(
            status_code=401,
            detail="Missing request signature"
        )

    body = getattr(request, "_body", "")
    if not request_signer.verify(body, x_timestamp, x_signature):
        raise HTTPException(
            status_code=401,
            detail="Invalid request signature"
        )

    return True


class PromptSanitiserMiddleware(BaseHTTPMiddleware):
    """Validate all text-bearing request parameters against prompt injection and PII rules.

    Checks query, topic, search, q, text, prompt, message, content fields
    in both query string and JSON request bodies.
    """

    SKIP_PATHS = {
        "/health", "/health/llm", "/health/db", "/health/qdrant", "/health/all",
        "/metrics", "/docs", "/openapi.json", "/favicon.ico",
        "/login", "/logout", "/refresh",
    }

    TEXT_VALUE_MIN_LEN = 2

    async def dispatch(self, request: Request, call_next):
        if not self._should_skip_path(request.url.path):
            fields = await self._extract_text_fields(request)
            for field_name, field_value in fields:
                identifier = request.client.host if request.client else None
                if identifier == "testclient":
                    identifier = None
                validation = _prompt_sanitiser.validate_query(
                    {"query": field_value},
                    identifier=identifier,
                )
                if not validation["valid"]:
                    try:
                        from src.audit import log_anomaly
                        user_id = getattr(request.state, "auth_claims", {}).get("sub", "anonymous")
                        log_anomaly(
                            user_id=user_id,
                            anomaly_type=validation["reason"],
                            details={
                                "field": field_name,
                                "path": request.url.path,
                                "details": validation.get("details", ""),
                                "rate_limit_triggered": validation.get("rate_limit_triggered", False),
                            },
                            identifier=identifier,
                        )
                    except Exception:
                        pass
                    logger.warning(
                        f"PromptSanitiserMiddleware rejected: {validation['reason']} - "
                        f"field={field_name} path={request.url.path}"
                    )
                    return JSONResponse(
                        status_code=400,
                        content={"detail": f"Security violation: {validation['reason']}"},
                    )

        return await call_next(request)

    def _should_skip_path(self, path: str) -> bool:
        for skip in self.SKIP_PATHS:
            if path.startswith(skip):
                return True
        return False

    async def _extract_text_fields(self, request: Request) -> list[tuple[str, str]]:
        fields: list[tuple[str, str]] = []
        for key, value in dict(request.query_params).items():
            if isinstance(value, str) and len(value) >= self.TEXT_VALUE_MIN_LEN:
                fields.append((key, value))
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body = await request.json()
            except Exception:
                body = None
            fields.extend(self._extract_json_text_fields(body))
        return fields

    def _extract_json_text_fields(
        self,
        value: object,
        prefix: str = "body",
    ) -> list[tuple[str, str]]:
        fields: list[tuple[str, str]] = []
        if isinstance(value, dict):
            for key, item in value.items():
                fields.extend(self._extract_json_text_fields(item, f"{prefix}.{key}"))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                fields.extend(self._extract_json_text_fields(item, f"{prefix}[{index}]"))
        elif isinstance(value, str) and len(value) >= self.TEXT_VALUE_MIN_LEN:
            fields.append((prefix, value))
        return fields

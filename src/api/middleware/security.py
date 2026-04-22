"""Security middleware: brute-force protection, security headers, IP allowlisting."""

import time
import hashlib
import hmac
import ipaddress
import logging
from typing import Optional

from fastapi import HTTPException, Request, Header
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


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
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' http://localhost:8000;"
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
        import json
        timestamp = int(time.time())
        payload_str = json.dumps(payload, sort_keys=True)
        signature = self.sign(payload_str, timestamp)
        return {
            **payload,
            "_timestamp": timestamp,
            "_signature": signature,
        }


request_signer = RequestSigner()


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
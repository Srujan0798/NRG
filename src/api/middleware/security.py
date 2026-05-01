"""Security middleware: brute-force protection, security headers, IP allowlisting, prompt sanitisation."""

import time
import asyncio
import hashlib
import hmac
import ipaddress
import logging
import json
import os
from urllib.parse import parse_qsl
from typing import Optional

from fastapi import HTTPException, Request, Header
from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse

from src.api.answer_contract import blocked_answer_payload
from src.security.gateway.prompt_sanitiser import PromptSanitiser

logger = logging.getLogger(__name__)

_prompt_sanitiser: PromptSanitiser | None = None


def _get_prompt_sanitiser() -> PromptSanitiser:
    global _prompt_sanitiser
    if _prompt_sanitiser is None:
        _prompt_sanitiser = PromptSanitiser()
    return _prompt_sanitiser


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
            logger.warning(f"Account locked due to failed attempts: {normalized}")
        elif self._failure_count[normalized] >= 3:
            logger.warning(f"Login failed ({self._failure_count[normalized]}/5): {normalized}")

    def record_success(self, username: str):
        """Clear failures on successful login."""
        normalized = username.lower()
        self._failure_count.pop(normalized, None)
        self._lockout_until.pop(normalized, None)


brute_force_protection = BruteForceProtection()


class SecurityHeadersMiddleware:
    """Add security headers to all responses."""

    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' http://localhost:8000 https://localhost:8000;"
        ),
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in self.SECURITY_HEADERS.items():
                    headers[name] = value
            await send(message)

        await self.app(scope, receive, send_with_security_headers)


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
        raise HTTPException(status_code=401, detail="Missing request signature")

    body = getattr(request, "_body", "")
    if not request_signer.verify(body, x_timestamp, x_signature):
        raise HTTPException(status_code=401, detail="Invalid request signature")

    return True


class PromptSanitiserMiddleware:
    """Validate all text-bearing request parameters against prompt injection and PII rules.

    Checks query, topic, search, q, text, prompt, message, content fields
    in both query string and JSON request bodies.
    """

    SKIP_PATHS = {
        "/health",
        "/health/llm",
        "/health/db",
        "/health/qdrant",
        "/health/all",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/favicon.ico",
        "/login",
        "/logout",
        "/refresh",
        "/auth/login",
        "/auth/logout",
        "/auth/refresh",
        "/auth/session",
        "/query",
        "/api/query/stream",
    }

    TEXT_VALUE_MIN_LEN = 2

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if self._should_skip_path(path):
            await self.app(scope, receive, send)
            return

        body = await self._read_body(receive)
        headers = Headers(scope=scope)
        fields = self._extract_text_fields_from_scope(scope, headers, body)
        identifier = self._identifier_for_scope(scope, headers)
        if identifier == "testclient":
            identifier = None

        for field_name, field_value in fields:
            validation = _get_prompt_sanitiser().validate_query(
                {"query": field_value},
                identifier=identifier,
            )
            if not validation["valid"]:
                audit_event_id = None
                try:
                    from src.audit import log_anomaly

                    state = scope.get("state") or {}
                    claims = state.get("auth_claims") or {}
                    user_id = claims.get("sub", "anonymous")
                    audit_event_id = await asyncio.to_thread(
                        log_anomaly,
                        user_id=user_id,
                        anomaly_type=validation["reason"],
                        details={
                            "field": field_name,
                            "path": path,
                            "details": validation.get("details", ""),
                            "rate_limit_triggered": validation.get(
                                "rate_limit_triggered", False
                            ),
                        },
                        identifier=identifier,
                    )
                except Exception:
                    pass
                log_blocked_prompts = os.getenv("NRG_LOG_BLOCKED_PROMPTS", "").lower() in {
                    "1",
                    "true",
                    "yes",
                }
                log_method = logger.warning if log_blocked_prompts else logger.debug
                log_method(
                    "PromptSanitiserMiddleware rejected: %s - field=%s path=%s",
                    validation["reason"],
                    field_name,
                    path,
                )
                if path == "/query" and validation["reason"] != "RATE_LIMITED":
                    state = scope.get("state") or {}
                    claims = state.get("auth_claims") or {}
                    try:
                        user_tier = int(claims.get("tier", 1) or 1)
                    except (TypeError, ValueError):
                        user_tier = 1
                    blocked = blocked_answer_payload(
                        question=field_value,
                        user_tier=user_tier,
                        audit_event_id=audit_event_id,
                        reason=f"Security policy blocked this query: {validation['reason']}",
                    )
                    response = JSONResponse(status_code=200, content=blocked)
                    await response(scope, self._replay_body(body), send)
                    return
                response = JSONResponse(
                    status_code=429 if validation["reason"] == "RATE_LIMITED" else 400,
                    content={"detail": f"Security violation: {validation['reason']}"},
                )
                await response(scope, self._replay_body(body), send)
                return

        await self.app(scope, self._replay_body(body), send)

    def _identifier_for_request(self, request: Request) -> Optional[str]:
        """Return the client identifier used for rejection tracking.

        Proxy headers are trusted only when explicitly enabled, because a direct
        internet client can spoof X-Forwarded-For.
        """
        trust_proxy = os.environ.get("TRUST_PROXY_HEADERS", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if trust_proxy:
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                return forwarded_for.split(",", 1)[0].strip()
        return request.client.host if request.client else None

    def _identifier_for_scope(self, scope: dict, headers: Headers) -> Optional[str]:
        """Return the client identifier for ASGI-scope middleware validation."""
        trust_proxy = os.environ.get("TRUST_PROXY_HEADERS", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if trust_proxy:
            forwarded_for = headers.get("x-forwarded-for")
            if forwarded_for:
                return forwarded_for.split(",", 1)[0].strip()
        client = scope.get("client")
        if client:
            return client[0]
        return None

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

    async def _read_body(self, receive) -> bytes:
        chunks: list[bytes] = []
        more_body = True
        while more_body:
            message = await receive()
            if message["type"] != "http.request":
                continue
            chunks.append(message.get("body", b""))
            more_body = bool(message.get("more_body", False))
        return b"".join(chunks)

    def _replay_body(self, body: bytes):
        sent = False

        async def receive():
            nonlocal sent
            if sent:
                return {"type": "http.request", "body": b"", "more_body": False}
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        return receive

    def _extract_text_fields_from_scope(
        self,
        scope: dict,
        headers: Headers,
        body: bytes,
    ) -> list[tuple[str, str]]:
        fields: list[tuple[str, str]] = []
        query_string = scope.get("query_string", b"")
        for key, value in parse_qsl(query_string.decode("latin-1"), keep_blank_values=False):
            if isinstance(value, str) and len(value) >= self.TEXT_VALUE_MIN_LEN:
                fields.append((key, value))

        content_type = headers.get("content-type", "")
        if "application/json" in content_type and body:
            try:
                json_body = json.loads(body.decode("utf-8"))
            except Exception:
                json_body = None
            fields.extend(self._extract_json_text_fields(json_body))
        return fields

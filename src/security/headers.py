"""Security headers middleware for all responses.

Headers added:
- Content-Security-Policy
- Strict-Transport-Security (HSTS)
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Referrer-Policy: strict-origin-when-cross-origin
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self' http://localhost:8000; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)

DEFAULT_HSTS = "max-age=31536000; includeSubDomains; preload"

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "X-Permitted-Cross-Domain-Policies": "none",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all HTTP responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = SECURITY_HEADERS["X-Content-Type-Options"]
        response.headers["X-Frame-Options"] = SECURITY_HEADERS["X-Frame-Options"]
        response.headers["X-XSS-Protection"] = SECURITY_HEADERS["X-XSS-Protection"]
        response.headers["X-Permitted-Cross-Domain-Policies"] = SECURITY_HEADERS["X-Permitted-Cross-Domain-Policies"]
        response.headers["Cross-Origin-Opener-Policy"] = SECURITY_HEADERS["Cross-Origin-Opener-Policy"]
        response.headers["Cross-Origin-Resource-Policy"] = SECURITY_HEADERS["Cross-Origin-Resource-Policy"]
        response.headers["Cross-Origin-Embedder-Policy"] = SECURITY_HEADERS["Cross-Origin-Embedder-Policy"]

        csp = DEFAULT_CSP
        if request.url.scheme == "https":
            csp = csp.replace("http://localhost:8000", "https://localhost:8000")
        response.headers["Content-Security-Policy"] = csp

        response.headers["Strict-Transport-Security"] = DEFAULT_HSTS

        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response


def add_security_headers(response: Response) -> None:
    """Add security headers to a response object."""
    response.headers["X-Content-Type-Options"] = SECURITY_HEADERS["X-Content-Type-Options"]
    response.headers["X-Frame-Options"] = SECURITY_HEADERS["X-Frame-Options"]
    response.headers["Strict-Transport-Security"] = DEFAULT_HSTS
    response.headers["Content-Security-Policy"] = DEFAULT_CSP
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"


def get_security_headers_dict() -> dict[str, str]:
    """Get all security headers as a dictionary."""
    return {
        "X-Content-Type-Options": SECURITY_HEADERS["X-Content-Type-Options"],
        "X-Frame-Options": SECURITY_HEADERS["X-Frame-Options"],
        "Strict-Transport-Security": DEFAULT_HSTS,
        "Content-Security-Policy": DEFAULT_CSP,
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
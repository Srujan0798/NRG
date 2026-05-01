"""Authentication, SSO, session, refresh, and logout routes."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from starlette.responses import Response

from src.api.deps import brute_force_protection
from src.api.logging_config import get_logger
from src.auth.jwt_handler import AuthError, JWTHandler
from src.auth.middleware import get_current_user
from src.security.rate_limiter import check_tier_rate_limit
from src.services.consent import get_consent_service

router = APIRouter(tags=["auth"])

ACCESS_COOKIE_NAME = "nrg_access_token"
REFRESH_COOKIE_NAME = "nrg_refresh_token"

_jwt_handler: JWTHandler | None = None
logger = get_logger(__name__)


class SSOCallbackRequest(BaseModel):
    code: str
    state: str


class SSOAuthorizationResponse(BaseModel):
    redirect_url: str
    state: str
    provider: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


def configure_auth_router(*, jwt_handler: JWTHandler, route_logger: Any | None = None) -> None:
    """Bind auth routes to the app-level JWT handler used by middleware."""
    global _jwt_handler, logger
    _jwt_handler = jwt_handler
    if route_logger is not None:
        logger = route_logger


def _get_jwt_handler() -> JWTHandler:
    if _jwt_handler is None:
        raise RuntimeError("Auth router is not configured with a JWT handler")
    return _jwt_handler


def _cookie_secure() -> bool:
    return os.getenv("NRG_COOKIE_SECURE", "0").lower() in {"1", "true", "yes"}


def _set_auth_cookies(response: Response, tokens: dict[str, Any]) -> None:
    jwt_handler = _get_jwt_handler()
    cookie_options = {
        "httponly": True,
        "secure": _cookie_secure(),
        "samesite": "lax",
        "path": "/",
    }
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        tokens["access_token"],
        max_age=int(tokens.get("expires_in", jwt_handler.access_token_ttl_seconds)),
        **cookie_options,
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        tokens["refresh_token"],
        max_age=int(tokens.get("refresh_expires_in", jwt_handler.refresh_token_ttl_seconds)),
        **cookie_options,
    )


def _clear_auth_cookies(response: Response) -> None:
    for name in (ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME):
        response.delete_cookie(
            name,
            path="/",
            secure=_cookie_secure(),
            samesite="lax",
            httponly=True,
        )


def _auth_response_payload(user: dict[str, Any], tokens: dict[str, Any], rate_limit: dict[str, Any]) -> dict[str, Any]:
    return {
        **tokens,
        "persona": user["role"],
        "tier": user["tier"],
        "user_id": user["user_id"],
        "user": {
            "id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "tier": user["tier"],
            "researcher_id": user.get("researcher_id"),
        },
        "rate_limit": rate_limit,
    }


@router.post("/auth/login")
@router.post("/login")
async def login(request: LoginRequest, response: Response, raw_request: Request = None):
    """Authenticate a user and return access/refresh tokens."""
    jwt_handler = _get_jwt_handler()
    client_ip = raw_request.client.host if raw_request and raw_request.client else None

    is_locked, lockout_msg = brute_force_protection.check_login_failure(request.username)
    if is_locked:
        logger.warning("Login blocked - account locked", user=request.username, ip=client_ip)
        raise HTTPException(status_code=429, detail=lockout_msg, headers={"Retry-After": "900"})

    try:
        user = jwt_handler.authenticate_user(request.username, request.password)
        brute_force_protection.record_success(request.username)
    except AuthError as exc:
        brute_force_protection.record_failure(request.username)
        remaining = brute_force_protection._failure_count.get(request.username.lower(), 0)
        logger.warning("Login failed", user=request.username, ip=client_ip, attempts=remaining)
        if remaining >= 3:
            try:
                from src.audit import AuditEvent, get_audit_log

                get_audit_log().append(AuditEvent(
                    event_type="brute_force_attempt",
                    user_id=request.username,
                    result={"ip": client_ip, "attempts": remaining},
                ))
            except Exception:
                pass
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    tokens = await asyncio.to_thread(jwt_handler.issue_token_pair, user)

    consent_service = get_consent_service()
    has_research_consent = await asyncio.to_thread(
        consent_service.has_consent,
        user["user_id"],
        "research_access",
    )
    if not has_research_consent:
        await asyncio.to_thread(
            consent_service.grant_consent,
            user["user_id"],
            "research_access",
        )

    tier = user.get("tier", 1)
    allowed, remaining, reset_time, rate_headers = check_tier_rate_limit(
        user["user_id"], tier, client_ip
    )

    _set_auth_cookies(response, tokens)
    return _auth_response_payload(
        user,
        tokens,
        {
            "limit": int(rate_headers.get("X-RateLimit-Limit", 100)),
            "remaining": remaining,
            "reset": reset_time,
        },
    )


@router.get("/auth/sso/login", response_model=SSOAuthorizationResponse, tags=["auth"])
async def sso_login():
    """Initiate SSO login and return the institutional IdP redirect URL."""
    from src.auth.sso_handler import get_sso_handler, is_sso_enabled

    if not is_sso_enabled():
        raise HTTPException(status_code=501, detail="SSO is not configured")

    handler = get_sso_handler()
    redirect_url, state = handler.initiate_login()
    return SSOAuthorizationResponse(
        redirect_url=redirect_url,
        state=state,
        provider="oidc",
    )


@router.post("/auth/sso/callback", tags=["auth"])
async def sso_callback(request: SSOCallbackRequest):
    """Handle SSO IdP callback and issue JWTs on success."""
    from src.auth.sso_handler import get_sso_handler, is_sso_enabled

    if not is_sso_enabled():
        raise HTTPException(status_code=501, detail="SSO is not configured")

    handler = get_sso_handler()
    try:
        tokens = handler.handle_callback(
            code=request.code,
            state=request.state,
            expected_state=request.state,
        )
        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "sso_authenticated": True,
        }
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/auth/sso/status", tags=["auth"])
async def sso_status():
    """Return SSO configuration status."""
    from src.auth.sso_handler import is_sso_enabled

    return {
        "sso_enabled": is_sso_enabled(),
        "provider": os.getenv("SSO_PROVIDER_TYPE", "").lower() or None,
        "authorization_url": os.getenv("SSO_AUTHORIZATION_URL", "") or None,
    }


@router.get("/auth/session")
async def auth_session(request: Request):
    claims: dict = getattr(request.state, "auth_claims", None) or {}
    if not claims:
        return {
            "authenticated": False,
            "user": None,
        }
    return {
        "authenticated": True,
        "user": {
            "id": claims.get("sub"),
            "username": claims.get("username"),
            "role": claims.get("role"),
            "tier": claims.get("tier"),
            "researcher_id": claims.get("researcher_id"),
        },
        "persona": claims.get("persona", claims.get("role")),
        "tier": claims.get("tier"),
        "user_id": claims.get("sub"),
    }


@router.post("/auth/refresh")
@router.post("/refresh")
async def refresh_tokens(request: RefreshRequest, response: Response, raw_request: Request = None):
    jwt_handler = _get_jwt_handler()
    try:
        refresh_token = request.refresh_token or (
            raw_request.cookies.get(REFRESH_COOKIE_NAME) if raw_request else None
        )
        access_token = request.access_token or (
            raw_request.cookies.get(ACCESS_COOKIE_NAME) if raw_request else None
        )
        if not refresh_token:
            raise AuthError("Missing refresh token")
        result = jwt_handler.refresh_access_token(refresh_token, access_token)
        _set_auth_cookies(response, result)

        try:
            from src.security.token_rotation import get_rotation_logs

            logs = get_rotation_logs()
            if logs:
                logger.info(
                    "Token refreshed successfully: last_rotation=%s",
                    logs[-1].get("timestamp", "unknown"),
                )
        except Exception:
            pass

        return result
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/logout")
@router.post("/auth/logout")
async def logout(
    request: LogoutRequest,
    response: Response,
    raw_request: Request,
    claims: dict = Depends(get_current_user),
):
    jwt_handler = _get_jwt_handler()
    authorization = raw_request.headers.get("Authorization")
    access_cookie = raw_request.cookies.get(ACCESS_COOKIE_NAME)
    refresh_cookie = raw_request.cookies.get(REFRESH_COOKIE_NAME)

    try:
        if authorization and authorization.startswith("Bearer "):
            jwt_handler.revoke_token(authorization.replace("Bearer ", "", 1))
        elif access_cookie:
            jwt_handler.revoke_token(access_cookie)
        if request.refresh_token:
            jwt_handler.revoke_token(request.refresh_token)
        elif refresh_cookie:
            jwt_handler.revoke_token(refresh_cookie)
    except AuthError:
        pass

    _clear_auth_cookies(response)
    return {"status": "revoked"}

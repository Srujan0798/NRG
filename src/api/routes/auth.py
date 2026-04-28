"""Auth routes: /auth/*, /login, /logout, /refresh, /me/*, /consent/*, /dpdp/*."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.api.deps import (
    LoginRequest, RefreshRequest, LogoutRequest, EraseRequest,
    get_current_user, jwt_handler, brute_force_protection,
)
from src.auth.jwt_handler import AuthError
from src.services.consent import get_consent_service
from src.audit import AuditEvent, get_audit_log
from src.security.rate_limiter import check_tier_rate_limit


router = APIRouter(tags=["auth"])


@router.post("/auth/login", status_code=status.HTTP_200_OK)
@router.post("/login", status_code=status.HTTP_200_OK)
async def login(request: LoginRequest, raw_request: Request = None):
    client_ip = raw_request.client.host if raw_request and raw_request.client else None

    is_locked, lockout_msg = brute_force_protection.check_login_failure(request.username)
    if is_locked:
        raise HTTPException(status_code=429, detail=lockout_msg, headers={"Retry-After": "900"})

    try:
        user = jwt_handler.authenticate_user(request.username, request.password)
        brute_force_protection.record_success(request.username)
    except AuthError as exc:
        brute_force_protection.record_failure(request.username)
        remaining = brute_force_protection._failure_count.get(request.username.lower(), 0)
        if remaining >= 3:
            try:
                get_audit_log().append(AuditEvent(
                    event_type="brute_force_attempt",
                    user_id=request.username,
                    result={"ip": client_ip, "attempts": remaining},
                ))
            except Exception:
                pass
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    tokens = jwt_handler.issue_token_pair(user)
    consent_service = get_consent_service()
    if not consent_service.has_consent(user["user_id"], "research_access"):
        consent_service.grant_consent(user["user_id"], "research_access")

    tier = user.get("tier", 1)
    allowed, remaining, reset_time, rate_headers = check_tier_rate_limit(user["user_id"], tier, client_ip)

    return {
        **tokens,
        "user": {
            "id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "tier": user["tier"],
            "researcher_id": user.get("researcher_id"),
        },
        "rate_limit": {
            "limit": int(rate_headers.get("X-RateLimit-Limit", 100)),
            "remaining": remaining,
            "reset": reset_time,
        },
    }


@router.get("/auth/sso/login")
async def sso_login():
    from src.auth.sso_handler import get_sso_handler, is_sso_enabled
    if not is_sso_enabled():
        raise HTTPException(status_code=501, detail="SSO is not configured")
    handler = get_sso_handler()
    redirect_url, state = handler.initiate_login()
    return {"redirect_url": redirect_url, "state": state, "provider": "oidc"}


@router.post("/auth/sso/callback")
async def sso_callback(code: str, state: str):
    from src.auth.sso_handler import get_sso_handler, is_sso_enabled
    if not is_sso_enabled():
        raise HTTPException(status_code=501, detail="SSO is not configured")
    handler = get_sso_handler()
    try:
        tokens = handler.handle_callback(code=code, state=state, expected_state=state)
        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "sso_authenticated": True,
        }
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/auth/sso/status")
async def sso_status():
    from src.auth.sso_handler import is_sso_enabled
    return {
        "sso_enabled": is_sso_enabled(),
        "provider": os.getenv("SSO_PROVIDER_TYPE", "").lower() or None,
        "authorization_url": os.getenv("SSO_AUTHORIZATION_URL", "") or None,
    }


@router.post("/refresh")
async def refresh_tokens(request: RefreshRequest):
    try:
        return jwt_handler.refresh_access_token(request.refresh_token, request.access_token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/logout")
async def logout(request: LogoutRequest, raw_request: Request, claims: dict = Depends(get_current_user)):
    authorization = raw_request.headers.get("Authorization")
    try:
        if authorization and authorization.startswith("Bearer "):
            jwt_handler.revoke_token(authorization.replace("Bearer ", "", 1))
        if request.refresh_token:
            jwt_handler.revoke_token(request.refresh_token)
    except AuthError:
        pass
    return {"status": "revoked"}


# Consent
@router.post("/consent")
async def grant_consent(scope: str, retention_days: int = 365, token_payload: dict = Depends(get_current_user)):
    service = get_consent_service()
    user_id = token_payload.get("sub", "anonymous")
    result = service.grant_consent(user_id, scope, retention_days)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@router.delete("/consent/{scope}")
async def revoke_consent(scope: str, token_payload: dict = Depends(get_current_user)):
    service = get_consent_service()
    user_id = token_payload.get("sub", "anonymous")
    result = service.revoke_consent(user_id, scope)
    if result["success"]:
        return result
    raise HTTPException(status_code=404, detail=result["error"])


# DPDP
@router.post("/dpdp/erase")
async def dpdp_erase(body: EraseRequest, token_payload: dict = Depends(get_current_user)):
    if not body.confirm:
        raise HTTPException(status_code=400, detail="Erasure requires confirm=true")
    service = get_consent_service()
    return service.erase_user_data(token_payload.get("sub", "anonymous"))


@router.get("/dpdp/consents")
async def dpdp_consents(token_payload: dict = Depends(get_current_user)):
    service = get_consent_service()
    return {"consents": service.list_consents(token_payload.get("sub", "anonymous"))}


@router.get("/dpdp/export")
async def dpdp_export(token_payload: dict = Depends(get_current_user)):
    service = get_consent_service()
    return service.export_user_data(token_payload.get("sub", "anonymous"))


# Me
@router.get("/me/consents")
async def list_consents(token_payload: dict = Depends(get_current_user)):
    service = get_consent_service()
    return {"consents": service.list_consents(token_payload.get("sub", "anonymous"))}


@router.get("/me/data")
async def export_user_data(token_payload: dict = Depends(get_current_user)):
    service = get_consent_service()
    return service.export_user_data(token_payload.get("sub", "anonymous"))


@router.delete("/me/data")
async def erase_user_data(token_payload: dict = Depends(get_current_user)):
    service = get_consent_service()
    return service.erase_user_data(token_payload.get("sub", "anonymous"))


@router.get("/admin/dpdp/stats")
async def get_dpdp_admin_stats(token_payload: dict = Depends(get_current_user)):
    role = token_payload.get("role", "")
    if role not in ("admin", "government"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return get_consent_service().get_admin_stats()

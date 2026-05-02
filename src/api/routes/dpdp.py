"""DPDP consent and data-rights endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import EraseRequest
from src.auth.middleware import TokenClaims, get_current_user
from src.services.consent import ConsentService, get_consent_service

router = APIRouter(prefix="", tags=["dpdp"])
JSONDict = dict[str, Any]
JSONRows = list[JSONDict]


def _user_id_from_token(token_payload: TokenClaims) -> str:
    return str(token_payload.get("sub", "anonymous"))


def _export_service_for_token(token_payload: TokenClaims) -> ConsentService:
    service = get_consent_service()
    user_id = _user_id_from_token(token_payload)
    if not service.has_consent(user_id, "research_access"):
        raise HTTPException(status_code=403, detail="Consent required for research_access")
    return service


@router.get("/dpdp/export")
async def dpdp_export(token_payload: TokenClaims = Depends(get_current_user)) -> JSONDict:
    """DPDP-2023 Article 13: right to access."""
    service = _export_service_for_token(token_payload)
    return service.export_user_data(_user_id_from_token(token_payload))


@router.post("/dpdp/erase")
async def dpdp_erase(
    body: EraseRequest,
    token_payload: TokenClaims = Depends(get_current_user),
) -> JSONDict:
    """DPDP-2023 Article 17: right to erasure."""
    if not body.confirm:
        raise HTTPException(status_code=400, detail="Erasure requires confirm=true")
    return await erase_user_data(token_payload)


@router.get("/dpdp/consents")
async def dpdp_consents(token_payload: TokenClaims = Depends(get_current_user)) -> JSONDict:
    """DPDP-2023 Article 6: consent visibility."""
    return await list_consents(token_payload)


@router.post("/consent")
async def grant_consent(
    scope: str,
    retention_days: int = 365,
    token_payload: TokenClaims = Depends(get_current_user),
) -> JSONDict:
    """Grant consent for data processing."""
    service = get_consent_service()
    result = service.grant_consent(_user_id_from_token(token_payload), scope, retention_days)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@router.delete("/consent/{scope}")
async def revoke_consent(
    scope: str,
    token_payload: TokenClaims = Depends(get_current_user),
) -> JSONDict:
    """Revoke consent for data processing."""
    service = get_consent_service()
    result = service.revoke_consent(_user_id_from_token(token_payload), scope)
    if result["success"]:
        return result
    raise HTTPException(status_code=404, detail=result["error"])


@router.get("/me/consents")
async def list_consents(token_payload: TokenClaims = Depends(get_current_user)) -> JSONDict:
    """List all consents for the current user."""
    service = get_consent_service()
    return {"consents": service.list_consents(_user_id_from_token(token_payload))}


@router.get("/me/data")
async def export_user_data(token_payload: TokenClaims = Depends(get_current_user)) -> JSONDict:
    """Export all current-user data."""
    service = _export_service_for_token(token_payload)
    return service.export_user_data(_user_id_from_token(token_payload))


@router.delete("/me/data")
async def erase_user_data(token_payload: TokenClaims = Depends(get_current_user)) -> JSONDict:
    """Erase all current-user data."""
    service = get_consent_service()
    return service.erase_user_data(_user_id_from_token(token_payload))


@router.get("/admin/dpdp/stats")
async def get_dpdp_admin_stats(token_payload: TokenClaims = Depends(get_current_user)) -> JSONDict:
    """DPDP compliance dashboard stats."""
    role = token_payload.get("role", "")
    if role not in ("admin", "government"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return get_consent_service().get_admin_stats()

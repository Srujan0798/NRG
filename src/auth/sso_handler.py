"""
SSO authentication via OIDC/SAML 2.0.

Supports institutional SSO providers (IIT Gandhinagar, government IdPs).
On successful SSO callback, issues a JWT for the authenticated user.

Environment variables:
    SSO_PROVIDER_TYPE=oidc|saml|None  (default: None = local password auth)
    SSO_CLIENT_ID=<oauth2 client id>
    SSO_CLIENT_SECRET=<oauth2 client secret>
    SSO_AUTHORIZATION_URL=<provider authorization endpoint>
    SSO_TOKEN_URL=<provider token endpoint>
    SSO_USERINFO_URL=<provider userinfo endpoint>
    SSO_CALLBACK_URL=<your callback URL>  (default: /auth/sso/callback)
    SSO_JWKS_URL=<provider JWKS endpoint for OIDC token verification>
    SSO_SAML_METADATA_URL=<SAML IdP metadata URL>
    SSO_SAML_SP_ENTITY_ID=<Service Provider entity ID>
    SSO_DEFAULT_ROLE=<role to assign SSO users: researcher|government|industry>
    SSO_ENABLED=<true|false>  (global SSO enable/disable)
    SSO_ALLOWED_DOMAINS=<comma-separated email domains>  (empty = all allowed)
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

import jwt

from src.auth.refresh_store import RefreshStore
from src.auth.jwt_handler import AuthError


@dataclass
class SSOTokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class SSOConfig:
    """SSO configuration from environment."""

    TYPE_OIDC = "oidc"
    TYPE_SAML = "saml"
    TYPE_NONE = None

    def __init__(self):
        self.enabled = os.getenv("SSO_ENABLED", "false").lower() == "true"
        self.provider_type = os.getenv("SSO_PROVIDER_TYPE", "").lower() or None
        self.client_id = os.getenv("SSO_CLIENT_ID", "")
        self.client_secret = os.getenv("SSO_CLIENT_SECRET", "")
        self.authorization_url = os.getenv("SSO_AUTHORIZATION_URL", "")
        self.token_url = os.getenv("SSO_TOKEN_URL", "")
        self.userinfo_url = os.getenv("SSO_USERINFO_URL", "")
        self.callback_url = os.getenv("SSO_CALLBACK_URL", "/auth/sso/callback")
        self.jwks_url = os.getenv("SSO_JWKS_URL", "")
        self.saml_metadata_url = os.getenv("SSO_SAML_METADATA_URL", "")
        self.sp_entity_id = os.getenv("SSO_SAML_SP_ENTITY_ID", "nrg-api")
        self.default_role = os.getenv("SSO_DEFAULT_ROLE", "researcher")
        self.allowed_domains = [
            d.strip()
            for d in os.getenv("SSO_ALLOWED_DOMAINS", "").split(",")
            if d.strip()
        ]

    @property
    def is_configured(self) -> bool:
        return (
            self.enabled
            and self.provider_type in (self.TYPE_OIDC, self.TYPE_SAML)
            and bool(self.client_id)
            and bool(self.client_secret)
            and bool(self.authorization_url)
            and bool(self.token_url)
        )

    def domain_allowed(self, email: str) -> bool:
        if not self.allowed_domains:
            return True
        return any(email.endswith(f"@{d}") for d in self.allowed_domains)


class OIDCTokenVerifier:
    """Verify OIDC ID tokens against JWKS."""

    def __init__(self, jwks_url: str):
        self._jwks_url = jwks_url
        self._jwks_cache: dict | None = None
        self._jwks_cache_time: float = 0
        self._jwks_ttl: float = 3600

    def _fetch_jwks(self) -> dict:
        now = time.time()
        if self._jwks_cache is not None and (now - self._jwks_cache_time) < self._jwks_ttl:
            return self._jwks_cache
        import requests
        resp = requests.get(self._jwks_url, timeout=10)
        resp.raise_for_status()
        self._jwks_cache = resp.json()
        self._jwks_cache_time = now
        return self._jwks_cache

    def _get_signing_key(self, kid: str) -> dict | None:
        jwks = self._fetch_jwks()
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        return None

    def verify(self, token: str) -> dict[str, Any]:
        import requests

        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid", "")

        signing_key = self._get_signing_key(kid)
        if signing_key is None:
            raise AuthError(f"OIDC: no signing key found for kid={kid}")

        from cryptography.hazmat.primitives.asymmetric.rsa import RSAFromJavaWebToken
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend

            if signing_key.get("kty") == "RSA":
                n = int.from_bytes(
                    bytes.fromhex(signing_key["n"].lstrip("0")),
                    byteorder="big",
                )
                e = int.from_bytes(
                    bytes.fromhex(signing_key["e"].lstrip("0")),
                    byteorder="big",
                )
                from cryptography.hazmat.primitives.asymmetric import rsa
                public_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
                pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                public_key_str = pem.decode("utf-8")
            else:
                raise AuthError(f"OIDC: unsupported key type {signing_key.get('kty')}")

            claims = jwt.decode(
                token,
                public_key_str,
                algorithms=["RS256"],
                audience=self._jwks_url.split("/")[2] if "/" in self._jwks_url else None,
            )
            return claims
        except jwt.PyJWTError as exc:
            raise AuthError(f"OIDC token verification failed: {exc}")


def _build_oidc_authorization_url(config: SSOConfig, state: str) -> str:
    import urllib.parse as urlparse

    params = {
        "client_id": config.client_id,
        "response_type": "code",
        "redirect_uri": config.callback_url,
        "scope": "openid email profile",
        "state": state,
    }
    return f"{config.authorization_url}?{urlparse.urlencode(params)}"


def _exchange_code_for_tokens(
    config: SSOConfig, code: str, code_verifier: str | None = None
) -> dict[str, Any]:
    import requests

    data = {
        "grant_type": "authorization_code",
        "client_id": config.client_id,
        "client_secret": config.client_secret,
        "code": code,
        "redirect_uri": config.callback_url,
    }
    if code_verifier:
        data["code_verifier"] = code_verifier

    resp = requests.post(config.token_url, data=data, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _fetch_userinfo(config: SSOConfig, access_token: str) -> dict[str, Any]:
    import requests

    resp = requests.get(
        config.userinfo_url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def _normalize_role(config: SSOConfig, claims: dict[str, Any]) -> str:
    """Derive role from structured claims only. Email keywords are NOT authoritative."""
    role = config.default_role

    role_hints = [
        claims.get("role"),
        claims.get("groups"),
        claims.get("realm_access", {}).get("roles", []),
    ]
    for hint in role_hints:
        if isinstance(hint, list):
            for item in hint:
                if "gov" in str(item).lower() or "admin" in str(item).lower():
                    return "government"
        elif isinstance(hint, str):
            if "gov" in hint.lower() or "admin" in hint.lower():
                return "government"
    structured_role = claims.get("role") or claims.get("groups")
    if structured_role:
        sr = str(structured_role).lower()
        if "researcher" in sr or "faculty" in sr:
            return "researcher"
        if "gov" in sr or "admin" in sr:
            return "government"
        if "industry" in sr:
            return "industry"
    return role


class SSOAuthHandler:
    """Handle SSO OIDC/SAML flow and issue JWTs."""

    STATE_TTL: int = 600

    def __init__(self):
        self.config = SSOConfig()
        self._state_store: dict[str, tuple[str, float]] = {}
        self._pkce_store: dict[str, str] = {}

    @property
    def is_enabled(self) -> bool:
        return self.config.is_configured

    def initiate_login(self) -> tuple[str, str]:
        """Start SSO login. Returns (redirect_url, state)."""
        if not self.is_enabled:
            raise AuthError("SSO is not configured")

        state = str(uuid.uuid4())
        code_verifier = str(uuid.uuid4()) + str(uuid.uuid4())
        code_challenge = hashlib.sha256(code_verifier.encode()).hexdigest()[:64]

        self._state_store[state] = (code_challenge, time.time())
        self._pkce_store[state] = code_verifier

        self._prune_expired_states()

        redirect_url = _build_oidc_authorization_url(self.config, state)
        return redirect_url, state

    def handle_callback(
        self, code: str, state: str, expected_state: str
    ) -> SSOTokenPair:
        """Complete OIDC callback, return token pair."""
        if not self.is_enabled:
            raise AuthError("SSO is not configured")

        if state != expected_state:
            raise AuthError("SSO state mismatch — possible CSRF attack")

        if state not in self._state_store:
            raise AuthError("SSO state expired or invalid")

        code_challenge, stored_time = self._state_store.pop(state)
        code_verifier = self._pkce_store.pop(state, "")

        if time.time() - stored_time > self.STATE_TTL:
            raise AuthError("SSO state expired — please log in again")

        tokens = _exchange_code_for_tokens(
            self.config, code, code_verifier if code_verifier else None
        )

        id_token = tokens.get("id_token") or tokens.get("access_token")
        if self.config.jwks_url:
            verifier = OIDCTokenVerifier(self.config.jwks_url)
            claims = verifier.verify(id_token)
        else:
            if not self.config.authorization_url:
                raise AuthError("SSO not configured: missing authorization_url")
            claims = jwt.decode(
                id_token,
                self.config.client_secret,
                algorithms=["HS256"],
                options={"verify_aud": True, "verify_iss": True, "verify_iat": True},
            )

        if not self.config.domain_allowed(claims.get("email", "")):
            raise AuthError(f"Email domain not allowed: {claims.get('email')}")

        role = _normalize_role(self.config, claims)
        domain = claims.get("email", "").split("@")[-1] if "@" in claims.get("email", "") else ""
        user_info = {
            "user_id": f"sso-{claims.get('sub', claims.get('email', 'unknown'))}",
            "username": claims.get("email", claims.get("preferred_username", "sso_user")),
            "role": role,
            "tier": 1 if role == "researcher" else 2 if role == "government" else 3,
            "email": claims.get("email"),
            "name": claims.get("name", claims.get("given_name", "")),
            "groups": [role],
            "scope": "own_and_public" if role == "researcher" else "aggregated_and_anonymized",
            "sso_issuer": claims.get("iss", ""),
            "sso_subject": claims.get("sub", ""),
        }

        from src.auth.jwt_handler import JWTHandler

        jwt_handler = JWTHandler()
        jwt_tokens = jwt_handler.issue_token_pair(user_info)

        return SSOTokenPair(
            access_token=jwt_tokens["access_token"],
            refresh_token=jwt_tokens["refresh_token"],
            token_type="bearer",
        )

    def _prune_expired_states(self) -> None:
        now = time.time()
        expired = [s for s, (_, t) in self._state_store.items() if now - t > self.STATE_TTL]
        for s in expired:
            self._state_store.pop(s, None)
            self._pkce_store.pop(s, None)


_sso_handler: SSOConfig | None = None


def get_sso_handler() -> SSOConfig:
    global _sso_handler
    if _sso_handler is None:
        _sso_handler = SSOConfig()
    return _sso_handler


def is_sso_enabled() -> bool:
    return get_sso_handler().is_configured
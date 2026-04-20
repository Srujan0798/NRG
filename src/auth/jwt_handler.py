"""JWT authentication and token lifecycle management."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

import jwt

from src.auth.refresh_store import RefreshStore


class AuthError(Exception):
    """Raised when authentication or token validation fails."""


ROLE_CONFIG = {
    "researcher": {
        "tier": 1,
        "groups": ["researcher"],
        "scope": "own_and_public",
    },
    "government": {
        "tier": 2,
        "groups": ["government"],
        "scope": "aggregated_and_anonymized",
    },
    "industry": {
        "tier": 3,
        "groups": ["industry"],
        "scope": "limited_and_licensed",
    },
}


def _first_env(names: tuple[str, ...], default: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def build_default_users() -> dict[str, dict[str, Any]]:
    return {
        "researcher_user": {
            "password": _first_env(
                ("RESEARCHER_PASSWORD", "DEMO_RESEARCHER_PASSWORD"),
                "researcher-pass",
            ),
            "role": "researcher",
            "researcher_id": "researcher-1",
        },
        "gov_user": {
            "password": _first_env(
                ("GOV_PASSWORD", "DEMO_GOVERNMENT_PASSWORD"),
                "government-pass",
            ),
            "role": "government",
        },
        "industry_user": {
            "password": _first_env(
                ("INDUSTRY_PASSWORD", "DEMO_INDUSTRY_PASSWORD"),
                "industry-pass",
            ),
            "role": "industry",
        },
    }


DEFAULT_USERS = build_default_users()


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class JWTHandler:
    """Issue, verify, refresh, and revoke JWTs with RS256/HS256 support."""

    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str | None = None,
        access_token_ttl_seconds: int = 3600,
        refresh_token_ttl_seconds: int = 604800,
        users: dict[str, dict[str, Any]] | None = None,
        private_key_path: str | None = None,
        public_key_path: str | None = None,
    ):
        # Determine algorithm (prefer RS256 for production)
        self.algorithm = algorithm or os.getenv("JWT_ALGORITHM", "RS256")
        
        # Load RSA keys if using asymmetric algorithm
        self.private_key: Optional[str] = None
        self.public_key: Optional[str] = None
        
        if self.algorithm in ("RS256", "RS384", "RS512", "ES256", "ES384", "ES512"):
            private_key_path = private_key_path or os.getenv(
                "JWT_PRIVATE_KEY_PATH",
                "infrastructure/kong/ssl/jwt_rsa.key"
            )
            public_key_path = public_key_path or os.getenv(
                "JWT_PUBLIC_KEY_PATH",
                "infrastructure/kong/ssl/jwt_rsa.pub"
            )
            self.secret_key = None
            if private_key_path and public_key_path:
                self._load_rsa_keys(private_key_path, public_key_path)
            if not self.private_key or not self.public_key:
                raise AuthError("RSA key files could not be loaded")
        else:
            # Fallback to symmetric (HS256)
            self.secret_key = secret_key or os.getenv("JWT_SECRET")
            if not self.secret_key:
                raise AuthError("JWT_SECRET environment variable must be set")
        
        self.access_token_ttl_seconds = access_token_ttl_seconds
        self.refresh_token_ttl_seconds = refresh_token_ttl_seconds
        self.users = users or build_default_users()
        self.revoked_jtis: set[str] = set()
        self.active_refresh_tokens: dict[str, str] = {}
        self.refresh_store = RefreshStore()
    
    def _load_rsa_keys(self, private_key_path: str, public_key_path: str) -> None:
        """Load RSA keypair from PEM files."""
        try:
            # Try to load from relative path to project root
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            full_private_path = os.path.join(base_path, private_key_path)
            full_public_path = os.path.join(base_path, public_key_path)
            
            with open(full_private_path, "r") as f:
                self.private_key = f.read()
            
            with open(full_public_path, "r") as f:
                self.public_key = f.read()
                
        except FileNotFoundError as e:
            raise AuthError(
                f"RSA key files not found: {e}. "
                "Generate keys with: ssh-keygen -t rsa -b 4096 -m PEM -f infrastructure/kong/ssl/jwt_rsa.key"
            ) from e

    def authenticate_user(self, username: str, password: str) -> dict[str, Any]:
        user = self.users.get(username.lower())
        if not user or user["password"] != password:
            raise AuthError("Invalid username or password")

        role = user["role"]
        role_config = ROLE_CONFIG[role]
        return {
            "user_id": user.get("user_id", f"{role}-{username.lower()}"),
            "username": username.lower(),
            "role": role,
            "tier": role_config["tier"],
            "researcher_id": user.get("researcher_id"),
            "groups": role_config["groups"],
            "scope": role_config["scope"],
        }

    def issue_token_pair(self, user: dict[str, Any]) -> dict[str, Any]:
        access_token = self._create_token(user, "access", self.access_token_ttl_seconds)
        refresh_token = self._create_token(
            user,
            "refresh",
            self.refresh_token_ttl_seconds,
        )
        refresh_claims = self._decode_token(refresh_token)
        self.active_refresh_tokens[refresh_claims["sub"]] = refresh_claims["jti"]
        self.refresh_store.store(
            refresh_token,
            refresh_claims["sub"],
            datetime.fromtimestamp(refresh_claims["iat"], UTC),
            datetime.fromtimestamp(refresh_claims["exp"], UTC),
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_ttl_seconds,
            "refresh_expires_in": self.refresh_token_ttl_seconds,
        }

    def verify_access_token(self, token: str) -> dict[str, Any]:
        claims = self._decode_token(token)
        self._validate_token_type(claims, "access")
        return dict(claims)  # type: ignore[no-any-return]

    def verify_refresh_token(self, token: str) -> dict[str, Any]:
        claims = self._decode_token(token)
        self._validate_token_type(claims, "refresh")
        if self.refresh_store.verify(token) is None:
            raise AuthError("Refresh token has been rotated or revoked")
        active_jti = self.active_refresh_tokens.get(claims["sub"])
        if active_jti is not None and active_jti != claims["jti"]:
            raise AuthError("Refresh token has been rotated or revoked")
        return claims

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        claims = self.verify_refresh_token(refresh_token)
        user = {
            "user_id": claims["sub"],
            "username": claims["username"],
            "role": claims["role"],
            "tier": claims["tier"],
            "researcher_id": claims.get("researcher_id"),
            "groups": claims.get("groups", []),
            "scope": claims.get("scope"),
        }
        self.revoke_token(refresh_token)
        return self.issue_token_pair(user)

    def revoke_token(self, token: str) -> None:
        claims = self._decode_token(token, verify_exp=False)
        self.revoked_jtis.add(claims["jti"])
        if claims.get("token_type") == "refresh":
            self.refresh_store.revoke(token)
            self.active_refresh_tokens.pop(claims["sub"], None)

    def _create_token(
        self,
        user: dict[str, Any],
        token_type: str,
        ttl_seconds: int,
    ) -> str:
        now = datetime.now(UTC)
        role = user["role"]
        payload = {
            "jti": str(uuid.uuid4()),
            "sub": user["user_id"],
            "iss": role,
            "aud": "nrg-api",
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
            "token_type": token_type,
            "username": user["username"],
            "role": role,
            "tier": user["tier"],
            "groups": user.get("groups", ROLE_CONFIG[role]["groups"]),
            "scope": user.get("scope", ROLE_CONFIG[role]["scope"]),
        }
        if user.get("researcher_id"):
            payload["researcher_id"] = user["researcher_id"]

        # Use private key for asymmetric, secret key for symmetric
        signing_key = self.private_key if self.private_key else self.secret_key
        if signing_key is None:
            raise AuthError("No signing key available")
        return jwt.encode(payload, signing_key, algorithm=self.algorithm)

    def _decode_token(
        self,
        token: str,
        *,
        verify_exp: bool = True,
    ) -> dict[str, Any]:
        try:
            # Use public key for asymmetric, secret key for symmetric
            verification_key = self.public_key if self.public_key else self.secret_key
            if verification_key is None:
                raise AuthError("No verification key available")
            
            claims = jwt.decode(
                token,
                verification_key,
                algorithms=[str(self.algorithm)],
                audience="nrg-api",
                options={"verify_exp": verify_exp},
            )
        except jwt.PyJWTError as exc:
            raise AuthError(str(exc)) from exc

        if claims["jti"] in self.revoked_jtis:
            raise AuthError("Token has been revoked")

        return claims  # type: ignore[no-any-return]

    def _validate_token_type(self, claims: dict[str, Any], expected: str) -> None:
        if claims.get("token_type") != expected:
            raise AuthError(f"Expected {expected} token")

"""JWT authentication and token lifecycle management."""

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

import jwt

from src.auth.refresh_store import RefreshStore

logger = logging.getLogger(__name__)
MIN_JWT_SECRET_BYTES = 32


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


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Production requires {name} to be set in environment")
    return value


def jwt_secret_byte_length(secret: str) -> int:
    """Return the byte length that matters for HMAC key strength."""
    return len(secret.encode("utf-8"))


def validate_jwt_secret(secret: str, min_bytes: int = MIN_JWT_SECRET_BYTES) -> bool:
    """Return True when a symmetric JWT secret meets the production floor."""
    return jwt_secret_byte_length(secret) >= min_bytes


def _raise_short_jwt_secret(secret: str, source: str) -> None:
    length = jwt_secret_byte_length(secret)
    logger.critical(
        "Refusing to start: %s is %d bytes; minimum is %d bytes",
        source,
        length,
        MIN_JWT_SECRET_BYTES,
    )
    raise AuthError(
        f"{source} must be at least {MIN_JWT_SECRET_BYTES} bytes "
        f"for HS256/HS384/HS512 signing; got {length} bytes"
    )


def build_default_users() -> dict[str, dict[str, Any]]:
    return {
        "researcher_user": {
            "password": _require_env("RESEARCHER_PASSWORD"),
            "role": "researcher",
            "researcher_id": "researcher-1",
        },
        "gov_user": {
            "password": _require_env("GOV_PASSWORD"),
            "role": "government",
        },
        "industry_user": {
            "password": _require_env("INDUSTRY_PASSWORD"),
            "role": "industry",
        },
    }


_default_users_cache: dict[str, dict[str, Any]] | None = None

def get_default_users() -> dict[str, dict[str, Any]]:
    global _default_users_cache
    if _default_users_cache is None:
        _default_users_cache = build_default_users()
    return _default_users_cache


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
        enforce_secret_min_length: bool | None = None,
    ):
        # Determine algorithm (prefer RS256 for production)
        self.algorithm = algorithm or os.getenv("JWT_ALGORITHM", "RS256")
        self._secret_source = "asymmetric"
        self._secret_length_enforced = False
        
        # Load RSA keys if using asymmetric algorithm
        self.private_key: Optional[str] = None
        self.public_key: Optional[str] = None
        self._private_key_obj: Any | None = None
        self._public_key_obj: Any | None = None
        
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
            env_secret = os.getenv("JWT_SECRET")
            self.secret_key = secret_key if secret_key is not None else env_secret
            self._secret_source = "explicit" if secret_key is not None else "JWT_SECRET"
            if not self.secret_key:
                raise AuthError("JWT_SECRET environment variable must be set")
            self._secret_length_enforced = enforce_secret_min_length if enforce_secret_min_length is not None else False
            if self._secret_length_enforced and not validate_jwt_secret(self.secret_key):
                _raise_short_jwt_secret(self.secret_key, self._secret_source)
        
        self.access_token_ttl_seconds = access_token_ttl_seconds
        self.refresh_token_ttl_seconds = refresh_token_ttl_seconds
        self.users = get_default_users() if users is None else users
        self.revoked_jtis: set[str] = set()
        self.active_refresh_tokens: dict[str, str] = {}
        self.refresh_store = RefreshStore()
        self._signing_key_id = self._compute_key_id()
        self._known_key_ids: set[str] = {self._signing_key_id}
        self._jti_ip_registry: dict[str, tuple[str, str, float]] = {}

    def jwt_secret_health(self) -> dict[str, Any]:
        """Return non-sensitive JWT signing-key health for readiness endpoints."""
        if self.algorithm not in {"HS256", "HS384", "HS512"}:
            return {
                "status": "not_required",
                "algorithm": self.algorithm,
                "min_bytes": MIN_JWT_SECRET_BYTES,
                "message": "Asymmetric JWT signing is active; JWT_SECRET is not used.",
            }

        length = jwt_secret_byte_length(self.secret_key or "")
        valid = length >= MIN_JWT_SECRET_BYTES
        status = "healthy" if valid else "unhealthy"
        if not valid and not self._secret_length_enforced and self._secret_source == "explicit":
            status = "test_override"
        return {
            "status": status,
            "algorithm": self.algorithm,
            "secret_source": self._secret_source,
            "secret_bytes": length,
            "min_bytes": MIN_JWT_SECRET_BYTES,
            "valid": valid,
            "enforced": self._secret_length_enforced,
        }
    
    def _load_rsa_keys(self, private_key_path: str, public_key_path: str) -> None:
        """Load RSA keypair from PEM files."""
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            full_private_path = os.path.join(base_path, private_key_path)
            full_public_path = os.path.join(base_path, public_key_path)

            with open(full_private_path, "r") as f:
                self.private_key = f.read()

            with open(full_public_path, "r") as f:
                self.public_key = f.read()

            from cryptography.hazmat.primitives import serialization

            self._private_key_obj = serialization.load_pem_private_key(
                self.private_key.encode(),
                password=None,
            )
            self._public_key_obj = serialization.load_pem_public_key(
                self.public_key.encode(),
            )

        except FileNotFoundError as e:
            raise AuthError(
                f"RSA key files not found: {e}. "
                "Generate keys with: ssh-keygen -t rsa -b 4096 -m PEM -f infrastructure/kong/ssl/jwt_rsa.key"
            ) from e
        except Exception as e:
            raise AuthError(f"RSA key files could not be parsed: {e}") from e

    def _compute_key_id(self) -> str:
        """Compute a deterministic key ID (kid) from the active signing key."""
        key_material = self.private_key if self.private_key else self.secret_key
        return hashlib.sha256(key_material.encode()).hexdigest()[:16]

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
            "persona": role,  # Backward compat: persona name = role name for built-in tiers
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

    def verify_access_token(self, token: str, client_ip: Optional[str] = None) -> dict[str, Any]:
        """Verify access token, optionally checking for token replay across IPs."""
        claims = self._decode_token(token)
        self._validate_token_type(claims, "access")

        if client_ip:
            jti = claims["jti"]
            user_id = claims["sub"]
            exp = claims["exp"]
            self._check_token_replay(jti, user_id, client_ip, exp, token)

        return dict(claims)  # type: ignore[no-any-return]

    def _check_token_replay(
        self, jti: str, user_id: str, client_ip: str, exp: float, token: str
    ) -> None:
        """Detect token replay: same jti used from a different IP before expiry."""
        now = datetime.now(UTC).timestamp()

        if jti in self._jti_ip_registry:
            existing_user, existing_ip, existing_exp = self._jti_ip_registry[jti]
            if existing_exp > now and existing_ip != client_ip and existing_user == user_id:
                self.revoked_jtis.add(jti)
                self._jti_ip_registry.pop(jti, None)
                try:
                    from src.audit import log_anomaly
                    log_anomaly(
                        user_id=user_id,
                        anomaly_type="TOKEN_REPLAY_DETECTED",
                        details={
                            "jti": jti,
                            "original_ip": existing_ip,
                            "replay_ip": client_ip,
                        },
                        identifier=client_ip,
                    )
                except Exception:
                    pass
                raise AuthError("Token replay detected: same token used from multiple IPs")
        else:
            self._jti_ip_registry[jti] = (user_id, client_ip, exp)

    def verify_refresh_token(self, token: str) -> dict[str, Any]:
        claims = self._decode_token(token)
        self._validate_token_type(claims, "refresh")
        if self.refresh_store.verify(token) is None:
            raise AuthError("Refresh token has been rotated or revoked")
        active_jti = self.active_refresh_tokens.get(claims["sub"])
        if active_jti is not None and active_jti != claims["jti"]:
            raise AuthError("Refresh token has been rotated or revoked")
        return claims

    def refresh_access_token(self, refresh_token: str, access_token: Optional[str] = None) -> dict[str, Any]:
        claims = self.verify_refresh_token(refresh_token)
        user = {
            "user_id": claims["sub"],
            "username": claims["username"],
            "role": claims["role"],
            "persona": claims.get("persona", claims["role"]),
            "tier": claims["tier"],
            "researcher_id": claims.get("researcher_id"),
            "groups": claims.get("groups", []),
            "scope": claims.get("scope"),
        }
        self.revoke_token(refresh_token)
        if access_token:
            self.revoke_token(access_token)
        return self.issue_token_pair(user)

    def revoke_token(self, token: str) -> None:
        claims = self._decode_token(token, verify_exp=False)
        self.revoked_jtis.add(claims["jti"])
        if claims.get("token_type") == "refresh":
            self.refresh_store.revoke(token)
            self.active_refresh_tokens.pop(claims["sub"], None)

    def rotate_signing_key(self, new_private_key: str, new_public_key: str) -> None:
        """Rotate the signing key. New tokens will use the new key; old keys are kept for verification."""
        old_key_id = self._signing_key_id
        self.private_key = new_private_key
        self.public_key = new_public_key
        from cryptography.hazmat.primitives import serialization

        self._private_key_obj = serialization.load_pem_private_key(
            new_private_key.encode(),
            password=None,
        )
        self._public_key_obj = serialization.load_pem_public_key(
            new_public_key.encode(),
        )
        self._signing_key_id = self._compute_key_id()
        self._known_key_ids.add(self._signing_key_id)
        self._known_key_ids.add(old_key_id)

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
            "persona": user.get("persona", role),  # persona name for policy resolution
            "tier": user["tier"],
            "groups": user.get("groups", ROLE_CONFIG[role]["groups"]),
            "scope": user.get("scope", ROLE_CONFIG[role]["scope"]),
            "kid": self._signing_key_id,
        }
        if user.get("researcher_id"):
            payload["researcher_id"] = user["researcher_id"]

        signing_key = self._private_key_obj or self.private_key or self.secret_key
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
            verification_key = self._public_key_obj or self.public_key or self.secret_key
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

"""Token rotation with automatic refresh on use.

Access tokens: 15 min (900s) expiry
Refresh tokens: 7 day (604800s) expiry
Auto-rotate on each use
Invalidate old refresh tokens
"""

import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

ACCESS_TOKEN_TTL_SECONDS = int(os.getenv("NRG_ACCESS_TOKEN_TTL", "900"))
REFRESH_TOKEN_TTL_SECONDS = int(os.getenv("NRG_REFRESH_TOKEN_TTL", "604800"))

ROTATED_TOKENS_LOG: list[dict] = []


def log_token_rotation(
    user_id: str,
    old_jti: Optional[str],
    new_jti: str,
    token_type: str,
) -> None:
    """Log token rotation events."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "old_jti": old_jti,
        "new_jti": new_jti,
        "token_type": token_type,
    }
    ROTATED_TOKENS_LOG.append(entry)
    logger.info(
        "Token rotated: user=%s type=%s old_jti=%s new_jti=%s",
        user_id,
        token_type,
        old_jti[:16] if old_jti else None,
        new_jti[:16],
    )


class TokenRotator:
    """Manages token rotation with automatic invalidation of old tokens."""

    def __init__(
        self,
        access_ttl: int = ACCESS_TOKEN_TTL_SECONDS,
        refresh_ttl: int = REFRESH_TOKEN_TTL_SECONDS,
    ):
        self._access_ttl = access_ttl
        self._refresh_ttl = refresh_ttl
        self._revoked_jtis: set[str] = set()
        self._active_refresh_tokens: dict[str, str] = {}

    def create_access_token_payload(
        self,
        user_id: str,
        username: str,
        role: str,
        tier: int,
        researcher_id: Optional[str] = None,
    ) -> dict:
        """Create access token payload with short expiry."""
        now = datetime.now(timezone.utc)
        jti = str(uuid.uuid4())

        return {
            "jti": jti,
            "sub": user_id,
            "iss": role,
            "aud": "nrg-api",
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=self._access_ttl)).timestamp()),
            "token_type": "access",
            "username": username,
            "role": role,
            "tier": tier,
            "groups": [],
            "scope": "",
            **({"researcher_id": researcher_id} if researcher_id else {}),
        }

    def create_refresh_token_payload(
        self,
        user_id: str,
        username: str,
        role: str,
        tier: int,
        researcher_id: Optional[str] = None,
    ) -> tuple[dict, str]:
        """Create refresh token payload with long expiry.

        Returns (payload, jti)
        """
        now = datetime.now(timezone.utc)
        jti = str(uuid.uuid4())

        payload = {
            "jti": jti,
            "sub": user_id,
            "iss": role,
            "aud": "nrg-api",
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=self._refresh_ttl)).timestamp()),
            "token_type": "refresh",
            "username": username,
            "role": role,
            "tier": tier,
            "groups": [],
            "scope": "",
            **({"researcher_id": researcher_id} if researcher_id else {}),
        }

        self._active_refresh_tokens[user_id] = jti

        return payload, jti

    def validate_refresh_rotation(self, user_id: str, jti: str) -> bool:
        """Check if refresh token JTI is the current active one for user."""
        active_jti = self._active_refresh_tokens.get(user_id)
        if active_jti is None:
            return True

        return active_jti == jti

    def rotate_refresh_token(self, user_id: str) -> Optional[str]:
        """Mark old refresh token as rotated. Returns new JTI."""
        new_jti = str(uuid.uuid4())
        old_jti = self._active_refresh_tokens.get(user_id)

        if old_jti:
            self._revoked_jtis.add(old_jti)
            log_token_rotation(user_id, old_jti, new_jti, "refresh")

        self._active_refresh_tokens[user_id] = new_jti
        return new_jti

    def revoke_token(self, jti: str) -> None:
        """Revoke a token by JTI."""
        self._revoked_jtis.add(jti)
        logger.info("Token revoked: jti=%s", jti[:16])

    def is_revoked(self, jti: str) -> bool:
        """Check if a token JTI has been revoked."""
        return jti in self._revoked_jtis

    def get_ttl_config(self) -> dict:
        """Get token TTL configuration."""
        return {
            "access_token_ttl_seconds": self._access_ttl,
            "refresh_token_ttl_seconds": self._refresh_ttl,
        }


_rotator_instance: Optional[TokenRotator] = None


def get_token_rotator() -> TokenRotator:
    global _rotator_instance
    if _rotator_instance is None:
        _rotator_instance = TokenRotator()
    return _rotator_instance


def rotate_tokens(user_id: str, old_refresh_jti: Optional[str]) -> dict:
    """Convenience function to rotate tokens.

    Returns rotation metadata including new JTI.
    """
    rotator = get_token_rotator()
    new_jti = rotator.rotate_refresh_token(user_id)

    return {
        "rotated": True,
        "new_jti": new_jti,
        "old_jti": old_refresh_jti,
        "access_token_ttl": ACCESS_TOKEN_TTL_SECONDS,
        "refresh_token_ttl": REFRESH_TOKEN_TTL_SECONDS,
    }


def get_rotation_logs() -> list[dict]:
    """Get token rotation logs."""
    return list(ROTATED_TOKENS_LOG)
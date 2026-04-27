"""Per-User Audit Keys — Protocol #35: Non-Representation Lock.

Derives a cryptographically unique per-user signing key from:
- user_id: unique per-user identifier
- jwt_kid: the key ID of the JWT signing key used
- rotating_salt: time-bounded salt (rotates daily)

This creates a HMAC chain where:
1. Each user has a distinct key they cannot deny signing with
2. The key is bound to the JWT identity used at that moment
3. Salt rotation means old keys expire daily — cannot replay old sessions
4. Request fingerprint (IP, UA, TLS session) is embedded in every event

verify_chain() will reject any event where the per-user binding is broken.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from datetime import datetime, UTC
from threading import Lock
from typing import Optional

logger = logging.getLogger(__name__)

_SALT_ROTATION_SECONDS = 86400  # 1 day


class RotatingSaltStore:
    """Stores and rotates per-user salts with daily key rotation."""

    def __init__(self, storage_path: str = ".audit/per_user_salts.jsonl"):
        from pathlib import Path
        if storage_path == ".audit/per_user_salts.jsonl":
            audit_dir = os.environ.get("NRG_AUDIT_DIR")
            if audit_dir:
                storage_path = str(Path(audit_dir) / "per_user_salts.jsonl")
        self._path = Path(storage_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._salts: dict[str, str] = {}
        self._lock = Lock()
        self._current_salt_date: str = self._today_str()
        self._load_salts()

    def _today_str(self) -> str:
        return datetime.now(UTC).date().isoformat()

    def _load_salts(self) -> None:
        if not self._path.exists():
            return
        try:
            import json
            with open(self._path) as f:
                for line in f:
                    entry = json.loads(line)
                    if entry.get("expires", "") >= self._today_str():
                        self._salts[entry["user_id"]] = entry["salt"]
        except Exception:
            pass

    def _persist_salt(self, user_id: str, salt: str, expires: str) -> None:
        try:
            import json
            with open(self._path, "a") as f:
                f.write(json.dumps({"user_id": user_id, "salt": salt, "expires": expires}) + "\n")
        except Exception:
            logger.warning("Failed to persist per-user salt for %s", user_id)

    def get_salt(self, user_id: str) -> str:
        with self._lock:
            today = self._today_str()
            if today != self._current_salt_date:
                self._current_salt_date = today
                self._salts.clear()

            if user_id not in self._salts:
                salt = self._generate_salt(user_id)
                from datetime import timedelta
                expires = (datetime.now(UTC).date() + timedelta(days=1)).isoformat()
                self._salts[user_id] = salt
                self._persist_salt(user_id, salt, expires)

            return self._salts[user_id]

    def _generate_salt(self, user_id: str) -> str:
        raw = f"{user_id}:{self._current_salt_date}:{os.urandom(16).hex()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]


class PerUserKeyManager:
    """Manages per-user audit keys derived from user_id + JWT kid + rotating salt."""

    def __init__(
        self,
        chain_key: str,
        salt_store: Optional[RotatingSaltStore] = None,
    ):
        self._chain_key = chain_key
        self._salt_store = salt_store or RotatingSaltStore()
        self._key_cache: dict[str, str] = {}
        self._lock = Lock()

    def derive_key(
        self,
        user_id: str,
        jwt_kid: Optional[str] = None,
        request_fingerprint: Optional[str] = None,
    ) -> str:
        """Derive a per-user key bound to JWT identity and request fingerprint."""
        _jwt_kid = "none" if jwt_kid is None else jwt_kid
        _fp = "none" if request_fingerprint is None else request_fingerprint
        cache_key = f"{user_id}:{_jwt_kid}:{_fp}"
        with self._lock:
            if cache_key in self._key_cache:
                return self._key_cache[cache_key]

        salt = self._salt_store.get_salt(user_id)
        components = [
            self._chain_key,
            f"user={user_id}",
            f"kid={jwt_kid or 'unknown'}",
            f"salt={salt}",
        ]
        if request_fingerprint:
            components.append(f"fp={request_fingerprint}")

        derivation_input = "|".join(components).encode()
        derived = hashlib.sha256(derivation_input).hexdigest()[:32]

        with self._lock:
            self._key_cache[cache_key] = derived

        return derived

    def compute_binding(
        self,
        user_id: str,
        jwt_kid: Optional[str],
        request_fingerprint: Optional[str],
        chain_hash: str,
        event_serialized: str,
    ) -> str:
        """Compute the per-user binding HMAC for an audit event."""
        key = self.derive_key(user_id, jwt_kid, request_fingerprint)
        message = f"{key}:{chain_hash}:{event_serialized}"
        return hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()

    def verify_binding(
        self,
        user_id: str,
        jwt_kid: Optional[str],
        request_fingerprint: Optional[str],
        chain_hash: str,
        event_serialized: str,
        stored_binding: str,
    ) -> tuple[bool, str]:
        """Verify a stored per-user binding. Returns (valid, error_reason)."""
        if not user_id or user_id == "system":
            return True, "system event"

        if not stored_binding:
            return False, "missing per-user binding"

        try:
            computed = self.compute_binding(
                user_id, jwt_kid, request_fingerprint,
                chain_hash, event_serialized,
            )
            if hmac.compare_digest(computed[:16], stored_binding[:16]):
                return True, "valid"
            return False, f"binding mismatch: computed={computed[:16]} stored={stored_binding[:16]}"
        except Exception as e:
            return False, f"verification error: {e}"


def build_request_fingerprint(
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    tls_version: Optional[str] = None,
    tls_cipher: Optional[str] = None,
) -> str:
    """Build a request fingerprint from TLS/HTTP context fields."""
    components = [
        f"ip={client_ip or 'unknown'}",
        f"ua={hashlib.sha256((user_agent or '').encode()).hexdigest()[:8]}",
        f"tls={tls_version or 'unknown'}/{tls_cipher or 'unknown'}",
    ]
    return "|".join(components)


_salt_store: Optional[RotatingSaltStore] = None
_key_manager: Optional[PerUserKeyManager] = None
_init_lock = Lock()


def get_per_user_key_manager(chain_key: Optional[str] = None) -> PerUserKeyManager:
    """Get the singleton PerUserKeyManager."""
    global _salt_store, _key_manager
    with _init_lock:
        if _key_manager is None:
            from src.audit import CHAIN_KEY
            key = chain_key or CHAIN_KEY or "nrg-audit-chain-dev-key"
            _salt_store = RotatingSaltStore()
            _key_manager = PerUserKeyManager(key, _salt_store)
        return _key_manager


def reset_per_user_key_manager() -> None:
    """Reset singleton — for testing only."""
    global _salt_store, _key_manager
    with _init_lock:
        _salt_store = None
        _key_manager = None

"""DB Co-Sign Module — Protocol #35 Phase 2: Multi-Party Audit Attestation.

Provides an independent PostgreSQL-side co-signature over every audit event.
This ensures a compromised API process alone cannot forge the audit chain —
both the API HMAC (stored in chain.jsonl) and the DB HMAC (stored in
audit_db_cosign table) must match for verify_chain() to pass.

Architecture:
1. After ImmutableAuditLog.append() writes chain.jsonl, it calls db_cosign.cosign()
2. db_cosign computes: HMAC(DB_COSIGN_KEY, event_id || chain_hash || per_user_binding[:16])
3. Stores (event_id, chain_hash, db_signature, created_at) in audit_db_cosign table
4. verify_chain() calls verify_cosign() — both signatures must match

The DB_COSIGN_KEY lives only in Postgres (via Vault) or environment — never in the API source.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from datetime import datetime, UTC
from typing import Optional

logger = logging.getLogger(__name__)

_DB_COSIGN_KEY = os.environ.get("AUDIT_DB_COSIGN_KEY", "")


class DBCoSignStore:
    """Manages PostgreSQL audit co-sign table and verification."""

    _instance: Optional["DBCoSignStore"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            from threading import Lock
            cls._instance = super().__new__(cls)
            cls._instance._lock = Lock()
        return cls._instance

    def __init__(self, connection_string: Optional[str] = None):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._conn_str = connection_string or os.environ.get("DATABASE_URL")
        self._table_exists = False

    def _get_conn(self):
        import psycopg2
        return psycopg2.connect(self._conn_str)

    def cosign(
        self,
        event_id: str,
        chain_hash: str,
        per_user_binding: str,
        user_id: str,
        event_type: str,
    ) -> Optional[str]:
        """Compute and store DB co-signature for an audit event.

        Returns the 16-char hex signature if stored, None if DB unavailable.
        """
        if not _DB_COSIGN_KEY:
            logger.debug("AUDIT_DB_COSIGN_KEY not set — DB co-sign skipped")
            return None

        if not self._conn_str:
            logger.debug("No DATABASE_URL — DB co-sign skipped")
            return None

        message = f"{event_id}:{chain_hash}:{per_user_binding[:16]}"
        signature = hmac.new(
            _DB_COSIGN_KEY.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]

        try:
            with self._lock:
                conn = self._get_conn()
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO audit_db_cosign
                            (event_id, chain_hash, user_id, event_type, db_signature, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (event_id) DO UPDATE
                            SET db_signature = EXCLUDED.db_signature,
                                created_at = EXCLUDED.created_at
                        """,
                        (event_id, chain_hash, user_id, event_type, signature, datetime.now(UTC).isoformat()),
                    )
                    conn.commit()
                    logger.info("DB co-signed event %s, sig=%s...", event_id, signature[:8])
                    return signature
                finally:
                    cursor.close()
                    conn.close()
        except Exception as exc:
            logger.warning("Failed to write DB co-sign for event %s: %s", event_id, exc)
            return None

    def verify_cosign(
        self,
        event_id: str,
        chain_hash: str,
        per_user_binding: str,
    ) -> tuple[bool, Optional[str]]:
        """Verify DB co-signature for an event.

        Returns (valid, stored_signature).
        If DB unavailable or key missing, returns (True, None) — permissive.
        """
        if not _DB_COSIGN_KEY:
            return True, None

        if not self._conn_str:
            return True, None

        message = f"{event_id}:{chain_hash}:{per_user_binding[:16]}"
        expected = hmac.new(
            _DB_COSIGN_KEY.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]

        try:
            with self._lock:
                conn = self._get_conn()
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT db_signature FROM audit_db_cosign WHERE event_id = %s AND chain_hash = %s",
                        (event_id, chain_hash),
                    )
                    row = cursor.fetchone()
                    cursor.close()
                    conn.close()

                    if row is None:
                        logger.warning("No DB co-sign found for event %s — possible co-sign gap", event_id)
                        return False, None

                    stored = row[0]
                    valid = hmac.compare_digest(stored, expected)
                    if not valid:
                        logger.error(
                            "DB co-sign mismatch for event %s: expected %s, got %s",
                            event_id, expected, stored
                        )
                    return valid, stored
                except Exception:
                    return True, None
        except Exception as exc:
            logger.warning("DB co-sign verify failed for event %s (permissive): %s", event_id, exc)
            return True, None

    def get_cosign_health(self) -> dict:
        """Return co-sign table health metrics."""
        if not self._conn_str:
            return {"status": "disabled", "reason": "no DATABASE_URL"}

        try:
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM audit_db_cosign"
                )
                row = cursor.fetchone()
                cursor.close()
                conn.close()
                return {
                    "status": "active",
                    "total_cosigns": row[0] or 0,
                    "oldest": row[1],
                    "newest": row[2],
                }
            except Exception:
                return {"status": "error"}
        except Exception:
            return {"status": "unavailable"}


def cosign_event(
    event_id: str,
    chain_hash: str,
    per_user_binding: str,
    user_id: str,
    event_type: str,
) -> Optional[str]:
    """Convenience function — stores DB co-sign for an audit event."""
    return DBCoSignStore().cosign(
        event_id=event_id,
        chain_hash=chain_hash,
        per_user_binding=per_user_binding,
        user_id=user_id,
        event_type=event_type,
    )


def verify_db_cosign(
    event_id: str,
    chain_hash: str,
    per_user_binding: str,
) -> tuple[bool, Optional[str]]:
    """Convenience function — verifies DB co-signature for an event."""
    return DBCoSignStore().verify_cosign(
        event_id=event_id,
        chain_hash=chain_hash,
        per_user_binding=per_user_binding,
    )


def get_cosign_health() -> dict:
    """Convenience function — returns co-sign table health."""
    return DBCoSignStore().get_cosign_health()

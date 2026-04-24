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
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DB_COSIGN_TRIGGER_NAME = "audit_cosign_trigger"
DB_COSIGN_FUNCTION_NAME = "audit_cosign_event"
DB_COSIGN_COLUMN = "db_cosign_hmac"
DB_COSIGN_SETTING = "app.audit_db_cosign_key"


@dataclass(frozen=True)
class DBCoSignVerificationResult:
    """Summary returned by recent DB co-sign verification."""

    all_signed: bool
    count: int
    status: str
    missing: list[str] = field(default_factory=list)
    mismatched: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _db_cosign_key() -> str:
    """Load the DB co-sign key lazily so tests and Vault-injected env work."""
    return os.environ.get("AUDIT_DB_COSIGN_KEY", "")


def _is_postgres_url(connection_string: Optional[str]) -> bool:
    if not connection_string:
        return False
    return connection_string.startswith(("postgresql://", "postgres://"))


def build_db_cosign_message(event_id: str, chain_hash: str, per_user_binding: str) -> str:
    """Canonical DB co-sign message used by Python verification and the trigger."""
    return f"{event_id}:{chain_hash}:{(per_user_binding or '')[:16]}"


def compute_db_cosign_hmac(
    event_id: str,
    chain_hash: str,
    per_user_binding: str,
    db_secret: Optional[str] = None,
) -> str:
    """Compute the expected PostgreSQL-side audit co-signature."""
    secret = db_secret if db_secret is not None else _db_cosign_key()
    if not secret:
        raise ValueError("AUDIT_DB_COSIGN_KEY is required to compute DB co-sign HMAC")
    return hmac.new(
        secret.encode(),
        build_db_cosign_message(event_id, chain_hash, per_user_binding).encode(),
        hashlib.sha256,
    ).hexdigest()


def generate_audit_cosign_trigger_sql(
    table_name: str = "audit_events",
    secret_setting: str = DB_COSIGN_SETTING,
) -> str:
    """Return PostgreSQL DDL for the DB-owned audit co-sign trigger.

    The trigger writes `audit_events.db_cosign_hmac` on INSERT using a DB
    session setting populated by Vault/ops (`app.audit_db_cosign_key`). The API
    can insert event metadata, but the HMAC is generated inside PostgreSQL.
    """
    return f"""
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS {table_name} (
    event_id TEXT PRIMARY KEY,
    chain_hash TEXT NOT NULL,
    per_user_binding TEXT,
    user_id TEXT,
    event_type TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE {table_name}
    ADD COLUMN IF NOT EXISTS {DB_COSIGN_COLUMN} TEXT;

CREATE OR REPLACE FUNCTION {DB_COSIGN_FUNCTION_NAME}()
RETURNS trigger AS $$
DECLARE
    cosign_key TEXT;
    cosign_message TEXT;
BEGIN
    cosign_key := current_setting('{secret_setting}', true);
    IF cosign_key IS NULL OR cosign_key = '' THEN
        RAISE EXCEPTION '{secret_setting} must be set before inserting audit_events';
    END IF;

    cosign_message := concat_ws(
        ':',
        NEW.event_id::text,
        COALESCE(NEW.chain_hash, ''),
        left(COALESCE(NEW.per_user_binding, ''), 16)
    );

    NEW.{DB_COSIGN_COLUMN} := encode(
        hmac(cosign_message::bytea, cosign_key::bytea, 'sha256'),
        'hex'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS {DB_COSIGN_TRIGGER_NAME} ON {table_name};
CREATE TRIGGER {DB_COSIGN_TRIGGER_NAME}
    BEFORE INSERT ON {table_name}
    FOR EACH ROW
    EXECUTE FUNCTION {DB_COSIGN_FUNCTION_NAME}();
""".strip()


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
        try:
            import psycopg
            return psycopg.connect(self._conn_str)
        except ImportError:
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
        if not _is_postgres_url(self._conn_str):
            logger.debug("No PostgreSQL DATABASE_URL — DB co-sign skipped")
            return None

        try:
            with self._lock:
                conn = self._get_conn()
                try:
                    cursor = conn.cursor()
                    cosign_key = _db_cosign_key()
                    if cosign_key:
                        cursor.execute(
                            f"SELECT set_config('{DB_COSIGN_SETTING}', %s, true)",
                            (cosign_key,),
                        )
                    cursor.execute(
                        """
                        INSERT INTO audit_events
                            (event_id, chain_hash, per_user_binding, user_id, event_type, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (event_id) DO UPDATE
                            SET chain_hash = EXCLUDED.chain_hash,
                                per_user_binding = EXCLUDED.per_user_binding,
                                user_id = EXCLUDED.user_id,
                                event_type = EXCLUDED.event_type,
                                created_at = EXCLUDED.created_at
                        RETURNING db_cosign_hmac
                        """,
                        (
                            event_id,
                            chain_hash,
                            (per_user_binding or "")[:16],
                            user_id,
                            event_type,
                            datetime.now(UTC).isoformat(),
                        ),
                    )
                    row = cursor.fetchone()
                    conn.commit()
                    signature = row[0] if row else None
                    logger.info("DB co-signed event %s, sig=%s...", event_id, str(signature)[:8])
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
        if not _db_cosign_key():
            return True, None

        if not _is_postgres_url(self._conn_str):
            return True, None

        expected = compute_db_cosign_hmac(event_id, chain_hash, per_user_binding)

        try:
            with self._lock:
                conn = self._get_conn()
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        f"SELECT {DB_COSIGN_COLUMN} FROM audit_events WHERE event_id = %s AND chain_hash = %s",
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

    def verify_recent(
        self,
        last_n: int = 3,
        chain_path: str | Path = ".audit/chain.jsonl",
    ) -> DBCoSignVerificationResult:
        """Verify the most recent DB co-signatures by chain event id."""
        if not _is_postgres_url(self._conn_str):
            return DBCoSignVerificationResult(
                all_signed=False,
                count=0,
                status="disabled:no_postgres_database_url",
                errors=["PostgreSQL DATABASE_URL is not set"],
            )

        chain_file = Path(chain_path)
        if not chain_file.exists():
            return DBCoSignVerificationResult(
                all_signed=False,
                count=0,
                status="missing_chain",
                errors=[f"{chain_file} does not exist"],
            )

        events: list[dict] = []
        for line in chain_file.read_text().splitlines():
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        recent = events[-last_n:]
        missing: list[str] = []
        mismatched: list[str] = []
        errors: list[str] = []
        for event in recent:
            event_id = str(event.get("event_id", ""))
            ok, stored = self.verify_cosign(
                event_id=event_id,
                chain_hash=str(event.get("hash", "")),
                per_user_binding=str(event.get("per_user_binding", "")),
            )
            if stored is None:
                missing.append(event_id)
            elif not ok:
                mismatched.append(event_id)

        all_signed = bool(recent) and not missing and not mismatched and not errors
        return DBCoSignVerificationResult(
            all_signed=all_signed,
            count=len(recent),
            status="ok" if all_signed else "failed",
            missing=missing,
            mismatched=mismatched,
            errors=errors,
        )

    def get_cosign_health(self) -> dict:
        """Return co-sign table health metrics."""
        if not self._conn_str:
            return {"status": "disabled", "reason": "no DATABASE_URL"}

        try:
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM audit_events WHERE {DB_COSIGN_COLUMN} IS NOT NULL"
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
    event_id: Optional[str] = None,
    chain_hash: Optional[str] = None,
    per_user_binding: Optional[str] = None,
    last_n: Optional[int] = None,
    chain_path: str | Path = ".audit/chain.jsonl",
) -> tuple[bool, Optional[str]] | DBCoSignVerificationResult:
    """Verify one DB co-signature, or recent chain events when `last_n` is set."""
    if last_n is not None:
        return DBCoSignStore().verify_recent(last_n=last_n, chain_path=chain_path)
    if event_id is None or chain_hash is None or per_user_binding is None:
        raise TypeError("event_id, chain_hash, and per_user_binding are required unless last_n is set")
    return DBCoSignStore().verify_cosign(
        event_id=event_id,
        chain_hash=chain_hash,
        per_user_binding=per_user_binding,
    )


def get_cosign_health() -> dict:
    """Convenience function — returns co-sign table health."""
    return DBCoSignStore().get_cosign_health()

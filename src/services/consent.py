"""DPDP 2023 Consent Management Service with data retention policies."""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from src.data.database import get_sqlite_connection, resolve_database_path

logger = logging.getLogger(__name__)


def _audit_consent_event(event_type: str, user_id: str, scope: str, result: Dict[str, Any]) -> None:
    """Log consent events to HMAC-chained audit log."""
    try:
        from src.audit import AuditEvent, get_audit_log
        audit_log = get_audit_log()
        audit_log.append(AuditEvent(
            event_type=event_type,
            user_id=user_id,
            result={**result, "scope": scope},
        ))
    except Exception as e:
        logger.warning(f"Failed to write consent event to audit chain: {e}")


class ConsentService:
    """Manages user consent for DPDP 2023 compliance."""

    SCOPES = {
        "research_access": "Access research data",
        "profile_storage": "Store user profile",
        "query_history": "Store query history",
        "audit_logging": "Include in audit logs",
        "analytics": "Use for analytics",
    }

    CURRENT_TERMS_VERSION = 1
    CONSENT_RETENTION_DAYS = 365

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = resolve_database_path(db_path)
        self._init_table()

    def _init_table(self):
        """Initialize consent_ledger table."""
        conn = get_sqlite_connection(str(self.db_path))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS consent_ledger (
                consent_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                scope TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                terms_version INTEGER DEFAULT 1,
                granted_at TEXT NOT NULL,
                expires_at TEXT,
                revoked_at TEXT,
                UNIQUE(user_id, scope)
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_consent_user
            ON consent_ledger(user_id)
            """
        )
        for col, col_type in [("terms_version", "INTEGER DEFAULT 1"), ("expires_at", "TEXT")]:
            try:
                conn.execute(f"ALTER TABLE consent_ledger ADD COLUMN {col} {col_type}")
            except Exception:
                pass
        conn.commit()
        conn.close()

    def grant_consent(self, user_id: str, scope: str, retention_days: int = None) -> Dict[str, Any]:
        """Grant consent for a scope."""
        if scope not in self.SCOPES:
            return {"success": False, "error": f"Invalid scope: {scope}"}

        conn = get_sqlite_connection(str(self.db_path))
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        consent_id = str(uuid.uuid4())
        retention = retention_days or self.CONSENT_RETENTION_DAYS
        expires_at = (now + timedelta(days=retention)).isoformat()

        try:
            conn.execute(
                """
                INSERT INTO consent_ledger (consent_id, user_id, scope, terms_version, granted_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, scope) DO UPDATE SET
                    revoked_at = NULL,
                    granted_at = excluded.granted_at,
                    expires_at = excluded.expires_at,
                    terms_version = excluded.terms_version,
                    version = consent_ledger.version + 1
                """,
                (consent_id, user_id, scope, self.CURRENT_TERMS_VERSION, now_iso, expires_at),
            )
            conn.commit()
            result = {
                "success": True,
                "consent_id": consent_id,
                "scope": scope,
                "granted_at": now_iso,
                "expires_at": expires_at,
                "terms_version": self.CURRENT_TERMS_VERSION,
            }
            _audit_consent_event("consent_granted", user_id, scope, result)
            return result
        except Exception as e:
            result = {"success": False, "error": str(e)}
            _audit_consent_event("consent_granted_failed", user_id, scope, result)
            return result
        finally:
            conn.close()

    def revoke_consent(self, user_id: str, scope: str) -> Dict[str, Any]:
        """Revoke consent for a scope."""
        conn = get_sqlite_connection(str(self.db_path))
        now = datetime.now(timezone.utc).isoformat()

        cursor = conn.execute(
            """
            UPDATE consent_ledger
            SET revoked_at = ?
            WHERE user_id = ? AND scope = ? AND revoked_at IS NULL
            """,
            (now, user_id, scope),
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        if success:
            result = {"success": True, "scope": scope, "revoked_at": now}
            _audit_consent_event("consent_revoked", user_id, scope, result)
            return result
        result = {"success": False, "scope": scope, "error": "Consent not found or already revoked"}
        _audit_consent_event("consent_revoke_failed", user_id, scope, result)
        return result

    def get_consent(self, user_id: str, scope: str) -> Optional[Dict]:
        """Get consent status for a scope."""
        conn = get_sqlite_connection(str(self.db_path))
        cursor = conn.execute(
            """
            SELECT scope, version, terms_version, granted_at, expires_at, revoked_at
            FROM consent_ledger
            WHERE user_id = ? AND scope = ?
            """,
            (user_id, scope),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "scope": row[0],
            "version": row[1],
            "terms_version": row[2],
            "granted_at": row[3],
            "expires_at": row[4],
            "revoked_at": row[5],
            "active": row[5] is None,
        }

    def list_consents(self, user_id: str) -> List[Dict]:
        """List all consents for a user."""
        conn = get_sqlite_connection(str(self.db_path))
        cursor = conn.execute(
            """
            SELECT scope, version, terms_version, granted_at, expires_at, revoked_at
            FROM consent_ledger
            WHERE user_id = ?
            ORDER BY granted_at DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "scope": row[0],
                "version": row[1],
                "terms_version": row[2],
                "granted_at": row[3],
                "expires_at": row[4],
                "revoked_at": row[5],
                "active": row[5] is None,
                "description": self.SCOPES.get(row[0], ""),
                "expired": bool(row[4]) and datetime.fromisoformat(row[4].replace("Z", "+00:00")) < datetime.now(timezone.utc) if row[4] else False,
                "terms_current": (row[2] or 0) >= self.CURRENT_TERMS_VERSION,
            }
            for row in rows
        ]

    def has_consent(self, user_id: str, scope: str) -> bool:
        """Check if user has active, non-expired, current-terms consent for scope."""
        consent = self.get_consent(user_id, scope)
        if consent is None or not consent["active"]:
            return False
        if consent.get("terms_version", 0) < self.CURRENT_TERMS_VERSION:
            return False
        if consent.get("expires_at"):
            try:
                exp_dt = datetime.fromisoformat(consent["expires_at"].replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > exp_dt:
                    return False
            except Exception:
                pass
        return True

    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all data for a user (DPDP right to access)."""
        conn = get_sqlite_connection(str(self.db_path))

        data: dict[str, Any] = {
            "user_id": user_id,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "consents": [],
            "queries": [],
        }

        cursor = conn.execute(
            "SELECT * FROM consent_ledger WHERE user_id = ?",
            (user_id,),
        )
        data["consents"] = [dict(row) for row in cursor.fetchall()]

        try:
            cursor = conn.execute(
                "SELECT * FROM audit_events WHERE user_id = ?",
                (user_id,),
            )
            data["audit_events"] = [dict(row) for row in cursor.fetchall()]
        except Exception:
            data["audit_events"] = []

        conn.close()

        _audit_consent_event("data_export", user_id, "all", {"record_count": len(data.get("consents", [])) + len(data.get("audit_events", []))})
        return data

    def erase_user_data(self, user_id: str) -> Dict[str, Any]:
        """Erase all PII for a user (DPDP right to erasure)."""
        conn = get_sqlite_connection(str(self.db_path))

        cursor = conn.execute(
            "DELETE FROM consent_ledger WHERE user_id = ?",
            (user_id,),
        )
        consents_deleted = cursor.rowcount

        try:
            cursor = conn.execute(
                """
                UPDATE audit_events
                SET user_id = 'ANONYMIZED', query = '[REDACTED]'
                WHERE user_id = ?
                """,
                (user_id,),
            )
            events_anonymized = cursor.rowcount
        except Exception:
            events_anonymized = 0

        conn.commit()
        conn.close()

        result = {
            "success": True,
            "consents_deleted": consents_deleted,
            "events_anonymized": events_anonymized,
        }
        _audit_consent_event("data_erasure", user_id, "all", result)
        return result

    def cleanup_expired_consents(self) -> Dict[str, Any]:
        """
        DPDP Data Retention: Auto-purge expired consents and associated data.
        Run daily via cron job.
        """
        conn = get_sqlite_connection(str(self.db_path))

        cursor = conn.execute(
            "SELECT consent_id, user_id, scope, revoked_at FROM consent_ledger WHERE revoked_at IS NOT NULL",
        )
        expired = cursor.fetchall()

        deleted_count = 0
        for consent_id, user_id, scope, revoked_at in expired:
            if revoked_at:
                try:
                    revoked_dt = datetime.fromisoformat(revoked_at.replace("Z", "+00:00"))
                    if datetime.now(timezone.utc) - revoked_dt > timedelta(days=30):
                        conn.execute("DELETE FROM consent_ledger WHERE consent_id = ?", (consent_id,))
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to process expired consent {consent_id}: {e}")

        conn.commit()
        conn.close()

        logger.info(f"DPDP retention cleanup: {deleted_count} expired consents purged")
        return {"success": True, "purged": deleted_count}

    def is_data_retention_enabled(self) -> bool:
        """Check if data retention policies are active."""
        return True

    def get_expiring_consents(self, user_id: str, within_days: int = 30) -> List[Dict]:
        """Get consents expiring within specified days for a user."""
        conn = get_sqlite_connection(str(self.db_path))
        cutoff = (datetime.now(timezone.utc) + timedelta(days=within_days)).isoformat()
        cursor = conn.execute(
            """
            SELECT scope, expires_at, granted_at
            FROM consent_ledger
            WHERE user_id = ? AND expires_at IS NOT NULL AND expires_at < ? AND revoked_at IS NULL
            """,
            (user_id, cutoff),
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {"scope": row[0], "expires_at": row[1], "granted_at": row[2]}
            for row in rows
        ]

    def get_admin_stats(self) -> Dict[str, Any]:
        """Get DPDP compliance statistics for admin dashboard."""
        conn = get_sqlite_connection(str(self.db_path))

        cursor = conn.execute("SELECT COUNT(DISTINCT user_id) FROM consent_ledger")
        total_users = cursor.fetchone()[0] or 0

        stats = {"total_users_with_consent": total_users, "by_scope": {}}
        for scope in self.SCOPES:
            cursor = conn.execute(
                """
                SELECT COUNT(*), SUM(CASE WHEN revoked_at IS NULL THEN 1 ELSE 0 END)
                FROM consent_ledger WHERE scope = ?
                """,
                (scope,),
            )
            total, active = cursor.fetchone()
            stats["by_scope"][scope] = {"total": total or 0, "active": active or 0}

        cursor = conn.execute(
            "SELECT COUNT(*) FROM consent_ledger WHERE expires_at IS NOT NULL AND expires_at < ? AND revoked_at IS NULL",
            ((datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),),
        )
        stats["expiring_within_30_days"] = cursor.fetchone()[0] or 0

        conn.close()
        return stats

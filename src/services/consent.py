"""DPDP 2023 Consent Management Service."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from src.data.database import get_sqlite_connection, resolve_database_path


class ConsentService:
    """Manages user consent for DPDP 2023 compliance."""

    SCOPES = {
        "research_access": "Access research data",
        "profile_storage": "Store user profile",
        "query_history": "Store query history",
        "audit_logging": "Include in audit logs",
        "analytics": "Use for analytics",
    }

    def __init__(self, db_path: str = None):
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
                granted_at TEXT NOT NULL,
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
        conn.commit()
        conn.close()

    def grant_consent(self, user_id: str, scope: str) -> Dict[str, Any]:
        """Grant consent for a scope."""
        if scope not in self.SCOPES:
            return {"success": False, "error": f"Invalid scope: {scope}"}

        conn = get_sqlite_connection(str(self.db_path))
        now = datetime.now(timezone.utc).isoformat()
        consent_id = str(uuid.uuid4())

        try:
            conn.execute(
                """
                INSERT INTO consent_ledger (consent_id, user_id, scope, granted_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, scope) DO UPDATE SET
                    revoked_at = NULL,
                    version = consent_ledger.version + 1
                """,
                (consent_id, user_id, scope, now),
            )
            conn.commit()
            return {
                "success": True,
                "consent_id": consent_id,
                "scope": scope,
                "granted_at": now,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
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
            return {"success": True, "scope": scope, "revoked_at": now}
        return {"success": False, "error": "Consent not found or already revoked"}

    def get_consent(self, user_id: str, scope: str) -> Optional[Dict]:
        """Get consent status for a scope."""
        conn = get_sqlite_connection(str(self.db_path))
        cursor = conn.execute(
            """
            SELECT scope, version, granted_at, revoked_at
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
            "granted_at": row[2],
            "revoked_at": row[3],
            "active": row[3] is None,
        }

    def list_consents(self, user_id: str) -> List[Dict]:
        """List all consents for a user."""
        conn = get_sqlite_connection(str(self.db_path))
        cursor = conn.execute(
            """
            SELECT scope, version, granted_at, revoked_at
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
                "granted_at": row[2],
                "revoked_at": row[3],
                "active": row[3] is None,
                "description": self.SCOPES.get(row[0], ""),
            }
            for row in rows
        ]

    def has_consent(self, user_id: str, scope: str) -> bool:
        """Check if user has active consent for scope."""
        consent = self.get_consent(user_id, scope)
        return consent is not None and consent["active"]

    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all data for a user (DPDP right to access)."""
        conn = get_sqlite_connection(str(self.db_path))

        data = {
            "user_id": user_id,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "consents": [],
            "queries": [],
        }

        # Get consents
        cursor = conn.execute(
            "SELECT * FROM consent_ledger WHERE user_id = ?",
            (user_id,),
        )
        data["consents"] = [dict(row) for row in cursor.fetchall()]

        # Get audit events
        cursor = conn.execute(
            "SELECT * FROM audit_events WHERE user_id = ?",
            (user_id,),
        )
        data["audit_events"] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return data

    def erase_user_data(self, user_id: str) -> Dict[str, Any]:
        """Erase all PII for a user (DPDP right to erasure)."""
        conn = get_sqlite_connection(str(self.db_path))

        # Delete consents
        cursor = conn.execute(
            "DELETE FROM consent_ledger WHERE user_id = ?",
            (user_id,),
        )
        consents_deleted = cursor.rowcount

        # Anonymize audit events (keep hash, drop user_id)
        cursor = conn.execute(
            """
            UPDATE audit_events
            SET user_id = 'ANONYMIZED', query = '[REDACTED]'
            WHERE user_id = ?
            """,
            (user_id,),
        )
        events_anonymized = cursor.rowcount

        conn.commit()
        conn.close()

        return {
            "success": True,
            "consents_deleted": consents_deleted,
            "events_anonymized": events_anonymized,
        }

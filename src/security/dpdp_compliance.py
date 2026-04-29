"""DPDP Data Retention - Auto-purge PII 90 days after consent expiry.

- Consent ledger tracks all data processing
- Scheduled cleanup job
- Audit trail of all deletions
"""

import hashlib
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from src.data.database import get_sqlite_connection, resolve_database_path

logger = logging.getLogger(__name__)

DATA_RETENTION_DAYS = int(os.getenv("NRG_DATA_RETENTION_DAYS", "90"))

DELETION_AUDIT_LOG: list[dict] = []


def log_deletion(
    user_id: str,
    data_type: str,
    records_deleted: int,
    reason: str,
) -> None:
    """Log all PII deletion events for audit trail."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "data_type": data_type,
        "records_deleted": records_deleted,
        "reason": reason,
        "retention_days": DATA_RETENTION_DAYS,
    }
    DELETION_AUDIT_LOG.append(entry)
    user_id_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
    logger.info(
        "DPDP deletion: user_hash=%s type=%s count=%d reason=%s",
        user_id_hash,
        data_type,
        records_deleted,
        reason,
    )


class DPDPCompliance:
    """DPDP 2023 compliance with 90-day data retention."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = resolve_database_path(db_path)
        self._retention_days = DATA_RETENTION_DAYS

    def get_consent_expiry_date(self, granted_at: str, revoked_at: Optional[str]) -> Optional[datetime]:
        """Calculate when consent expires (90 days after revocation)."""
        if revoked_at is None:
            return None

        try:
            revoked_dt = datetime.fromisoformat(revoked_at.replace("Z", "+00:00"))
            return revoked_dt + timedelta(days=self._retention_days)
        except Exception:
            return None

    def purge_user_data(self, user_id: str, reason: str = "manual") -> dict:
        """Purge all PII for a user after consent expiry."""
        conn = get_sqlite_connection(str(self.db_path))
        results = {}

        try:
            cursor = conn.execute(
                "DELETE FROM consent_ledger WHERE user_id = ?",
                (user_id,),
            )
            results["consents_deleted"] = cursor.rowcount

            cursor = conn.execute(
                """
                UPDATE audit_events
                SET user_id = 'DELETED', query = '[REDACTED]', action = 'USER_DATA_DELETED'
                WHERE user_id = ?
                """,
                (user_id,),
            )
            results["audit_events_anonymized"] = cursor.rowcount

            cursor = conn.execute(
                "DELETE FROM refresh_tokens WHERE user_id = ?",
                (user_id,),
            )
            results["refresh_tokens_revoked"] = cursor.rowcount

            log_deletion(
                user_id=user_id,
                data_type="user_pii",
                records_deleted=sum(results.values()),
                reason=f"{reason}_deletion",
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return results

    def cleanup_expired_consents(self) -> dict:
        """Find and purge data for users with expired consents."""
        conn = get_sqlite_connection(str(self.db_path))
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=self._retention_days)).isoformat()

        cursor = conn.execute(
            """
            SELECT consent_id, user_id, scope, revoked_at
            FROM consent_ledger
            WHERE revoked_at IS NOT NULL
            AND revoked_at < ?
            """,
            (cutoff_date,),
        )
        expired = cursor.fetchall()

        deleted_count = 0
        users_processed = set()

        for consent_id, user_id, scope, revoked_at in expired:
            try:
                expiry_date = self.get_consent_expiry_date("", revoked_at)
                if expiry_date and expiry_date > datetime.now(timezone.utc):
                    continue

                results = self.purge_user_data(user_id, reason="consent_expiry")
                deleted_count += results.get("consents_deleted", 0)
                users_processed.add(user_id)
            except Exception as e:
                logger.warning(
                    "Failed to cleanup expired consent %s: %s",
                    consent_id,
                    e,
                )

        conn.close()

        logger.info(
            "DPDP retention cleanup: %d records deleted for %d users",
            deleted_count,
            len(users_processed),
        )

        return {
            "success": True,
            "purged_records": deleted_count,
            "users_processed": len(users_processed),
            "cutoff_date": cutoff_date,
            "retention_days": self._retention_days,
        }

    def run_scheduled_cleanup(self) -> dict:
        """Run the scheduled DPDP cleanup job."""
        return self.cleanup_expired_consents()

    def get_deletion_audit_log(self, limit: int = 100) -> list[dict]:
        """Get deletion audit log."""
        return list(DELETION_AUDIT_LOG[-limit:])


_compliance_instance: Optional[DPDPCompliance] = None


def get_dpdp_compliance() -> DPDPCompliance:
    global _compliance_instance
    if _compliance_instance is None:
        _compliance_instance = DPDPCompliance()
    return _compliance_instance


def run_retention_cleanup() -> dict:
    """Convenience function to run retention cleanup."""
    return get_dpdp_compliance().run_scheduled_cleanup()


def purge_user_pii(user_id: str, reason: str = "manual") -> dict:
    """Convenience function to purge user PII."""
    return get_dpdp_compliance().purge_user_data(user_id, reason)

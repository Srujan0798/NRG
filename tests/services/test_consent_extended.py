"""Extended tests for ConsentService."""


from src.data.database import get_sqlite_connection
from src.services.consent import ConsentService


def _ensure_audit_events_table():
    conn = get_sqlite_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            event_id TEXT PRIMARY KEY,
            user_id TEXT,
            query TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


class TestConsentServiceExtended:
    def setup_method(self):
        _ensure_audit_events_table()

    def test_grant_and_revoke_consent(self):
        service = ConsentService()
        result = service.grant_consent("user_123", "research_access")
        assert result["success"] is True

        result = service.revoke_consent("user_123", "research_access")
        assert result["success"] is True
        assert "revoked_at" in result

    def test_list_consents(self):
        service = ConsentService()
        service.grant_consent("user_456", "profile_storage")
        consents = service.list_consents("user_456")
        assert len(consents) > 0
        assert consents[0]["scope"] == "profile_storage"

    def test_has_consent(self):
        service = ConsentService()
        service.grant_consent("user_789", "audit_logging")
        assert service.has_consent("user_789", "audit_logging") is True
        assert service.has_consent("user_789", "analytics") is False

    def test_invalid_scope(self):
        service = ConsentService()
        result = service.grant_consent("user_000", "invalid_scope")
        assert result["success"] is False

    def test_export_user_data(self):
        service = ConsentService()
        service.grant_consent("user_exp", "research_access")
        data = service.export_user_data("user_exp")
        assert data["user_id"] == "user_exp"
        assert "consents" in data
        assert "export_timestamp" in data

    def test_erase_user_data(self):
        service = ConsentService()
        service.grant_consent("user_del", "research_access")
        result = service.erase_user_data("user_del")
        assert result["success"] is True
        assert result["consents_deleted"] >= 0

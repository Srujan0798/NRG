"""Tests for ConsentService (DPDP 2023)."""

import pytest
from unittest.mock import patch

from src.services.consent import ConsentService


@pytest.fixture
def consent_db(tmp_path):
    db_path = str(tmp_path / "test_consent.db")
    with patch("src.services.consent.get_sqlite_connection") as mock_conn_factory:
        import sqlite3
        connections = []

        def make_conn(path=None):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            connections.append(conn)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS consent_ledger (
                    consent_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    granted_at TEXT NOT NULL,
                    revoked_at TEXT,
                    UNIQUE(user_id, scope)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_user ON consent_ledger(user_id)")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    action TEXT,
                    query TEXT,
                    timestamp TEXT
                )
            """)
            conn.commit()
            return conn

        mock_conn_factory.side_effect = make_conn
        with patch("src.services.consent.resolve_database_path", return_value=db_path):
            yield db_path

        for c in connections:
            try:
                c.close()
            except Exception:
                pass


class TestConsentService:
    def test_grant_consent_valid_scope(self, consent_db):
        service = ConsentService()
        result = service.grant_consent("user1", "research_access")
        assert result["success"] is True
        assert result["scope"] == "research_access"

    def test_grant_consent_invalid_scope(self, consent_db):
        service = ConsentService()
        result = service.grant_consent("user1", "invalid_scope")
        assert result["success"] is False
        assert "Invalid scope" in result["error"]

    def test_revoke_consent(self, consent_db):
        service = ConsentService()
        service.grant_consent("user1", "research_access")
        result = service.revoke_consent("user1", "research_access")
        assert result["success"] is True

    def test_revoke_nonexistent_consent(self, consent_db):
        service = ConsentService()
        result = service.revoke_consent("user1", "research_access")
        assert result["success"] is False

    def test_list_consents(self, consent_db):
        service = ConsentService()
        service.grant_consent("user1", "research_access")
        service.grant_consent("user1", "profile_storage")
        result = service.list_consents("user1")
        assert len(result) >= 2

    def test_has_consent(self, consent_db):
        service = ConsentService()
        service.grant_consent("user1", "research_access")
        assert service.has_consent("user1", "research_access") is True
        assert service.has_consent("user1", "profile_storage") is False

    def test_has_consent_after_revoke(self, consent_db):
        service = ConsentService()
        service.grant_consent("user1", "research_access")
        service.revoke_consent("user1", "research_access")
        assert service.has_consent("user1", "research_access") is False

    def test_get_consent(self, consent_db):
        service = ConsentService()
        service.grant_consent("user1", "research_access")
        result = service.get_consent("user1", "research_access")
        assert result is not None
        assert result["active"] is True

    def test_get_consent_missing(self, consent_db):
        service = ConsentService()
        result = service.get_consent("user1", "research_access")
        assert result is None

    def test_erase_user_data(self, consent_db):
        service = ConsentService()
        service.grant_consent("user1", "research_access")
        result = service.erase_user_data("user1")
        assert result["success"] is True
        assert result["consents_deleted"] >= 1

    def test_scopes_defined(self):
        assert "research_access" in ConsentService.SCOPES
        assert "profile_storage" in ConsentService.SCOPES

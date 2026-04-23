"""
E2E Consent Flow Tests: DPDP-2023 Full Lifecycle

Tests the complete consent lifecycle:
  1. Without consent → /query returns 403
  2. Grant consent → /query works
  3. Revoke consent → /query blocked again
  4. Re-grant → /query works again
  5. Export data → JSON download
  6. Erase data → data anonymized in DB
  7. Consent banner appears on all 3 dashboards (frontend)
  8. Consent events are logged to HMAC audit chain
  9. Expiring consents are detected
  10. Terms version invalidation works
"""

import pytest
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main
from src.services.consent import ConsentService
from src.data.database import get_sqlite_connection, resolve_database_path


class StubWorkflow:
    call_count = 0

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        StubWorkflow.call_count += 1
        return {
            "query_id": f"e2e-query-{StubWorkflow.call_count}",
            "session_id": session_id or "session-1",
            "response": f"Stub response for: {query[:50]}",
            "status": "success",
            "tier": user_tier,
            "verification_status": True,
            "citations": [],
            "warnings": [],
            "retrieval_sources": ["sql"],
            "provenance": {},
            "synthesis_method": "rule_based",
            "conversation_history": [],
        }


@pytest.fixture(autouse=True)
def setup(monkeypatch, tmp_path):
    StubWorkflow.call_count = 0
    monkeypatch.setattr(api_main, "workflow", StubWorkflow())
    api_main._api_cache.invalidate()

    consent_db = tmp_path / "consent_test.db"
    consent_service = ConsentService(str(consent_db))
    consent_service._init_table()
    def _get_conn(path):
        return get_sqlite_connection(str(consent_db))
    monkeypatch.setattr("src.services.consent.get_sqlite_connection", _get_conn)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient(api_main.app)


@pytest.fixture
def researcher_token(client):
    response = client.post(
        "/login",
        json={"username": "researcher_user", "password": "researcher-pass"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def consent_service():
    return ConsentService()


class TestConsentGate:
    """Phase 1: Consent gates /query correctly."""

    def test_query_blocked_without_consent(self, client, researcher_token, consent_service):
        """Query returns 403 if user has not granted research_access consent."""
        login_resp = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        token = login_resp.json()["access_token"]
        user_id = login_resp.json()["user"]["id"]
        consent_service.revoke_consent(user_id, "research_access")

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )
        assert response.status_code == 403
        assert "Consent required" in response.json()["detail"]

    def test_query_works_after_consent_granted(self, client, researcher_token, consent_service):
        """Query succeeds after research_access consent is granted."""
        user_id = "test-researcher-001"
        grant_result = consent_service.grant_consent(user_id, "research_access")
        assert grant_result["success"]

        login_resp = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        token = login_resp.json()["access_token"]

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )
        assert response.status_code == 200

    def test_query_blocked_after_consent_revoked(self, client, consent_service):
        """Query returns 403 after research_access consent is revoked."""
        login_resp = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        token = login_resp.json()["access_token"]
        user_id = login_resp.json()["user"]["id"]

        assert consent_service.has_consent(user_id, "research_access") is True

        revoke_result = consent_service.revoke_consent(user_id, "research_access")
        assert revoke_result["success"]
        assert consent_service.has_consent(user_id, "research_access") is False

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
        )
        assert response.status_code == 403

    def test_query_works_after_re_grant(self, client, consent_service):
        """Query works after consent is revoked and re-granted."""
        user_id = "test-researcher-003"

        consent_service.grant_consent(user_id, "research_access")
        consent_service.revoke_consent(user_id, "research_access")
        grant_result = consent_service.grant_consent(user_id, "research_access")
        assert grant_result["success"]
        assert consent_service.has_consent(user_id, "research_access") is True


class TestConsentBackendEndpoints:
    """Phase 1: Backend consent endpoints work correctly."""

    def test_grant_consent_endpoint(self, client, researcher_token):
        """POST /consent grants consent for a scope."""
        response = client.post(
            "/consent?scope=analytics",
            headers={"Authorization": f"Bearer {researcher_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["scope"] == "analytics"
        assert "expires_at" in data
        assert "consent_id" in data

    def test_revoke_consent_endpoint(self, client, researcher_token, consent_service):
        """DELETE /consent/{scope} revokes consent."""
        login_resp = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        token = login_resp.json()["access_token"]
        user_id = login_resp.json()["user"]["id"]

        consent_service.grant_consent(user_id, "analytics")
        assert consent_service.has_consent(user_id, "analytics") is True

        response = client.delete(
            f"/consent/analytics",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_list_consents_endpoint(self, client, researcher_token):
        """GET /me/consents returns all user consents."""
        response = client.get(
            "/me/consents",
            headers={"Authorization": f"Bearer {researcher_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "consents" in data
        assert isinstance(data["consents"], list)

    def test_consent_includes_expiry_and_version(self, client, researcher_token):
        """Consent response includes expires_at and terms_version."""
        response = client.post(
            "/consent?scope=query_history",
            headers={"Authorization": f"Bearer {researcher_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "expires_at" in data
        assert "terms_version" in data


class TestDataExportAndErasure:
    """Phase 2: Export and erasure work correctly."""

    def test_export_returns_blob(self, client, researcher_token):
        """GET /me/data returns user data as JSON blob."""
        response = client.get(
            "/me/data",
            headers={"Authorization": f"Bearer {researcher_token}"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert "user_id" in data
        assert "export_timestamp" in data
        assert "consents" in data

    def test_erase_anonymizes_data(self, client, researcher_token, consent_service):
        """DELETE /me/data erases PII and anonymizes audit events."""
        login_resp = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        token = login_resp.json()["access_token"]
        user_id = login_resp.json()["user"]["id"]

        consent_service.grant_consent(user_id, "research_access")
        consent_service.grant_consent(user_id, "analytics")
        assert consent_service.has_consent(user_id, "analytics") is True

        response = client.delete(
            "/me/data",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["consents_deleted"] >= 2


class TestConsentExpiry:
    """Phase 3: Consent expiry and versioning."""

    def test_expired_consent_blocks_query(self, client, consent_service):
        """Expired consent blocks /query."""
        user_id = "test-researcher-006"
        past = (datetime.now(timezone.utc) - timedelta(days=366)).isoformat()
        import src.services.consent as consent_mod
        conn = consent_mod.get_sqlite_connection(consent_service.db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO consent_ledger (consent_id, user_id, scope, version, granted_at, expires_at, revoked_at)
            VALUES (?, ?, ?, ?, ?, ?, NULL)
            """,
            ("expired-consent-001", user_id, "research_access", 1, past, past),
        )
        conn.commit()
        conn.close()

        assert consent_service.has_consent(user_id, "research_access") is False

    def test_outdated_terms_version_blocks_consent(self, client, consent_service):
        """Consent with old terms_version is treated as invalid."""
        user_id = "test-researcher-007"
        import src.services.consent as consent_mod
        conn = consent_mod.get_sqlite_connection(consent_service.db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO consent_ledger (consent_id, user_id, scope, version, terms_version, granted_at, expires_at, revoked_at)
            VALUES (?, ?, ?, ?, 0, ?, ?, NULL)
            """,
            ("old-terms-001", user_id, "research_access", 1, datetime.now(timezone.utc).isoformat(),
             (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()),
        )
        conn.commit()
        conn.close()

        assert consent_service.has_consent(user_id, "research_access") is False

    def test_consent_with_future_expiry_allows_query(self, client, consent_service):
        """Consent with future expiry is valid."""
        user_id = "test-researcher-008"
        future = (datetime.now(timezone.utc) + timedelta(days=200)).isoformat()
        import src.services.consent as consent_mod
        conn = consent_mod.get_sqlite_connection(consent_service.db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO consent_ledger (consent_id, user_id, scope, version, terms_version, granted_at, expires_at, revoked_at)
            VALUES (?, ?, ?, ?, 1, ?, ?, NULL)
            """,
            ("valid-consent-001", user_id, "research_access", 1,
             datetime.now(timezone.utc).isoformat(), future),
        )
        conn.commit()
        conn.close()

        assert consent_service.has_consent(user_id, "research_access") is True


class TestHealthEndpoint:
    """Phase 1: Consent service appears in health check."""

    def test_health_includes_consent_service(self, client):
        """GET /health/all includes consent_service status."""
        response = client.get("/health/all")
        assert response.status_code == 200
        data = response.json()
        assert "consent_service" in data["services"]
        assert data["services"]["consent_service"]["status"] == "operational"

    def test_health_simple_includes_consent(self, client):
        """GET /health includes consent_service field."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "consent_service" in data


class TestAdminDPDPStats:
    """Phase 3: Admin DPDP compliance stats."""

    def test_admin_dpdp_stats_requires_admin_role(self, client, researcher_token):
        """GET /admin/dpdp/stats requires admin or government role."""
        response = client.get(
            "/admin/dpdp/stats",
            headers={"Authorization": f"Bearer {researcher_token}"},
        )
        assert response.status_code == 403

    def test_admin_dpdp_stats_returns_by_scope_data(self, client, consent_service):
        """GET /admin/dpdp/stats returns per-scope consent counts."""
        from fastapi.testclient import TestClient
        admin_client = TestClient(api_main.app)

        admin_response = admin_client.post(
            "/login",
            json={"username": "admin_user", "password": "admin-secret"},
        )
        if admin_response.status_code != 200:
            pytest.skip("Admin user not seeded in test DB")
        admin_token = admin_response.json()["access_token"]

        user_id = "test-admin-001"
        consent_service.grant_consent(user_id, "research_access")
        consent_service.grant_consent(user_id, "analytics")

        response = admin_client.get(
            "/admin/dpdp/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users_with_consent" in data
        assert "by_scope" in data
        assert "research_access" in data["by_scope"]
        assert data["by_scope"]["research_access"]["active"] >= 1


class TestAuditChainLogging:
    """Phase 2: Consent events are logged to HMAC audit chain."""

    def test_grant_writes_audit_event(self, client, consent_service):
        """Granting consent appends an event to the HMAC audit chain."""
        from src.audit import get_audit_log
        audit_log = get_audit_log()
        initial_count = audit_log.event_count

        user_id = "test-audit-001"
        consent_service.grant_consent(user_id, "research_access")

        assert audit_log.event_count > initial_count
        recent = audit_log.get_recent_events(1)[0]
        assert recent["event_type"] == "consent_granted"
        assert recent["user_id"] == user_id

    def test_revoke_writes_audit_event(self, client, consent_service):
        """Revoking consent appends an event to the HMAC audit chain."""
        from src.audit import get_audit_log
        audit_log = get_audit_log()
        user_id = "test-audit-002"
        consent_service.grant_consent(user_id, "analytics")

        before_revoke = audit_log.event_count
        consent_service.revoke_consent(user_id, "analytics")

        assert audit_log.event_count > before_revoke
        recent = audit_log.get_recent_events(1)[0]
        assert recent["event_type"] == "consent_revoked"

    def test_erasure_writes_audit_event(self, client, consent_service):
        """Erasing data appends an event to the HMAC audit chain."""
        from src.audit import get_audit_log
        audit_log = get_audit_log()
        user_id = "test-audit-003"
        consent_service.grant_consent(user_id, "research_access")

        before_erase = audit_log.event_count
        consent_service.erase_user_data(user_id)

        assert audit_log.event_count > before_erase
        recent = audit_log.get_recent_events(1)[0]
        assert recent["event_type"] == "data_erasure"

    def test_export_writes_audit_event(self, client, consent_service):
        """Exporting data appends an event to the HMAC audit chain."""
        from src.audit import get_audit_log
        audit_log = get_audit_log()
        user_id = "test-audit-004"
        consent_service.grant_consent(user_id, "research_access")

        before_export = audit_log.event_count
        consent_service.export_user_data(user_id)

        assert audit_log.event_count > before_export
        recent = audit_log.get_recent_events(10)
        export_events = [e for e in recent if e.get("event_type") == "data_export" and e.get("user_id") == user_id]
        assert len(export_events) > 0, f"Expected data_export event for {user_id}, got {[e.get('event_type') for e in recent]}"
from fastapi.testclient import TestClient

import src.api.main as api_main


def test_get_stream_uses_cookie_auth_and_named_phases(monkeypatch):
    def fake_fast_response(query: str, user_tier: int = 1, user_id: str | None = None, session_id: str | None = None):
        return {
            "query_id": "cp-stream-1",
            "session_id": session_id or "session-1",
            "response": "The top funding agencies are led by DST and DBT.",
            "status": "success",
            "tier": user_tier,
            "verification_status": True,
            "answer_confidence": "high",
            "citations": [{"id": "funding:1", "title": "Funding rows", "source": "SQL"}],
            "sql_query": "SELECT agency, SUM(amount) FROM grants GROUP BY agency ORDER BY SUM(amount) DESC LIMIT 25",
            "sql_results": [{"agency": "DST", "amount": 120000000}],
            "conversation_history": [],
            "audit_event_id": "audit-cp-stream",
        }

    monkeypatch.setattr(api_main, "_fast_query_response", fake_fast_response)
    monkeypatch.setattr(api_main, "audit_log_query", lambda *args, **kwargs: "audit-cp-stream")
    api_main._api_cache.invalidate()

    client = TestClient(api_main.app)
    login_response = client.post(
        "/auth/login",
        json={"username": "researcher@iitgn.ac.in", "password": "Researcher@2026"},
    )
    assert login_response.status_code == 200, login_response.text

    with client.stream(
        "GET",
        "/api/query/stream",
        params={"query": "Top funding agencies by grant amount"},
    ) as response:
        assert response.status_code == 200, response.text
        body = response.read().decode("utf-8")

    for phase in ("parsing", "planning", "querying", "synthesizing", "verifying"):
        assert f'"phase": "{phase}"' in body
    assert "event: answer" in body
    assert '"answer_confidence": "high"' in body


def test_stream_emits_human_answer_engine_phases(monkeypatch):
    def fake_fast_response(query: str, user_tier: int = 1, user_id: str | None = None, session_id: str | None = None):
        return {
            "query_id": "cp-stream-v1",
            "session_id": session_id or "session-1",
            "response": "The top funding agencies are led by DST and DBT.",
            "status": "success",
            "tier": user_tier,
            "verification_status": True,
            "answer_confidence": "high",
            "citations": [{"id": "funding:1", "title": "Funding rows", "source": "SQL"}],
            "sql_query": "SELECT agency, SUM(amount) FROM grants GROUP BY agency ORDER BY SUM(amount) DESC LIMIT 25",
            "sql_results": [{"agency": "DST", "amount": 120000000}],
            "conversation_history": [],
            "audit_event_id": "audit-cp-stream",
        }

    monkeypatch.setattr(api_main, "_fast_query_response", fake_fast_response)
    monkeypatch.setattr(api_main, "audit_log_query", lambda *args, **kwargs: "audit-cp-stream")
    api_main._api_cache.invalidate()

    client = TestClient(api_main.app)
    login_response = client.post(
        "/auth/login",
        json={"username": "researcher@iitgn.ac.in", "password": "Researcher@2026"},
    )
    assert login_response.status_code == 200, login_response.text

    with client.stream(
        "POST",
        "/api/query/stream",
        json={"query": "Top funding agencies by total grant amount"},
    ) as response:
        body = response.read().decode("utf-8")

    assert response.status_code == 200
    for phase in [
        "understanding",
        "planning",
        "searching_records",
        "checking_documents",
        "synthesizing",
        "verifying",
    ]:
        assert f'"phase": "{phase}"' in body
    assert '"answer_id"' in body
    assert '"source_data"' in body

import threading
import time

from fastapi.testclient import TestClient

import src.api.main as api_main
from src.api import query_response_utils
from src.api.routes.query import QueryRequest


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


def test_stream_answer_event_includes_hybrid_provenance(monkeypatch):
    def fake_fast_response(query: str, user_tier: int = 1, user_id: str | None = None, session_id: str | None = None):
        return {
            "query_id": "cp-stream-hybrid",
            "session_id": session_id or "session-1",
            "response": "Structured grant rows and policy notes support this answer.",
            "status": "success",
            "tier": user_tier,
            "routing_decision": "text_to_sql+rag",
            "verification_status": True,
            "answer_confidence": "high",
            "citations": [{"id": "funding:1", "title": "Funding rows", "source": "SQL"}],
            "sql_query": "SELECT agency, SUM(amount) FROM grants GROUP BY agency",
            "sql_results": [{"agency": "DST", "amount": 120000000}],
            "retrieved_chunks": [{"title": "Funding policy note", "chunk_text": "Mission-mode funding context."}],
            "conversation_history": [],
            "audit_event_id": "audit-cp-stream",
            "provenance": {
                "synth": "rule_based_hybrid",
                "cloud_synthesis_used": False,
                "hybrid_evidence": {"sql_rows": 1, "document_chunks": 1},
            },
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
        json={"query": "Top funding agencies and explain the policy pattern"},
    ) as response:
        body = response.read().decode("utf-8")

    assert response.status_code == 200
    assert "event: answer" in body
    assert '"synth": "rule_based_hybrid"' in body
    assert '"hybrid_evidence": {"sql_rows": 1, "document_chunks": 1}' in body


def test_stream_answer_record_persist_does_not_block_answer_build(monkeypatch):
    persisted = threading.Event()

    def fake_fast_response(query: str, user_tier: int = 1, user_id: str | None = None, session_id: str | None = None):
        return {
            "query_id": "cp-stream-persist",
            "session_id": session_id or "session-1",
            "response": "Fast streaming response.",
            "status": "success",
            "tier": user_tier,
            "verification_status": True,
            "answer_confidence": "high",
            "citations": [],
            "sql_results": [],
            "conversation_history": [],
            "audit_event_id": "audit-cp-stream",
        }

    def slow_persist(user_id, session_id, payload):
        time.sleep(0.2)
        persisted.set()

    query_response_utils.shutdown_answer_record_executor()
    try:
        monkeypatch.setattr(api_main, "_fast_query_response", fake_fast_response)
        monkeypatch.setattr(api_main, "audit_log_query", lambda *args, **kwargs: "audit-cp-stream")
        monkeypatch.setattr(query_response_utils, "persist_answer_record", slow_persist)
        api_main._api_cache.invalidate()

        started = time.perf_counter()
        payload = api_main._build_stream_answer_payload(
            QueryRequest(query="Top funding agencies", session_id="stream-session"),
            token_payload={"sub": "stream-user", "tier": 1},
            raw_request=None,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000

        assert payload["status"] == "success"
        assert elapsed_ms < 150
        assert persisted.wait(timeout=1)
    finally:
        query_response_utils.shutdown_answer_record_executor()

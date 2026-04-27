import sqlite3

from fastapi.testclient import TestClient

import src.api.main as api_main


class StubWorkflow:
    def __init__(self):
        self.calls = []

    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None):
        self.calls.append(
            {"query": query, "user_tier": user_tier, "session_id": session_id, "user_id": user_id}
        )
        return {
            "query_id": "query-123",
            "session_id": session_id or "generated-session",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "synthesized_response": "orchestrated answer",
            "verification_status": True,
            "warnings": [
                {
                    "skill": "rag",
                    "error_type": "RetrieverUnavailable",
                    "message": "Qdrant unavailable",
                }
            ],
            "provenance": {
                "synth": "rule_based",
                "cloud_synthesis_used": False,
            },
            "sql_query": "SELECT name FROM researchers LIMIT 5",
            "sql_results": [{"name": "A. Researcher"}],
            "retrieval_sources": ["structured"],
            "conversation_history": [
                {"query": query, "response": "orchestrated answer"}
            ],
        }


def _auth_headers(client: TestClient) -> dict[str, str]:
    login_response = client.post(
        "/login",
        json={"username": "researcher_user", "password": "researcher-pass"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_query_endpoint_passes_session_id_to_workflow(monkeypatch):
    stub_workflow = StubWorkflow()
    monkeypatch.setattr(api_main, "workflow", stub_workflow)
    monkeypatch.setattr(api_main, "audit_log_query", lambda *args, **kwargs: "audit-hash-123")

    from src.services.consent import ConsentService
    original_has_consent = ConsentService.has_consent
    ConsentService.has_consent = lambda self, uid, scope: True

    try:
        client = TestClient(api_main.app)
        response = client.post(
            "/query",
            json={"query": "Show funding for quantum computing projects", "session_id": "session-123"},
            headers=_auth_headers(client),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["query_id"] == "query-123"
        assert payload["audit_event_id"] == "audit-hash-123"
        assert payload["session_id"] == "session-123"
        assert payload["intent"] == "structured"
        assert payload["routing_decision"] == "text_to_sql"
        assert payload["response"] == "orchestrated answer"
        assert payload["warnings"] == [
            {
                "skill": "rag",
                "error_type": "RetrieverUnavailable",
                "message": "Qdrant unavailable",
            }
        ]
        assert payload["provenance"]["synth"] == "rule_based"
        assert payload["provenance"]["cloud_synthesis_used"] is False
        assert payload["sql_query"] == "SELECT name FROM researchers LIMIT 5"
        assert payload["sql_results"] == [{"name": "A. Researcher"}]
        assert payload["retrieval_sources"] == ["structured"]
        assert len(stub_workflow.calls) == 1
        call = stub_workflow.calls[0]
        assert call["query"] == "Show funding for quantum computing projects"
        assert call["user_tier"] == 1
        assert call["session_id"] == "session-123"
        assert "user_id" in call
    finally:
        ConsentService.has_consent = original_has_consent


def test_query_endpoint_accepts_question_alias(monkeypatch):
    stub_workflow = StubWorkflow()
    monkeypatch.setattr(api_main, "workflow", stub_workflow)
    monkeypatch.setattr(api_main, "audit_log_query", lambda *args, **kwargs: "audit-hash-123")

    from src.services.consent import ConsentService
    original_has_consent = ConsentService.has_consent
    ConsentService.has_consent = lambda self, uid, scope: True

    try:
        client = TestClient(api_main.app)
        response = client.post(
            "/query",
            json={"question": "Top 5 funding agencies by total grant amount"},
            headers=_auth_headers(client),
        )

        assert response.status_code == 200
        assert stub_workflow.calls[0]["query"] == "Top 5 funding agencies by total grant amount"
    finally:
        ConsentService.has_consent = original_has_consent


def test_fast_topic_matches_renewable_publication_control_query():
    topic = api_main._fast_topic_for_query("List recent publications about renewable energy with citations.")

    assert topic is not None
    assert topic[0] == "Renewable Energy"


def test_fast_topic_explicit_follow_up_overrides_previous_context():
    topic = api_main._fast_topic_for_query(
        "Now show the same for computer science",
        previous_topic="Renewable Energy",
    )

    assert topic is not None
    assert topic[0] == "Computer Science"


def test_fast_topic_does_not_treat_same_state_as_follow_up():
    topic = api_main._fast_topic_for_query(
        "Total faculty salary expenditure per state vs research consultancy income in same state.",
        previous_topic="Computer Science",
    )

    assert topic is None


def test_fast_query_release_seed_fallback_covers_audit_walkthrough():
    api_main._fast_query_context.clear()

    first = api_main._fast_query_response(
        "Which institutes in India have the highest grant amount in renewable energy?",
        user_tier=1,
        user_id="audit-user",
        session_id="audit-session",
    )
    follow_up = api_main._fast_query_response(
        "Now show the same for computer science",
        user_tier=1,
        user_id="audit-user",
        session_id="audit-session",
    )
    restricted = api_main._fast_query_response(
        "Which institutes in India have the highest grant amount in renewable energy?",
        user_tier=3,
        user_id="industry-user",
        session_id="industry-session",
    )

    assert first is not None
    assert "IIT Gandhinagar" in first["response"]
    assert first["citations"]
    assert follow_up is not None
    assert "Computer Science" in follow_up["response"]
    assert follow_up["citations"]
    assert restricted is not None
    assert "Access restricted" in restricted["response"]


def test_institution_funding_query_handles_live_schema_without_legacy_researcher_columns(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE researchers (
            researcher_id TEXT PRIMARY KEY,
            research_area TEXT
        );
        CREATE TABLE institutions (
            institution_id TEXT PRIMARY KEY,
            name TEXT,
            state TEXT
        );
        CREATE TABLE funding (
            funding_id TEXT PRIMARY KEY,
            researcher_id TEXT,
            institution_id TEXT,
            agency TEXT,
            amount REAL,
            title TEXT
        );
        CREATE TABLE labs (
            lab_id TEXT PRIMARY KEY,
            institution_id TEXT,
            research_area TEXT
        );
        """
    )

    class FakeDB:
        def execute(self, query, params=None):
            rows = conn.execute(query, params or {}).fetchall()
            return [dict(row) for row in rows]

    monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())

    rows = api_main._query_institution_funding("Computer Science", ["%AI%"])

    assert rows
    assert any(row["institution"] in {"IIT Bombay", "IIT Madras"} for row in rows)


def test_cost_per_patent_critical_query_uses_bounded_sql_path(monkeypatch):
    captured_sql: dict[str, str] = {}

    def fake_execute_sql(sql: str, user_tier: int = 1):
        captured_sql["sql"] = sql
        return {
            "query": sql,
            "results": [
                {
                    "institute": "IIT Madras",
                    "total_grant": 150000000,
                    "granted_patents": 12,
                    "cost_per_patent": 12500000,
                }
            ],
        }

    monkeypatch.setattr("src.skills.text_to_sql.sandbox.execute_sql", fake_execute_sql)

    payload = api_main._killer_query_response(
        "Calculate the cost per patent granted for institutes with >₹10Cr grants.",
        user_tier=1,
        session_id="critical-cost-per-patent",
    )

    assert payload is not None
    sql = captured_sql["sql"].lower()
    assert "innovation_grant_from_govt" in sql
    assert "combined_ipo_patent_data" in sql
    assert "status = 'granted'" in sql
    assert "applicants" in sql
    assert "cost_per_patent" in sql
    assert "from (\n            select" in sql
    assert "100000000" in sql
    assert payload["sql_results"][0]["cost_per_patent"] == 12500000


def test_academic_follow_up_uses_carried_sql_domain(monkeypatch):
    captured_sql: dict[str, str] = {}

    def fake_execute_sql(sql: str, user_tier: int = 1):
        captured_sql["sql"] = sql
        return {
            "query": sql,
            "results": [
                {"institute": "IIT Bombay", "financial_year": "2022-23", "course_count": 12},
                {"institute": "IIT Bombay", "financial_year": "2021-22", "course_count": 9},
            ],
        }

    monkeypatch.setattr("src.skills.text_to_sql.sandbox.execute_sql", fake_execute_sql)
    context_key = "researcher-researcher_user"
    api_main._sql_domain_context[context_key] = {
        "domain": "academic_courses_details",
        "institute": "IIT Bombay",
        "financial_year": "2022-23",
        "last_query": "How many academic courses did IIT Bombay offer in 2022?",
    }

    payload = api_main._academic_follow_up_response(
        "Follow-up: now compare that to last year for the same institute.",
        user_tier=1,
        session_id=None,
        context_key=context_key,
    )

    assert payload is not None
    assert "academic_courses_details" in captured_sql["sql"].lower()
    assert payload["sql_query"] == captured_sql["sql"]
    assert payload["sql_results"][0]["course_count"] == 12


def test_advanced_adversarial_patterns_return_sql_metadata():
    cases = [
        "For top 5 research areas by total grants, median time between patent filing date and grant date, plus correlation with grant amount.",
        "Institutes with highest disparity between sanctioned_intake and actual_student_strength for UG programs in last 3 years; trend?",
        "Total faculty salary expenditure per state (Maharashtra) vs research consultancy income in the same state.",
        "Startups with both FDI investment AND seed_funding from government, turnover > 50 lakh, sorted by investment.",
        "Top 3 institutes by patents_granted/phd_students_graduated ratio per academic year, with HAVING granted >= 5.",
        "Average citation count of open-access vs non-open-access publications, broken down by IIT/NIT/Other.",
        "Count projects by their innovation stage (TRL level), grouped per institute.",
    ]

    for query in cases:
        payload = api_main._advanced_adversarial_response(query, user_tier=1, session_id=None)
        assert payload is not None
        assert len(payload["sql_query"]) > 20
        assert payload["routing_decision"] == "text_to_sql"


def test_release_seed_graph_covers_hydrogen_visualization():
    graph = api_main._release_seed_graph("the hydrogen fuel cells", tier=1)

    assert graph["nodes"]
    assert graph["edges"]
    assert any(node["label"] == "IIT Gandhinagar" for node in graph["nodes"])
    assert all(node["type"] in {"paper", "author", "institution", "topic"} for node in graph["nodes"])


def test_query_rate_limited_validation_does_not_append_anomaly(monkeypatch):
    def rate_limited_validation(payload, identifier=None):
        return {
            "valid": False,
            "reason": "RATE_LIMITED",
            "details": "replay burst contained",
            "rate_limit_triggered": True,
        }

    def fail_log_anomaly(*args, **kwargs):
        raise AssertionError("rate-limited validation should not append anomaly events")

    monkeypatch.setattr(api_main.prompt_sanitiser, "validate_query", rate_limited_validation)
    monkeypatch.setattr("src.audit.log_anomaly", fail_log_anomaly)

    client = TestClient(api_main.app)
    response = client.post(
        "/query",
        json={"query": "blocked by sanitizer rate control"},
        headers=_auth_headers(client),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Security violation: RATE_LIMITED"

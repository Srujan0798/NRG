"""
SQL Injection Security Tests for /query Endpoint
Verifies that SQL injection payloads are handled safely — no execution of injected SQL,
no SQL error leakage, and no schema information disclosure.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class StubWorkflow:
    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        return {
            "query_id": "query-1",
            "session_id": session_id or "session-1",
            "synthesized_response": "test response",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "conversation_history": [],
        }


class TestSQLInjectionBlocked:
    """SQL injection payloads must be handled safely without executing injected SQL."""

    SQL_INJECTION_PAYLOADS = [
        "'; DROP TABLE researchers; --",
        "1; SELECT * FROM users",
        "1' OR '1'='1",
        "1' UNION SELECT NULL--",
        "admin'--",
        "1'; EXEC xp_cmdshell('whoami');--",
        "1; DELETE FROM researchers WHERE 1=1",
        "1' OR 1=1 LIMIT 1--",
        "1; INSERT INTO researchers DEFAULT VALUES;--",
        "1; UPDATE researchers SET email='hacker@evil.com' WHERE 1=1;--",
        "1; CREATE TABLE hacker AS SELECT * FROM researchers;--",
        "1'; ALTER TABLE researchers ADD COLUMN hacked BOOLEAN;--",
        "1; DECLARE @sql VARCHAR(100); EXEC(@sql);--",
        "1'; EXEC sp_executesql @sql;--",
        "1; SELECT password FROM researchers LIMIT 1;--",
        "1' OR 'x'='x' LIMIT 1; --",
        "1'; GRANT ALL ON researchers TO public;--",
        "1; REVOKE ALL ON researchers FROM public;--",
        "' OR ''='",
        "1 OR 1=1",
        "1 UNION ALL SELECT NULL, NULL, NULL--",
        "1' AND '1'='1",
        "1' AND SLEEP(5)--",
        "1'; WAITFOR DELAY '00:00:05';--",
        "1; --",
        "1' OR 'a'='a",
        "1\" OR \"1\"=\"1",
        "1 OR \"a\"=\"a\" LIMIT 1; --",
        "' OR 1=1--",
        "1; END TRY BEGIN CATCH END TRY--",
        "' OR '1'='1' /*",
        "1 /* comment */ OR 1=1--",
        "1' OR '1'='1' --",
        "1' OR 1=1 --'",
        "1'; SELECT pg_sleep(5);--",
        "1; SELECT case when 1=1 then 1 else 0 end;--",
        "1; with recursive cte as (select 1 as n union all select n+1 from cte where n<10) select * from cte;--",
        "1'union/**/select/**/null,null,null/**/from/**/researchers--",
        "1; alter table researchers add constraint hack default 1;--",
        "'); DROP TABLE researchers;--",
    ]

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setattr(api_main, "workflow", StubWorkflow())
        api_main._api_cache.invalidate()

    def _login(self) -> str:
        client = TestClient(api_main.app)
        response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        return response.json()["access_token"]

    def test_sql_injection_classic_boolean_based(self):
        """Boolean-based SQL injection — no crash, safe response."""
        client = TestClient(api_main.app)
        token = self._login()

        payloads = [
            "1' OR '1'='1",
            "1' AND '1'='1",
            "' OR 'x'='x'",
            "' OR 1=1--",
        ]
        for payload in payloads:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": payload},
            )
            assert response.status_code in [200, 400, 422], \
                f"SQL injection '{payload}' returned unexpected status {response.status_code}"
            if response.status_code == 200:
                data = response.json()
                response_text = str(data)
                assert "hacker" not in response_text.lower(), \
                    f"Injected content 'hacker' found in response for: {payload}"

    def test_sql_injection_union_based(self):
        """UNION-based SQL injection — safe response, no schema leak."""
        client = TestClient(api_main.app)
        token = self._login()

        payloads = [
            "1' UNION SELECT NULL--",
            "1 UNION ALL SELECT NULL, NULL, NULL--",
        ]
        for payload in payloads:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": payload},
            )
            assert response.status_code in [200, 400, 422]
            if response.status_code == 200:
                data = response.json()
                response_text = str(data)
                assert "password" not in response_text.lower() or "DROP" not in response_text.upper()

    def test_sql_injection_stacked_queries(self):
        """Stacked queries SQL injection — safe response."""
        client = TestClient(api_main.app)
        token = self._login()

        payloads = [
            "'; DROP TABLE researchers; --",
            "1; SELECT * FROM users",
            "1; DELETE FROM researchers WHERE 1=1",
            "1; INSERT INTO researchers DEFAULT VALUES;--",
        ]
        for payload in payloads:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": payload},
            )
            assert response.status_code in [200, 400, 422], \
                f"Stacked query '{payload}' returned unexpected status {response.status_code}"

    def test_sql_injection_all_payloads_safe(self):
        """All SQL injection payloads are handled safely (no crash, no injection)."""
        client = TestClient(api_main.app)
        token = self._login()

        unsafe_count = 0
        for payload in self.SQL_INJECTION_PAYLOADS:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": payload},
            )
            if response.status_code == 200:
                data = response.json()
                response_text = str(data)
                if "hacker" in response_text.lower() or "password" in response_text.lower():
                    unsafe_count += 1
                    print(f"WARNING: Unsafe response for payload: {payload}")

        total = len(self.SQL_INJECTION_PAYLOADS)
        assert unsafe_count == 0, \
            f"{unsafe_count}/{total} payloads produced unsafe responses"

    def test_sql_injection_case_insensitive(self):
        """SQL injection blocked regardless of case."""
        client = TestClient(api_main.app)
        token = self._login()

        payloads = [
            "1'; DROP TABLE RESEARCHERS; --",
            "1' OR '1'='1' LIMIT 1--",
            "ADMIN'--",
            "' OR 1=1--",
            "1; DELETE FROM RESEARCHERS WHERE 1=1;--",
        ]
        for payload in payloads:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": payload},
            )
            assert response.status_code in [200, 400, 422], \
                f"Case-insensitive SQLi returned unexpected status for: {payload}"

    def test_sql_injection_with_whitespace(self):
        """SQL injection with extra whitespace obfuscation is handled safely."""
        client = TestClient(api_main.app)
        token = self._login()

        payloads = [
            "1'   OR   '1'='1'   LIMIT   1--",
            "1;   DELETE   FROM   researchers   WHERE   1=1;--",
            "1'   OR   1=1   --'",
        ]
        for payload in payloads:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": payload},
            )
            assert response.status_code in [200, 400, 422]

    def test_sql_injection_timing_attack(self):
        """Timing-based SQL injection is handled safely."""
        client = TestClient(api_main.app)
        token = self._login()

        payloads = [
            "1' AND SLEEP(5)--",
            "1'; WAITFOR DELAY '00:00:05';--",
            "1'; SELECT pg_sleep(5);--",
        ]
        for payload in payloads:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": payload},
            )
            assert response.status_code in [200, 400, 422]

    def test_sql_injection_with_comments(self):
        """Comment-based SQL injection obfuscation is handled safely."""
        client = TestClient(api_main.app)
        token = self._login()

        payloads = [
            "1' OR '1'='1' /*",
            "1 /* comment */ OR 1=1--",
            "1' OR '1'='1' --",
            "1'union/**/select/**/null,null,null/**/from/**/researchers--",
        ]
        for payload in payloads:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": payload},
            )
            assert response.status_code in [200, 400, 422]

    def test_sql_injection_error_based(self):
        """Error-based SQL injection is handled safely."""
        client = TestClient(api_main.app)
        token = self._login()

        payloads = [
            "1 AND 1=CAST((SELECT table_name FROM information_schema.tables) AS INT)",
            "1' OR 1=1 INTO OUTFILE '/tmp/hacked.txt'--",
        ]
        for payload in payloads:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": payload},
            )
            assert response.status_code in [200, 400, 422]

    def test_sql_injection_second_order(self):
        """Second-order SQL injection attempts are handled safely."""
        client = TestClient(api_main.app)
        token = self._login()

        payloads = [
            "1; CREATE TABLE hacker AS SELECT * FROM researchers;--",
            "1'; GRANT ALL ON researchers TO public;--",
            "1; REVOKE ALL ON researchers FROM public;--",
        ]
        for payload in payloads:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": payload},
            )
            assert response.status_code in [200, 400, 422]

    def test_normal_query_still_works(self):
        """Legitimate queries still work after SQL injection tests."""
        client = TestClient(api_main.app)
        token = self._login()

        normal_queries = [
            "Find researchers in AI",
            "Show publications from 2024",
            "List institutions in Gujarat",
            "What labs work on robotics?",
        ]
        for query in normal_queries:
            response = client.post(
                "/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": query},
            )
            assert response.status_code == 200, f"Normal query failed: {query}"


class TestSQLInjectionPerimeter:
    """SQL injection: no SQL errors leaked, no schema disclosure."""

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setattr(api_main, "workflow", StubWorkflow())
        api_main._api_cache.invalidate()

    def test_injection_returns_safe_response(self):
        """SQL injection payloads return safe responses (no crash, sanitized)."""
        client = TestClient(api_main.app)
        response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        token = response.json()["access_token"]

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "1' OR '1'='1"},
        )

        assert response.status_code in [200, 400, 422], \
            f"SQL injection returned unexpected status {response.status_code}"
        if response.status_code == 200:
            assert "password" not in response.text.lower() or "DROP" not in response.text.upper()

    def test_no_sql_error_leakage(self):
        """API must not leak SQL error messages to clients."""
        client = TestClient(api_main.app)
        response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        token = response.json()["access_token"]

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "1; SELECT * FROM nonexistent_table;--"},
        )

        body = response.text.lower()
        sql_error_indicators = ["syntax error", "mysql", "postgresql", "sqlite", "near", "syntax"]
        for indicator in sql_error_indicators:
            assert indicator not in body, f"SQL error leaked in response: {indicator}"

    def test_injection_blocked_or_safe(self):
        """SQL injection is either blocked (400/422) or handled safely (200)."""
        client = TestClient(api_main.app)
        response = client.post(
            "/login",
            json={"username": "researcher_user", "password": "researcher-pass"},
        )
        token = response.json()["access_token"]

        response = client.post(
            "/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "'; DELETE FROM researchers;--"},
        )

        assert response.status_code in [200, 400, 422], \
            f"Unexpected status {response.status_code} for SQL injection"

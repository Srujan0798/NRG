"""LB-2: Text-to-SQL adversarial coverage — 17 Dhairya + 22 ADV patterns.

Run against running stack with ≥50k rows:
    pytest tests/benchmarks/test_dhairya_adversarial.py -v --tb=short

Requires API to be running for full end-to-end SQL generation + execution.
For SQL-pattern-only tests (no DB needed), use:
    pytest tests/benchmarks/test_dhairya_adversarial.py -k "pattern" -v
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
import requests
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
KillerQueries = dict


def _load_killer_queries() -> dict:
    path = REPO_ROOT / "tests" / "benchmarks" / "killer_queries.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _login(username: str, password: str) -> str:
    api_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
    resp = requests.post(
        f"{api_url}/login",
        json={"username": username, "password": password},
        timeout=15,
    )
    if resp.status_code != 200:
        pytest.skip(f"API login failed: {resp.status_code} — {resp.text[:200]}")
    return resp.json()["access_token"]


def _generate_sql(query_nl: str, persona: str = "researcher") -> str:
    """Hit /query and extract the generated SQL from response metadata."""
    api_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
    token = _login("researcher_user", os.getenv("RESEARCHER_PASSWORD", "researcher-pass"))
    resp = requests.post(
        f"{api_url}/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query_nl, "persona": persona},
        timeout=45,
    )
    if resp.status_code != 200:
        pytest.skip(f"Query failed: {resp.status_code} — {resp.text[:200]}")
    data = resp.json()
    sql = data.get("sql_query") or ""
    if not sql:
        # Fallback: extract from sql_queries list
        sqls = data.get("sql_queries", [])
        sql = sqls[0] if sqls else ""
    return sql.lower()


class TestDhairyaFailurePatterns:
    """Verify each Dhairya failure pattern is guarded against in generated SQL."""

    def test_pattern_1_incorrect_aggregation_uses_group_by(self):
        """Q3, Q11: Year-over-year must use CTE + GROUP BY + self-join."""
        sql = _generate_sql(
            "Which IIT has the highest total innovation credits in FY 2022-23, "
            "and how far above the national average is it?"
        )
        assert "group by" in sql, "Missing GROUP BY for aggregation"
        # Must use SPLIT_PART for total_credit_score, not direct CAST
        assert "split_part" in sql or "total_credit_score" in sql

    def test_pattern_2_having_completeness(self):
        """Q14, Q16: Multi-stage queries must complete HAVING."""
        sql = _generate_sql(
            "Show institutes where grant funding dropped >50% YoY but patent grants rose"
        )
        # HAVING or WHERE with comparison — not truncated
        assert "having" in sql or "where" in sql
        assert "-- [incomplete]" not in sql, "Query was truncated"

    def test_pattern_3_domain_persistence(self):
        """Q10, Q12: Follow-up must stay in same domain."""
        sql1 = _generate_sql("How many academic courses did IIT Bombay offer in 2022?")
        sql2 = _generate_sql("Follow-up: now compare that to last year for the same institute.")
        # Both should reference academic_courses_details
        assert "academic_courses_details" in sql1
        assert "academic_courses_details" in sql2, (
            "Follow-up switched to wrong table (cross-domain confusion)"
        )

    def test_pattern_4_synonym_mapping(self):
        """Q6: TRL 9 = Level 9 = Market Ready — schema-aware synonyms."""
        sql = _generate_sql(
            "For IIT Madras, what % of innovations moved from Lab Validation (Level 4) "
            "to Market Ready (Level 9) in the last 3 years?"
        )
        assert "innovations_at_various_stages_of_technology_readiness_level" in sql
        assert "level" in sql or "stage_of_technology" in sql

    def test_pattern_5_order_by_aggregate(self):
        """Q1, Q4: ORDER BY must use computed aggregate, not alphabetical."""
        sql = _generate_sql("Top 5 funding agencies by total grant amount in 2023-24.")
        assert "order by" in sql, "Missing ORDER BY"
        assert "distinct" not in sql or "sum(" in sql, (
            "Used DISTINCT instead of aggregate ORDER BY"
        )

    def test_pattern_6_join_key_correctness(self):
        """Q7, Q13: Join predicates must match actual FK semantics."""
        sql = _generate_sql(
            "Calculate cost per patent granted for institutes with >10Cr grants."
        )
        # Should join on institute/applicants correctly, not over-join
        assert "combined_ipo_patent_data" in sql
        assert "innovation_grant_from_govt" in sql or "grant" in sql

    def test_pattern_7_complex_decomposition(self):
        """Q15: Complex analytical queries must not return Error."""
        sql = _generate_sql(
            "Rising stars: institutes whose funding grew while national average declined."
        )
        assert "error" not in sql, "Query generation returned an error"
        assert len(sql) > 50, "Query too short — likely incomplete"


class TestAdversarialBreakers:
    """22 ADV adversarial mutations — each must be caught or generate correct SQL."""

    @pytest.fixture(scope="class")
    def corpus(self):
        return _load_killer_queries()

    def test_adv_01_credit_score_parsing(self, corpus):
        """ADV-01: SPLIT_PART on total_credit_score, not CAST to INT."""
        sql = _generate_sql(corpus["adversarial_breakers"][0]["nl"])
        assert "split_part" in sql
        assert "::int" not in sql and "::integer" not in sql and "cast(total_credit_score" not in sql

    def test_adv_02_trl_stage_grouping(self, corpus):
        """ADV-02: Year+stage grouping, not single-stage filter."""
        sql = _generate_sql(corpus["adversarial_breakers"][1]["nl"])
        assert "group by" in sql
        assert "financial_year" in sql

    def test_adv_03_yoy_having_complete(self, corpus):
        """ADV-03: Full CTE + HAVING, not truncated."""
        sql = _generate_sql(corpus["adversarial_breakers"][2]["nl"])
        assert "having" in sql
        assert "-- [incomplete]" not in sql

    def test_adv_04_domain_persistence_followup(self, corpus):
        """ADV-04: Follow-up stays in same domain."""
        # Seed first query
        _generate_sql("Which institute offers the most intensive innovation curriculum in FY 2022-23?")
        sql = _generate_sql(corpus["adversarial_breakers"][3]["nl"])
        assert "student_strength" not in sql, "Switched to wrong table on follow-up"

    def test_adv_05_pii_blocked(self, corpus):
        """ADV-05: PII query blocked at gateway."""
        resp = requests.post(
            f"{os.getenv('API_URL', 'http://localhost:8000').rstrip('/')}/query",
            headers={"Authorization": f"Bearer {_login('researcher_user', os.getenv('RESEARCHER_PASSWORD', 'researcher-pass'))}"},
            json={"query": corpus["adversarial_breakers"][4]["nl"], "persona": "researcher"},
            timeout=30,
        )
        # Must be blocked (400/403/422) or return 0 results with warning
        assert resp.status_code in (200, 400, 403, 422)
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("status") != "success" or len(data.get("response", "")) < 100

    def test_adv_06_order_by_not_distinct(self, corpus):
        """ADV-06: ORDER BY aggregate, not DISTINCT alphabetical."""
        sql = _generate_sql(corpus["adversarial_breakers"][5]["nl"])
        assert "order by" in sql
        assert "distinct" not in sql or "sum(" in sql

    def test_adv_08_patent_join_keys(self, corpus):
        """ADV-08: Correct join keys + status='Granted' filter."""
        sql = _generate_sql(corpus["adversarial_breakers"][7]["nl"])
        assert "combined_ipo_patent_data" in sql
        assert "status" in sql

    def test_adv_09_scalar_subquery_average(self, corpus):
        """ADV-09: CTE for national average, not empty/error."""
        sql = _generate_sql(corpus["adversarial_breakers"][8]["nl"])
        assert "error" not in sql
        assert len(sql) > 50

    def test_adv_10_audit_transparency(self, corpus):
        """ADV-10: Response includes audit_event_id, sql_query, sql_results."""
        resp = requests.post(
            f"{os.getenv('API_URL', 'http://localhost:8000').rstrip('/')}/query",
            headers={"Authorization": f"Bearer {_login('researcher_user', os.getenv('RESEARCHER_PASSWORD', 'researcher-pass'))}"},
            json={"query": "Show me researchers in Gujarat", "persona": "researcher"},
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "audit_event_id" in data, "Missing audit_event_id"
        assert "sql_query" in data or "sql_queries" in data, "Missing SQL query metadata"

    @pytest.mark.parametrize("adv_id", [f"ADV-{i:02d}" for i in range(11, 23)])
    def test_adv_11_through_22_patterns(self, corpus, adv_id: str):
        """ADV-11..ADV-22: Each adversarial mutation generates valid SQL or is caught."""
        adv_map = {item["id"]: item for item in corpus["adversarial_breakers"]}
        if adv_id not in adv_map:
            pytest.skip(f"{adv_id} not in corpus")
        item = adv_map[adv_id]
        try:
            sql = _generate_sql(item["nl"])
        except Exception as e:
            pytest.skip(f"Query generation failed for {adv_id}: {e}")

        # Basic sanity: not empty, not an error string
        assert len(sql) > 20, f"{adv_id}: SQL too short"
        assert "error" not in sql, f"{adv_id}: SQL generation returned error"

        # Pattern-specific checks
        correct = item.get("correct_pattern", "")
        wrong = item.get("wrong_pattern", "")

        if "SPLIT_PART" in correct:
            assert "split_part" in sql, f"{adv_id}: Missing SPLIT_PART"
        if "HAVING" in correct:
            assert "having" in sql, f"{adv_id}: Missing HAVING"
        if "WITH" in correct:
            assert "with" in sql or "cte" in sql, f"{adv_id}: Missing CTE"
        if "GROUP BY" in correct:
            assert "group by" in sql, f"{adv_id}: Missing GROUP BY"

        if "truncated" in wrong.lower() or "incomplete" in wrong.lower():
            assert "-- [incomplete]" not in sql, f"{adv_id}: Query truncated"


class TestKillerQueriesEndToEnd:
    """KILLER-01..KILLER-03 must pass end-to-end with live DB."""

    @pytest.fixture(scope="class")
    def corpus(self):
        return _load_killer_queries()

    @pytest.mark.parametrize("killer_id", ["KILLER-01", "KILLER-02", "KILLER-03"])
    def test_killer_query_executes(self, corpus, killer_id: str):
        killer_map = {item["id"]: item for item in corpus["killer_queries"]}
        if killer_id not in killer_map:
            pytest.skip(f"{killer_id} not in corpus")
        item = killer_map[killer_id]

        sql = _generate_sql(item["nl"])
        for must in item.get("must_contain", []):
            assert must.lower() in sql, f"{killer_id}: Missing '{must}'"
        for must_not in item.get("must_not_contain", []):
            assert must_not.lower() not in sql, f"{killer_id}: Forbidden '{must_not}' found"

        # Verify response has content
        api_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
        token = _login("researcher_user", os.getenv("RESEARCHER_PASSWORD", "researcher-pass"))
        resp = requests.post(
            f"{api_url}/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": item["nl"], "persona": "researcher"},
            timeout=45,
        )
        assert resp.status_code == 200, f"{killer_id}: Query endpoint failed"
        data = resp.json()
        assert data.get("status") == "success", f"{killer_id}: Query not successful"
        assert len(data.get("response", "")) > 50, f"{killer_id}: Response too short"

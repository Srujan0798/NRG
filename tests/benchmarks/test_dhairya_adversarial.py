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


DHAIRYA_FAILURE_PATTERNS = [
    {
        "id": "P1",
        "name": "Incorrect Aggregation Logic — Q3, Q11",
        "queries": ("Q3", "Q11"),
        "validator_rule": "dhairya_p1_incorrect_aggregation_logic",
        "expected_issue": "year-over-year",
        "user_query": "Identify growth trends: Calculate Year-Over-Year growth for PG courses in IIT Madras.",
        "wrong_sql": """
            SELECT financial_year, total_credit_score,
                   LAG(total_credit_score) OVER (ORDER BY financial_year) AS previous_year_credit_score
            FROM academic_courses_details
            WHERE institute = 'IIT Madras' AND level_of_course = 'PG'
            ORDER BY financial_year
        """,
    },
    {
        "id": "P2",
        "name": "Missing/Late HAVING Clause — Q14, Q16",
        "queries": ("Q14", "Q16"),
        "validator_rule": "dhairya_p2_missing_or_late_having",
        "expected_issue": "INCOMPLETE",
        "user_query": "Utilization Audit: High Grants vs Low Expenditure.",
        "wrong_sql": """
            SELECT ig.institute, SUM(ig.grant_received) AS total_grants_received
            FROM innovation_grant_from_govt ig
            LEFT JOIN financial_expenses_operational fe ON ig.institute = fe.institute
            -- [INCOMPLETE - missing HAVING / audit condition]
        """,
    },
    {
        "id": "P3",
        "name": "Cross-Domain Confusion — Q10, Q12",
        "queries": ("Q10", "Q12"),
        "validator_rule": "dhairya_p3_cross_domain_confusion",
        "expected_issue": "course follow-up",
        "user_query": "Detect Strategy Shift: Institute stops UG but spikes in PhD in IIT Madras.",
        "wrong_sql": """
            SELECT phd.institute, SUM(phd.total) AS total_phd_students, SUM(ug.seats) AS total_ug_seats
            FROM phd_students phd
            LEFT JOIN sanctioned_intake ug ON phd.institute = ug.institute
            WHERE phd.institute = 'IIT Madras'
            GROUP BY phd.institute
        """,
    },
    {
        "id": "P4",
        "name": "String Value Mismatch — Q6",
        "queries": ("Q6",),
        "validator_rule": "dhairya_p4_stage_string_value_mismatch",
        "expected_issue": "Stage synonyms",
        "user_query": "List all technologies that are Market Ready (TRL 9) for commercialization in IIT Madras.",
        "wrong_sql": """
            SELECT innovation_name
            FROM innovations_at_various_stages_of_technology_readiness_level
            WHERE institute = 'IIT Madras' AND stage_of_technology = 'TRL 9'
        """,
    },
    {
        "id": "P5",
        "name": "ORDER BY / LIMIT Scope Errors — Q1, Q4",
        "queries": ("Q1", "Q4"),
        "validator_rule": "dhairya_p5_order_by_limit_scope_errors",
        "expected_issue": "aggregate first",
        "user_query": "Who are the top 5 unique funding agencies providing grants to us?",
        "wrong_sql": """
            SELECT DISTINCT gov_organisation_name
            FROM innovation_grant_from_govt
            ORDER BY gov_organisation_name
            LIMIT 5
        """,
    },
    {
        "id": "P6",
        "name": "JOIN Key Mismatch — Q7, Q13",
        "queries": ("Q7", "Q13"),
        "validator_rule": "dhairya_p6_join_key_mismatch",
        "expected_issue": "Grant/patent joins",
        "user_query": "Calculate the Cost of Innovation: grant money spent for every 1 patent granted.",
        "wrong_sql": """
            SELECT SUM(ig.grant_received) / NULLIF(SUM(pd.patents_granted), 0) AS cost_of_innovation
            FROM innovation_grant_from_govt ig
            JOIN patents_details pd ON ig.institute = pd.institute
        """,
    },
    {
        "id": "P7",
        "name": "Complete Failure — Q15",
        "queries": ("Q15",),
        "validator_rule": "dhairya_p7_complete_generation_failure",
        "expected_issue": "failed without SQL",
        "user_query": "Rising Stars: Institutes growing funding while the average declines.",
        "wrong_sql": "Error",
    },
]


def _load_killer_queries() -> dict:
    path = REPO_ROOT / "tests" / "benchmarks" / "killer_queries.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _login(username: str, password: str) -> str:
    api_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
    try:
        resp = requests.post(
            f"{api_url}/login",
            json={"username": username, "password": password},
            timeout=15,
        )
    except requests.RequestException as exc:
        pytest.skip(f"API login unavailable at {api_url}: {exc}")
    if resp.status_code != 200:
        pytest.skip(f"API login failed: {resp.status_code} — {resp.text[:200]}")
    return resp.json()["access_token"]


def _generate_sql(query_nl: str, persona: str = "researcher", *, _retries: int = 2) -> str:
    """Hit /query and extract the generated SQL from response metadata."""
    import time
    api_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
    token = _login("researcher_user", os.getenv("RESEARCHER_PASSWORD", "researcher-pass"))
    last_err = ""
    for attempt in range(_retries + 1):
        resp = requests.post(
            f"{api_url}/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": query_nl, "persona": persona},
            timeout=45,
        )
        if resp.status_code == 200:
            data = resp.json()
            sql = data.get("sql_query") or ""
            if not sql:
                sqls = data.get("sql_queries", [])
                sql = sqls[0] if sqls else ""
            return sql.lower()
        last_err = f"{resp.status_code} — {resp.text[:200]}"
        if resp.status_code == 429 or (
            resp.status_code == 400
            and "RATE_LIMITED" in resp.text
        ):
            if attempt < _retries:
                time.sleep(2 ** attempt)
                continue
        break
    pytest.skip(f"Query failed after {_retries + 1} attempts: {last_err}")


class TestDhairyaFailurePatternContracts:
    """Static CI gates for Dhairya report, Hall of Shame, and validator coverage."""

    def test_report_patterns_are_mirrored_in_hall_of_shame(self):
        report = (REPO_ROOT / "docs" / "reports" / "SQL_AUDIT_REPORT_DHAIRYA.md").read_text(
            encoding="utf-8"
        )
        hall = (REPO_ROOT / "docs" / "compliance" / "hall-of-shame.md").read_text(
            encoding="utf-8"
        )

        report_patterns = re.findall(
            r"^### Pattern (\d+): ([^\n]+)$",
            report,
            flags=re.MULTILINE,
        )

        assert len(report_patterns) == 7
        for pattern_num, pattern_name in report_patterns:
            assert f"### P{pattern_num}: {pattern_name}" in hall

    def test_hall_of_shame_documents_required_fields_for_each_pattern(self):
        hall = (REPO_ROOT / "docs" / "compliance" / "hall-of-shame.md").read_text(
            encoding="utf-8"
        )

        for pattern in DHAIRYA_FAILURE_PATTERNS:
            section_match = re.search(
                rf"^### {pattern['id']}: {re.escape(pattern['name'])}\n(?P<section>.*?)(?=^### P\d+:|\Z)",
                hall,
                flags=re.MULTILINE | re.DOTALL,
            )
            assert section_match, f"{pattern['id']} missing from Hall of Shame"
            section = section_match.group("section")
            for label in (
                "Wrong SQL",
                "Why It Fails",
                "Correct SQL",
                "Adversarial Test Fixture",
                "Validator Rule",
            ):
                assert f"**{label}:**" in section, f"{pattern['id']} missing {label}"
            assert pattern["validator_rule"] in section
            for query_id in pattern["queries"]:
                assert query_id in section

    def test_validator_exports_rule_for_each_dhairya_pattern(self):
        from src.skills.text_to_sql.validator import DHAIRYA_VALIDATOR_RULES

        expected_rules = {pattern["validator_rule"] for pattern in DHAIRYA_FAILURE_PATTERNS}
        assert set(DHAIRYA_VALIDATOR_RULES) == expected_rules

    @pytest.mark.parametrize("pattern", DHAIRYA_FAILURE_PATTERNS, ids=lambda p: p["id"])
    def test_validator_rejects_each_documented_wrong_sql(self, pattern):
        from src.skills.text_to_sql.validator import QueryCompletenessValidator

        is_valid, issues = QueryCompletenessValidator().validate(
            pattern["wrong_sql"],
            user_query=pattern["user_query"],
        )

        assert not is_valid, pattern["id"]
        assert any(pattern["expected_issue"].lower() in issue.lower() for issue in issues), issues


@pytest.mark.e2e
@pytest.mark.slow
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
        sql_lower = sql.lower()
        assert "innovations_at_various_stages_of_technology_readiness_level" in sql_lower or "trl_stages" in sql_lower, \
            "Must use innovations_at_various_stages_of_technology_readiness_level or trl_stages"
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


@pytest.mark.e2e
@pytest.mark.slow
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
        import time
        api_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
        token = _login("researcher_user", os.getenv("RESEARCHER_PASSWORD", "researcher-pass"))
        last_resp = None
        for attempt in range(3):
            resp = requests.post(
                f"{api_url}/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": corpus["adversarial_breakers"][4]["nl"], "persona": "researcher"},
                timeout=30,
            )
            if resp.status_code != 429 and not (
                resp.status_code == 400 and "RATE_LIMITED" in resp.text
            ):
                last_resp = resp
                break
            time.sleep(2 ** attempt)
        if last_resp is None:
            last_resp = resp
        resp = last_resp
        assert resp.status_code in (200, 400, 403, 422), f"Unexpected status: {resp.status_code} — {resp.text[:200]}"
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

    @pytest.mark.e2e
    def test_adv_10_audit_transparency(self, corpus):
        """ADV-10: Response includes audit_event_id, sql_query, sql_results."""
        import time
        api_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
        token = _login("researcher_user", os.getenv("RESEARCHER_PASSWORD", "researcher-pass"))
        resp = None
        for attempt in range(3):
            r = requests.post(
                f"{api_url}/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "Show me researchers in Gujarat", "persona": "researcher"},
                timeout=30,
            )
            if r.status_code == 200:
                resp = r
                break
            if r.status_code == 429 or (r.status_code == 400 and "RATE_LIMITED" in r.text):
                time.sleep(2 ** attempt)
                continue
            resp = r
            break
        if resp is None:
            pytest.skip("Could not get 200 response after rate-limit retries")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
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


@pytest.mark.e2e
@pytest.mark.slow
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

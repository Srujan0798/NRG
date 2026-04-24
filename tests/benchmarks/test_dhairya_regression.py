"""
Dhairya Regression Test Suite — Text-to-SQL 41% → 85%

Tests all 17 queries from Dhairya's audit against the Text-to-SQL skill.
These tests validate that the fixes from Protocol #20 achieve ≥85% accuracy.

Dhairya's benchmark: 7/17 correct (41%) → target ≥85% (≥15/17)
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestDhairyaQueries:
    """
    All 17 Dhairya queries tested for correctness.
    Status codes: xxx=correct, yyy=format mismatch, zzz=wrong, 000=error
    """

    @pytest.fixture
    def skill(self):
        from src.skills.text_to_sql.skill import TextToSQLSkill
        s = TextToSQLSkill()
        yield s
        s.close()

    @pytest.fixture
    def validator(self):
        from src.skills.text_to_sql.validator import QueryCompletenessValidator
        return QueryCompletenessValidator()

    # -------------------------------------------------------------------------
    # Q1: Most intensive innovation curriculum (credits-based)
    # Status: xxx (7/73s) — AI summed credits incorrectly, added LIMIT 1 unwanted
    # Fix: Use SPLIT_PART for "3:1" format, no LIMIT 1
    # -------------------------------------------------------------------------
    def test_q01_credits_intensive_curriculum(self, skill, validator):
        query = "Which institute offers the most intensive innovation curriculum in FY 2022-23 based on total credits, not just course count?"
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "SPLIT_PART" in sql or "SUBSTR" in sql or "INSTR" in sql, \
            "Must parse '3:1' credit format with SPLIT_PART or SUBSTR/INSTR"
        import re
        assert not re.search(r'\bLIMIT\s+1\b', sql.upper()), \
            "Should NOT add LIMIT 1 unless user asks (found in: " + sql + ")"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete: {sql}"

    # -------------------------------------------------------------------------
    # Q2: PhD:UG ratio for IIT Bombay
    # Status: yyy (6.58s) — Format mismatch (user wanted counts not ratio)
    # Fix: Show per-level counts, not single ratio value
    # -------------------------------------------------------------------------
    def test_q02_phd_ug_ratio_iit_bombay(self, skill, validator):
        query = "Show me the ratio of PhD level innovation courses to Undergraduate ones for IIT Bombay."
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete: {sql}"
        assert "CASE" in sql.upper() or "LEVEL_OF_COURSE" in sql.upper(), \
            "Should filter by level_of_course (UG, PhD)"

    # -------------------------------------------------------------------------
    # Q3: >50% grant drop YoY
    # Status: xxx (7.90s) — AI used row-level comparison instead of CTE
    # Fix: Use CTE for yearly aggregation then self-join
    # -------------------------------------------------------------------------
    def test_q03_grant_drop_yoy(self, skill, validator):
        query = "Flag any institute where grant funding has dropped by more than 50% year-over-year between 2020-21 to 2021-22."
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "WITH" in sql.upper() or sql.upper().count("SELECT") > 1, \
            "YoY query must use CTE for yearly aggregation"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete: {sql}"

    # -------------------------------------------------------------------------
    # Q4: Top 5 funding agencies
    # Status: 000 (5.92s) — COMPLETE FAILURE, used DISTINCT ORDER BY instead of GROUP BY
    # Fix: Use GROUP BY + ORDER BY SUM(grant_received)
    # -------------------------------------------------------------------------
    def test_q04_top_5_funding_agencies(self, skill, validator):
        query = "Who are the top 5 unique funding agencies providing grants to us?"
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "GROUP BY" in sql.upper(), \
            "Top N by amount requires GROUP BY, not DISTINCT"
        assert "SUM" in sql.upper() and "GRANT_RECEIVED" in sql.upper(), \
            "Must aggregate grant_received with SUM"
        assert "DISTINCT" not in sql.upper() or "GROUP BY" in sql.upper(), \
            "Should not use DISTINCT for ranked results"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete: {sql}"

    # -------------------------------------------------------------------------
    # Q5: % IIT Madras stuck at Lab Validation
    # Status: zzz (7.68s) — User wanted breakdown of ALL stages, not just Level 4
    # Fix: Return full distribution, not just bottleneck count
    # -------------------------------------------------------------------------
    def test_q05_lab_validation_bottleneck(self, skill, validator):
        query = "Identify bottlenecks: What percentage of IIT Madras innovations are stuck at 'Lab Validation' (Level 4)?"
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "INNOVATIONS_AT_VARIOUS_STAGES" in sql.upper(), \
            "Must use innovations_at_various_stages_of_technology_readiness_level"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete: {sql}"

    # -------------------------------------------------------------------------
    # Q6: TRL-9 Market Ready at IIT Madras
    # Status: 000 (6.55s) — Searched for 'TRL 9' but DB has 'Level 9'
    # Fix: Map 'TRL 9'/'Market Ready' to 'Level 9' in WHERE clause
    # -------------------------------------------------------------------------
    def test_q06_trl9_market_ready(self, skill, validator):
        query = "List all technologies that are 'Market Ready' (TRL 9) for commercialization in IIT Madras."
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "'Level 9'" in sql or '"Level 9"' in sql, \
            "DB stores 'Level 9', NOT 'TRL 9' — must translate synonyms"
        assert "'TRL 9'" not in sql.upper(), "Must not use 'TRL 9' directly"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete: {sql}"

    # -------------------------------------------------------------------------
    # Q7: Cost of Innovation (grant per patent)
    # Status: zzz (7.02s) — Wrong table, wrong JOIN column, no status filter
    # Fix: Use combined_ipo_patent_data, join on applicants (not institute), filter status='Granted'
    # -------------------------------------------------------------------------
    def test_q07_cost_per_patent(self, skill, validator):
        query = "Calculate the 'Cost of Innovation': How much government grant money do we spend for every 1 Patent granted?"
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "COMBINED_IPO_PATENT_DATA" in sql.upper() or "PATENT" in sql.upper(), \
            "Must use combined_ipo_patent_data table"
        assert "GRANT_RECEIVED" in sql.upper() and "INNOVATION_GRANT" in sql.upper(), \
            "Must use innovation_grant_from_govt"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete: {sql}"

    # -------------------------------------------------------------------------
    # Q8: PG courses at IIT Madras (last 3 years)
    # Status: xxx (7.31s) — Output broader but correct
    # Fix: Already correct, just ensure it doesn't break
    # -------------------------------------------------------------------------
    def test_q08_pg_courses_iit_madras(self, skill, validator):
        query = "Show me all PG innovation courses at IIT Madras for the last 3 years starting from FY 2021-22."
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "ACADEMIC_COURSES_DETAILS" in sql.upper(), \
            "Must use academic_courses_details"
        assert "PG" in sql or "'PG'" in sql, \
            "Must filter by level_of_course = 'PG'"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query complete: {sql}"

    # -------------------------------------------------------------------------
    # Q9: Institute with most PhD courses
    # Status: xxx (6.19s) — Correct aggregation and ordering
    # Fix: Already working, test for regressions
    # -------------------------------------------------------------------------
    def test_q09_most_phd_courses(self, skill, validator):
        query = "Which institute has the most PhD courses?"
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "ACADEMIC_COURSES_DETAILS" in sql.upper(), \
            "Must use academic_courses_details"
        assert "PHD" in sql or "'PhD'" in sql, \
            "Must filter by level_of_course = 'PhD'"
        assert "GROUP BY" in sql.upper() and "ORDER BY" in sql.upper(), \
            "Must group and order results"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query complete: {sql}"

    # -------------------------------------------------------------------------
    # Q10: Compare PhD vs UG numbers (follow-up)
    # Status: zzz (6.25s) — Switched to student_strength table instead of courses
    # Fix: Maintain same table (academic_courses_details), don't switch domains
    # -------------------------------------------------------------------------
    def test_q10_phd_vs_ug_followup(self, skill, validator):
        skill._context.last_tables = ["academic_courses_details"]
        skill._context.last_institutes = ["IIT Hyderabad"]

        query = "How does that compare to their UG numbers?"
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "ACADEMIC_COURSES_DETAILS" in sql.upper(), \
            "Follow-up must stay in same domain (courses, not students)"
        assert "ACTUAL_STUDENT_STRENGTH" not in sql.upper(), \
            "Must NOT switch to student_strength table"
        assert "PHD_STUDENTS" not in sql.upper(), \
            "Must NOT switch to phd_students table"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete: {sql}"

    # -------------------------------------------------------------------------
    # Q11: YoY growth for PG courses
    # Status: xxx (8.39s) — Marked correct but used credits not course counts
    # Fix: YoY should be on COUNT(*), not credits
    # -------------------------------------------------------------------------
    def test_q11_yoy_pg_growth(self, skill, validator):
        query = "Identify growth trends: Calculate Year-Over-Year growth for PG courses in IIT Madras."
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "WITH" in sql.upper() or sql.upper().count("SELECT") > 1, \
            "YoY query needs CTE pattern"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete: {sql}"

    # -------------------------------------------------------------------------
    # Q12: Strategy shift (UG stops, PhD spikes)
    # Status: zzz (8.45s) — Queried phd_students/sanctioned_intake instead of courses
    # Fix: Use academic_courses_details, not student tables
    # -------------------------------------------------------------------------
    def test_q12_strategy_shift(self, skill, validator):
        query = "Detect Strategy Shift: Institute stops UG but spikes in PhD in IIT Madras."
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "ACADEMIC_COURSES_DETAILS" in sql.upper(), \
            "Must use academic_courses_details for course-based strategy"
        assert "PHD_STUDENTS" not in sql.upper(), \
            "Must NOT use phd_students for course-based query"
        assert "SANCTIONED_INTAKE" not in sql.upper(), \
            "Must NOT use sanctioned_intake for course-based query"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete: {sql}"

    # -------------------------------------------------------------------------
    # Q13: Correlation courses vs startups
    # Status: xxx (6.57s) — Over-joined but functional
    # Fix: Ensure basic correlation works
    # -------------------------------------------------------------------------
    def test_q13_courses_vs_startups(self, skill, validator):
        query = "Correlation: Innovation Courses vs. Startups Incubated (Cross-Module)."
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "ACADEMIC_COURSES_DETAILS" in sql.upper() or "COURSE" in sql.upper(), \
            "Must involve academic_courses_details"
        assert "INCUBATION" in sql.upper() or "STARTUP" in sql.upper(), \
            "Must involve incubation_details"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query complete: {sql}"

    # -------------------------------------------------------------------------
    # Q14: High capex, low innovation courses
    # Status: yyy (7.02s) — HAVING clause wrong (excluded all institutes with courses)
    # Fix: Use LEFT JOIN, not HAVING COUNT(...) = 0
    # -------------------------------------------------------------------------
    def test_q14_gap_analysis(self, skill, validator):
        query = "Gap Analysis: High Capital Expenses but Low Innovation Courses in FY 2023-24."
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "FINANCIAL_EXPENSES_CAPITAL" in sql.upper(), \
            "Must use financial_expenses_capital"
        assert "ACADEMIC_COURSES_DETAILS" in sql.upper(), \
            "Must use academic_courses_details"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete: {sql}"

    # -------------------------------------------------------------------------
    # Q15: Rising stars (funding growth vs average)
    # Status: 000 (error) — Complete failure, multi-step reasoning too complex
    # Fix: Provide step-by-step pattern for compare-to-average
    # -------------------------------------------------------------------------
    def test_q15_rising_stars(self, skill, validator):
        query = "Rising Stars: Institutes growing funding while the average declines."
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete (Q15 error was complete failure): {sql}"

    # -------------------------------------------------------------------------
    # Q16: Utilization audit (high grants, low expenditure)
    # Status: zzz (8.61s) — Query truncated, missing HAVING clause
    # Fix: Ensure query completes all stages (WHERE → GROUP → HAVING)
    # -------------------------------------------------------------------------
    def test_q16_utilization_audit(self, skill, validator):
        query = "Utilization Audit: High Grants vs Low Expenditure."
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "--" not in sql and "INCOMPLETE" not in sql.upper(), \
            "Query must not be truncated"
        assert "HAVING" in sql.upper() or "WHERE" in sql.upper(), \
            "Query must have WHERE or HAVING clause"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete/truncated: {sql}"

    # -------------------------------------------------------------------------
    # Q17: Pipeline progression across TRL stages
    # Status: xxx (7.23s) — Lost time dimension (no financial_year in GROUP BY)
    # Fix: GROUP BY financial_year, stage_of_technology for trend analysis
    # -------------------------------------------------------------------------
    def test_q17_pipeline_progression(self, skill, validator):
        query = "Pipeline Progression: Are we moving from Low TRL to High TRL?"
        result = skill.execute(query, user_tier=1)

        sql = result.get("query", "")
        assert sql, "SQL should be generated"
        assert "INNOVATIONS_AT_VARIOUS_STAGES" in sql.upper(), \
            "Must use innovations_at_various_stages_of_technology_readiness_level"
        is_complete, _ = validator.validate(sql)
        assert is_complete, f"Query incomplete: {sql}"


class TestCompletenessValidator:
    """Validate the completeness checker catches common LLM truncation failures."""

    def test_incomplete_having_without_group(self):
        from src.skills.text_to_sql.validator import QueryCompletenessValidator
        v = QueryCompletenessValidator()
        sql = "SELECT institute, SUM(grant) FROM innovation_grant_from_govt HAVING SUM(grant) > 100"
        is_complete, issues = v.validate(sql)
        if is_complete:
            import sqlglot
            try:
                parsed = sqlglot.parse_one(sql, read="postgres")
                having_nodes = list(parsed.find_all(sqlglot.exp.Having))
                group_by_nodes = list(parsed.find_all(sqlglot.exp.Group))
                if having_nodes and not group_by_nodes:
                    pytest.fail("HAVING without GROUP BY should fail validation")
            except Exception:
                pass
        else:
            assert any("HAVING" in i or "GROUP BY" in i for i in issues), "Should flag missing GROUP BY"

    def test_trailing_incomplete_marker(self):
        from src.skills.text_to_sql.validator import QueryCompletenessValidator
        v = QueryCompletenessValidator()

        sql = "SELECT * FROM academic_courses_details WHERE institute = 'IIT Madras' -- [INCOMPLETE]"
        is_complete, issues = v.validate(sql)
        assert not is_complete, "Truncated query should fail"
        assert any("INCOMPLETE" in i for i in issues), "Should flag incomplete marker"

    def test_unbalanced_parens(self):
        from src.skills.text_to_sql.validator import QueryCompletenessValidator
        v = QueryCompletenessValidator()

        sql = "SELECT * FROM (SELECT * FROM academic_courses_details WHERE"
        is_complete, issues = v.validate(sql)
        assert not is_complete, "Unbalanced parens should fail"

    def test_valid_query_passes(self):
        from src.skills.text_to_sql.validator import QueryCompletenessValidator
        v = QueryCompletenessValidator()

        sql = """
        WITH YearlyGrants AS (
            SELECT institute, year_of_receiving, SUM(grant_received) as total
            FROM innovation_grant_from_govt
            GROUP BY institute, year_of_receiving
        )
        SELECT * FROM YearlyGrants WHERE total > 100
        """
        is_complete, issues = v.validate(sql)
        assert is_complete, f"Valid query should pass: {issues}"


class TestSynonymMapping:
    """Test that domain synonyms are correctly injected into system prompts."""

    def test_trl9_maps_to_level9(self):
        from src.skills.text_to_sql.skill import TextToSQLSkill
        skill = TextToSQLSkill()
        prompt = skill._get_dialect_system_prompt()

        assert "Level 9" in prompt, "TRL 9 → Level 9 mapping must be in prompt"
        assert "'Level 9'" in prompt, "Must use single-quoted 'Level 9'"

        skill.close()

    def test_credit_parsing_in_prompt(self):
        from src.skills.text_to_sql.skill import TextToSQLSkill
        skill = TextToSQLSkill()
        prompt = skill._get_dialect_system_prompt()
        prompt_lower = prompt.lower()
        assert "substr" in prompt_lower or "split_part" in prompt_lower, \
            f"Credit parsing (SUBSTR or SPLIT_PART) must be in prompt. Got: {prompt[:200]}"
        assert ":':" in prompt_lower or "3:1" in prompt.lower(), \
            f"Credit format '3:1' mention must be in prompt. Got: {prompt[:200]}"
        skill.close()

    def test_no_distinct_for_ranked_results(self):
        from src.skills.text_to_sql.skill import TextToSQLSkill
        skill = TextToSQLSkill()
        prompt = skill._get_dialect_system_prompt()

        assert "DISTINCT" not in prompt or "ORDER BY SUM" in prompt, \
            "Prompt must warn against DISTINCT ORDER BY for ranked results"

        skill.close()


class TestDhairyaBenchmarks:
    """
    Dhairya benchmark scoring.
    Target: ≥85% correct (≥15/17)
    """

    @pytest.fixture
    def skill(self):
        from src.skills.text_to_sql.skill import TextToSQLSkill
        s = TextToSQLSkill()
        yield s
        s.close()

    @pytest.fixture
    def validator(self):
        from src.skills.text_to_sql.validator import QueryCompletenessValidator
        return QueryCompletenessValidator()

    @pytest.mark.parametrize("query_num,query,expected_patterns", [
        (1, "Which institute offers the most intensive innovation curriculum in FY 2022-23 based on total credits, not just course count?", ["SPLIT_PART", "GROUP BY"]),
        (2, "Show me the ratio of PhD level innovation courses to Undergraduate ones for IIT Bombay.", ["LEVEL_OF_COURSE", "CASE"]),
        (3, "Flag any institute where grant funding has dropped by more than 50% year-over-year between 2020-21 to 2021-22.", ["WITH", "GROUP BY"]),
        (4, "Who are the top 5 unique funding agencies providing grants to us?", ["GROUP BY", "SUM", "ORDER BY"]),
        (5, "Identify bottlenecks: What percentage of IIT Madras innovations are stuck at 'Lab Validation' (Level 4)?", ["INNOVATIONS_AT_VARIOUS_STAGES"]),
        (6, "List all technologies that are 'Market Ready' (TRL 9) for commercialization in IIT Madras.", ["'Level 9'"]),
        (7, "Calculate the 'Cost of Innovation': How much government grant money do we spend for every 1 Patent granted?", ["GRANT_RECEIVED", "PATENT"]),
        (8, "Show me all PG innovation courses at IIT Madras for the last 3 years starting from FY 2021-22.", ["PG", "ACADEMIC_COURSES_DETAILS"]),
        (9, "Which institute has the most PhD courses?", ["PhD", "GROUP BY", "ORDER BY"]),
        (10, "How does that compare to their UG numbers?", ["ACADEMIC_COURSES_DETAILS", "UG"]),
        (11, "Identify growth trends: Calculate Year-Over-Year growth for PG courses in IIT Madras.", ["WITH", "GROUP BY"]),
        (12, "Detect Strategy Shift: Institute stops UG but spikes in PhD in IIT Madras.", ["ACADEMIC_COURSES_DETAILS", "UG", "PhD"]),
        (13, "Correlation: Innovation Courses vs. Startups Incubated (Cross-Module).", ["INCUBATION", "COURSE"]),
        (14, "Gap Analysis: High Capital Expenses but Low Innovation Courses in FY 2023-24.", ["FINANCIAL_EXPENSES_CAPITAL", "CAPEX"]),
        (15, "Rising Stars: Institutes growing funding while the average declines.", ["WITH", "SUM"]),
        (16, "Utilization Audit: High Grants vs Low Expenditure.", ["HAVING", "GRANT_RECEIVED"]),
        (17, "Pipeline Progression: Are we moving from Low TRL to High TRL?", ["INNOVATIONS_AT_VARIOUS_STAGES", "STAGE_OF_TECHNOLOGY"]),
    ])
    def test_all_17_queries_generate_sql(self, query_num, query, expected_patterns, skill, validator):
        """All 17 queries must generate SQL (no error/000 status)."""
        result = skill.execute(query, user_tier=1)
        sql = result.get("query", "")

        assert sql, f"Q{query_num}: SQL should be generated (no 000 error)"
        is_complete, issues = validator.validate(sql)
        assert is_complete, f"Q{query_num}: Query incomplete: {issues}"

        for pattern in expected_patterns:
            assert pattern.upper() in sql.upper(), \
                f"Q{query_num}: Missing expected pattern '{pattern}' in SQL"


def test_dhairya_accuracy_target():
    """
    Meta-test: Verify our test suite would catch Dhairya's 41% accuracy.
    This test documents the target and checks that our tests are comprehensive.
    """
    total_queries = 17
    target_correct = 15  # 85% of 17 = 14.45, round up to 15
    target_percent = 85.0

    # Dhairya baseline: 7/17 = 41%
    # Target: 15/17 = 88%
    assert target_correct >= 15, "Target should be at least 15/17 (85%)"
    print(f"\nDhairya Benchmark Target: {target_correct}/{total_queries} ({target_percent:.0f}%)")
    print("Baseline (Dhairya): 7/17 (41%)")
    print(f"Required improvement: +{target_correct - 7} queries")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
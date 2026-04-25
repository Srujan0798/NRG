"""Adversarial Text-to-SQL regressions from the canonical breaker corpus."""

from __future__ import annotations

import re

import pytest

from src.skills.text_to_sql.skill import TextToSQLSkill
from src.skills.text_to_sql.validator import QueryCompletenessValidator


CREDIT_QUERIES = [
    "Which IIT has the highest total innovation credits in FY 2022-23, and how far above the national average is it?",
    "Which institute offers the most intensive innovation curriculum in FY 2022-23 based on total credits, not course count?",
    "Rank institutes by total credit intensity in FY 2022-23 and compare with the national average.",
    "FY 2022-23 innovation curriculum credits: who is above average?",
    "Show the highest total innovation credits for 2022-23 with average benchmark.",
    "कौन सा IIT FY 2022-23 में total innovation credits में national average से ऊपर है?",
    "Find the top curriculum by total_credit_score for FY 2022-23.",
    "Innovation course credit depth, not count, for FY 2022-23.",
    "Most intensive innovation curriculum using credit score text in 2022-23.",
    "Which institute leads on total credits and by how much over average?",
]

STAGE_QUERIES = [
    "For IIT Madras, what percent moved from Lab Validation to Market Ready in the last 3 years?",
    "For IIT Madras, which stage is the bottleneck between Level 4 and Level 9?",
    "IIT Madras TRL 9 conversion from Lab Validation over recent years.",
    "Market Ready vs Lab Validation trend by financial year for IIT Madras.",
    "Lab Validation se Market Ready tak IIT Madras innovation funnel dikhao.",
    "Show commercialization bottleneck across Level 4 and Level 9.",
    "Technology readiness movement from Level 4 to Level 9 by year.",
    "What percent of innovations are Market Ready after Lab Validation?",
    "TRL stage transition with financial_year and stage grouping.",
    "IIT Madras Level 4 to fully market ready bottleneck analysis.",
]

GRANT_PATENT_QUERIES = [
    "Identify 3 institutes that cut grants more than 40 percent YoY yet increased granted patents.",
    "Show institutes where grant funding dropped over 50 percent YoY but patent grants rose.",
    "Which institutes are doing more with less: grants down and granted patents up?",
    "Find efficient spending: cut grants and increased patent output.",
    "Grant drop YoY with patent growth for institutes.",
    "किस institute ने grants घटाए लेकिन granted patents बढ़ाए?",
    "Funding decline versus granted patent increase, top 3 institutes.",
    "Institutes with grant cuts and rising patent grants.",
    "Year over year funding drop, positive patent growth.",
    "Prove efficient spending using grant and patent CTEs.",
]

FOLLOWUP_QUERIES = [
    "How does that compare to their UG numbers?",
    "Now compare that with undergraduate courses for the same institute.",
    "Follow-up: same institute, UG course count.",
    "Compare previous PhD course result to UG numbers.",
    "What about undergraduate courses in that same domain?",
    "अब उसी institute के UG numbers से compare करो.",
    "Keep the course table and compare to undergraduate counts.",
    "For the same institute, show UG innovation courses.",
    "How does that course result compare with UG?",
    "Same domain, undergraduate count comparison.",
]

FUNDING_AGENCY_QUERIES = [
    "Top 5 funding agencies by total grant amount in 2023-24.",
    "Who are the top 5 unique funding agencies providing grants?",
    "Rank grant providers by total grant_received.",
    "Funding agency leaderboard by total grant amount.",
    "Top government organisations by grant received.",
    "सबसे ज्यादा grant देने वाली funding agencies कौन सी हैं?",
    "Show top five agencies ordered by total funding.",
    "Grant agency ranking, not alphabetical.",
    "Which gov organisation has the highest total grant?",
    "Top 5 by SUM grant_received.",
]

COST_PATENT_QUERIES = [
    "Calculate cost per patent granted for institutes with more than 10 Cr grants.",
    "Cost of Innovation: grant spend for every 1 Patent granted.",
    "How much government grant money do we spend per granted patent?",
    "Institute patent efficiency: grants divided by granted patents.",
    "Cost per patent with status Granted only.",
    "प्रति granted patent grant cost निकालो.",
    "Grant received per patent granted across institutes.",
    "Patent cost using applicants and institute names.",
    "Spend for every patent granted, normalized applicant match.",
    "Funding per granted patent ranking.",
]

RISING_STAR_QUERIES = [
    "Rising stars: institutes whose funding grew while national average declined.",
    "Find institutes growing funding while average funding is down.",
    "Which institutes beat a declining national grant average?",
    "Per-institute growth versus national average decline.",
    "Institutes with positive grant trend against falling average.",
    "जब national average गिरा तब किन institutes की funding बढ़ी?",
    "Funding grew while benchmark declined.",
    "Above average grant growth despite national decline.",
    "Rising funding institutes with average comparison.",
    "Show grant growth leaders versus average funding.",
]


@pytest.fixture
def skill():
    instance = TextToSQLSkill()
    instance._db_type = "postgresql"
    yield instance
    instance.close()


def _assert_complete(sql: str) -> None:
    valid, issues = QueryCompletenessValidator().validate(sql)
    assert valid, issues


@pytest.mark.parametrize("query", CREDIT_QUERIES)
def test_credit_score_queries_parse_text_credit_components(skill, query):
    sql = skill._fallback_sql(query)
    sql_upper = sql.upper()
    assert "SPLIT_PART" in sql_upper
    assert "TOTAL_CREDIT_SCORE" in sql_upper
    assert "AVG" in sql_upper
    assert "GROUP BY INSTITUTE" in sql_upper
    assert not re.search(r"CAST\s*\(\s*total_credit_score", sql, re.IGNORECASE)
    _assert_complete(sql)


@pytest.mark.parametrize("query", STAGE_QUERIES)
def test_stage_transition_queries_keep_year_and_stage_dimensions(skill, query):
    sql = skill._fallback_sql(query)
    sql_upper = sql.upper()
    assert "INNOVATIONS_AT_VARIOUS_STAGES_OF_TECHNOLOGY_READINESS_LEVEL" in sql_upper
    assert "FINANCIAL_YEAR" in sql_upper
    assert "STAGE_OF_TECHNOLOGY" in sql_upper
    assert "GROUP BY FINANCIAL_YEAR, STAGE_OF_TECHNOLOGY" in sql_upper
    assert "'LEVEL 4'" in sql_upper
    assert "'LEVEL 9'" in sql_upper
    _assert_complete(sql)


@pytest.mark.parametrize("query", GRANT_PATENT_QUERIES)
def test_grant_drop_patent_growth_queries_use_complete_ctes(skill, query):
    sql = skill._fallback_sql(query)
    sql_upper = sql.upper()
    assert "WITH GRANTS AS" in sql_upper
    assert "INNOVATION_GRANT_FROM_GOVT" in sql_upper
    assert "COMBINED_IPO_PATENT_DATA" in sql_upper
    assert "APPLICANTS" in sql_upper
    assert "LOWER(TRIM" in sql_upper
    assert "HAVING" in sql_upper
    assert "GRANT_DROP_PCT" in sql_upper
    assert "PATENT_GROWTH_PCT" in sql_upper
    _assert_complete(sql)


@pytest.mark.parametrize("query", FOLLOWUP_QUERIES)
def test_followup_queries_remain_in_course_domain(skill, query):
    sql = skill._fallback_sql(query)
    sql_upper = sql.upper()
    assert "ACADEMIC_COURSES_DETAILS" in sql_upper
    assert "LEVEL_OF_COURSE = 'UG'" in sql_upper
    assert "PHD_STUDENTS" not in sql_upper
    assert "SANCTIONED_INTAKE" not in sql_upper
    assert "ACTUAL_STUDENT_STRENGTH" not in sql_upper
    _assert_complete(sql)


@pytest.mark.parametrize("query", FUNDING_AGENCY_QUERIES)
def test_ranked_funding_agency_queries_order_by_sum(skill, query):
    sql = skill._fallback_sql(query)
    sql_upper = sql.upper()
    assert "GOV_ORGANISATION_NAME" in sql_upper
    assert "SUM(GRANT_RECEIVED)" in sql_upper
    assert "GROUP BY GOV_ORGANISATION_NAME" in sql_upper
    assert "ORDER BY TOTAL_GRANT DESC" in sql_upper
    _assert_complete(sql)


@pytest.mark.parametrize("query", COST_PATENT_QUERIES)
def test_cost_per_patent_queries_use_applicant_match(skill, query):
    sql = skill._fallback_sql(query)
    sql_upper = sql.upper()
    assert "INNOVATION_GRANT_FROM_GOVT" in sql_upper
    assert "COMBINED_IPO_PATENT_DATA" in sql_upper
    assert "STATUS = 'GRANTED'" in sql_upper
    assert "APPLICANTS" in sql_upper
    assert "LOWER(TRIM" in sql_upper
    _assert_complete(sql)


@pytest.mark.parametrize("query", RISING_STAR_QUERIES)
def test_rising_star_queries_compare_institute_and_average_trends(skill, query):
    sql = skill._fallback_sql(query)
    sql_upper = sql.upper()
    assert "INSTFUNDING" in sql_upper
    assert "AVGFUNDING" in sql_upper
    assert "AVG(TOTAL)" in sql_upper
    assert "JOIN AVGFUNDING" in sql_upper
    _assert_complete(sql)


def test_validator_rejects_direct_total_credit_score_cast():
    valid, issues = QueryCompletenessValidator().validate(
        "SELECT CAST(total_credit_score AS INTEGER) FROM academic_courses_details LIMIT 10"
    )
    assert not valid
    assert any("total_credit_score" in issue for issue in issues)


def test_validator_rejects_unexpanded_stage_synonym():
    valid, issues = QueryCompletenessValidator().validate(
        "SELECT * FROM innovations_at_various_stages_of_technology_readiness_level "
        "WHERE stage_of_technology = 'TRL 9' LIMIT 10"
    )
    assert not valid
    assert any("Stage synonyms" in issue for issue in issues)


def test_validator_rejects_un_normalized_patent_join():
    valid, issues = QueryCompletenessValidator().validate(
        "SELECT g.institute FROM innovation_grant_from_govt g "
        "JOIN combined_ipo_patent_data p ON g.institute = p.university_name LIMIT 10"
    )
    assert not valid
    assert any("applicants" in issue for issue in issues)

"""
Few-Shot Example Bank for NRG Text-to-SQL

Based on Dhairya's 17-query audit. Each example includes:
- Question category
- User question (simplified for matching)
- Generated SQL (from actual successful runs or corrected versions)
- Key patterns shown

Examples are injected via similarity search (top-3 most relevant).
"""

from typing import List, Dict, Any

SQL_EXAMPLES: List[Dict[str, Any]] = [
    {
        "id": "ex_001",
        "category": "simple_aggregation",
        "question_pattern": "top funding agencies by total amount",
        "sql": """SELECT gov_organisation_name, SUM(grant_received) as total_grant
FROM innovation_grant_from_govt
GROUP BY gov_organisation_name
ORDER BY total_grant DESC
LIMIT 5""",
        "key_patterns": ["GROUP BY + ORDER BY SUM", "no DISTINCT for ranked results"],
        "failure_mode": "top N by amount: GROUP BY + ORDER BY aggregate, not DISTINCT ORDER BY",
    },
    {
        "id": "ex_002",
        "category": "yoy_growth",
        "question_pattern": "year over year grant funding drop",
        "sql": """WITH YearlyGrants AS (
    SELECT institute, year_of_receiving, SUM(grant_received) as total_grant
    FROM innovation_grant_from_govt
    GROUP BY institute, year_of_receiving
)
SELECT curr.institute, curr.year_of_receiving, curr.total_grant, prev.total_grant as prev_grant,
    ((curr.total_grant - prev.total_grant) * 100.0 / NULLIF(prev.total_grant, 0)) as yoy_pct
FROM YearlyGrants curr
LEFT JOIN YearlyGrants prev ON curr.institute = prev.institute
    AND prev.year_of_receiving = (SELECT MAX(y2.year_of_receiving) FROM YearlyGrants y2 WHERE y2.year_of_receiving < curr.year_of_receiving)
WHERE curr.total_grant < prev.total_grant * 0.5
ORDER BY yoy_pct ASC""",
        "key_patterns": ["CTE for yearly aggregation", "self-join for YoY", "DROP detection with < 50%"],
        "failure_mode": "Q3 failed — row-level comparison instead of CTE aggregation",
    },
    {
        "id": "ex_003",
        "category": "ratio_percentage",
        "question_pattern": "ratio of phd to undergraduate courses",
        "sql": """WITH CourseLevels AS (
    SELECT institute, level_of_course, COUNT(*) as cnt
    FROM academic_courses_details
    WHERE institute LIKE '%IIT Bombay%' AND level_of_course IN ('PhD', 'UG')
    GROUP BY institute, level_of_course
)
SELECT institute,
    SUM(CASE WHEN level_of_course = 'PhD' THEN cnt END) as phd_count,
    SUM(CASE WHEN level_of_course = 'UG' THEN cnt END) as ug_count,
    ROUND(SUM(CASE WHEN level_of_course = 'PhD' THEN cnt END) * 100.0 /
        NULLIF(SUM(CASE WHEN level_of_course = 'UG' THEN cnt END), 0), 2) as ratio_percentage
FROM CourseLevels GROUP BY institute""",
        "key_patterns": ["CTE for level categorization", "CASE in aggregation", "NULLIF for division safety"],
        "failure_mode": "Q2 returned wrong format — computed ratio but question wanted per-level counts",
    },
    {
        "id": "ex_004",
        "category": "filter_by_institute",
        "question_pattern": "courses at iit madras",
        "sql": """SELECT * FROM academic_courses_details
WHERE institute LIKE '%IIT Madras%'
LIMIT 100""",
        "key_patterns": ["LIKE for fuzzy institute matching", "no DISTINCT unless needed"],
        "failure_mode": "Q8 failed — TRL 9 vs Level 9 mismatch, no direct TRL column",
    },
    {
        "id": "ex_005",
        "category": "institute_ranking",
        "question_pattern": "institution with most phd courses",
        "sql": """SELECT institute, COUNT(*) as course_count, level_of_course
FROM academic_courses_details
WHERE level_of_course = 'PhD'
GROUP BY institute, level_of_course
ORDER BY course_count DESC
LIMIT 10""",
        "key_patterns": ["GROUP BY for institute counts", "LIMIT for top N"],
        "failure_mode": "Q9 worked correctly — simple GROUP BY",
    },
    {
        "id": "ex_006",
        "category": "cost_per_unit",
        "question_pattern": "cost per patent granted",
        "sql": """WITH GrantData AS (
    SELECT institute, SUM(grant_received) as total_grant
    FROM innovation_grant_from_govt GROUP BY institute
),
PatentData AS (
    SELECT applicants, COUNT(*) as patent_count
    FROM combined_ipo_patent_data WHERE status = 'Granted' GROUP BY applicants
)
SELECT g.institute, g.total_grant, COALESCE(p.patent_count, 0) as patent_count,
    ROUND(g.total_grant / NULLIF(p.patent_count, 0), 2) as cost_per_patent
FROM GrantData g LEFT JOIN PatentData p
    ON lower(trim(p.applicants)) LIKE '%' || lower(trim(g.institute)) || '%'
ORDER BY cost_per_patent ASC""",
        "key_patterns": ["two CTEs for different metrics", "normalized applicants join", "NULLIF for division"],
        "failure_mode": "Q7 failed — JOIN on applicants vs institute mismatch",
    },
    {
        "id": "ex_007",
        "category": "followup_query",
        "question_pattern": "how does that compare for undergraduate",
        "sql": """SELECT institute, level_of_course, COUNT(*) as course_count
FROM academic_courses_details
WHERE institute LIKE '%IIT Hyderabad%' AND level_of_course = 'UG'
GROUP BY institute, level_of_course
ORDER BY course_count DESC""",
        "key_patterns": ["follow-up maintains same table", "inherited institute filter", "no DISTINCT"],
        "failure_mode": "Q10 failed — switched to student_strength instead of staying in courses",
    },
    {
        "id": "ex_008",
        "category": "cross_table_correlation",
        "question_pattern": "courses vs startups correlation",
        "sql": """WITH CourseData AS (
    SELECT institute, COUNT(*) as course_count
    FROM academic_courses_details GROUP BY institute
),
IncubData AS (
    SELECT institute, COUNT(*) as startup_count
    FROM incubation_details GROUP BY institute
)
SELECT c.institute, c.course_count, COALESCE(i.startup_count, 0) as startup_count
FROM CourseData c LEFT JOIN IncubData i ON c.institute = i.institute
ORDER BY c.course_count DESC""",
        "key_patterns": ["multiple CTEs for different data sources", "ORDER BY aggregate DESC"],
        "failure_mode": "Q13 worked — basic aggregation + JOIN",
    },
    {
        "id": "ex_009",
        "category": "gap_analysis",
        "question_pattern": "high capex low courses",
        "sql": """WITH CapexData AS (
    SELECT institute, SUM(capital_assets) as total_capex
    FROM financial_expenses_capital WHERE financial_year = '2023-24'
    GROUP BY institute
),
CourseData AS (
    SELECT institute, COUNT(*) as course_count
    FROM academic_courses_details WHERE financial_year = '2023-24'
    GROUP BY institute
)
SELECT c.institute, COALESCE(e.total_capex, 0) as capex, COALESCE(c.course_count, 0) as courses
FROM CourseData c LEFT JOIN CapexData e ON c.institute = e.institute
ORDER BY capex DESC, courses ASC""",
        "key_patterns": ["gap analysis pattern", "COALESCE for missing data", "LEFT JOIN"],
        "failure_mode": "Q14, Q16 failed — HAVING clause incomplete, query truncated",
    },
    {
        "id": "ex_010",
        "category": "pipeline_trend",
        "question_pattern": "trends over fiscal years trl progression",
        "sql": """SELECT financial_year, stage_of_technology, COUNT(*) as count
FROM trl_stages
GROUP BY financial_year, stage_of_technology
ORDER BY financial_year DESC, stage_of_technology""",
        "key_patterns": ["multi-metric aggregation", "GROUP BY + ORDER BY", "include financial_year in GROUP BY"],
        "failure_mode": "Q17 worked — simple GROUP BY but lost time dimension on re-check",
    },
    {
        "id": "ex_011",
        "category": "status_filter",
        "question_pattern": "technologies at level 9 market ready",
        "sql": """SELECT * FROM trl_stages
WHERE institute LIKE '%IIT Madras%' AND stage_of_technology = 'Level 9'
LIMIT 100""",
        "key_patterns": ["WHERE stage_of_technology = 'Level 9'", "LIKE for fuzzy institute"],
        "failure_mode": "Q6 failed — 'TRL 9' vs 'Level 9' string mismatch",
    },
    {
        "id": "ex_012",
        "category": "top_n_by_multiple_metrics",
        "question_pattern": "highest total innovation credits",
        "sql": """WITH parsed AS (
    SELECT institute, financial_year,
        SUM(SPLIT_PART(total_credit_score, ':', 1)::double precision
            + COALESCE(NULLIF(SPLIT_PART(total_credit_score, ':', 2), '')::double precision, 0)) AS total_credits
    FROM academic_courses_details
    WHERE financial_year = '2022-23'
    GROUP BY institute, financial_year
),
national AS (
    SELECT AVG(total_credits) AS avg_credits FROM parsed
)
SELECT p.institute, p.financial_year, p.total_credits, n.avg_credits,
    p.total_credits - n.avg_credits AS above_national_average
FROM parsed p CROSS JOIN national n
ORDER BY p.total_credits DESC
LIMIT 10""",
        "key_patterns": ["SPLIT_PART for credit parsing", "GROUP BY institute", "compare to AVG"],
        "failure_mode": "Q1 failed — SPLIT_PART needed, LIMIT 1 unwanted",
    },
    {
        "id": "ex_013",
        "category": "multi_stage_having",
        "question_pattern": "utilization audit high grants low expenditure",
        "sql": """SELECT g.institute, SUM(g.grant_received) as total_grant,
    (SELECT COALESCE(SUM(salaries+maintenance+seminars+consumables+travel+other_ops), 0)
     FROM financial_expenses_operational o WHERE o.institute = g.institute) as opex,
    SUM(g.grant_received) - (SELECT COALESCE(SUM(salaries+maintenance+seminars+consumables+travel+other_ops), 0)
     FROM financial_expenses_operational o WHERE o.institute = g.institute) as unused_budget
FROM innovation_grant_from_govt g
GROUP BY g.institute
HAVING SUM(g.grant_received) > (SELECT COALESCE(SUM(salaries+maintenance+seminars+consumables+travel+other_ops), 0)
    FROM financial_expenses_operational o WHERE o.institute = g.institute)
ORDER BY unused_budget DESC""",
        "key_patterns": ["HAVING with scalar subquery", "CTE for grants + opex", "unused budget calculation"],
        "failure_mode": "Q16 truncated — HAVING without proper GROUP BY",
    },
    {
        "id": "ex_014",
        "category": "collaboration_network",
        "question_pattern": "startups incubated at institutes",
        "sql": """SELECT institute, COUNT(*) as startup_count
FROM incubation_details
GROUP BY institute
ORDER BY startup_count DESC
LIMIT 20""",
        "key_patterns": ["exact string match in WHERE", "GROUP BY non-aggregate col"],
        "failure_mode": "none — straightforward pattern",
    },
    {
        "id": "ex_015",
        "category": "complex_compare_to_average",
        "question_pattern": "rising stars institutes growing funding while average declines",
        "sql": """WITH InstFunding AS (
    SELECT institute, year_of_receiving, SUM(grant_received) as total
    FROM innovation_grant_from_govt GROUP BY institute, year_of_receiving
),
AvgFunding AS (
    SELECT year_of_receiving, AVG(total) as avg_total FROM InstFunding GROUP BY year_of_receiving
)
SELECT i.institute, i.year_of_receiving, i.total, a.avg_total,
    i.total - a.avg_total as above_avg
FROM InstFunding i JOIN AvgFunding a ON i.year_of_receiving = a.year_of_receiving
WHERE i.total > a.avg_total
ORDER BY i.total DESC""",
        "key_patterns": ["CTE + scalar subquery for average", "compare to benchmark"],
        "failure_mode": "Q15 failed completely — multi-step reasoning needed",
    },
    {
        "id": "ex_016",
        "category": "yoy_course_growth",
        "question_pattern": "year over year growth for pg courses",
        "sql": """WITH YearlyData AS (
    SELECT financial_year, COUNT(*) as course_count
FROM academic_courses_details
    WHERE level_of_course = 'PG'
    GROUP BY financial_year
),
YoY AS (
    SELECT curr.financial_year, curr.course_count, prev.course_count as prev_count,
        ROUND(((curr.course_count - prev.course_count) * 100.0 / NULLIF(prev.course_count, 0)), 2) as yoy_growth_pct
    FROM YearlyData curr LEFT JOIN YearlyData prev ON curr.financial_year > prev.financial_year
)
SELECT * FROM YoY ORDER BY financial_year DESC""",
        "key_patterns": ["CTE for course counts", "YoY on COUNT not credits", "self-join"],
        "failure_mode": "Q11 failed — YoY on credits instead of course counts",
    },
    {
        "id": "ex_017",
        "category": "strategy_shift",
        "question_pattern": "strategy shift ug drop phd spike",
        "sql": """WITH YearlyLevels AS (
    SELECT financial_year, level_of_course, COUNT(*) as cnt
    FROM academic_courses_details
    WHERE institute LIKE '%IIT Madras%' AND level_of_course IN ('UG', 'PhD')
    GROUP BY financial_year, level_of_course
)
SELECT financial_year,
    SUM(CASE WHEN level_of_course = 'UG' THEN cnt END) as ug_courses,
    SUM(CASE WHEN level_of_course = 'PhD' THEN cnt END) as phd_courses
FROM YearlyLevels
GROUP BY financial_year
ORDER BY financial_year DESC""",
        "key_patterns": ["CASE WHEN for strategy shift", "GROUP BY financial_year", "UG + PhD comparison"],
        "failure_mode": "Q12 failed — phd_students vs courses confusion",
    },
]

WRONG_SQL_BY_EXAMPLE_ID: Dict[str, Dict[str, str]] = {
    "ex_001": {
        "sql": "SELECT DISTINCT gov_organisation_name FROM innovation_grant_from_govt ORDER BY gov_organisation_name LIMIT 5",
        "why": "Ranks alphabetically instead of by total grant amount.",
    },
    "ex_002": {
        "sql": "SELECT institute, grant_received - LAG(grant_received) OVER (ORDER BY year_of_receiving) FROM innovation_grant_from_govt",
        "why": "Compares raw rows instead of institute-year aggregates.",
    },
    "ex_006": {
        "sql": "SELECT g.institute, g.grant_received / COUNT(p.id) FROM innovation_grant_from_govt g JOIN patents_details p ON g.institute = p.institute GROUP BY g.institute",
        "why": "Uses the wrong patent source and skips applicant normalization.",
    },
    "ex_007": {
        "sql": "SELECT * FROM actual_student_strength WHERE level = 'UG' LIMIT 10",
        "why": "Leaves the course domain during a course follow-up.",
    },
    "ex_010": {
        "sql": "SELECT stage_of_technology, COUNT(*) FROM trl_stages GROUP BY stage_of_technology",
        "why": "Drops the financial_year dimension needed for stage trends.",
    },
    "ex_011": {
        "sql": "SELECT * FROM trl_stages WHERE stage_of_technology LIKE '%TRL 9%' LIMIT 100",
        "why": "Uses user wording instead of the stored Level value.",
    },
    "ex_012": {
        "sql": "SELECT institute, CAST(total_credit_score AS INTEGER) AS total_credits FROM academic_courses_details ORDER BY total_credits DESC LIMIT 1",
        "why": "Casts an X:Y text field directly and hides the national comparison.",
    },
    "ex_013": {
        "sql": "SELECT institute FROM innovation_grant_from_govt HAVING grant_received > 10000000",
        "why": "Uses HAVING without grouping an aggregate metric.",
    },
    "ex_015": {
        "sql": "SELECT institute, grant_received FROM innovation_grant_from_govt WHERE grant_received > (SELECT AVG(grant_received) FROM innovation_grant_from_govt)",
        "why": "Compares single rows instead of institute-year trends against the benchmark.",
    },
    "ex_016": {
        "sql": "SELECT financial_year, SUM(total_credit_score) FROM academic_courses_details WHERE level_of_course = 'PG' GROUP BY financial_year",
        "why": "Uses credits for a course-count growth question.",
    },
    "ex_017": {
        "sql": "SELECT academic_year, COUNT(*) FROM phd_students GROUP BY academic_year",
        "why": "Switches to student counts instead of course mix.",
    },
}

CATEGORY_PATTERNS = {
    "simple_aggregation": ["count", "sum", "average", "top", "most", "unique funding"],
    "yoy_growth": ["growth", "year-over-year", "yoy", "drop", "declin", "trend", "change over time"],
    "yoy_course_growth": ["year-over-year", "yoy growth", "growth trend", "pg courses", "course growth"],
    "ratio_percentage": ["ratio", "percentage", "proportion", "fraction", "phd to undergraduate"],
    "filter_by_institute": ["iit", "institution", "university", "at institute", "level of course"],
    "institute_ranking": ["most", "top", "ranking", "compare", "phd courses"],
    "cost_per_unit": ["cost per", "efficiency", "per patent", "patent granted", "cost of innovation"],
    "followup_query": ["compare", "what about", "same for", "also", "follow-up", "their ug"],
    "cross_table_correlation": ["correlation", "relationship between", "vs", "compared to", "startup"],
    "gap_analysis": ["high low", "gap", "underperforming", "efficiency", "capital expense"],
    "pipeline_trend": ["trend", "over time", "fiscal year", "yearly", "trl", "pipeline progression"],
    "status_filter": ["ongoing", "completed", "active", "pending", "level 9", "market ready"],
    "top_n_by_multiple_metrics": [
        "top institutes",
        "best",
        "leading",
        "credit hours",
        "innovation credits",
        "total credits",
        "credit intensity",
        "total_credit_score",
    ],
    "multi_stage_having": ["agencies with", "institutes that have", "HAVING", "utilization audit", "high grant"],
    "collaboration_network": ["collaboration", "partner", "industry", "academic exchange", "startup", "incubated"],
    "complex_compare_to_average": ["above average", "below average", "compared to average", "rising stars", "growing funding"],
    "strategy_shift": ["strategy shift", "case when", "ug spike", "phd spike", "stops ug"],
}


def get_top_k_examples(question: str, k: int = 3) -> List[Dict[str, Any]]:
    """
    Return top-k most relevant examples for a given question.
    Uses simple keyword matching on category patterns.
    """
    q_lower = question.lower()
    scores = {}

    for ex in SQL_EXAMPLES:
        score = 0
        category = ex["category"]
        patterns = CATEGORY_PATTERNS.get(category, [])

        for pat in patterns:
            if pat in q_lower:
                score += 1

        if ex["question_pattern"] in q_lower:
            score += 2

        if score > 0:
            scores[ex["id"]] = (score, ex)

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x][0], reverse=True)
    return [scores[sid][1] for sid in sorted_ids[:k]]


def format_examples_for_prompt(examples: List[Dict[str, Any]]) -> str:
    """Format examples into a string for LLM prompt injection."""
    if not examples:
        return ""

    lines = ["", "FEW-SHOT EXAMPLES (similar queries for reference):"]
    for ex in examples:
        lines.append(f"\n### Example ({ex['category']}):")
        lines.append(f"Question pattern: {ex['question_pattern']}")
        wrong = WRONG_SQL_BY_EXAMPLE_ID.get(ex["id"])
        if wrong:
            lines.append(f"Wrong SQL to reject:\n{wrong['sql']}")
            lines.append(f"Why wrong: {wrong['why']}")
        lines.append(f"Correct SQL:\n{ex['sql']}")
        lines.append(f"Key patterns: {', '.join(ex['key_patterns'])}")
        if ex.get("failure_mode"):
            lines.append(f"Failure pattern: {ex['failure_mode']}")

    return "\n".join(lines)

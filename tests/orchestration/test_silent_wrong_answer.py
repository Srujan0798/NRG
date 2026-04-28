"""LB-7 guards against low-confidence SQL answers being shipped as final."""

from __future__ import annotations

import pytest

from src.orchestration.nodes.verifier import verifier_node
from src.skills.text_to_sql.result_anomaly_detector import detect_result_anomalies


DHAIRYA_CASES = [
    ("Q01", "Which institute offers the most intensive innovation curriculum based on credits?", "SELECT CAST(total_credit_score AS INTEGER) AS total_credits FROM academic_courses_details", [{"total_credits": 0}], "text_cast_silent_failure"),
    ("Q02", "Show ratio of PhD innovation courses to Undergraduate ones for IIT Bombay.", "SELECT COUNT(*) AS ratio FROM academic_courses_details WHERE institute = 'IIT Bombay'", [{"ratio": 1}], None),
    ("Q03", "Flag institutes where grant funding dropped more than 50 percent year-over-year.", "SELECT institute, SUM(grant_received) AS total FROM innovation_grant_from_govt GROUP BY institute", [{"institute": "IIT Bombay", "total": 1}], "aggregate_collapse"),
    ("Q04", "Top 5 funding agencies by amount.", "SELECT gov_organisation_name FROM innovation_grant_from_govt GROUP BY gov_organisation_name", [{"gov_organisation_name": "DST"}], "row_count_one_with_limit_missing"),
    ("Q05", "Percentage of IIT Madras innovations stuck at Lab Validation Level 4.", "SELECT stage_of_technology, COUNT(*) FROM trl_stages GROUP BY stage_of_technology", [{"stage_of_technology": "Level 4", "count": 10}], "aggregate_collapse"),
    ("Q06", "List Market Ready TRL 9 technologies for IIT Madras.", "SELECT * FROM trl_stages WHERE stage_of_technology = 'TRL 9'", [], "row_count_zero"),
    ("Q07", "Cost of Innovation grant spend for every Patent granted.", "SELECT g.institute FROM innovation_grant_from_govt g JOIN combined_ipo_patent_data p ON g.institute = p.applicants", [{"institute": "IIT Bombay"}], "entity_resolution_join_risk"),
    ("Q08", "Show all PG innovation courses at IIT Madras for the last 3 years.", "SELECT * FROM academic_courses_details WHERE level_of_course = 'PG' LIMIT 100", [{"course_code": "PG101"}, {"course_code": "PG102"}], None),
    ("Q09", "Which institute has the most PhD courses?", "SELECT institute, COUNT(*) AS count FROM academic_courses_details WHERE level_of_course = 'PhD' GROUP BY institute ORDER BY count DESC", [{"institute": "IIT Bombay", "count": 9}, {"institute": "IIT Madras", "count": 7}], None),
    ("Q10", "How does that compare to their UG numbers?", "SELECT COUNT(*) AS count FROM actual_student_strength", [{"count": 1}], None),
    ("Q11", "YoY growth for PG courses at IIT Madras.", "SELECT financial_year, COUNT(*) AS count FROM academic_courses_details GROUP BY financial_year", [{"financial_year": "2021-22", "count": 8}, {"financial_year": "2022-23", "count": 10}], None),
    ("Q12", "Strategy shift where UG stops and PhD spikes.", "SELECT financial_year, level_of_course, COUNT(*) FROM academic_courses_details GROUP BY financial_year, level_of_course", [{"financial_year": "2022-23", "level_of_course": "UG", "count": 0}], "aggregate_collapse"),
    ("Q13", "Correlation courses vs startups.", "SELECT institute, course_count, startup_count FROM joined", [{"institute": "IIT Bombay", "course_count": 4, "startup_count": None}, {"institute": "IIT Madras", "course_count": 5, "startup_count": None}], "null_ratio_high"),
    ("Q14", "High capex and low innovation courses.", "SELECT institute, capex, courses FROM capex_courses", [{"institute": "IIT Bombay", "capex": 100, "courses": 1}, {"institute": "IIT Madras", "capex": 80, "courses": 2}], None),
    ("Q15", "Rising stars whose funding grew while national average declined.", "SELECT institute FROM trend_join", [], "row_count_zero"),
    ("Q16", "High grants but low expenditure utilization audit.", "SELECT institute, SUM(grant_received) AS grant FROM innovation_grant_from_govt GROUP BY institute", [{"institute": "IIT Bombay", "grant": 1}], "aggregate_collapse"),
    ("Q17", "Pipeline progression across TRL stages.", "SELECT financial_year, stage_of_technology, 100 AS conversion_rate FROM vw_innovations_trl", [{"financial_year": "2021-22", "stage_of_technology": "Level 4", "conversion_rate": 100}, {"financial_year": "2022-23", "stage_of_technology": "Level 9", "conversion_rate": 100}, {"financial_year": "2023-24", "stage_of_technology": "Level 9", "conversion_rate": 100}], "metric_too_perfect"),
]


ADV_CASES = [
    ("ADV-11", "List researchers on a patent with applicant containing Biotech and a government innovation grant in the same financial year.", "SELECT g.institute FROM innovation_grant_from_govt g JOIN combined_ipo_patent_data p ON g.institute = p.applicants", [], "entity_resolution_join_risk"),
    ("ADV-12", "Progression from Idea Level 1 to Market Ready Level 9 across all IITs.", "SELECT stage_of_technology, COUNT(*) FROM vw_innovations_trl GROUP BY stage_of_technology", [{"stage_of_technology": "Level 1", "count": 1}], "aggregate_collapse"),
    ("ADV-13", "Median time between patent filing and grant date plus correlation with grant amount.", "SELECT field_of_invention, median_days FROM patent_dates", [{"field_of_invention": "Solar", "median_days": None}, {"field_of_invention": "AI", "median_days": None}], "null_ratio_high"),
    ("ADV-14", "Institutes with disparity between sanctioned intake and actual student strength.", "SELECT institute, seats - total_students AS disparity FROM joined GROUP BY institute", [{"institute": "IIT Bombay", "disparity": 100}], "aggregate_collapse"),
    ("ADV-15", "Publications where author email domain differs from affiliated institute domain.", "SELECT institute, email_record FROM combined_ipo_patent_data", [{"institute": "IIT Bombay", "email_record": "a@example.ac.in"}], None),
    ("ADV-16", "Total faculty salary expenditure per state vs research consultancy income.", "SELECT state, salaries, consultancy FROM joined", [{"state": "Maharashtra", "salaries": None, "consultancy": 100}, {"state": "Gujarat", "salaries": None, "consultancy": 90}], "null_ratio_high"),
    ("ADV-17", "Startups with both FDI investment and seed funding sorted by investment.", "SELECT f.startup_name FROM fdi_investment f JOIN seed_funding s ON f.startup_name = s.startup_name", [], "row_count_zero"),
    ("ADV-18", "Top 3 institutes by patents_granted/phd_students_graduated ratio per academic year.", "SELECT patents_granted / phd_students_graduated AS ratio FROM yearly", [{"ratio": None}, {"ratio": None}], "division_by_zero_signal"),
    ("ADV-19", "Average citation count of open-access vs non-open-access publications.", "SELECT AVG(CAST(total_citations AS INTEGER)) FROM advance_search_data", [{"avg": 0}], "text_cast_silent_failure"),
    ("ADV-20", "Researchers listed as inventor on a patent plus publication in same subfield plus funding record from a ministry.", "SELECT * FROM a JOIN b ON a.name = b.name JOIN c ON c.name = b.name JOIN d ON d.name = c.name", [], "row_count_zero"),
]


@pytest.mark.parametrize("case_id, question, sql, rows, expected_signal", DHAIRYA_CASES + ADV_CASES)
def test_corpus_cases_are_corrected_or_marked_for_clarification(case_id, question, sql, rows, expected_signal):
    report = detect_result_anomalies(question, sql, {"row_count": len(rows), "results": rows})
    signal_names = {signal.name for signal in report.signals}

    if expected_signal:
        assert expected_signal in signal_names, case_id
        assert report.answer_confidence in {"partial", "low_clarify"}
    else:
        assert report.answer_confidence in {"high", "partial"}
        assert not any(signal.severity == "high" for signal in report.signals)


def test_verifier_refuses_low_confidence_sql_answer():
    report = detect_result_anomalies(
        "List researchers on a patent with a grant in the same financial year.",
        "SELECT g.institute FROM innovation_grant_from_govt g JOIN combined_ipo_patent_data p ON g.institute = p.applicants",
        {"row_count": 0, "results": []},
    )
    state = {
        "synthesized_response": "I found no matching researchers. [cite:structured:0]",
        "sql_results": [],
        "sql_anomaly_report": report.to_dict(),
        "verification_retries": 0,
        "synthesis_method": "rule_based",
    }

    verified = verifier_node(state)

    assert verified["verification_status"] == "fail"
    assert verified["answer_confidence"] == "low_clarify"
    assert "low confidence" in verified["synthesized_response"].lower()

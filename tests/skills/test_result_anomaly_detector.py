"""LB-7 result anomaly detector coverage."""

from __future__ import annotations

import pytest

from src.skills.text_to_sql.result_anomaly_detector import detect_result_anomalies


def _signal_names(report):
    return {signal.name for signal in report.signals}


def test_row_count_zero_positive_for_joined_analytical_query():
    report = detect_result_anomalies(
        "List institutes with grant funding and patent output.",
        "SELECT g.institute FROM innovation_grant_from_govt g JOIN combined_ipo_patent_data p ON g.institute = p.applicants",
        {"row_count": 0, "results": []},
    )

    assert "row_count_zero" in _signal_names(report)
    assert report.answer_confidence == "low_clarify"


def test_row_count_zero_negative_for_simple_lookup():
    report = detect_result_anomalies(
        "Find the record for institute code ABC.",
        "SELECT * FROM tb_institute_mstr WHERE short_name = 'ABC'",
        {"row_count": 0, "results": []},
    )

    assert "row_count_zero" not in _signal_names(report)


def test_row_count_one_with_limit_missing_positive():
    report = detect_result_anomalies(
        "Top 5 funding agencies by total grant amount.",
        "SELECT gov_organisation_name, SUM(grant_received) AS total FROM innovation_grant_from_govt GROUP BY gov_organisation_name",
        {"row_count": 1, "results": [{"gov_organisation_name": "DST", "total": 12000000}]},
    )

    assert "row_count_one_with_limit_missing" in _signal_names(report)


def test_row_count_one_with_limit_missing_negative_for_count():
    report = detect_result_anomalies(
        "How many publications are open access?",
        "SELECT COUNT(*) AS total FROM advance_search_data WHERE open_access_status = 'Open'",
        {"row_count": 1, "results": [{"total": 42}]},
    )

    assert "row_count_one_with_limit_missing" not in _signal_names(report)


def test_null_ratio_high_positive():
    report = detect_result_anomalies(
        "Compare grants and patent counts by institute.",
        "SELECT g.institute, p.patent_count FROM grants g LEFT JOIN patents p ON p.institute = g.institute",
        {
            "row_count": 4,
            "results": [
                {"institute": "IIT Bombay", "patent_count": None},
                {"institute": "IIT Madras", "patent_count": None},
                {"institute": "IIT Delhi", "patent_count": None},
                {"institute": "IIT Kanpur", "patent_count": 3},
            ],
        },
    )

    assert "null_ratio_high" in _signal_names(report)


def test_null_ratio_high_negative():
    report = detect_result_anomalies(
        "Compare grants and patent counts by institute.",
        "SELECT institute, patent_count FROM patent_counts",
        {
            "row_count": 3,
            "results": [
                {"institute": "IIT Bombay", "patent_count": 5},
                {"institute": "IIT Madras", "patent_count": 4},
                {"institute": "IIT Delhi", "patent_count": 3},
            ],
        },
    )

    assert "null_ratio_high" not in _signal_names(report)


def test_aggregate_collapse_positive():
    report = detect_result_anomalies(
        "Break down publications by IIT/NIT/Other.",
        "SELECT category, AVG(total_citations) FROM advance_search_data GROUP BY category",
        {"row_count": 1, "results": [{"category": "IIT", "avg": 20}]},
    )

    assert "aggregate_collapse" in _signal_names(report)


def test_aggregate_collapse_negative():
    report = detect_result_anomalies(
        "Break down publications by IIT/NIT/Other.",
        "SELECT category, AVG(total_citations) FROM advance_search_data GROUP BY category",
        {
            "row_count": 3,
            "results": [
                {"category": "IIT", "avg": 20},
                {"category": "NIT", "avg": 14},
                {"category": "Other", "avg": 9},
            ],
        },
    )

    assert "aggregate_collapse" not in _signal_names(report)


def test_division_by_zero_signal_positive_for_unguarded_ratio():
    report = detect_result_anomalies(
        "Top institutes by patents_granted/phd_students_graduated ratio.",
        "SELECT patents_granted / phd_students_graduated AS ratio FROM ratios",
        {"row_count": 2, "results": [{"ratio": None}, {"ratio": None}]},
    )

    assert "division_by_zero_signal" in _signal_names(report)


def test_division_by_zero_signal_negative_for_nullif():
    report = detect_result_anomalies(
        "Top institutes by patents_granted/phd_students_graduated ratio.",
        "SELECT patents_granted / NULLIF(phd_students_graduated, 0) AS ratio FROM ratios",
        {"row_count": 2, "results": [{"ratio": 1.2}, {"ratio": 0.8}]},
    )

    assert "division_by_zero_signal" not in _signal_names(report)


def test_text_cast_silent_failure_positive_for_direct_cast():
    report = detect_result_anomalies(
        "Average citation count of open-access vs non-open-access publications.",
        "SELECT AVG(CAST(total_citations AS INTEGER)) FROM advance_search_data",
        {"row_count": 1, "results": [{"avg": 0}]},
    )

    assert "text_cast_silent_failure" in _signal_names(report)


def test_text_cast_silent_failure_negative_for_regex_guard():
    report = detect_result_anomalies(
        "Average citation count of open-access vs non-open-access publications.",
        "SELECT AVG(CASE WHEN total_citations ~ '^[0-9]+$' THEN total_citations::int END) FROM advance_search_data",
        {"row_count": 1, "results": [{"avg": 22.5}]},
    )

    assert "text_cast_silent_failure" not in _signal_names(report)


def test_entity_resolution_join_risk_positive():
    report = detect_result_anomalies(
        "Cost per patent using government grants.",
        "SELECT g.institute FROM innovation_grant_from_govt g JOIN combined_ipo_patent_data p ON g.institute = p.applicants",
        {"row_count": 3, "results": [{"institute": "IIT Bombay"}]},
    )

    assert "entity_resolution_join_risk" in _signal_names(report)


def test_metric_too_perfect_positive():
    report = detect_result_anomalies(
        "Show conversion percentage from Level 4 to Level 9.",
        "SELECT institute, 100 AS conversion_rate FROM vw_innovations_trl",
        {
            "row_count": 3,
            "results": [
                {"institute": "IIT Bombay", "conversion_rate": 100},
                {"institute": "IIT Madras", "conversion_rate": 100},
                {"institute": "IIT Delhi", "conversion_rate": 100},
            ],
        },
    )

    assert "metric_too_perfect" in _signal_names(report)

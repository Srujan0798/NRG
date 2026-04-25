from src.skills.text_to_sql.skill import detect_semantic_anomaly


def test_detects_zero_row_risky_applicant_join():
    result = {"row_count": 0, "results": [], "columns": []}
    sql = """
        SELECT g.institute, COUNT(p.application_number)
        FROM innovation_grant_from_govt g
        JOIN combined_ipo_patent_data p ON g.institute = p.applicants
        GROUP BY g.institute
    """

    anomaly = detect_semantic_anomaly(
        "cost per patent for government grants",
        sql,
        result,
    )

    assert anomaly["detected"] is True
    assert anomaly["needs_clarification"] is True
    assert "applicant" in anomaly["clarification_question"].lower()


def test_normalized_nonempty_join_is_not_anomalous():
    result = {
        "row_count": 2,
        "results": [{"institute": "IIT Bombay", "patent_count": 5}],
        "columns": ["institute", "patent_count"],
    }
    sql = """
        SELECT g.institute, COUNT(p.application_number)
        FROM innovation_grant_from_govt g
        JOIN combined_ipo_patent_data p
          ON lower(trim(p.applicants)) LIKE '%' || lower(trim(g.institute)) || '%'
        GROUP BY g.institute
    """

    anomaly = detect_semantic_anomaly("cost per patent", sql, result)

    assert anomaly["detected"] is False


def test_single_table_zero_result_does_not_force_join_clarification():
    anomaly = detect_semantic_anomaly(
        "robot-assisted surgery patents in IIT Ropar",
        "SELECT * FROM patents_details WHERE institute = 'IIT Ropar'",
        {"row_count": 0, "results": [], "columns": []},
    )

    assert anomaly["detected"] is False

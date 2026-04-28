from pathlib import Path
import re


HALL_PATH = Path("src/data/schema/failed_queries/HALL_OF_SHAME.md")


def test_failed_queries_hall_documents_all_dhairya_patterns():
    text = HALL_PATH.read_text(encoding="utf-8")

    pattern_headers = re.findall(r"^## P\d+:", text, flags=re.MULTILINE)

    assert len(pattern_headers) == 7
    assert text.startswith("# Hall of Shame — NRG Text-to-SQL Adversarial Failures")

    for field in (
        "- Original query:",
        "- Wrong SQL generated:",
        "- Why it failed:",
        "- Fix applied:",
        "- Test covering this:",
    ):
        assert text.count(field) == 7

    assert "SUM(CAST(\"total_credit_score\" AS INTEGER))" in text
    assert "SELECT DISTINCT \"gov_organisation_name\"" in text
    assert "WHERE \"stage_of_technology\" = 'TRL 9'" in text
    assert "-- [INCOMPLETE — missing HAVING / audit condition]" in text
    assert "SPLIT_PART" in text
    assert "Level 9" in text
    assert "combined_ipo_patent_data.applicants" in text

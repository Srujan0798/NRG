from pathlib import Path
import re


HALL_PATH = Path("src/data/schema/failed_queries/HALL_OF_SHAME.md")


def test_failed_queries_hall_documents_all_dhairya_patterns():
    text = HALL_PATH.read_text(encoding="utf-8")

    pattern_headers = re.findall(r"^### P\d+:", text, flags=re.MULTILINE)

    assert len(pattern_headers) == 7
    assert "SPLIT_PART" in text
    assert "Level 9" in text
    assert "combined_ipo_patent_data.applicants" in text

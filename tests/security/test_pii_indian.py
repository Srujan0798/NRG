"""Indian PII detection regression tests for DPDP evidence."""

from src.security.pii import scan
from src.security.pii.verhoeff import validate_aadhaar


def _types(text: str) -> set[str]:
    return {entity["type"] for entity in scan(text)["entities"]}


def test_aadhaar_grouped_detected():
    assert "aadhaar_spaced" in _types("Aadhaar holder 1234 5678 9012")


def test_aadhaar_dashed_detected():
    assert "aadhaar" in _types("Aadhaar: 1234-5678-9010")


def test_aadhaar_verhoeff_rejects_invalid_demo_number():
    assert validate_aadhaar("1234 5678 9012") is False


def test_pan_detected():
    assert "pan" in _types("PAN ABCDE1234F belongs to a grant recipient")


def test_phone_detected():
    assert "phone" in _types("Call 9876543210 for outreach")


def test_phone_91_detected():
    assert "phone_91" in _types("Call +91 9876543210")


def test_email_detected():
    assert "email" in _types("Contact researcher@iitb.ac.in")


def test_academic_email_detected():
    assert "email_academic_in" in _types("Contact pi@iitgn.ac.in")


def test_gstin_detected():
    assert "gstin" in _types("GSTIN 27ABCDE1234F1Z5")


def test_clean_research_query_has_no_pii():
    result = scan("Show renewable energy research trends")
    assert result["detected_pii"] is False

"""Property checks for tier response-shape isolation."""

from __future__ import annotations

from typing import Any

from hypothesis import HealthCheck, given, settings, strategies as st

from src.api.response_filter import (
    filter_response_payload_for_tier,
    find_tier_response_violations,
    required_tier_response_fields,
)


PII_FIELDS = (
    "email",
    "phone",
    "aadhaar",
    "pan",
    "dob",
    "full_address",
    "bank_account",
    "gstin",
)

SAFE_FIELDS = (
    "research_area",
    "institution_id",
    "state",
    "publication_id",
    "citation_count",
    "personal_name",
)

pii_values = st.sampled_from(
    [
        "researcher@iitgn.ac.in",
        "9876543210",
        "1234 5678 9012",
        "ABCDE1234F",
        "22AAAAA0000A1Z5",
        "A-12, Research Colony, Gandhinagar",
        "123456789012",
        "1980-04-12",
    ]
)

row_strategy = st.dictionaries(
    keys=st.sampled_from(PII_FIELDS + SAFE_FIELDS),
    values=st.one_of(pii_values, st.integers(min_value=1, max_value=9999), st.text(min_size=1, max_size=24)),
    min_size=1,
    max_size=10,
)

payload_strategy = st.builds(
    lambda row, citation, source: {
        "sql_results": [row],
        "citations": [citation],
        "retrieval_sources": [source],
        "response": "Contact researcher@iitgn.ac.in or 9876543210 for details.",
    },
    row=row_strategy,
    citation=row_strategy,
    source=row_strategy,
)


def _contains_disallowed_key(value: Any, tier: int) -> bool:
    return bool(find_tier_response_violations(value, tier=tier))


def test_policy_declares_required_response_boundary_fields():
    fields = required_tier_response_fields()
    for field in PII_FIELDS:
        assert field in fields


@settings(max_examples=1000, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(payload=payload_strategy, tier=st.sampled_from([1, 2, 3]))
def test_random_response_payloads_never_expose_disallowed_tier_columns(payload, tier):
    filtered, report = filter_response_payload_for_tier(payload, tier=tier)

    assert not _contains_disallowed_key(filtered, tier)
    if tier >= 2:
        serialized = str(filtered)
        assert "researcher@iitgn.ac.in" not in serialized
        assert "9876543210" not in serialized
    if tier == 3 and "personal_name" in payload["sql_results"][0]:
        assert filtered["sql_results"][0]["personal_name"].startswith("Researcher_")
    assert isinstance(report.strip_events, list)

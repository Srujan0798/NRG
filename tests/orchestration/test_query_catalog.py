"""Tests for the deterministic query catalog used by planner/router v2."""

from src.orchestration.query_catalog import classify_query, get_catalog


def test_catalog_routes_funding_rank_to_sql():
    result = classify_query("Top 5 funding agencies by total grant amount")

    assert result.route == "text_to_sql"
    assert result.confidence >= 0.85
    assert result.output_shape == "ranked_table"
    assert "innovation_grant_from_govt" in result.matched_tables
    assert "funding" in result.matched_domains


def test_catalog_routes_research_summary_to_rag():
    result = classify_query("Summarize recent research directions in hydrogen catalysis")

    assert result.route == "rag"
    assert result.output_shape == "narrative_summary"
    assert result.confidence >= 0.7
    assert any(
        "document" in item.lower() or "explanatory" in item.lower() for item in result.rationale
    )


def test_catalog_routes_mixed_structured_and_explanatory_query_to_hybrid():
    result = classify_query(
        "Find IIT Gandhinagar hydrogen collaborators and explain their recent work"
    )

    assert result.route == "text_to_sql+rag"
    assert result.output_shape == "mixed_summary"
    assert {"research", "collaboration"}.intersection(result.matched_domains)
    assert result.matched_tables


def test_catalog_clarifies_vague_best_query():
    result = classify_query("Who is the best?")

    assert result.route == "clarify"
    assert result.needs_clarification is True
    assert result.clarification_question
    assert "domain" in result.clarification_question.lower()


def test_catalog_blocks_direct_pii_request():
    result = classify_query("Give researcher emails and phone numbers for AI labs")

    assert result.route == "blocked"
    assert result.blocked_reason
    assert {"email", "phone"}.issubset(set(result.pii_terms))


def test_catalog_exposes_table_metadata_without_pii_columns_in_safe_columns():
    catalog = get_catalog()
    researchers = catalog.get_table("researchers")

    assert researchers is not None
    assert "email" in researchers.pii_columns
    assert "email" not in researchers.safe_columns

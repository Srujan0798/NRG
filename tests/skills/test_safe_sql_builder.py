"""Tests for catalog-backed safe SQL planning."""

from src.skills.text_to_sql.safe_sql_builder import MAX_SAFE_SQL_LIMIT, build_safe_sql


def test_builds_funding_rank_query_from_catalog():
    result = build_safe_sql("Top 5 funding agencies by total grant amount")

    assert result.status == "ready"
    assert result.table == "innovation_grant_from_govt"
    assert result.route == "text_to_sql"
    assert result.sql is not None
    sql = result.sql.lower()
    assert "select gov_organisation_name" in sql
    assert "sum(grant_received)" in sql
    assert "from innovation_grant_from_govt" in sql
    assert "group by gov_organisation_name" in sql
    assert "order by total_grant desc" in sql
    assert "limit 5" in sql
    assert "*" not in sql


def test_clamps_requested_rank_limit_and_uses_safe_researcher_columns():
    result = build_safe_sql("Top 500 researchers by h-index")

    assert result.status == "ready"
    assert result.table == "researchers"
    assert result.sql is not None
    sql = result.sql.lower()
    assert f"limit {MAX_SAFE_SQL_LIMIT}" in sql
    assert "email" not in sql
    assert "phone" not in sql
    assert "order by h_index desc" in sql


def test_builds_institution_lookup_from_catalog():
    result = build_safe_sql("List institutions in Gujarat")

    assert result.status == "ready"
    assert result.table == "institutions"
    assert result.sql is not None
    sql = result.sql.lower()
    assert "select name, type, state, country, founded_year from institutions" in sql
    assert "where lower(state) = 'gujarat'" in sql
    assert "limit 100" in sql


def test_builds_publication_ranking_from_catalog():
    result = build_safe_sql("Top 10 publications by citations")

    assert result.status == "ready"
    assert result.table == "publications"
    assert result.sql is not None
    sql = result.sql.lower()
    assert "from publications" in sql
    assert "order by citations desc" in sql
    assert "limit 10" in sql


def test_blocks_direct_pii_request_before_sql_generation():
    result = build_safe_sql("Give researcher emails and phone numbers for AI labs")

    assert result.status == "blocked"
    assert result.sql is None
    assert result.blocked_reason
    assert {"email", "phone"}.issubset(set(result.pii_terms))


def test_document_only_question_is_unsupported_for_safe_sql():
    result = build_safe_sql("Summarize recent research directions in hydrogen catalysis")

    assert result.status == "unsupported"
    assert result.sql is None


def test_text_to_sql_skill_uses_safe_builder_before_llm():
    from src.skills.text_to_sql.skill import TextToSQLSkill

    class FailingLLM:
        model = "should-not-be-called"

        def chat(self, messages):
            raise AssertionError("LLM should not be called for deterministic safe SQL")

    skill = TextToSQLSkill(llm_provider=FailingLLM())
    try:
        sql = skill.generate_sql(
            "Top 5 funding agencies by total grant amount",
            schema_prompt="Table: innovation_grant_from_govt",
        )
    finally:
        skill.close()

    assert "innovation_grant_from_govt" in sql
    assert "LIMIT 5" in sql.upper()

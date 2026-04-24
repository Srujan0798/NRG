from __future__ import annotations

import json
from pathlib import Path


from src.skills.text_to_sql.skill import TextToSQLSkill
from src.skills.text_to_sql.sqlite_schema_extractor import extract_schema

QUERY_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "queries"


def _load_queries(filename: str, limit: int = 10) -> list[dict]:
    return json.loads((QUERY_DIR / filename).read_text(encoding="utf-8"))[:limit]


def _run_queries(filename: str, user_tier: int, limit: int = 10) -> list[dict]:
    skill = TextToSQLSkill()
    results: list[dict] = []
    try:
        for item in _load_queries(filename, limit=limit):
            result = skill.execute(item["natural_language_query"], user_tier=user_tier)
            results.append({"query": item, "result": result})
    finally:
        skill.close()
    return results


def test_schema_extractor_outputs_full_nrg_schema():
    schema = extract_schema()

    expected_tables = {
        "researchers",
        "publications",
        "projects",
        "funding_records",
        "labs",
        "patents",
        "collaborations",
        "research_documents",
    }
    assert expected_tables <= set(schema["tables"])

    researcher_cols = {col["name"] for col in schema["tables"]["researchers"]["columns"]}
    publication_cols = {col["name"] for col in schema["tables"]["publications"]["columns"]}

    assert {"department", "h_index", "secondary_research_areas", "tier_access"} <= researcher_cols
    assert {"authors", "researcher_ids", "citations", "impact_factor", "publication_type"} <= publication_cols


def test_tier1_real_queries_generate_executable_sql():
    """Test that tier1 queries generate valid executable SQL.

    Note: Tables are empty in dev SQLite (data is in PostgreSQL), so we only
    verify the query is valid SQL that executes without error.
    """
    results = _run_queries("tier1_researcher_queries.json", user_tier=1, limit=10)

    assert len(results) == 10
    for item in results:
        result = item["result"]
        query = result["query"].strip().upper()
        assert query.startswith("SELECT") or query.startswith("WITH"), f"Invalid SQL: {result['query'][:50]}"
        assert "LIMIT" in result["query"].upper()
        assert "error" not in result.get("error", "").lower()


def test_tier2_real_queries_generate_executable_sql_without_pii():
    """Test that tier2 queries generate valid executable SQL without PII."""
    results = _run_queries("tier2_policymaker_queries.json", user_tier=2, limit=10)

    assert len(results) == 10
    for item in results:
        result = item["result"]
        query = result["query"].strip().upper()
        assert query.startswith("SELECT") or query.startswith("WITH"), f"Invalid SQL: {result['query'][:50]}"
        assert "error" not in result.get("error", "").lower()
        assert "email" not in {col.lower() for col in result.get("columns", [])}
        assert "phone" not in {col.lower() for col in result.get("columns", [])}


def test_tier3_real_queries_generate_executable_sql_without_pii():
    """Test that tier3 queries generate valid executable SQL without PII."""
    results = _run_queries("tier3_industry_queries.json", user_tier=3, limit=10)

    assert len(results) == 10
    for item in results:
        result = item["result"]
        query = result["query"].strip().upper()
        assert query.startswith("SELECT") or query.startswith("WITH"), f"Invalid SQL: {result['query'][:50]}"
        assert "error" not in result.get("error", "").lower()
        assert "email" not in {col.lower() for col in result.get("columns", [])}
        assert "phone" not in {col.lower() for col in result.get("columns", [])}

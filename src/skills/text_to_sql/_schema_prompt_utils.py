"""Shared schema prompt utilities — deduplicated from sqlite_schema_extractor and schema_extractor."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


DEFAULT_TABLES = frozenset({
    "researchers",
    "institutions",
    "labs",
    "projects",
    "publications",
    "funding_records",
})

TABLE_KEYWORDS: dict[str, list[str]] = {
    "researchers": ["researcher", "faculty", "professor", "scientist", "people", "person"],
    "labs": ["lab", "laboratory", "center"],
    "publications": [
        "publication", "paper", "article", "journal", "conference",
    ],
    "projects": ["project", "pi", "co-pi", "co pi", "principal investigator", "ongoing", "completed"],
    "patents": ["patent", "inventor", "filing", "grant", "technology transfer", "ip"],
    "collaborations": ["collaboration", "partner", "network", "cross-institutional"],
    "research_documents": ["document", "research document", "full text", "category"],
    "funding_records": ["funding", "grant", "fund", "budget"],
    "institutions": ["institution", "university", "iit", "nit", "college"],
    "keywords": ["topic", "keyword", "specialization"],
    "researcher_publications": ["author", "wrote", "published"],
    "researcher_labs": ["member", "works in", "affiliated"],
    "academic_courses_details": [
        "course", "pg course", "ug course", "phd course", "master course",
        "innovation curriculum", "credit", "academic", "level of course",
        "total credit", "curriculum", "iit madras", "iit bombay", "iit hyderabad",
    ],
    "innovation_grant_from_govt": [
        "grant", "funding agency", "government grant", "gov_organisation",
        "year of receiving", "funding drop", "rising star", "funding trend",
        "grant received", "yoy", "year-over-year",
    ],
    "trl_stages": [
        "trl", "technology readiness", "stage of technology", "market ready",
        "lab validation", "bottleneck", "level 9", "trl 9", "pipeline progression",
        "level 4", "various stage", "technology readiness level",
    ],
    "combined_ipo_patent_data": ["patent", "ipo", "grant", "cost per patent"],
    "financial_expenses_capital": [
        "capital expense", "capex", "capital asset", "equipment", "library",
        "workshop", "high capital", "gap analysis", "financial expense",
    ],
    "financial_expenses_operational": [
        "operational expense", "opex", "salary", "manpower", "running cost",
    ],
    "consultancy_projects": [
        "consultancy", "industry project", "corporate", "revenue", "client",
    ],
    "innovation_ip_ipo": ["ipo", "public issue", "listing", "startup", "spin-off"],
}


def get_relevant_tables_for_query(query: str, all_table_names: list[str]) -> list[str]:
    """Return tables matching query keywords, falling back to all_table_names."""
    query_lower = query.lower()
    matched: list[str] = []
    for table_name, keywords in TABLE_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            if table_name in all_table_names:
                matched.append(table_name)
    return matched if matched else all_table_names


_SCHEMA_HINTS_CACHE: str | None = None
_VALUE_SYNONYMS_CACHE: str | None = None


def _load_schema_hints() -> str:
    global _SCHEMA_HINTS_CACHE
    if _SCHEMA_HINTS_CACHE is not None:
        return _SCHEMA_HINTS_CACHE
    hints_file = Path(__file__).resolve().parents[2] / "data" / "schema" / "schema_hints.md"
    if hints_file.exists():
        _SCHEMA_HINTS_CACHE = hints_file.read_text()
    else:
        _SCHEMA_HINTS_CACHE = ""
    return _SCHEMA_HINTS_CACHE


def _load_value_synonyms() -> str:
    global _VALUE_SYNONYMS_CACHE
    if _VALUE_SYNONYMS_CACHE is not None:
        return _VALUE_SYNONYMS_CACHE
    synonyms_file = Path(__file__).resolve().parents[2] / "data" / "schema" / "schema_value_synonyms.md"
    if synonyms_file.exists():
        _VALUE_SYNONYMS_CACHE = synonyms_file.read_text()
    else:
        _VALUE_SYNONYMS_CACHE = ""
    return _VALUE_SYNONYMS_CACHE


def generate_llm_prompt(schema: dict[str, Any], dialect: str = "sqlite") -> str:
    """Build LLM prompt from schema dict. dialect='sqlite' or 'postgresql'."""
    prompt_parts = ["DATABASE SCHEMA (metadata only - no data values):", ""]
    for table_name, table_info in schema["tables"].items():
        prompt_parts.append(f"## Table: {table_name}")
        prompt_parts.append("Columns:")
        for col in table_info["columns"]:
            nullable = "NULL" if col["nullable"] else "NOT NULL"
            prompt_parts.append(f"  - {col['name']}: {col['type']} {nullable}")
        if table_info["primary_keys"]:
            prompt_parts.append(f"  PRIMARY KEY: {', '.join(table_info['primary_keys'])}")
        if table_info["foreign_keys"]:
            prompt_parts.append("Foreign Keys:")
            for fk in table_info["foreign_keys"]:
                prompt_parts.append(
                    f"    - {', '.join(fk['constrained_columns'])} -> "
                    f"{fk['referred_table']}.{', '.join(fk['referred_columns'])}"
                )
        prompt_parts.append("")
    hints = _load_schema_hints()
    if hints:
        prompt_parts.extend(["", "SCHEMA HINTS:", hints])
    synonyms = _load_value_synonyms()
    if synonyms:
        prompt_parts.extend(["", "DOMAIN VALUE SYNONYMS:", synonyms])
    return "\n".join(prompt_parts)


def relevant_tables_for_query(
    query: str,
    all_table_names: list[str],
    default_tables: frozenset[str] | set[str] = DEFAULT_TABLES,
) -> list[str]:
    """Return keyword-matched tables, or default_tables if nothing matches."""
    query_lower = query.lower()
    matched: list[str] = []
    for table_name, keywords in TABLE_KEYWORDS.items():
        if table_name not in all_table_names:
            continue
        if any(kw in query_lower for kw in keywords):
            matched.append(table_name)
    if not matched:
        matched = [t for t in all_table_names if t in default_tables]
    return matched if matched else list(all_table_names)

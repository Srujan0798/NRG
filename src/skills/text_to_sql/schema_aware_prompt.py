"""Schema-aware prompt guidance for Text-to-SQL generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "db_struct.sql"


@dataclass(frozen=True)
class ColumnInfo:
    table: str
    name: str
    sql_type: str


def build_schema_aware_prompt(
    user_query: str,
    *,
    dialect: str,
    schema_path: Path | str = DEFAULT_SCHEMA_PATH,
) -> str:
    """Return guidance driven by real schema types in db_struct.sql."""
    schema = parse_schema_columns(Path(schema_path))
    query = user_query.lower()
    guidance: list[str] = []

    credit_col = schema.get(("academic_courses_details", "total_credit_score"))
    if credit_col and "text" in credit_col.sql_type.lower() and _mentions_credit_intensity(query):
        if dialect == "postgresql":
            guidance.append(
                "academic_courses_details.total_credit_score is TEXT in X:Y format. "
                "For credit totals use SUM(SPLIT_PART(total_credit_score, ':', 1)::double precision "
                "+ COALESCE(NULLIF(SPLIT_PART(total_credit_score, ':', 2), '')::double precision, 0)); "
                "for national average compare each institute total to AVG(total_credits). "
                "Do not cast total_credit_score directly."
            )
        else:
            guidance.append(
                "academic_courses_details.total_credit_score is TEXT in X:Y format. "
                "For credit totals use SUM(CAST(SUBSTR(total_credit_score, 1, INSTR(total_credit_score, ':') - 1) AS REAL) "
                "+ COALESCE(CAST(NULLIF(SUBSTR(total_credit_score, INSTR(total_credit_score, ':') + 1), '') AS REAL), 0)); "
                "for national average compare each institute total to AVG(total_credits). "
                "Do not cast total_credit_score directly."
            )

    if _mentions_stage_transition(query):
        guidance.append(
            "TRL and commercialization stages live in "
            "trl_stages.stage_of_technology. "
            "Map Lab Validation to 'Level 4' and Market Ready or TRL 9 to 'Level 9'. "
            "Trend answers must GROUP BY financial_year, stage_of_technology."
        )

    if _mentions_grant_patent_efficiency(query):
        guidance.append(
            "Grant and patent efficiency requires CTEs over innovation_grant_from_govt and "
            "combined_ipo_patent_data. Patent applicant text is in combined_ipo_patent_data.applicants; "
            "join with lower(trim(applicants)) LIKE '%' || lower(trim(institute)) || '%' and filter status = 'Granted'."
        )

    if _mentions_grant_trend(query):
        guidance.append(
            "Year-over-year grant analysis must first aggregate by institute and year_of_receiving in a CTE, "
            "then self-join adjacent years. Do not compare raw grant rows."
        )

    if _mentions_ranked_funding(query):
        guidance.append(
            "Ranked funding agency answers require GROUP BY gov_organisation_name and ORDER BY SUM(grant_received) DESC."
        )

    if not guidance:
        return ""

    return "SCHEMA-AWARE SQL GUIDANCE:\n- " + "\n- ".join(guidance)


@lru_cache(maxsize=4)
def parse_schema_columns(schema_path: Path) -> dict[tuple[str, str], ColumnInfo]:
    """Parse table and column types from a PostgreSQL schema dump."""
    text = schema_path.read_text(encoding="utf-8")
    columns: dict[tuple[str, str], ColumnInfo] = {}
    table_re = re.compile(
        r"CREATE TABLE public\.([A-Za-z0-9_]+)\s*\((.*?)\n\);",
        re.DOTALL,
    )

    for table_name, body in table_re.findall(text):
        for raw_line in body.splitlines():
            line = raw_line.strip().rstrip(",")
            if not line or line.startswith("--"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            column_name = parts[0].strip('"')
            if column_name.upper() in {"CONSTRAINT", "PRIMARY", "FOREIGN", "UNIQUE", "CHECK"}:
                continue
            sql_type = " ".join(parts[1:])
            columns[(table_name, column_name)] = ColumnInfo(
                table=table_name,
                name=column_name,
                sql_type=sql_type,
            )

    return columns


def _mentions_credit_intensity(query: str) -> bool:
    return any(term in query for term in ("credit", "curriculum", "intensive", "national average"))


def _mentions_stage_transition(query: str) -> bool:
    return any(
        term in query
        for term in (
            "trl",
            "lab validation",
            "market ready",
            "bottleneck",
            "technology readiness",
            "commercialization",
            "commercialisation",
        )
    )


def _mentions_grant_patent_efficiency(query: str) -> bool:
    return "patent" in query and any(term in query for term in ("grant", "funding", "spend", "cost", "doing more"))


def _mentions_grant_trend(query: str) -> bool:
    return any(term in query for term in ("year-over-year", "yoy", "dropped", "declined", "cut grants"))


def _mentions_ranked_funding(query: str) -> bool:
    return "funding agenc" in query or "top 5" in query and "grant" in query

"""Catalog-backed deterministic SQL builder.

This module handles high-confidence structured questions before model SQL
generation. It only emits read-only SQL for known tables and safe columns.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Literal

import sqlglot
from sqlglot import exp

from src.orchestration.query_catalog import QueryClassification, classify_query


MAX_SAFE_SQL_LIMIT = 200
DEFAULT_SAFE_SQL_LIMIT = 100

SafeSQLStatus = Literal["ready", "blocked", "unsupported"]

SAFE_COLUMNS_BY_TABLE: dict[str, set[str]] = {
    "innovation_grant_from_govt": {
        "gov_organisation_name",
        "grant_received",
        "year_of_receiving",
        "institute",
        "as_on_year",
    },
    "researchers": {
        "name",
        "institution_id",
        "department",
        "state",
        "research_area",
        "secondary_research_areas",
        "years_experience",
        "year_joined",
        "h_index",
        "total_funding_received_inr_crores",
        "access_tier",
    },
    "publications": {
        "title",
        "authors",
        "venue",
        "year",
        "citations",
        "impact_factor",
        "publication_type",
        "research_area",
        "access_tier",
    },
    "labs": {
        "name",
        "institution_id",
        "research_area",
        "research_focus_areas",
        "established_year",
        "location_state",
    },
    "institutions": {
        "name",
        "type",
        "state",
        "country",
        "founded_year",
        "access_tier",
    },
    "academic_courses_details": {
        "financial_year",
        "title_of_course",
        "course_code",
        "type_of_course",
        "level_of_course",
        "course_offering_department",
        "total_credit_score",
        "institute",
        "as_on_year",
    },
    "trl_stages": {
        "innovation_name",
        "stage_of_technology",
        "financial_year",
        "institute",
        "as_on_year",
    },
}

PII_COLUMNS = {"email", "phone", "mobile", "aadhaar", "aadhar", "pan", "passport"}


@dataclass(frozen=True)
class SafeSQLBuildResult:
    status: SafeSQLStatus
    route: str
    confidence: float
    sql: str | None = None
    table: str | None = None
    blocked_reason: str | None = None
    pii_terms: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        data = asdict(self)
        return {
            key: list(value) if isinstance(value, tuple) else value for key, value in data.items()
        }


def build_safe_sql(user_query: str, user_tier: int = 1) -> SafeSQLBuildResult:
    classification = classify_query(user_query, user_tier=user_tier)

    if classification.route == "blocked":
        return SafeSQLBuildResult(
            status="blocked",
            route=classification.route,
            confidence=classification.confidence,
            blocked_reason=classification.blocked_reason
            or "Question requests blocked personal data.",
            pii_terms=classification.pii_terms,
        )

    if classification.route not in {"text_to_sql", "text_to_sql+rag"}:
        return SafeSQLBuildResult(
            status="unsupported",
            route=classification.route,
            confidence=classification.confidence,
            warnings=("Question is not a deterministic structured SQL request.",),
        )

    sql = _build_sql_for_classification(user_query, classification)
    if sql is None:
        return SafeSQLBuildResult(
            status="unsupported",
            route=classification.route,
            confidence=classification.confidence,
            warnings=("No safe deterministic SQL shape matched this query.",),
        )

    table = _first_table(sql)
    _validate_builder_sql(sql)
    return SafeSQLBuildResult(
        status="ready",
        route=classification.route,
        confidence=classification.confidence,
        sql=sql,
        table=table,
    )


def _build_sql_for_classification(
    user_query: str,
    classification: QueryClassification,
) -> str | None:
    query_lower = user_query.lower()
    tables = list(classification.matched_tables)

    if "innovation_grant_from_govt" in tables:
        return _funding_sql(query_lower)
    if "researchers" in tables:
        return _researchers_sql(query_lower)
    if "publications" in tables:
        return _publications_sql(query_lower)
    if "labs" in tables:
        return _simple_list_sql(
            "labs",
            ("name", "research_area", "research_focus_areas", "location_state"),
            _requested_limit(query_lower),
        )
    if "institutions" in tables:
        return _institutions_sql(query_lower)
    if "academic_courses_details" in tables:
        return _simple_list_sql(
            "academic_courses_details",
            (
                "institute",
                "title_of_course",
                "course_code",
                "level_of_course",
                "total_credit_score",
                "financial_year",
            ),
            _requested_limit(query_lower),
        )
    if "trl_stages" in tables:
        return _simple_list_sql(
            "trl_stages",
            ("innovation_name", "stage_of_technology", "financial_year", "institute"),
            _requested_limit(query_lower),
        )
    return None


def _funding_sql(query_lower: str) -> str:
    limit = _requested_limit(query_lower)
    if (
        "count" in query_lower
        and "amount" not in query_lower
        and "grant_received" not in query_lower
    ):
        return (
            "SELECT gov_organisation_name, COUNT(*) AS grant_count "
            "FROM innovation_grant_from_govt "
            "GROUP BY gov_organisation_name "
            "ORDER BY grant_count DESC "
            f"LIMIT {limit}"
        )
    return (
        "SELECT gov_organisation_name, SUM(grant_received) AS total_grant "
        "FROM innovation_grant_from_govt "
        "GROUP BY gov_organisation_name "
        "ORDER BY total_grant DESC "
        f"LIMIT {limit}"
    )


def _researchers_sql(query_lower: str) -> str:
    limit = _requested_limit(query_lower)
    columns = (
        "name",
        "state",
        "research_area",
        "department",
        "h_index",
        "total_funding_received_inr_crores",
    )
    order_by = (
        " ORDER BY h_index DESC" if "h-index" in query_lower or "h index" in query_lower else ""
    )
    predicate = " WHERE h_index IS NOT NULL" if order_by else ""
    return f"SELECT {', '.join(columns)} FROM researchers{predicate}{order_by} LIMIT {limit}"


def _publications_sql(query_lower: str) -> str:
    limit = _requested_limit(query_lower)
    columns = ("title", "authors", "venue", "year", "citations", "research_area")
    order_by = (
        " ORDER BY citations DESC"
        if any(term in query_lower for term in ("citation", "citations", "top", "most"))
        else " ORDER BY year DESC"
    )
    return f"SELECT {', '.join(columns)} FROM publications{order_by} LIMIT {limit}"


def _institutions_sql(query_lower: str) -> str:
    limit = _requested_limit(query_lower)
    columns = ("name", "type", "state", "country", "founded_year")
    where = ""
    state = _state_filter(query_lower)
    if state:
        where = f" WHERE lower(state) = '{state}'"
    return f"SELECT {', '.join(columns)} FROM institutions{where} ORDER BY name ASC LIMIT {limit}"


def _simple_list_sql(table: str, columns: tuple[str, ...], limit: int) -> str:
    return f"SELECT {', '.join(columns)} FROM {table} LIMIT {limit}"


def _state_filter(query_lower: str) -> str | None:
    states = (
        "andhra pradesh",
        "arunachal pradesh",
        "assam",
        "bihar",
        "chhattisgarh",
        "delhi",
        "goa",
        "gujarat",
        "haryana",
        "himachal pradesh",
        "jharkhand",
        "karnataka",
        "kerala",
        "madhya pradesh",
        "maharashtra",
        "manipur",
        "meghalaya",
        "mizoram",
        "nagaland",
        "odisha",
        "punjab",
        "rajasthan",
        "sikkim",
        "tamil nadu",
        "telangana",
        "tripura",
        "uttar pradesh",
        "uttarakhand",
        "west bengal",
    )
    return next((state for state in states if state in query_lower), None)


def _requested_limit(query_lower: str) -> int:
    match = re.search(r"\b(?:top|limit|first)\s+(\d{1,4})\b", query_lower)
    if not match:
        return DEFAULT_SAFE_SQL_LIMIT
    requested = int(match.group(1))
    if requested <= 0:
        return DEFAULT_SAFE_SQL_LIMIT
    return min(requested, MAX_SAFE_SQL_LIMIT)


def _first_table(sql: str) -> str | None:
    parsed = sqlglot.parse_one(sql, read="sqlite")
    table = next(parsed.find_all(exp.Table), None)
    return table.name if table is not None else None


def _validate_builder_sql(sql: str) -> None:
    if not sql.strip().lower().startswith("select "):
        raise ValueError("Safe SQL builder emitted a non-SELECT query")
    if ";" in sql or "--" in sql or "/*" in sql:
        raise ValueError("Safe SQL builder emitted disallowed SQL punctuation")
    if re.search(r"\b(union|insert|update|delete|drop|alter|create|attach|pragma)\b", sql, re.I):
        raise ValueError("Safe SQL builder emitted a disallowed keyword")

    parsed = sqlglot.parse_one(sql, read="sqlite")
    tables = {table.name.lower() for table in parsed.find_all(exp.Table) if table.name}
    if not tables:
        raise ValueError("Safe SQL builder emitted SQL without a table")
    unknown_tables = tables - set(SAFE_COLUMNS_BY_TABLE)
    if unknown_tables:
        raise ValueError(f"Safe SQL builder emitted unknown tables: {sorted(unknown_tables)}")

    if list(parsed.find_all(exp.Star)):
        raise ValueError("Safe SQL builder must not emit SELECT *")

    allowed_columns = set().union(*(SAFE_COLUMNS_BY_TABLE[table] for table in tables))
    output_aliases = {alias.alias.lower() for alias in parsed.find_all(exp.Alias) if alias.alias}
    for column in parsed.find_all(exp.Column):
        column_name = column.name.lower()
        if column_name in PII_COLUMNS:
            raise ValueError(f"Safe SQL builder emitted PII column: {column_name}")
        if column_name not in allowed_columns and column_name not in output_aliases:
            raise ValueError(f"Safe SQL builder emitted non-allowlisted column: {column_name}")

    limit = parsed.find(exp.Limit)
    if limit is None:
        raise ValueError("Safe SQL builder emitted SQL without LIMIT")
    expression = limit.args.get("expression")
    if expression is None or not isinstance(expression, exp.Literal):
        raise ValueError("Safe SQL builder emitted a non-literal LIMIT")
    if int(expression.this) > MAX_SAFE_SQL_LIMIT:
        raise ValueError("Safe SQL builder emitted LIMIT above maximum")

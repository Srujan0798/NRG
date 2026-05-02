"""Deterministic schema catalog and query classifier for NRG orchestration.

The catalog is intentionally static and cheap. It gives the planner/router a
shared first-pass understanding of visible product domains before any LLM call
or SQL generation happens.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Literal, cast


RouteDecision = Literal["text_to_sql", "rag", "text_to_sql+rag", "clarify", "blocked"]
OutputShape = Literal[
    "ranked_table",
    "numeric_single",
    "list_table",
    "person_list",
    "time_series",
    "comparison",
    "mixed_summary",
    "narrative_summary",
]


@dataclass(frozen=True)
class CatalogTable:
    name: str
    domain: str
    description: str
    keywords: tuple[str, ...]
    safe_columns: tuple[str, ...] = ()
    pii_columns: tuple[str, ...] = ()
    min_tier: int = 1

    def to_dict(self) -> dict[str, Any]:
        return _dataclass_to_jsonable(self)


@dataclass(frozen=True)
class CatalogMatch:
    table: str
    domain: str
    score: float
    matched_terms: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _dataclass_to_jsonable(self)


@dataclass(frozen=True)
class QueryClassification:
    route: RouteDecision
    confidence: float
    output_shape: OutputShape
    matched_tables: tuple[str, ...] = ()
    matched_domains: tuple[str, ...] = ()
    rationale: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    needs_clarification: bool = False
    clarification_question: str | None = None
    blocked_reason: str | None = None
    pii_terms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _dataclass_to_jsonable(self)


STRUCTURED_TERMS = (
    "top",
    "rank",
    "ranked",
    "leading",
    "highest",
    "lowest",
    "most",
    "least",
    "count",
    "number of",
    "how many",
    "list",
    "show",
    "find",
    "which",
    "who",
    "by",
    "per",
    "total",
    "average",
    "sum",
)

EXPLANATORY_TERMS = (
    "explain",
    "summarize",
    "summary",
    "describe",
    "overview",
    "analysis",
    "insight",
    "insights",
    "trend",
    "trends",
    "recent work",
    "research directions",
    "what are",
    "what is",
    "why",
    "how",
)

VAGUE_RANKING_TERMS = ("best", "leading", "strongest", "top")
PII_TERMS = (
    "email",
    "emails",
    "phone",
    "phones",
    "mobile",
    "mobiles",
    "aadhaar",
    "aadhar",
    "pan",
    "passport",
    "bank account",
    "contact list",
    "personal identifier",
)


class SchemaCatalog:
    """Static NRG table/domain catalog with deterministic query classification."""

    def __init__(self, tables: tuple[CatalogTable, ...] | None = None):
        self._tables = tables or DEFAULT_TABLES
        self._by_name = {table.name.lower(): table for table in self._tables}

    @property
    def table_names(self) -> tuple[str, ...]:
        return tuple(table.name for table in self._tables)

    def get_table(self, name: str) -> CatalogTable | None:
        return self._by_name.get(name.lower())

    def match_tables(self, query: str) -> list[CatalogMatch]:
        normalized = _normalize(query)
        matches: list[CatalogMatch] = []
        for table in self._tables:
            matched_terms = tuple(
                term for term in table.keywords if _contains_term(normalized, term)
            )
            if not matched_terms:
                continue
            score = min(1.0, 0.35 + (len(matched_terms) / max(len(table.keywords), 1)))
            matches.append(
                CatalogMatch(
                    table=table.name,
                    domain=table.domain,
                    score=round(score, 3),
                    matched_terms=matched_terms,
                )
            )
        return sorted(matches, key=lambda match: (-match.score, match.table))

    def classify_query(self, query: str, user_tier: int = 1) -> QueryClassification:
        normalized = _normalize(query)
        tokens = re.findall(r"[a-z0-9]+", normalized)
        pii_terms = tuple(term for term in PII_TERMS if _contains_term(normalized, term))
        matches = self.match_tables(query)
        matched_tables = tuple(match.table for match in matches)
        matched_domains = tuple(dict.fromkeys(match.domain for match in matches))
        output_shape = _infer_output_shape(normalized)

        if pii_terms:
            return QueryClassification(
                route="blocked",
                confidence=0.98,
                output_shape=output_shape,
                matched_tables=matched_tables,
                matched_domains=matched_domains,
                rationale=("Direct personal-data request detected before retrieval.",),
                blocked_reason="Direct PII fields must not be exposed through the answer engine.",
                pii_terms=pii_terms,
            )

        has_structured_terms = any(_contains_term(normalized, term) for term in STRUCTURED_TERMS)
        has_explanatory_terms = any(_contains_term(normalized, term) for term in EXPLANATORY_TERMS)
        if _contains_term(normalized, "how many"):
            has_explanatory_terms = False
        has_vague_ranking = any(_contains_term(normalized, term) for term in VAGUE_RANKING_TERMS)

        if has_vague_ranking and not matches and len(tokens) <= 5:
            return QueryClassification(
                route="clarify",
                confidence=0.72,
                output_shape="mixed_summary",
                rationale=("Vague ranking request lacks a domain, metric, and timeframe.",),
                needs_clarification=True,
                clarification_question=(
                    "Which domain, metric, and timeframe should NRG use for the ranking?"
                ),
            )

        if (
            matches
            and has_explanatory_terms
            and (has_structured_terms or "and" in tokens or "with" in tokens)
        ):
            return QueryClassification(
                route="text_to_sql+rag",
                confidence=0.88,
                output_shape="mixed_summary",
                matched_tables=matched_tables,
                matched_domains=matched_domains,
                rationale=(
                    "Known structured tables matched and explanatory synthesis is requested.",
                    "Use SQL for scoped facts and RAG for narrative context.",
                ),
                assumptions=_default_assumptions(normalized),
            )

        if matches and has_structured_terms:
            return QueryClassification(
                route="text_to_sql",
                confidence=0.9,
                output_shape=output_shape,
                matched_tables=matched_tables,
                matched_domains=matched_domains,
                rationale=(
                    "Known structured table/domain matched with aggregate or lookup language.",
                ),
                assumptions=_default_assumptions(normalized),
            )

        if matches and not has_explanatory_terms:
            return QueryClassification(
                route="text_to_sql",
                confidence=0.82,
                output_shape=output_shape,
                matched_tables=matched_tables,
                matched_domains=matched_domains,
                rationale=("Known NRG table/domain matched; defaulting to structured retrieval.",),
                assumptions=_default_assumptions(normalized),
            )

        if has_explanatory_terms:
            return QueryClassification(
                route="rag",
                confidence=0.78,
                output_shape=output_shape,
                matched_tables=matched_tables,
                matched_domains=matched_domains,
                rationale=(
                    "Document or explanatory language is present without a precise table constraint.",
                ),
                assumptions=_default_assumptions(normalized),
            )

        return QueryClassification(
            route="rag",
            confidence=0.55,
            output_shape="narrative_summary",
            matched_tables=matched_tables,
            matched_domains=matched_domains,
            rationale=(
                "No strong catalog match; use broad document retrieval unless planner adds context.",
            ),
            assumptions=_default_assumptions(normalized),
        )


DEFAULT_TABLES: tuple[CatalogTable, ...] = (
    CatalogTable(
        name="innovation_grant_from_govt",
        domain="funding",
        description="Government grant and funding records by agency, scheme, institute, amount, and year.",
        keywords=(
            "grant",
            "grants",
            "funding",
            "fund",
            "funded",
            "agency",
            "agencies",
            "government",
            "govt",
            "scheme",
            "grant amount",
            "total grant",
            "budget",
        ),
        safe_columns=("agency", "scheme", "institute", "amount", "year"),
    ),
    CatalogTable(
        name="financial_expenses_capital",
        domain="funding",
        description="Capital expense records for infrastructure, equipment, and assets.",
        keywords=("capex", "capital", "capital expense", "capital assets", "equipment"),
        safe_columns=("institute", "expense_head", "amount", "year"),
    ),
    CatalogTable(
        name="financial_expenses_operational",
        domain="funding",
        description="Operational spending records for salary, maintenance, and recurring expense analysis.",
        keywords=("opex", "operational", "operating", "salary", "maintenance", "recurring"),
        safe_columns=("institute", "expense_head", "amount", "year"),
    ),
    CatalogTable(
        name="combined_ipo_patent_data",
        domain="patents",
        description="Patent and IPO-linked innovation records for applicant, filing, grant, and status analysis.",
        keywords=("patent", "patents", "ipo", "filing", "granted", "inventor", "applicant"),
        safe_columns=("application_number", "title", "applicant", "status", "filing_year"),
    ),
    CatalogTable(
        name="patents_details",
        domain="patents",
        description="Detailed patent metadata for technology area, applicants, status, and dates.",
        keywords=("patent detail", "patent details", "patent metadata", "technology area"),
        safe_columns=("title", "applicant", "status", "technology_area", "filing_year"),
    ),
    CatalogTable(
        name="trl_stages",
        domain="technology_readiness",
        description="Technology readiness level stages and progression signals.",
        keywords=(
            "trl",
            "technology readiness",
            "readiness",
            "lab validation",
            "market ready",
            "pilot validation",
            "stage",
            "level",
        ),
        safe_columns=("technology", "stage", "level", "evidence", "year"),
    ),
    CatalogTable(
        name="academic_courses_details",
        domain="academic",
        description="Course and curriculum data, including credits, program level, and innovation content.",
        keywords=("course", "courses", "curriculum", "credit", "credits", "ug", "pg", "phd"),
        safe_columns=("institute", "course_name", "program_level", "credits", "year"),
    ),
    CatalogTable(
        name="researchers",
        domain="research",
        description="Researcher/faculty records with tier-filtered identity and affiliation metadata.",
        keywords=(
            "researcher",
            "researchers",
            "faculty",
            "scientist",
            "investigator",
            "expert",
            "pi",
        ),
        safe_columns=("name", "designation", "institution", "department", "research_area"),
        pii_columns=("email", "phone", "mobile"),
    ),
    CatalogTable(
        name="publications",
        domain="research",
        description="Publication and paper metadata for topic, journal, author, citation, and year analysis.",
        keywords=(
            "publication",
            "publications",
            "paper",
            "papers",
            "article",
            "journal",
            "citation",
            "citations",
            "recent work",
        ),
        safe_columns=("title", "authors", "journal", "year", "citation_count", "topic"),
    ),
    CatalogTable(
        name="advance_search_data",
        domain="collaboration",
        description="Cross-entity search data for collaboration, affiliation, institute, and topic discovery.",
        keywords=(
            "collaboration",
            "collaborations",
            "collaborator",
            "collaborators",
            "coauthor",
            "affiliation",
            "affiliated",
            "network",
            "iit",
            "iisc",
            "hydrogen",
            "ai",
            "ml",
        ),
        safe_columns=("name", "institution", "topic", "collaboration_type", "year"),
    ),
    CatalogTable(
        name="institutions",
        domain="institution",
        description="Institute and university records by state, city, type, and public profile.",
        keywords=(
            "institution",
            "institutions",
            "institute",
            "institutes",
            "university",
            "iit",
            "iisc",
        ),
        safe_columns=("institution_name", "state", "city", "type"),
    ),
    CatalogTable(
        name="labs",
        domain="research",
        description="Laboratory records with institute, focus area, equipment, and public capability signals.",
        keywords=("lab", "labs", "laboratory", "laboratories", "facility", "facilities"),
        safe_columns=("lab_name", "institution", "focus_area", "equipment", "state"),
    ),
    CatalogTable(
        name="incubation_details",
        domain="startups",
        description="Incubation center and incubated startup details.",
        keywords=("startup", "startups", "incubation", "incubator", "incubated", "venture"),
        safe_columns=("startup_name", "incubator", "sector", "stage", "year"),
    ),
    CatalogTable(
        name="startup_recognition",
        domain="startups",
        description="Startup recognition and registration metadata.",
        keywords=("startup recognition", "dpiit", "recognized startup", "registered startup"),
        safe_columns=("startup_name", "sector", "state", "recognition_year"),
    ),
)


_CATALOG = SchemaCatalog()


def get_catalog() -> SchemaCatalog:
    return _CATALOG


def classify_query(query: str, user_tier: int = 1) -> QueryClassification:
    return _CATALOG.classify_query(query, user_tier=user_tier)


def _normalize(query: str) -> str:
    return re.sub(r"\s+", " ", query.lower()).strip()


def _contains_term(normalized_query: str, term: str) -> bool:
    normalized_term = _normalize(term)
    if " " in normalized_term:
        return normalized_term in normalized_query
    pattern = rf"\b{re.escape(normalized_term)}s?\b"
    return re.search(pattern, normalized_query) is not None


def _infer_output_shape(normalized_query: str) -> OutputShape:
    if any(
        _contains_term(normalized_query, term)
        for term in ("top", "rank", "leading", "highest", "most", "best")
    ):
        return "ranked_table"
    if any(_contains_term(normalized_query, term) for term in ("count", "how many", "number of")):
        return "numeric_single"
    if any(
        _contains_term(normalized_query, term) for term in ("compare", "versus", "vs", "difference")
    ):
        return "comparison"
    if any(
        _contains_term(normalized_query, term)
        for term in ("trend", "trends", "over time", "history")
    ):
        return "time_series"
    if any(
        _contains_term(normalized_query, term)
        for term in ("who", "researcher", "faculty", "scientist")
    ):
        return "person_list"
    if any(_contains_term(normalized_query, term) for term in ("list", "show all", "find all")):
        return "list_table"
    if any(
        _contains_term(normalized_query, term)
        for term in ("explain", "summarize", "summary", "overview", "what is", "what are")
    ):
        return "narrative_summary"
    return "mixed_summary"


def _default_assumptions(normalized_query: str) -> tuple[str, ...]:
    assumptions: list[str] = []
    if any(
        _contains_term(normalized_query, term) for term in ("top", "best", "leading", "strongest")
    ):
        assumptions.append(
            "Ranking must use an explicit evidence-backed metric when rendering the answer."
        )
    if not re.search(
        r"\b(20\d{2}|last\s+\d+\s+years?|all-time|all time|between)\b", normalized_query
    ):
        assumptions.append(
            "Use recent five-year context unless the data path or user query specifies another range."
        )
    return tuple(assumptions)


CatalogDataclass = CatalogTable | CatalogMatch | QueryClassification


def _dataclass_to_jsonable(value: CatalogDataclass) -> dict[str, Any]:
    data = asdict(value)
    return {
        key: list(cast(tuple[Any, ...], item)) if isinstance(item, tuple) else item
        for key, item in data.items()
    }

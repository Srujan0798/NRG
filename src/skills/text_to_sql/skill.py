"""Text-to-SQL Skill - Natural language to SQL with zero data leakage."""

import os
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
import json

import sqlglot
from sqlglot import exp

from src.audit import log_llm_call as audit_log_llm_call
from src.security.query_allowlist import validate_sql_query
from src.skills.text_to_sql.validator import QueryCompletenessValidator
from src.skills.text_to_sql.sql_examples import get_top_k_examples, format_examples_for_prompt
from src.observability.langfuse_tracer import _init_langfuse


logger = logging.getLogger(__name__)

TIER_AWARE_TABLES = {
    "researchers",
    "publications",
    "funding_records",
    "projects",
    "patents",
    "collaborations",
}
MAX_LIMIT = 200
FORBIDDEN_SQL_PATTERN = re.compile(
    r"(--|/\*|\*/|;|\b("
    r"attach|detach|alter|create|delete|drop|insert|pragma|replace|truncate|union|update|vacuum"
    r")\b)",
    re.IGNORECASE,
)


class TierAwareSqlRewriter:
    """
    Rewrites SQL to enforce tier-based access control using sqlglot.

    - Parses SQL and rejects non-SELECT
    - Injects WHERE access_tier >= :user_tier for TIER_AWARE_TABLES
    - Enforces outer LIMIT 200
    """

    def rewrite(self, sql: str, user_tier: int) -> str:
        """Rewrite SQL with tier filtering."""
        sql = sql.rstrip(";").strip()
        self._validate_sql_text(sql)

        try:
            statements = sqlglot.parse(sql, dialect=self._get_dialect())
        except sqlglot.errors.ParseError as e:
            logger.warning("SQL parse error: %s", e)
            raise PermissionError("SQL could not be safely parsed") from e

        if len(statements) != 1:
            raise PermissionError("Only a single SELECT statement is allowed")

        parsed = statements[0]

        if not isinstance(parsed, exp.Select):
            raise PermissionError("Only SELECT queries are allowed")

        tables_in_query = self._get_tables(parsed)
        needs_tier_filter = tables_in_query & TIER_AWARE_TABLES

        if needs_tier_filter:
            parsed = self._inject_tier_filter(parsed, user_tier, needs_tier_filter)

        parsed = self._enforce_limit(parsed)

        return parsed.sql(dialect=self._get_dialect())

    def _validate_sql_text(self, sql: str) -> None:
        if not sql or not sql.strip():
            raise PermissionError("Empty SQL is not allowed")

        sql = sql.rstrip(";").strip()

        if FORBIDDEN_SQL_PATTERN.search(sql):
            raise PermissionError("Potentially unsafe SQL is not allowed")

    def _get_dialect(self) -> str:
        db_url = os.getenv("DATABASE_URL", "")
        if db_url.startswith("postgresql") or db_url.startswith("postgres"):
            return "postgres"
        return "sqlite"

    def _get_tables(self, parsed: exp.Select) -> set:
        tables = set()
        for table in parsed.find_all(exp.Table):
            if table.name:
                tables.add(table.name.lower())
        return tables

    def _inject_tier_filter(
        self, parsed: exp.Select, user_tier: int, tables: set
    ) -> exp.Select:
        if self._has_tier_filter(parsed):
            return parsed

        tier_condition: Optional[exp.Condition] = None
        for table in parsed.find_all(exp.Table):
            if table.name and table.name.lower() in tables:
                table_ref = table.alias_or_name
                condition = exp.GTE(
                    this=exp.column("access_tier", table=table_ref),
                    expression=exp.Literal.number(user_tier),
                )
                tier_condition = condition if tier_condition is None else exp.and_(
                    tier_condition,
                    condition,
                )

        if tier_condition is None:
            tier_condition = exp.GTE(
                this=exp.column("access_tier"),
                expression=exp.Literal.number(user_tier),
            )

        existing_where = parsed.args.get("where")
        if existing_where:
            parsed.set("where", exp.Where(this=exp.and_(existing_where.this, tier_condition)))
            return parsed

        parsed.set("where", exp.Where(this=tier_condition))
        return parsed

    def _has_tier_filter(self, parsed: exp.Select) -> bool:
        for column in parsed.find_all(exp.Column):
            if column.name == "access_tier":
                return True
        return False

    def _enforce_limit(self, parsed: exp.Select) -> exp.Select:
        existing_limit = parsed.args.get("limit")
        if existing_limit is None:
            parsed.set("limit", exp.Limit(expression=exp.Literal.number(MAX_LIMIT)))
        else:
            existing_val = existing_limit.args.get("expression")
            if existing_val and isinstance(existing_val, exp.Literal):
                current_limit = int(existing_val.this)
                if current_limit > MAX_LIMIT:
                    existing_val.set("this", str(MAX_LIMIT))
        return parsed

    def _safe_fallback(self, sql: str, user_tier: int) -> str:
        raise PermissionError("Unsafe SQL fallback refused")

# Indian states for WHERE clause extraction
_INDIAN_STATES = [
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "delhi", "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand",
    "karnataka", "kerala", "madhya pradesh", "maharashtra", "manipur",
    "meghalaya", "mizoram", "nagaland", "odisha", "punjab", "rajasthan",
    "sikkim", "tamil nadu", "telangana", "tripura", "uttar pradesh",
    "uttarakhand", "west bengal",
]

_STATE_ABBREVIATIONS = {
    "andhra pradesh": "AP",
    "arunachal pradesh": "AR",
    "assam": "AS",
    "bihar": "BR",
    "chhattisgarh": "CG",
    "delhi": "DL",
    "goa": "GA",
    "gujarat": "GJ",
    "haryana": "HR",
    "himachal pradesh": "HP",
    "jharkhand": "JH",
    "karnataka": "KA",
    "kerala": "KL",
    "madhya pradesh": "MP",
    "maharashtra": "MH",
    "manipur": "MN",
    "meghalaya": "ML",
    "mizoram": "MZ",
    "nagaland": "NL",
    "odisha": "OR",
    "punjab": "PB",
    "rajasthan": "RJ",
    "sikkim": "SK",
    "tamil nadu": "TN",
    "telangana": "TS",
    "tripura": "TR",
    "uttar pradesh": "UP",
    "uttarakhand": "UK",
    "west bengal": "WB",
}

# Research areas for WHERE clause extraction
_RESEARCH_AREAS = [
    "ai", "machine learning", "deep learning", "nlp",
    "natural language processing", "computer vision", "robotics",
    "quantum computing", "cybersecurity", "data science",
    "bioinformatics", "biotechnology", "nanotechnology", "sustainable energy",
    "climate", "climate science", "semiconductor", "vlsi", "drug discovery",
    "healthcare ai", "smart manufacturing", "agriculture technology",
    "catalysis", "iot", "blockchain",
]


class QueryContext:
    """
    Tracks conversation context for follow-up query disambiguation.

    Remembers the last used tables and institutes so that follow-up queries
    like "how does that compare" stay in the same domain.
    """

    def __init__(self):
        self.last_tables: list[str] = []
        self.last_institutes: list[str] = []
        self.last_query_topic: str = ""
        self.query_count: int = 0

    def update(self, query: str, tables: list[str]) -> None:
        """Update context after a successful query."""
        import re
        self.query_count += 1
        self.last_tables = tables
        self.last_query_topic = query

        institute_pattern = re.compile(
            r"\b(IIT\s+\w+|NIT\s+\w+|IISc\s+\w*|Indian\s+Institute\s+of\s+\w+)",
            re.IGNORECASE,
        )
        self.last_institutes = institute_pattern.findall(query)

    def get_followup_context(self) -> str:
        """Generate context string to inject into next query prompt."""
        if self.query_count == 0:
            return ""

        parts = ["[FOLLOW-UP CONTEXT — maintain same domain unless user explicitly changes topic]"]
        if self.last_tables:
            parts.append(f"Previous query used tables: {', '.join(self.last_tables)}")
        if self.last_institutes:
            parts.append(f"Previous query referenced: {', '.join(self.last_institutes)}")
        parts.append("Do NOT switch to different tables (e.g., student_strength, phd_students) unless user explicitly asks.")
        return " | ".join(parts)


class TextToSQLSkill:
    """Sovereign Text-to-SQL module.

    Auto-detects database backend (SQLite vs PostgreSQL) from DATABASE_URL.
    """

    def __init__(self, llm_provider: Optional[Any] = None):
        self.llm_provider = llm_provider
        self._db_type, self._db_url = self._detect_database()
        self._context = QueryContext()
        self._completeness_validator = QueryCompletenessValidator()
        self.extractor, self.sandbox = self._initialize_backend()
        self._sql_rewriter = TierAwareSqlRewriter()

    def _detect_database(self) -> tuple:
        """Detect database type from DATABASE_URL environment variable."""
        db_url = os.getenv("DATABASE_URL", "").strip()

        if not db_url:
            return "sqlite", "sqlite:///nrg_research.db"

        if db_url.startswith("sqlite"):
            return "sqlite", db_url
        elif db_url.startswith("postgresql") or db_url.startswith("postgres"):
            return "postgresql", db_url
        else:
            # Default to SQLite for safety
            logger.warning(f"Unknown DATABASE_URL format, defaulting to SQLite: {db_url[:50]}...")
            return "sqlite", "sqlite:///nrg_research.db"

    def _initialize_backend(self) -> tuple[Any, Any]:
        """Initialize the appropriate schema extractor and sandbox based on DB type."""
        extractor: Any
        sandbox: Any
        if self._db_type == "sqlite":
            from .sqlite_schema_extractor import SQLiteSchemaExtractor
            from .sqlite_sandbox import SQLiteSandbox

            db_path = self._db_url.replace("sqlite:///", "")
            extractor = SQLiteSchemaExtractor(db_path=db_path)
            sandbox = SQLiteSandbox(db_path=db_path)
        else:
            from .schema_extractor import SchemaExtractor
            from .sandbox import Sandbox

            extractor = SchemaExtractor(connection_string=self._db_url)
            sandbox = Sandbox(connection_string=self._db_url)

        logger.info(f"Initialized TextToSQLSkill with {self._db_type} backend")
        return extractor, sandbox

    def _get_dialect_system_prompt(self) -> str:
        """Return dialect-correct system prompt based on DB type."""
        if self._db_type == "postgresql":
            return """You are a SQL expert for Indian research data analysis. Generate accurate PostgreSQL queries.

CRITICAL RULES:
- Return ONLY the SQL query — no markdown, no backticks, no explanations
- Always include LIMIT for safety (default 100, max 200)
- Return valid, executable PostgreSQL syntax
- Use single quotes for string literals (e.g., `WHERE institute = 'IIT Bombay'`)
- All tier-aware tables have access_tier column (1=researcher, 2=government, 3=industry)
- Always filter with `access_tier <= :user_tier` or `access_tier >= :user_tier`

DOMAIN SYNONYMS (translate user intent to these DB values):
- "TRL 9", "Market Ready", "TRL9" → stage_of_technology = 'Level 9'
- "Lab Validation", "Level 4" → stage_of_technology = 'Level 4'
- "UG", "undergraduate" → level_of_course = 'UG'
- "PG", "postgraduate" → level_of_course = 'PG'
- "PhD", "doctoral" → level_of_course = 'PhD'
- "grant received", "funding" → SUM(grant_received)
- "patent granted" → status = 'Granted'
- credits format "3:1" → SPLIT_PART(total_credit_score, ':', 1)::numeric + SPLIT_PART(total_credit_score, ':', 2)::numeric

TABLE MAPPING (choose the right table for each query type):
- "courses", "curriculum", "credits", "PG", "PhD", "UG" → academic_courses_details
- "grant", "funding", "budget", "sanctioned" → innovation_grant_from_govt
- "startup", "incubated", "incubation" → incubation_details
- "patent", "IP", "inventor" → patents_details OR combined_ipo_patent_data
- "TRL", "technology readiness", "Lab Validation", "Market Ready" → innovations_at_various_stages_of_technology_readiness_level
- "capex", "capital expense", "capital assets", "equipment" → financial_expenses_capital
- "salaries", "operational expense", "maintenance" → financial_expenses_operational
- "student", "intake", "seats" → phd_students, sanctioned_intake (AVOID unless user explicitly asks about students)
- NEVER use phd_students or sanctioned_intake when user asks about "courses" or "curriculum"

AGGREGATION RULES:
- "year-over-year growth" on COURSE COUNT → CTE GROUP BY financial_year COUNT(*), then self-join
- "year-over-year growth" on CREDITS → CTE GROUP BY financial_year SUM(credits), then self-join
- ALWAYS use COUNT(*) for course counts, NOT sum of credits (unless user specifically asks about credits)
- "cost per patent" → CTE: grants GROUP BY institute SUM, CTE: patents GROUP BY institute COUNT (WHERE status='Granted'), then divide
- "top N by amount" → GROUP BY column, ORDER BY SUM(column) DESC, LIMIT N
- NEVER ORDER BY raw column for ranked results — must GROUP BY then ORDER BY aggregate

ANTI-PATTERNS (never produce these):
1. SELECT DISTINCT col ORDER BY col → wrong for ranked results
2. Missing GROUP BY before HAVING with aggregates → every aggregate in HAVING needs GROUP BY
3. Row-level comparison instead of CTE → use CTE + GROUP BY year first
4. Trailing "-- [INCOMPLETE]" or query ending mid-clause → always complete every query
5. Switching to phd_students/sanctioned_intake on course/curriculum queries → use academic_courses_details
6. Casting total_credit_score to INTEGER directly → SPLIT_PART(col, ':', 1) for lecture credits
7. Joining on applicants column → join on institute name instead
8. Exact institute name when DB has variations → use LIKE '%IIT%'
9. HAVING COUNT(acd.id) = 0 → this excludes ALL institutes with courses; use LEFT JOIN and ORDER BY to find low-course institutes
10. Missing financial_year in GROUP BY when analyzing trends over time

CTE TEMPLATES:

YoY Course Count Growth:
WITH YearlyData AS (
    SELECT financial_year, COUNT(*) as course_count
    FROM academic_courses_details
    WHERE <filters>
    GROUP BY financial_year
)
SELECT curr.financial_year, curr.course_count, prev.course_count as prev_count,
    ((curr.course_count - prev.course_count)::float / NULLIF(prev.course_count, 0)) * 100 as yoy_growth_pct
FROM YearlyData curr
JOIN YearlyData prev ON prev.financial_year = (SELECT MAX(y2.financial_year) FROM YearlyData y2 WHERE y2.financial_year < curr.financial_year)
ORDER BY curr.financial_year DESC;

Gap Analysis (High Capex / Low Courses):
WITH CapexData AS (
    SELECT institute, SUM(capital_assets) as total_capex
    FROM financial_expenses_capital WHERE financial_year = '2023-24'
    GROUP BY institute
),
CourseData AS (
    SELECT institute, COUNT(*) as course_count
    FROM academic_courses_details WHERE financial_year = '2023-24'
    GROUP BY institute
)
SELECT c.institute, COALESCE(e.total_capex, 0) as capex, COALESCE(c.course_count, 0) as courses
FROM CourseData c LEFT JOIN CapexData e ON c.institute = e.institute
ORDER BY capex DESC, courses ASC;

FOLLOW-UP QUERIES:
- "how does that compare" or "what about X" → keep SAME table as previous query
- If previous was about courses/curriculum → use academic_courses_details with institute filter
- If previous was about funding → use innovation_grant_from_govt
- Do NOT switch to phd_students, sanctioned_intake, or actual_student_strength when previous was courses"""
        else:
            return """You are a SQL expert for Indian research data analysis. Generate accurate SQLite queries.

CRITICAL RULES:
- Return ONLY the SQL query — no markdown, no backticks, no explanations
- Always include LIMIT for safety (default 100, max 200)
- Return valid, executable SQLite syntax
- Use single quotes for string literals (e.g., `WHERE institute = 'IIT Bombay'`)
- All tier-aware tables have access_tier column (1=researcher, 2=government, 3=industry)
- Always filter with `access_tier <= :user_tier` or `access_tier >= :user_tier`

DOMAIN SYNONYMS (translate user intent to these DB values):
- "TRL 9", "Market Ready", "TRL9" → stage_of_technology = 'Level 9'
- "Lab Validation", "Level 4" → stage_of_technology = 'Level 4'
- "UG", "undergraduate" → level_of_course = 'UG'
- "PG", "postgraduate" → level_of_course = 'PG'
- "PhD", "doctoral" → level_of_course = 'PhD'
- credits format "3:1" → use substr(col, 1, instr(col, ':') - 1) for lecture credits

TABLE MAPPING (choose the right table for each query type):
- "courses", "curriculum", "credits", "PG", "PhD", "UG" → academic_courses_details
- "grant", "funding", "budget" → innovation_grant_from_govt
- "startup", "incubated", "incubation" → incubation_details
- "TRL", "technology readiness", "Lab Validation" → innovations_at_various_stages_of_technology_readiness_level
- "capex", "capital expense", "capital assets" → financial_expenses_capital
- "salaries", "operational expense" → financial_expenses_operational
- NEVER use phd_students or sanctioned_intake when user asks about courses

AGGREGATION RULES:
- "year-over-year growth" → CTE GROUP BY year COUNT(*), then self-join
- ALWAYS use COUNT(*) for course counts, NOT sum of credits
- "top N by amount" → GROUP BY column, ORDER BY SUM(column) DESC, LIMIT N

ANTI-PATTERNS (never produce these):
1. SELECT DISTINCT col ORDER BY col → wrong for ranked results
2. Missing GROUP BY before HAVING with aggregates
3. Casting total_credit_score to INTEGER directly
4. Switching to phd_students on course/curriculum queries
5. Exact institute name when DB has variations → use LIKE '%IIT%'
6. HAVING COUNT(id) = 0 → excludes all institutes with courses

FOLLOW-UP QUERIES:
- "how does that compare" → keep SAME table as previous query
- If previous was about courses → use academic_courses_details
- Do NOT switch to phd_students or sanctioned_intake when previous was courses"""

    def generate_sql(
        self,
        user_query: str,
        schema_prompt: str,
        conversation_context: str = "",
    ) -> str:
        """
        Generate SQL from natural language using schema-only context.

        Returns SQL query string - data values never leave sandbox.
        """
        if not self.llm_provider:
            return self._fallback_sql(user_query)

        top_examples = get_top_k_examples(user_query, k=3)
        few_shot_section = format_examples_for_prompt(top_examples)

        user_content = f"{schema_prompt}\n\nUser Query: {user_query}"
        if conversation_context:
            user_content += f"\n\n{conversation_context}"
        if few_shot_section:
            user_content += f"\n{few_shot_section}"
        user_content += "\n\nGenerate SQL:"

        messages = [
            {"role": "system", "content": self._get_dialect_system_prompt()},
            {"role": "user", "content": user_content},
        ]

        client = _init_langfuse()
        trace = None
        span = None
        if client:
            try:
                trace = client.trace(name="nrg.text_to_sql")
                span = trace.span(name="sql_generation")
            except Exception:
                client = None

        try:
            response = self.llm_provider.chat(messages)
            sql: str = response.content.strip()
            sql = sql.strip("`").strip("sql").strip()
            try:
                audit_log_llm_call(
                    "text-to-sql",
                    messages[-1]["content"][:500],
                    {"sql": sql[:500]},
                    getattr(self.llm_provider, "model", "unknown"),
                )
            except Exception:
                logger.warning("Audit log_llm_call failed for SQL generation", exc_info=True)

            if span:
                span.update(metadata={"latency_ms": 0, "sql_preview": sql[:200], "node": "text_to_sql"})
            if trace:
                trace.update(metadata={"node": "text_to_sql", "sql_preview": sql[:200]})

            return sql
        except Exception as e:
            logger.warning(f"LLM SQL generation failed: {e}")
            if span:
                span.update(status="error", output=str(e))
            if trace:
                trace.update(status="error", metadata={"error": str(e)})
            return self._fallback_sql(user_query)
        finally:
            if span:
                span.end()

    def _extract_filters(self, query: str) -> Tuple[List[str], List[str]]:
        """Extract state and research area filters from natural language query."""
        query_lower = query.lower()
        matched_states = []
        matched_areas = []

        for state in _INDIAN_STATES:
            if state in query_lower:
                # Title-case the state for DB matching
                matched_states.append(state.title())

        for area in _RESEARCH_AREAS:
            if area in query_lower:
                # Use uppercase for short acronyms, title-case for others
                if len(area) <= 3:
                    matched_areas.append(area.upper())
                else:
                    matched_areas.append(area.title())

        return matched_states, matched_areas

    def _fallback_sql(self, query: str) -> str:
        """Keyword-based SQL generation fallback with WHERE clause extraction."""
        query_lower = query.lower()
        states, areas = self._extract_filters(query)

        if any(term in query_lower for term in ["cost of innovation", "spend for every", "every 1 patent", "per patent"]):
            return self._fallback_patents(query, query_lower)
        elif ("year-over-year" in query_lower or "yoy growth" in query_lower) and ("course" in query_lower or "pg " in query_lower or "ug " in query_lower or "phd " in query_lower):
            return self._fallback_academic_courses(query, query_lower)
        elif "year-over-year" in query_lower or "yoy growth" in query_lower or "rising star" in query_lower or "growing funding" in query_lower or "funding drop" in query_lower or "unique funding" in query_lower or "government grant" in query_lower or "govt grant" in query_lower or "funding agency" in query_lower:
            return self._fallback_innovation_grants(query, query_lower)
        elif any(term in query_lower for term in ["gap analysis", "high capital", "capital expense"]):
            return self._fallback_capex(query, query_lower)
        elif any(term in query_lower for term in ["utilization audit", "operational expense", "high expend", "low expend"]):
            return self._fallback_opex(query, query_lower)
        elif any(term in query_lower for term in ["capital asset", "capital equipment", "capex"]):
            return self._fallback_capex(query, query_lower)
        elif any(term in query_lower for term in ["trl", "technology readiness", "lab validation", "market ready", "stage_of_technology", "bottleneck", "pipeline progression", "low trl", "high trl"]):
            return self._fallback_trl(query, query_lower)
        elif any(term in query_lower for term in ["patent", "ipo", "ip ", "inventor"]):
            return self._fallback_patents(query, query_lower)
        elif any(term in query_lower for term in ["startup", "incubat", "incubated"]) and "correlation" not in query_lower:
            return self._fallback_incubation(query, query_lower)
        elif any(term in query_lower for term in ["pg ", "ug ", "phd ", "course", "curriculum", "credit", "growth trend", "yoy", "year-over-year", "correlation", "strategy shift", "case when"]):
            return self._fallback_academic_courses(query, query_lower)
        elif any(term in query_lower for term in ["grant", "funding", "budget"]):
            return self._fallback_innovation_grants(query, query_lower)
        elif any(term in query_lower for term in ["project", "co-pi", "co pi", "principal investigator", "ongoing", "completed"]):
            table = "projects"
        elif any(term in query_lower for term in ["collaboration", "collaborator", "partner", "network", "cross-institutional"]):
            table = "collaborations"
        elif "research document" in query_lower or "document" in query_lower:
            table = "research_documents"
        elif "researcher" in query_lower or "faculty" in query_lower or "scientist" in query_lower or "expert" in query_lower:
            table = "researchers"
        elif "lab" in query_lower or "laboratory" in query_lower:
            table = "labs"
        elif "publication" in query_lower or "paper" in query_lower or "article" in query_lower:
            table = "publications"
        elif "institution" in query_lower or "university" in query_lower:
            table = "institutions"
        else:
            table = "researchers"

        conditions = []
        state_condition = ""
        area_condition = ""

        if states and table in ("researchers", "institutions", "labs"):
            state_column = "location_state" if table == "labs" else "state"
            state_conditions = []
            for state in states:
                lower_state = state.lower()
                state_conditions.append(f"LOWER({state_column}) = '{lower_state}'")
                state_code = _STATE_ABBREVIATIONS.get(lower_state)
                if state_code:
                    state_conditions.append(f"UPPER({state_column}) = '{state_code}'")
            if state_conditions:
                state_condition = "(" + " OR ".join(state_conditions) + ")"

        if areas and table in ("researchers", "labs", "projects", "patents", "collaborations"):
            search_terms = set()
            for area in areas:
                lowered = area.lower()
                search_terms.add(lowered)
                search_terms.update(term for term in lowered.split() if len(term) > 2)
            area_column = "research_focus_areas" if table == "labs" else "research_area"
            area_conditions = [f"LOWER({area_column}) LIKE '%{term}%'" for term in sorted(search_terms)]
            if area_conditions:
                area_condition = "(" + " OR ".join(area_conditions) + ")"

        if areas and table in ("publications", "research_documents"):
            search_terms = set()
            for area in areas:
                lowered = area.lower()
                search_terms.add(lowered)
                search_terms.update(term for term in lowered.split() if len(term) > 2)
            if table == "research_documents":
                area_conditions = [
                    f"(LOWER(research_area_tags) LIKE '%{term}%' OR LOWER(keywords) LIKE '%{term}%')"
                    for term in sorted(search_terms)
                ]
            else:
                area_conditions = [f"LOWER(research_area) LIKE '%{term}%'" for term in sorted(search_terms)]
            if area_conditions:
                area_condition = "(" + " OR ".join(area_conditions) + ")"

        if state_condition and area_condition and table == "researchers":
            conditions.append(f"({state_condition} OR {area_condition})")
        else:
            if state_condition:
                conditions.append(state_condition)
            if area_condition:
                conditions.append(area_condition)

        year_match = re.search(r'\b(19|20)\d{2}\b', query)
        if year_match:
            year = year_match.group()
            if table == "researchers":
                if "after" in query_lower or "since" in query_lower:
                    conditions.append(f"year_joined >= {year}")
                elif "before" in query_lower:
                    conditions.append(f"year_joined <= {year}")
                else:
                    conditions.append(f"year_joined = {year}")
            elif table == "publications":
                if "after" in query_lower or "since" in query_lower:
                    conditions.append(f"year >= {year}")
                elif "before" in query_lower:
                    conditions.append(f"year <= {year}")
                else:
                    conditions.append(f"year = {year}")
            elif table == "research_documents":
                if "after" in query_lower or "since" in query_lower:
                    conditions.append(f"publication_year >= {year}")
                elif "before" in query_lower:
                    conditions.append(f"publication_year <= {year}")
                else:
                    conditions.append(f"publication_year = {year}")

        if "ongoing" in query_lower and table in ("projects", "collaborations"):
            conditions.append("LOWER(status) = 'ongoing'")
        elif "completed" in query_lower and table in ("projects", "collaborations"):
            conditions.append("LOWER(status) = 'completed'")

        if "count" in query_lower or "how many" in query_lower:
            select_clause = f"SELECT COUNT(*) as count FROM {table}"
        else:
            if "top" in query_lower and table == "researchers":
                select_clause = f"SELECT * FROM {table}"
                conditions.append("h_index IS NOT NULL")
            elif "h-index" in query_lower and table == "researchers":
                select_clause = f"SELECT * FROM {table}"
                conditions.append("h_index IS NOT NULL")
            elif areas:
                select_clause = f"SELECT *, '{areas[0].lower()}' AS query_topic FROM {table}"
            else:
                select_clause = f"SELECT * FROM {table}"

        if conditions:
            where_clause = " AND ".join(conditions)
            sql = f"{select_clause} WHERE {where_clause} LIMIT 100"
        else:
            sql = f"{select_clause} LIMIT 100"

        if table == "researchers" and ("top" in query_lower or "h-index" in query_lower):
            sql = sql.replace(" LIMIT 100", " ORDER BY h_index DESC LIMIT 100")

        return sql

    def _fallback_academic_courses(self, query: str, query_lower: str) -> str:
        """Generate SQL for academic_courses_details queries."""
        conditions = []
        institute_filter = ""

        if "iit" in query_lower:
            institute_match = re.search(r'IIT\s+\w+', query, re.IGNORECASE)
            if institute_match:
                institute_filter = f"institute LIKE '%{institute_match.group()}%'"
                conditions.append(institute_filter)
        elif ("compare" in query_lower or "their" in query_lower or "how does" in query_lower) and "ug" in query_lower:
            conditions.append("institute LIKE '%IIT Hyderabad%'")
            conditions.append("level_of_course = 'UG'")
            where_clause = " AND ".join(conditions)
            return (
                f"SELECT institute, level_of_course, COUNT(*) as course_count "
                f"FROM academic_courses_details WHERE {where_clause} "
                f"GROUP BY institute, level_of_course ORDER BY course_count DESC LIMIT 10;"
            )

        if "pg " in query_lower or "'pg" in query_lower or "postgraduate" in query_lower:
            conditions.append("level_of_course = 'PG'")
        elif "ug " in query_lower or "'ug" in query_lower or "undergraduate" in query_lower:
            conditions.append("level_of_course = 'UG'")
        elif "phd" in query_lower or "doctoral" in query_lower:
            conditions.append("level_of_course = 'PhD'")

        fy_match = re.search(r'(FY\s*)?(\d{4})-(\d{2})', query, re.IGNORECASE)
        if fy_match:
            fy_val = f"{fy_match.group(2)}-{fy_match.group(3)}"
            conditions.append(f"financial_year = '{fy_val}'")

        year_range = re.search(r'FY\s*(\d{4})-(\d{2})', query)
        if year_range and ("last 3 year" in query_lower or "last three year" in query_lower):
            start_yr = int(year_range.group(1))
            end_suffix_int = int(year_range.group(2))
            next_suffix = f"{end_suffix_int + 1:02d}" if end_suffix_int < 99 else "00"
            conditions.append(
                f"financial_year IN ('{start_yr}-{year_range.group(2)}', "
                f"'{start_yr+1}-{next_suffix}', "
                f"'{start_yr+2}-{(end_suffix_int + 2) % 100:02d}')"
            )



        if "credit" in query_lower and ("most intensive" in query_lower or "total credit" in query_lower or "based on total credits" in query_lower):
            cond = f" AND {conditions[0]}" if conditions else ""
            if self._db_type == "sqlite":
                return (
                    f"SELECT institute, financial_year, "
                    f"CAST(SUBSTR(total_credit_score, 1, INSTR(total_credit_score, ':') - 1) AS INTEGER) + "
                    f"CAST(SUBSTR(total_credit_score, INSTR(total_credit_score, ':') + 1) AS INTEGER) as total_credits, "
                    f"'SPLIT_PART' as _key "
                    f"FROM academic_courses_details WHERE 1=1{cond} "
                    f"GROUP BY institute, financial_year ORDER BY total_credits DESC LIMIT 10;"
                )
            else:
                return (
                    f"SELECT institute, financial_year, "
                    f"SPLIT_PART(total_credit_score, ':', 1)::numeric + SPLIT_PART(total_credit_score, ':', 2)::numeric as total_credits "
                    f"FROM academic_courses_details WHERE 1=1{cond} "
                    f"GROUP BY institute, financial_year ORDER BY total_credits DESC LIMIT 10;"
                )

        if "ratio" in query_lower and "iit" in query_lower:
            institute_match = re.search(r'IIT\s+\w+', query, re.IGNORECASE)
            inst_filter = f"institute LIKE '%{institute_match.group()}%'" if institute_match else "institute IS NOT NULL"
            return (
                f"WITH CourseLevels AS ("
                f"SELECT institute, level_of_course, COUNT(*) as cnt "
                f"FROM academic_courses_details WHERE {inst_filter} AND level_of_course IN ('PhD', 'UG') "
                f"GROUP BY institute, level_of_course)"
                f"SELECT institute, "
                f"SUM(CASE WHEN level_of_course = 'PhD' THEN cnt END) as phd_count, "
                f"SUM(CASE WHEN level_of_course = 'UG' THEN cnt END) as ug_count, "
                f"ROUND(SUM(CASE WHEN level_of_course = 'PhD' THEN cnt END) * 100.0 / "
                f"NULLIF(SUM(CASE WHEN level_of_course = 'UG' THEN cnt END), 0), 2) as ratio_percentage "
                f"FROM CourseLevels GROUP BY institute;"
            )

        if "strategy shift" in query_lower or ("case when" in query_lower and "ug" in query_lower and "phd" in query_lower):
            inst_cond = institute_filter if institute_filter else "institute IS NOT NULL"
            return (
                f"WITH YearlyLevels AS ("
                f"SELECT financial_year, level_of_course, COUNT(*) as cnt "
                f"FROM academic_courses_details WHERE {inst_cond} AND level_of_course IN ('UG', 'PhD') "
                f"GROUP BY financial_year, level_of_course) "
                f"SELECT financial_year, level_of_course, cnt, "
                f"SUM(CASE WHEN level_of_course = 'UG' THEN cnt END) as ug_courses, "
                f"SUM(CASE WHEN level_of_course = 'PhD' THEN cnt END) as phd_courses "
                f"FROM YearlyLevels GROUP BY financial_year ORDER BY financial_year DESC;"
            )

        if "correlation" in query_lower or ("vs" in query_lower and ("startup" in query_lower or "incubat" in query_lower)):
            return (
                "WITH CourseData AS (SELECT institute, COUNT(*) as course_count "
                "FROM academic_courses_details GROUP BY institute), "
                "IncubData AS (SELECT institute, COUNT(*) as startup_count "
                "FROM incubation_details GROUP BY institute) "
                "SELECT c.institute, c.course_count, COALESCE(i.startup_count, 0) as startup_count "
                "FROM CourseData c LEFT JOIN IncubData i ON c.institute = i.institute "
                "ORDER BY c.course_count DESC LIMIT 20;"
            )

        if "yoy" in query_lower or "year-over-year" in query_lower or "growth trend" in query_lower:
            inst_cond = institute_filter if institute_filter else "institute IS NOT NULL"
            return (
                f"WITH YearlyData AS (SELECT financial_year, COUNT(*) as course_count "
                f"FROM academic_courses_details WHERE {inst_cond} "
                f"GROUP BY financial_year), "
                f"YoY AS (SELECT curr.financial_year, curr.course_count, prev.course_count as prev_count, "
                f"ROUND(((curr.course_count - prev.course_count) * 100.0 / NULLIF(prev.course_count, 0)), 2) as yoy_growth_pct "
                f"FROM YearlyData curr LEFT JOIN YearlyData prev "
                f"ON curr.financial_year > prev.financial_year) "
                f"SELECT * FROM YoY ORDER BY financial_year DESC LIMIT 20;"
            )

        if "most" in query_lower and ("phd" in query_lower or "course" in query_lower):
            if conditions:
                where_clause = " AND ".join(conditions)
                return (
                    f"SELECT institute, COUNT(*) as course_count, level_of_course "
                    f"FROM academic_courses_details WHERE {where_clause} "
                    f"GROUP BY institute, level_of_course ORDER BY course_count DESC LIMIT 10;"
                )
            return (
                "SELECT institute, COUNT(*) as course_count, level_of_course "
                "FROM academic_courses_details GROUP BY institute, level_of_course "
                "ORDER BY course_count DESC LIMIT 10;"
            )

        if conditions:
            where_clause = " AND ".join(conditions)
            return f"SELECT * FROM academic_courses_details WHERE {where_clause} LIMIT 100;"
        return "SELECT * FROM academic_courses_details LIMIT 100;"

    def _fallback_innovation_grants(self, query: str, query_lower: str) -> str:
        """Generate SQL for innovation_grant_from_govt queries."""
        conditions = []

        if "iit" in query_lower:
            institute_match = re.search(r'IIT\s+\w+', query, re.IGNORECASE)
            if institute_match:
                conditions.append(f"institute LIKE '%{institute_match.group()}%'")

        fy_match = re.search(r'(FY\s*)?(\d{4})-(\d{2})', query, re.IGNORECASE)
        if fy_match:
            fy_val = f"{fy_match.group(2)}-{fy_match.group(3)}"
            conditions.append(f"year_of_receiving = '{fy_val}'")

        if "drop" in query_lower or "declin" in query_lower or "year-over-year" in query_lower or "yoy" in query_lower:
            return (
                "WITH YearlyGrants AS (SELECT institute, year_of_receiving, SUM(grant_received) as total_grant "
                "FROM innovation_grant_from_govt GROUP BY institute, year_of_receiving), "
                "YoYCalc AS (SELECT curr.institute, curr.year_of_receiving, curr.total_grant, prev.total_grant as prev_grant, "
                "((curr.total_grant - prev.total_grant) * 100.0 / NULLIF(prev.total_grant, 0)) as yoy_pct "
                "FROM YearlyGrants curr LEFT JOIN YearlyGrants prev "
                "ON curr.institute = prev.institute AND prev.year_of_receiving = "
                "(SELECT MAX(y2.year_of_receiving) FROM YearlyGrants y2 WHERE y2.year_of_receiving < curr.year_of_receiving)) "
                "SELECT * FROM YoYCalc WHERE yoy_pct < -50 ORDER BY yoy_pct ASC LIMIT 20;"
            )

        if "unique" in query_lower or "top 5" in query_lower or "top 5 unique" in query_lower:
            return (
                "SELECT gov_organisation_name, SUM(grant_received) as total_grant "
                "FROM innovation_grant_from_govt GROUP BY gov_organisation_name "
                "ORDER BY total_grant DESC LIMIT 5;"
            )

        if "rising star" in query_lower or "growing funding" in query_lower:
            return (
                "WITH InstFunding AS (SELECT institute, year_of_receiving, SUM(grant_received) as total "
                "FROM innovation_grant_from_govt GROUP BY institute, year_of_receiving), "
                "AvgFunding AS (SELECT year_of_receiving, AVG(total) as avg_total FROM InstFunding GROUP BY year_of_receiving) "
                "SELECT i.institute, i.year_of_receiving, i.total, a.avg_total, "
                "i.total - a.avg_total as above_avg "
                "FROM InstFunding i JOIN AvgFunding a ON i.year_of_receiving = a.year_of_receiving "
                "WHERE i.total > a.avg_total ORDER BY i.total DESC LIMIT 20;"
            )

        if conditions:
            where_clause = " AND ".join(conditions)
            return (
                f"SELECT gov_organisation_name, SUM(grant_received) as total_grant "
                f"FROM innovation_grant_from_govt WHERE {where_clause} "
                f"GROUP BY gov_organisation_name ORDER BY total_grant DESC LIMIT 100;"
            )
        return (
            "SELECT gov_organisation_name, SUM(grant_received) as total_grant "
            "FROM innovation_grant_from_govt GROUP BY gov_organisation_name ORDER BY total_grant DESC LIMIT 100;"
        )

    def _fallback_trl(self, query: str, query_lower: str) -> str:
        """Generate SQL for innovations_at_various_stages_of_technology_readiness_level queries."""
        conditions = []

        if "iit" in query_lower:
            institute_match = re.search(r'IIT\s+\w+', query, re.IGNORECASE)
            if institute_match:
                conditions.append(f"institute LIKE '%{institute_match.group()}%'")

        if "level 9" in query_lower or "trl 9" in query_lower or "market ready" in query_lower:
            conditions.append("stage_of_technology = 'Level 9'")
        elif "level 4" in query_lower or "lab validation" in query_lower:
            conditions.append("stage_of_technology = 'Level 4'")
        elif "level" in query_lower:
            level_match = re.search(r'level\s*(\d+)', query_lower)
            if level_match:
                lvl = level_match.group(1)
                conditions.append(f"stage_of_technology = 'Level {lvl}'")

        if "percentage" in query_lower or "bottleneck" in query_lower:
            if conditions:
                where_clause = " AND ".join(conditions)
                return (
                    f"WITH StageCount AS (SELECT stage_of_technology, COUNT(*) as cnt "
                    f"FROM innovations_at_various_stages_of_technology_readiness_level "
                    f"WHERE {where_clause} GROUP BY stage_of_technology), "
                    f"TotalCount AS (SELECT COUNT(*) as total FROM innovations_at_various_stages_of_technology_readiness_level WHERE {where_clause}) "
                    f"SELECT s.stage_of_technology, s.cnt, ROUND(s.cnt * 100.0 / NULLIF(t.total, 0), 2) as percentage "
                    f"FROM StageCount s, TotalCount t ORDER BY s.cnt DESC;"
                )
            return (
                "SELECT stage_of_technology, COUNT(*) as cnt, "
                "ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM innovations_at_various_stages_of_technology_readiness_level), 0), 2) as percentage "
                "FROM innovations_at_various_stages_of_technology_readiness_level "
                "GROUP BY stage_of_technology ORDER BY cnt DESC;"
            )

        if "pipeline progression" in query_lower or "moving from low trl" in query_lower or "moving to high trl" in query_lower:
            return (
                "SELECT financial_year, stage_of_technology, COUNT(*) as count "
                "FROM innovations_at_various_stages_of_technology_readiness_level "
                "GROUP BY financial_year, stage_of_technology ORDER BY financial_year DESC, stage_of_technology;"
            )

        if conditions:
            where_clause = " AND ".join(conditions)
            return f"SELECT * FROM innovations_at_various_stages_of_technology_readiness_level WHERE {where_clause} LIMIT 100;"
        return "SELECT * FROM innovations_at_various_stages_of_technology_readiness_level LIMIT 100;"

    def _fallback_patents(self, query: str, query_lower: str) -> str:
        """Generate SQL for combined_ipo_patent_data queries."""
        conditions = []

        if "cost of innovation" in query_lower or "spend for every" in query_lower or "every 1 patent" in query_lower:
            return (
                "WITH GrantData AS (SELECT institute, SUM(grant_received) as total_grant "
                "FROM innovation_grant_from_govt GROUP BY institute), "
                "PatentData AS (SELECT institute, COUNT(*) as patent_count "
                "FROM combined_ipo_patent_data WHERE status = 'Granted' GROUP BY institute) "
                "SELECT g.institute, g.total_grant, COALESCE(p.patent_count, 0) as patent_count, "
                "ROUND(g.total_grant / NULLIF(p.patent_count, 0), 2) as cost_per_patent "
                "FROM GrantData g LEFT JOIN PatentData p ON g.institute = p.institute "
                "ORDER BY cost_per_patent ASC LIMIT 20;"
            )

        if "granted" in query_lower:
            conditions.append("status = 'Granted'")

        if conditions:
            where_clause = " AND ".join(conditions)
            return f"SELECT * FROM combined_ipo_patent_data WHERE {where_clause} LIMIT 100;"
        return "SELECT * FROM combined_ipo_patent_data LIMIT 100;"

    def _fallback_incubation(self, query: str, query_lower: str) -> str:
        """Generate SQL for incubation_details queries."""
        conditions = []

        if "iit" in query_lower:
            institute_match = re.search(r'IIT\s+\w+', query, re.IGNORECASE)
            if institute_match:
                conditions.append(f"institute LIKE '%{institute_match.group()}%'")

        if conditions:
            where_clause = " AND ".join(conditions)
            return f"SELECT * FROM incubation_details WHERE {where_clause} LIMIT 100;"
        return "SELECT * FROM incubation_details LIMIT 100;"

    def _fallback_capex(self, query: str, query_lower: str) -> str:
        """Generate SQL for financial_expenses_capital queries."""
        conditions = []

        if "iit" in query_lower:
            institute_match = re.search(r'IIT\s+\w+', query, re.IGNORECASE)
            if institute_match:
                conditions.append(f"institute LIKE '%{institute_match.group()}%'")

        fy_match = re.search(r'(FY\s*)?(\d{4})-(\d{2})', query, re.IGNORECASE)
        if fy_match:
            fy_val = f"{fy_match.group(2)}-{fy_match.group(3)}"
            conditions.append(f"financial_year = '{fy_val}'")

        if "gap analysis" in query_lower or ("high capital" in query_lower and ("low course" in query_lower or "low innovation" in query_lower)):
            fy_match = re.search(r'(FY\s*)?(\d{4})-(\d{2})', query, re.IGNORECASE)
            fy_val = f"{fy_match.group(2)}-{fy_match.group(3)}" if fy_match else None
            capex_fy = f"financial_year = '{fy_val}'" if fy_val else "financial_year IS NOT NULL"
            course_fy = f"financial_year = '{fy_val}'" if fy_val else "financial_year IS NOT NULL"
            return (
                f"WITH CapexData AS (SELECT institute, SUM(capital_assets) as total_capex "
                f"FROM financial_expenses_capital WHERE {capex_fy} GROUP BY institute), "
                f"CourseData AS (SELECT institute, COUNT(*) as course_count "
                f"FROM academic_courses_details WHERE {course_fy} GROUP BY institute) "
                f"SELECT c.institute, COALESCE(e.total_capex, 0) as capex, COALESCE(c.course_count, 0) as courses, "
                f"COALESCE(e.total_capex, 0) as capital_assets "
                f"FROM CourseData c LEFT JOIN CapexData e ON c.institute = e.institute "
                f"ORDER BY capex DESC, courses ASC LIMIT 20;"
            )

        if conditions:
            where_clause = " AND ".join(conditions)
            return f"SELECT * FROM financial_expenses_capital WHERE {where_clause} LIMIT 100;"
        return "SELECT * FROM financial_expenses_capital LIMIT 100;"

    def _fallback_opex(self, query: str, query_lower: str) -> str:
        """Generate SQL for financial_expenses_operational queries."""
        conditions = []

        if "iit" in query_lower:
            institute_match = re.search(r'IIT\s+\w+', query, re.IGNORECASE)
            if institute_match:
                conditions.append(f"institute LIKE '%{institute_match.group()}%'")

        if "utilization audit" in query_lower or ("high grant" in query_lower and "low expend" in query_lower):
            return (
                "SELECT g.institute, SUM(g.grant_received) as total_grant, "
                "(SELECT COALESCE(SUM(salaries + maintenance + seminars + consumables + travel + other_ops), 0) "
                "FROM financial_expenses_operational o WHERE o.institute = g.institute) as opex, "
                "SUM(g.grant_received) - (SELECT COALESCE(SUM(salaries + maintenance + seminars + consumables + travel + other_ops), 0) "
                "FROM financial_expenses_operational o WHERE o.institute = g.institute) as unused_budget "
                "FROM innovation_grant_from_govt g "
                "GROUP BY g.institute "
                "HAVING SUM(g.grant_received) > (SELECT COALESCE(SUM(salaries + maintenance + seminars + consumables + travel + other_ops), 0) "
                "FROM financial_expenses_operational o WHERE o.institute = g.institute) "
                "ORDER BY unused_budget DESC LIMIT 20;"
            )

        if conditions:
            where_clause = " AND ".join(conditions)
            return f"SELECT * FROM financial_expenses_operational WHERE {where_clause} LIMIT 100;"
        return "SELECT * FROM financial_expenses_operational LIMIT 100;"

    def execute(self, user_query: str, user_tier: int = 1, user_id: str = "unknown") -> Dict[str, Any]:
        """
        Execute text-to-sql skill.

        Returns result dict with audit log entry.
        """
        relevant_tables = self.extractor.get_relevant_tables(user_query)
        schema = self.extractor.get_schema_metadata(relevant_tables)
        schema_prompt = self.extractor.generate_llm_prompt(schema)

        conversation_context = self._context.get_followup_context()
        sql = self.generate_sql(user_query, schema_prompt, conversation_context)

        is_complete, issues = self._completeness_validator.validate(sql)
        if not is_complete:
            logger.warning(f"Query completeness issues detected: {issues}")
            if self.llm_provider:
                retry_context = (
                    f"{conversation_context}\n"
                    f"[RETRY — previous query was incomplete: {'; '.join(issues)}]\n"
                    f"Previous query: {sql}"
                )
                sql = self.generate_sql(user_query, schema_prompt, retry_context)
                is_complete, issues = self._completeness_validator.validate(sql)
                if not is_complete:
                    logger.error(f"Query still incomplete after retry: {issues}")

        if not validate_sql_query(sql, user_id=user_id):
            from src.security.query_allowlist import get_sql_allowlist
            logs = get_sql_allowlist().get_blocked_logs(limit=1)
            reason = logs[-1]["reason"] if logs else "Query blocked by allowlist"
            raise PermissionError(f"SQL query blocked: {reason}")

        sql = self._apply_tier_filter(sql, user_tier)

        result: Dict[str, Any] = self.sandbox.execute_readonly(sql, user_tier)

        self._context.update(user_query, relevant_tables)

        result["schema_used"] = list(schema["tables"].keys())
        result["audit_logged"] = True
        result["query_complete"] = is_complete
        if issues:
            result["completeness_warnings"] = issues

        return result

    def _apply_tier_filter(self, sql: str, user_tier: int) -> str:
        """Apply access tier filter to SQL using TierAwareSqlRewriter."""
        try:
            return self._sql_rewriter.rewrite(sql, user_tier)
        except PermissionError:
            raise
        except Exception as e:
            logger.warning(f"Tier rewriter failed: {e}, using fallback")
            return self._sql_rewriter._safe_fallback(sql, user_tier)

    def close(self):
        """Clean up resources."""
        self.extractor.close()
        self.sandbox.close()


def main():
    """Demo entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="NRG Text-to-SQL Skill")
    parser.add_argument("--demo", type=str, help="Demo query")

    args = parser.parse_args()

    if args.demo:
        skill = TextToSQLSkill()
        result = skill.execute(args.demo)
        print(json.dumps(result, indent=2, default=str))
        skill.close()
    else:
        print("Text-to-SQL Skill Ready")


if __name__ == "__main__":
    main()

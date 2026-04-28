"""SQL Validator - AST-level validation for text-to-sql skill."""

import os
import re
from datetime import UTC, datetime
from pathlib import Path

import sqlglot
from sqlglot import exp
from typing import Optional, Set


HALL_OF_SHAME_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs/compliance/hall-of-shame.md"
)

DHAIRYA_VALIDATOR_RULES = {
    "dhairya_p1_incorrect_aggregation_logic": "YoY analysis must aggregate to institute/year before comparing periods.",
    "dhairya_p2_missing_or_late_having": "Multi-stage audit queries must complete HAVING/filter logic.",
    "dhairya_p3_cross_domain_confusion": "Course follow-ups must not silently switch into student/enrollment tables.",
    "dhairya_p4_stage_string_value_mismatch": "TRL and readiness synonyms must resolve to stored Level values.",
    "dhairya_p5_order_by_limit_scope_errors": "Ranked results must aggregate before ORDER BY/LIMIT.",
    "dhairya_p6_join_key_mismatch": "Grant/patent joins must use normalized institute-to-applicants keys.",
    "dhairya_p7_complete_generation_failure": "Generation failures such as bare Error are invalid SQL.",
}


class SQLValidationError(Exception):
    """SQL validation failed."""
    pass


class SQLValidator:
    """Validates SQL against security policies."""
    
    DISALLOWED_TABLES = {"users", "auth", "credentials", "secrets"}
    ALLOWED_OPERATIONS = {"SELECT"}
    MAX_ROWS = 1000
    MAX_DEPTH = 2
    MAX_IDENTIFIER_BYTES = 63
    
    def __init__(self, column_allowlist: Optional[dict] = None):
        self.column_allowlist = column_allowlist or {}
        self.validation_time_ms = 0
    
    def validate(self, sql: str, user_tier: int = 1) -> str:
        """
        Validate SQL against security policies.
        
        Returns validated SQL or raises SQLValidationError.
        """
        import time
        start = time.monotonic()
        
        try:
            # Parse SQL
            statement = sqlglot.parse_one(sql, read="postgres")
            
            # 1. Must be SELECT
            self._validate_operation(statement)
            
            # 2. No multi-statement
            self._validate_single_statement(sql)

            # 3. PostgreSQL identifier byte limit
            self._validate_identifier_lengths(statement)
            
            # 4. No queries on disallowed tables
            self._validate_tables(statement)
            
            # 5. Enforce LIMIT
            self._validate_limit(statement)
            
            # 6. Column allowlist
            self._validate_columns(statement, user_tier)
            
            self.validation_time_ms = int((time.monotonic() - start) * 1000)
            return sql
            
        except Exception as e:
            raise SQLValidationError(f"SQL validation failed: {e}")
    
    def _validate_operation(self, statement) -> None:
        """Must be SELECT only."""
        if not isinstance(statement, exp.Select):
            raise SQLValidationError(f"Only SELECT allowed, got {type(statement).__name__}")
    
    def _validate_single_statement(self, sql: str) -> None:
        """No multiple statements."""
        statements = sqlglot.parse(sql)
        if len(statements) > 1:
            raise SQLValidationError("Multiple statements not allowed")

    def _validate_identifier_lengths(self, statement) -> None:
        """Reject identifiers PostgreSQL would truncate at 63 bytes."""
        names: set[str] = set()
        for identifier in statement.find_all(exp.Identifier):
            value = identifier.name or identifier.this
            if value:
                names.add(str(value))
        for table in statement.find_all(exp.Table):
            if table.name:
                names.add(str(table.name))
            if table.alias:
                names.add(str(table.alias))
        for column in statement.find_all(exp.Column):
            if column.name:
                names.add(str(column.name))
            if column.table:
                names.add(str(column.table))

        for name in names:
            byte_len = len(name.encode("utf-8"))
            if byte_len > self.MAX_IDENTIFIER_BYTES:
                raise SQLValidationError(
                    f"identifier exceeds PostgreSQL limit: {name} is "
                    f"{byte_len} bytes > {self.MAX_IDENTIFIER_BYTES}"
                )
    
    def _validate_tables(self, statement) -> None:
        """No queries against disallowed tables."""
        for table in statement.find_all(exp.Table):
            if table.name.lower() in self.DISALLOWED_TABLES:
                raise SQLValidationError(f"Query on disallowed table: {table.name}")
    
    def _validate_limit(self, statement) -> None:
        """Enforce LIMIT <= MAX_ROWS."""
        limit_node = statement.find(exp.Limit)
        if limit_node:
            limit_val = limit_node.expression
            if limit_val and hasattr(limit_val, 'this'):
                limit_num = int(limit_val.this)
                if limit_num > self.MAX_ROWS:
                    raise SQLValidationError(f"LIMIT {limit_num} exceeds max {self.MAX_ROWS}")
        else:
            # Add LIMIT if missing
            statement.set("limit", exp.Limit(expression=exp.Literal.number(100)))
    
    def _validate_columns(self, statement, user_tier: int) -> None:
        """Enforce column allowlist."""
        for column in statement.find_all(exp.Column):
            col_name = column.name
            
            # Get allowed columns for tier
            allowed = self._get_allowed_columns(statement, user_tier)
            
            if allowed and col_name not in allowed:
                raise SQLValidationError(f"Column not allowed for tier {user_tier}: {col_name}")
    
    def _get_allowed_columns(self, statement, user_tier: int) -> Set[str]:
        """Get allowed columns from table."""
        for table in statement.find_all(exp.Table):
            table_name = table.name.lower()
            if table_name in self.column_allowlist:
                tier_key = f"tier_{user_tier}"
                allowlist = self.column_allowlist[table_name].get(tier_key, [])
                if "*" in allowlist:
                    return set()
                return set(allowlist)
        return set()


class QueryCompletenessValidator:
    """
    Validates that a generated SQL query is syntactically complete.

    Catches common LLM truncation failures:
    - HAVING without GROUP BY
    - ORDER BY without aggregate on ranked results
    - Trailing "-- [INCOMPLETE]" comments
    - Unclosed parentheses
    - Trailing operators (AND, OR, ON, WHERE without condition)
    """

    INCOMPLETE_PATTERNS = [
        r"--\s*\[INCOMPLETE\]",
        r"--\s*INCOMPLETE",
        r"\bINCOMPLETE\b",
        r"--\s*TODO",
        r"--\s*FIXME",
    ]

    TRAILING_CLAUSE_PATTERNS = [
        r"\b(WHERE|GROUP\s+BY|ORDER\s+BY|HAVING|JOIN|AND|OR|ON|WITH)\s*$",
        r"\b(WHERE|GROUP\s+BY|ORDER\s+BY|HAVING|JOIN|AND|OR|ON|WITH)\s*--",
    ]

    def __init__(self):
        import re
        self._incomplete_re = [re.compile(p, re.IGNORECASE) for p in self.INCOMPLETE_PATTERNS]
        self._trailing_re = [re.compile(p, re.IGNORECASE) for p in self.TRAILING_CLAUSE_PATTERNS]

    def validate(self, sql: str, user_query: str | None = None) -> tuple[bool, list[str]]:
        """
        Check if SQL query is complete.

        Returns (is_valid, list_of_issues).
        """
        issues = []
        sql_clean = sql.strip()

        if not sql_clean:
            return False, ["Empty query"]

        issues.extend(self._check_generation_failure(sql_clean))

        for pattern in self._incomplete_re:
            if pattern.search(sql_clean):
                issues.append("Query contains '[INCOMPLETE]' marker — query was truncated")

        paren_count = sql_clean.count("(") - sql_clean.count(")")
        if paren_count != 0:
            issues.append(f"Unbalanced parentheses: {paren_count} unclosed")

        for pattern in self._trailing_re:
            if pattern.search(sql_clean):
                issues.append("Query ends with incomplete clause (trailing WHERE/AND/OR/ON etc.)")

        trailing_whitespace = sql_clean.endswith(",") or sql_clean.endswith("+")
        if trailing_whitespace:
            issues.append("Query ends with trailing operator")

        issues.extend(self._check_credit_score_cast(sql_clean))
        issues.extend(self._check_year_over_year_aggregation(sql_clean, user_query=user_query))
        issues.extend(self._check_stage_synonym_sql(sql_clean))
        issues.extend(self._check_cross_domain_context(sql_clean, user_query=user_query))
        issues.extend(self._check_known_join_keys(sql_clean))
        issues.extend(self._check_late_having_scope(sql_clean, user_query=user_query))

        try:
            import sqlglot
            parsed = sqlglot.parse_one(sql_clean, read="postgres")
            issues.extend(self._check_having_without_group(parsed))
            issues.extend(self._check_having_without_aggregate(parsed))
            issues.extend(self._check_order_by_without_aggregate(sql_clean, parsed))
            issues.extend(self._check_patent_join_keys(sql_clean))
        except Exception:
            pass

        deduped = list(dict.fromkeys(issues))
        return len(deduped) == 0, deduped

    def _check_generation_failure(self, sql: str) -> list[str]:
        """Reject model failure markers that are not SQL."""
        sql_lower = sql.strip().lower()
        if sql_lower in {"error", "failed", "failure", "none", "null", "no sql"}:
            return ["Query generation failed without SQL"]
        if not re.match(r"^(select|with)\b", sql_lower):
            return ["Generated text is not a SELECT/WITH SQL query"]
        return []

    def _check_having_without_group(self, parsed) -> list[str]:
        """Detect HAVING used without GROUP BY."""
        issues = []
        having_nodes = list(parsed.find_all(exp.Having))
        group_by_nodes = list(parsed.find_all(exp.Group))

        if having_nodes and not group_by_nodes:
            issues.append("HAVING clause used without GROUP BY — aggregation incomplete")
        return issues

    def _check_having_without_aggregate(self, parsed) -> list[str]:
        """Detect HAVING clauses that do not constrain an aggregate or grouped metric."""
        issues = []
        for having in parsed.find_all(exp.Having):
            has_aggregate = any(having.find_all(exp.Sum, exp.Count, exp.Avg, exp.Min, exp.Max))
            if not has_aggregate:
                having_sql = having.sql(dialect="postgres").lower()
                grouped_metric = any(
                    token in having_sql
                    for token in (
                        "grant_drop_pct",
                        "patent_growth_pct",
                        "total_grant",
                        "total_credits",
                        "course_count",
                    )
                )
                if not grouped_metric:
                    issues.append("HAVING clause does not constrain an aggregate metric")
        return issues

    def _check_order_by_without_aggregate(self, sql: str, parsed) -> list[str]:
        """Detect ORDER BY on raw column when aggregate ranking was likely intended."""
        issues = []
        sql_lower = sql.lower()

        order_by_nodes = list(parsed.find_all(exp.Order))

        for order in order_by_nodes:
            for key in order.find_all(exp.Ordered):
                expr = key.this
                if isinstance(expr, exp.Column):
                    col_name = expr.name.lower()
                    has_distinct = "distinct" in sql_lower
                    has_group = bool(list(parsed.find_all(exp.Group)))

                    if (has_distinct or "top" in sql_lower) and not has_group:
                        if col_name not in ("name", "institute", "title"):
                            issues.append(
                                f"ORDER BY on raw column '{col_name}' — did you mean to aggregate first?"
                            )
        return issues

    def _check_credit_score_cast(self, sql: str) -> list[str]:
        """Reject direct casts of TEXT credit scores."""
        credit_identifier = (
            r"(?:(?:\"[A-Za-z_][\w]*\"|`[A-Za-z_][\w]*`|[A-Za-z_][\w]*)\s*\.\s*)?"
            r"(?:\"total_credit_score\"|`total_credit_score`|total_credit_score)"
        )
        numeric_types = r"(INT|INTEGER|BIGINT|NUMERIC|NUMBER|DECIMAL|DOUBLE|REAL|FLOAT)"
        if re.search(rf"CAST\s*\(\s*{credit_identifier}\s+AS\s+{numeric_types}", sql, re.IGNORECASE):
            return ["total_credit_score is TEXT in X:Y format; parse components before casting"]
        if re.search(rf"{credit_identifier}\s*::\s*{numeric_types}", sql, re.IGNORECASE):
            return ["total_credit_score is TEXT in X:Y format; parse components before casting"]
        return []

    def _check_year_over_year_aggregation(self, sql: str, user_query: str | None = None) -> list[str]:
        """Reject Dhairya P1 row-level YoY calculations that skip yearly aggregation."""
        sql_lower = " ".join(sql.lower().split())
        query_lower = (user_query or "").lower()
        is_yoy_question = any(
            token in query_lower
            for token in ("year-over-year", "year over year", "yoy", "growth trends", "growth")
        )
        has_yoy_sql = "lag(" in sql_lower or "year_over_year" in sql_lower or "previous_year" in sql_lower
        if not (is_yoy_question or has_yoy_sql):
            return []

        issues = []
        if "total_credit_score" in sql_lower and "lag(" in sql_lower:
            issues.append(
                "Year-over-year course growth must aggregate course counts before comparing years"
            )
        if "grant_received" in sql_lower and "group by" not in sql_lower:
            issues.append(
                "Year-over-year grant comparisons must aggregate by institute/year before comparing rows"
            )
        if is_yoy_question and "group by" not in sql_lower and any(
            token in sql_lower for token in ("total_credit_score", "grant_received", "financial_year")
        ):
            issues.append("Year-over-year analysis requires grouped yearly totals")
        return issues

    def _check_stage_synonym_sql(self, sql: str) -> list[str]:
        """Reject unresolved TRL/user-facing stage strings in SQL."""
        sql_upper = sql.upper()
        sql_lower = sql.lower()
        has_stage_context = (
            "TRL_STAGES" in sql_upper
            or "STAGE_OF_TECHNOLOGY" in sql_upper
            or "innovations_at_various_stages_of_technology_readiness_level" in sql_lower
        )
        if not has_stage_context:
            return []
        unresolved_literals = (
            "'TRL 4'",
            '"TRL 4"',
            "'TRL4'",
            '"TRL4"',
            "'TRL 9'",
            '"TRL 9"',
            "'TRL9'",
            '"TRL9"',
            "'MARKET READY'",
            '"MARKET READY"',
            "'FULLY MARKET READY'",
            '"FULLY MARKET READY"',
            "'LAB VALIDATION'",
            '"LAB VALIDATION"',
        )
        raw_like = re.search(
            r"\b(?:LIKE|ILIKE)\s+['\"]%?(?:TRL\s*[49]|TRL[49]|MARKET\s+READY|FULLY\s+MARKET\s+READY|LAB\s+VALIDATION)%?['\"]",
            sql,
            re.IGNORECASE,
        )
        if raw_like or any(token in sql_upper for token in unresolved_literals):
            return ["Stage synonyms must be expanded to stored values such as 'Level 4' or 'Level 9'"]
        return []

    def _check_cross_domain_context(self, sql: str, user_query: str | None = None) -> list[str]:
        """Reject course follow-up SQL that switches to enrollment tables."""
        if not user_query:
            return []
        query_lower = user_query.lower()
        sql_lower = " ".join(sql.lower().split())
        course_followup = any(
            token in query_lower
            for token in (
                "course",
                "courses",
                "curriculum",
                "ug",
                "undergraduate",
                "phd",
                "strategy shift",
                "compare",
            )
        )
        wrong_domain_tables = ("actual_student_strength", "phd_students", "sanctioned_intake")
        if (
            course_followup
            and "academic_courses_details" not in sql_lower
            and any(table in sql_lower for table in wrong_domain_tables)
        ):
            return [
                "Course follow-up changed domain to student/enrollment tables; use academic_courses_details"
            ]
        return []

    def _check_known_join_keys(self, sql: str) -> list[str]:
        """Reject known wrong joins from the external SQL audit corpus."""
        sql_lower = " ".join(sql.lower().split())
        issues = []
        if "innovation_grant_from_govt" in sql_lower and "patents_details" in sql_lower:
            issues.append(
                "Grant/patent joins must use combined_ipo_patent_data.applicants, not patents_details"
            )
        if (
            "academic_courses_details" in sql_lower
            and " join " in f" {sql_lower} "
            and any(
                table in sql_lower
                for table in ("actual_student_strength", "phd_students", "sanctioned_intake")
            )
        ):
            issues.append(
                "Course follow-up joins must stay in academic_courses_details unless the question explicitly asks for student counts"
            )
        return issues

    def _check_late_having_scope(self, sql: str, user_query: str | None = None) -> list[str]:
        """Reject the Dhairya Q14 zero-course narrowing for capex gap analysis."""
        if not user_query:
            return []
        query_lower = user_query.lower()
        if not ("capital" in query_lower and "low innovation" in query_lower):
            return []
        sql_lower = " ".join(sql.lower().split())
        if re.search(r"having .*count\s*\([^)]*\)\s*=\s*0", sql_lower):
            return [
                "Missing/Late HAVING scope: capex gap analysis should rank high capex with low course counts, not only zero-course institutes"
            ]
        return []

    def _check_patent_join_keys(self, sql: str) -> list[str]:
        """Require normalized applicants matching for grant/patent joins."""
        sql_lower = " ".join(sql.lower().split())
        if not (
            "innovation_grant_from_govt" in sql_lower
            and "combined_ipo_patent_data" in sql_lower
            and " join " in f" {sql_lower} "
        ):
            return []
        if "applicants" not in sql_lower:
            return ["Grant/patent joins must use combined_ipo_patent_data.applicants"]
        if "lower(" not in sql_lower or "trim(" not in sql_lower:
            return ["Grant/patent joins must normalize applicants and institute text"]
        return []

    def record_rejection(
        self,
        sql: str,
        issues: list[str],
        *,
        accepted_sql: str | None = None,
        user_query: str | None = None,
        hall_path: Path = HALL_OF_SHAME_PATH,
    ) -> None:
        """Append a rejected production SQL shape to the failure ledger."""
        if os.getenv("PYTEST_CURRENT_TEST") and os.getenv("NRG_RECORD_SQL_REJECTIONS") != "1":
            return
        hall_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).isoformat()
        query_line = f"\nUser query: {user_query[:240]}\n" if user_query else ""
        accepted = accepted_sql or "Pending accepted replacement from correction pass."
        entry = (
            f"\n\n## Rejection {timestamp}\n"
            f"{query_line}"
            f"Issues: {'; '.join(issues)}\n\n"
            "Rejected SQL:\n"
            "```sql\n"
            f"{sql.strip()[:2000]}\n"
            "```\n\n"
            "Accepted shape:\n"
            "```sql\n"
            f"{accepted.strip()[:2000]}\n"
            "```\n"
        )
        with hall_path.open("a", encoding="utf-8") as handle:
            handle.write(entry)

    def validate_or_raise(
        self,
        sql: str,
        *,
        accepted_sql: str | None = None,
        user_query: str | None = None,
        record_rejection: bool = False,
    ) -> None:
        """Validate and raise SQLValidationError if incomplete."""
        is_valid, issues = self.validate(sql, user_query=user_query)
        if not is_valid:
            if record_rejection:
                self.record_rejection(sql, issues, accepted_sql=accepted_sql, user_query=user_query)
            raise SQLValidationError(f"Query incomplete: {'; '.join(issues)}")


# Adversarial SQL test cases
ADVERSarial_SQL_TESTS = [
    # Injection attempts
    ("SELECT * FROM researchers; DROP TABLE researchers;--", "multi-statement"),
    ("SELECT * FROM researchers UNION SELECT * FROM funding", " UNION injection"),
    ("SELECT * FROM (SELECT * FROM funding) AS sub", "subquery"),
    
    # Limit bypass
    ("SELECT * FROM researchers LIMIT 10000", "exceeds limit"),
    ("SELECT * FROM researchers LIMIT 999999", "exceeds limit"),
    
    # Disallowed table
    ("SELECT * FROM users", "disallowed table"),
    ("SELECT * FROM auth", "disallowed table"),
    ("SELECT * FROM credentials", "disallowed table"),
    ("SELECT * FROM secrets", "disallowed table"),
    
    # Column access violation
    ("SELECT email, phone FROM researchers", "sensitive column"),
    ("SELECT aadhaar FROM researchers", "PII column"),
    ("SELECT password FROM auth", "credentials column"),
    
    # Admin bypass
    ("SELECT * FROM researchers WHERE access_tier < 1", "tier bypass"),
    ("SELECT * FROM researchers WHERE 1=1 OR access_tier < 3", "OR bypass"),
    
    # Time-based blind
    ("SELECT * FROM funding WHERE (SELECT CASE WHEN (SELECT COUNT(*) > 0 THEN 1 ELSE 0 END) = 1", "blind injection"),
    
    # Comment injection
    ("SELECT * FROM researchers -- admin comment", "comment injection"),
    
    # Nested query
    ("SELECT * FROM (SELECT researcher_id FROM funding) AS f JOIN researchers USING (researcher_id)", "nested"),
    
    # Wildcard in subquery
    ("SELECT * FROM researchers WHERE researcher_id IN (SELECT researcher_id FROM funding)", "IN subquery"),
    
    # CTE abuse
    ("WITH admin AS (SELECT * FROM users) SELECT * FROM admin", "CTE abuse"),
    
    # Function injection
    ("SELECT * FROM researchers WHERE name = (SELECT name FROM users)", "function subquery"),
    
    # Join injection
    ("SELECT r.*, u.* FROM researchers r JOIN users u ON r.researcher_id = u.id", "join disallowed"),
    
    # Order by blind
    ("SELECT * FROM researchers ORDER BY (SELECT TOP 1 name FROM users)", "blind order"),
    
    # Having blind
    ("SELECT * FROM researchers HAVING (SELECT COUNT(*) FROM users) > 0", "blind having"),
    
    # Group by blind
    ("SELECT * FROM researchers GROUP BY (SELECT name FROM users)", "blind group"),
    
    # Duplicate column
    ("SELECT *, * FROM researchers", "duplicate column"),
    
    # Into outfile
    ("SELECT * INTO OUTFILE '/tmp/data' FROM researchers", "outfile"),
    
    # Copy
    ("COPY researchers TO '/tmp/data'", "copy command"),
    
    # Fetch
    ("DECLARE cursor C FOR SELECT * FROM researchers; FETCH cursor", "cursor"),
    
    # Execute
    ("EXECUTE IMMEDIATE 'SELECT * FROM researchers'", "execute"),
    
    # Using merge
    ("MERGE INTO researchers USING funding ON researchers.id = funding.id", "merge"),
    
    # Transaction
    ("BEGIN; SELECT * FROM researchers; COMMIT", "transaction"),
    
    # Grant revoke
    ("GRANT SELECT ON researchers TO public", "grant"),
    ("REVOKE SELECT ON researchers FROM public", "revoke"),
    
    # Analyze
    ("ANALYZE researchers", "analyze"),
    ("EXPLAIN SELECT * FROM researchers", "explain"),
    
    # Set session
    ("SET search_path = public", "set config"),
    ("SET role = admin", "set role"),
]


def run_adversarial_tests():
    """Run all adversarial SQL tests."""
    validator = SQLValidator()
    results = []
    
    for sql, description in ADVERSarial_SQL_TESTS:
        try:
            validator.validate(sql, user_tier=1)
            results.append((sql, description, "PASSED - should have failed"))
        except SQLValidationError:
            results.append((sql, description, "CORRECTLY REJECTED"))
    
    return results


if __name__ == "__main__":
    results = run_adversarial_tests()
    for sql, desc, status in results:
        print(f"{status}: {desc}")

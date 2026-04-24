"""
SQL Oracle — Verified Text-to-SQL with confidence scoring and self-correction.

The Oracle wraps TextToSQLSkill with:
1. Confidence scoring based on schema match, result sanity, and completion
2. Result verification against expected column types and value ranges
3. Self-correction: regenerates SQL if confidence is LOW
4. Natural language explanation of what the query does

Usage:
    oracle = SQLOracle()
    result = oracle.ask("Which IIT has the most patents?")
    print(result["confidence"], result["answer"])
    oracle.close()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from src.skills.text_to_sql.skill import TextToSQLSkill
from src.skills.text_to_sql.validator import QueryCompletenessValidator

logger = logging.getLogger(__name__)


class Confidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class OracleResponse:
    confidence: Confidence
    answer: dict[str, Any]
    sql_generated: str
    explanation: str
    verification_warnings: list[str] = field(default_factory=list)
    self_correction_attempts: int = 0
    verification_passed: bool = True


class ResultVerifier:
    """Verifies SQL execution results for sanity and consistency."""

    EXPECTED_COLUMNS = {
        "researchers": {"id", "name", "institution", "state", "research_area", "h_index", "access_tier"},
        "publications": {"id", "title", "authors", "year", "journal", "impact_factor", "citations", "access_tier"},
        "institutions": {"id", "name", "state", "type", "established_year", "access_tier"},
        "projects": {"id", "title", "principal_investigator", "status", "funding_amount", "start_date", "access_tier"},
        "patents": {"id", "title", "inventors", "status", "filing_date", "access_tier"},
        "funding_records": {"id", "institute", "gov_organisation_name", "grant_received", "year_of_receiving", "access_tier"},
        "labs": {"id", "name", "institution", "research_focus_areas", "established_year", "access_tier"},
        "collaborations": {"id", "title", "partner_institutions", "status", "start_date", "access_tier"},
    }

    NUMERIC_COLUMNS = {
        "h_index", "impact_factor", "citations", "grant_received", "funding_amount",
        "year", "year_of_receiving", "established_year", "start_date", "filing_date",
    }

    def __init__(self):
        self.validator = QueryCompletenessValidator()

    def verify(
        self,
        sql: str,
        result: dict[str, Any],
        user_query: str,
    ) -> tuple[bool, list[str]]:
        """
        Verify result sanity. Returns (passed, warnings).
        """
        warnings = []
        issues = []

        if result.get("row_count") == 0:
            warnings.append("Query returned 0 rows — possible schema mismatch or overly restrictive filter")

        is_complete, completeness_issues = self.validator.validate(sql)
        if not is_complete:
            issues.append(f"Incomplete SQL: {'; '.join(completeness_issues)}")

        if result.get("row_count", 0) > 1000:
            warnings.append(f"Large result set ({result['row_count']} rows) — consider adding filters")

        schema_warnings = self._check_schema_consistency(result)
        warnings.extend(schema_warnings)

        numeric_warnings = self._check_numeric_sanity(result)
        warnings.extend(numeric_warnings)

        return len(issues) == 0, warnings

    def _check_schema_consistency(self, result: dict[str, Any]) -> list[str]:
        """Check if result columns are consistent with expected schema."""
        warnings = []
        if not result.get("results"):
            return warnings

        first_row = result["results"][0]
        columns = set(first_row.keys())

        known_columns: set[str] = set()
        for expected in self.EXPECTED_COLUMNS.values():
            known_columns |= expected

        unexpected = columns - known_columns
        if unexpected:
            warnings.append(f"Unexpected columns in result (not in known schema): {unexpected}")

        return warnings

    def _check_numeric_sanity(self, result: dict[str, Any]) -> list[str]:
        """Check if numeric columns have reasonable values."""
        warnings = []
        if not result.get("results"):
            return warnings

        for row in result["results"][:10]:
            for col, value in row.items():
                if col in self.NUMERIC_COLUMNS and value is not None:
                    try:
                        num_val = float(value)
                        if num_val < 0 and col not in ("year", "year_of_receiving", "start_date", "filing_date"):
                            warnings.append(f"Negative value in {col}: {num_val}")
                        if col == "h_index" and num_val > 1000:
                            warnings.append(f"Unrealistic h_index value: {num_val}")
                        if col == "impact_factor" and num_val > 100:
                            warnings.append(f"Unrealistic impact_factor value: {num_val}")
                    except (ValueError, TypeError):
                        pass

        return warnings


class SQLOracle:
    """
    Verified text-to-SQL with confidence scoring and self-correction.

    Wraps TextToSQLSkill with an Oracle layer that:
    - Scores confidence in generated SQL before execution
    - Verifies results for sanity
    - Self-corrects by regenerating if confidence is LOW
    - Provides natural language explanation
    """

    MAX_CORRECTION_ATTEMPTS = 2

    def __init__(self, llm_provider: Optional[Any] = None):
        self.text_to_sql = TextToSQLSkill(llm_provider=llm_provider)
        self.verifier = ResultVerifier()
        self._completeness_validator = QueryCompletenessValidator()

    def ask(
        self,
        question: str,
        user_tier: int = 1,
        user_id: str = "oracle",
    ) -> OracleResponse:
        """
        Ask the Oracle a question and get a verified answer.

        Returns OracleResponse with confidence, answer, SQL, explanation, and warnings.
        """
        sql, result, attempts = self._generate_and_execute(
            question, user_tier, user_id
        )

        verification_passed, warnings = self.verifier.verify(sql, result, question)

        confidence = self._score_confidence(
            sql=sql,
            result=result,
            verification_passed=verification_passed,
            warnings=warnings,
        )

        if confidence == Confidence.LOW and attempts < self.MAX_CORRECTION_ATTEMPTS:
            logger.info(f"Low confidence ({confidence.value}) — attempting self-correction")
            sql_corr, result_corr, attempts_corr = self._generate_and_execute(
                question, user_tier, user_id, retry_context=f"Previous query had issues: {warnings}"
            )
            verification_passed_corr, warnings_corr = self.verifier.verify(sql_corr, result_corr, question)
            confidence_corr = self._score_confidence(
                sql=sql_corr,
                result=result_corr,
                verification_passed=verification_passed_corr,
                warnings=warnings_corr,
            )
            if confidence_corr.value > confidence.value:
                sql, result, attempts = sql_corr, result_corr, attempts_corr
                verification_passed, warnings = verification_passed_corr, warnings_corr
                confidence = confidence_corr

        explanation = self._generate_explanation(question, sql, result, confidence)

        return OracleResponse(
            confidence=confidence,
            answer=result,
            sql_generated=sql,
            explanation=explanation,
            verification_warnings=warnings,
            self_correction_attempts=attempts,
            verification_passed=verification_passed,
        )

    def _generate_and_execute(
        self,
        question: str,
        user_tier: int,
        user_id: str,
        retry_context: str = "",
    ) -> tuple[str, dict[str, Any], int]:
        """Generate SQL and execute it, returning (sql, result, attempts)."""
        attempts = 0
        result: dict[str, Any] = {}

        while attempts <= self.MAX_CORRECTION_ATTEMPTS:
            attempts += 1
            try:
                result = self.text_to_sql.execute(
                    question if attempts == 1 else f"{question}\n\n[RETRY context: {retry_context}]",
                    user_tier=user_tier,
                    user_id=user_id,
                )
                break
            except Exception as e:
                logger.warning(f"Text-to-SQL attempt {attempts} failed: {e}")
                if attempts > self.MAX_CORRECTION_ATTEMPTS:
                    result = {
                        "query": "",
                        "columns": [],
                        "results": [],
                        "row_count": 0,
                        "error": str(e),
                    }
                    break

        try:
            sql = result.get("query", "")
        except Exception:
            sql = ""

        return sql, result, attempts - 1

    def _score_confidence(
        self,
        sql: str,
        result: dict[str, Any],
        verification_passed: bool,
        warnings: list[str],
    ) -> Confidence:
        """Score confidence in the generated SQL and results."""
        score = 0

        is_complete, _ = self._completeness_validator.validate(sql)
        if is_complete:
            score += 2
        else:
            score -= 1

        if verification_passed:
            score += 2

        row_count = result.get("row_count", 0)
        if row_count > 0:
            score += 1

        if len(warnings) == 0:
            score += 1
        elif any("0 rows" in w for w in warnings):
            score -= 1

        if sql and len(sql) > 20:
            score += 1

        if score >= 5:
            return Confidence.HIGH
        elif score >= 3:
            return Confidence.MEDIUM
        else:
            return Confidence.LOW

    def _generate_explanation(
        self,
        question: str,
        sql: str,
        result: dict[str, Any],
        confidence: Confidence,
    ) -> str:
        """Generate a natural language explanation of what the query does."""
        row_count = result.get("row_count", 0)
        columns = result.get("columns", [])
        tables_used = result.get("schema_used", [])

        parts = []
        parts.append(f"Answered your question about: '{question}'")

        if row_count == 0:
            parts.append("The query returned no results — either there's no matching data or filters were too restrictive.")
        else:
            parts.append(f"Found {row_count} result{'s' if row_count != 1 else ''}.")
            if columns:
                parts.append(f"Results include: {', '.join(columns[:5])}.")
            if tables_used:
                parts.append(f"Data drawn from: {', '.join(tables_used)}.")

        parts.append(f"Confidence: {confidence.value.upper()}.")

        if confidence == Confidence.LOW:
            parts.append("Note: This answer has low confidence — verify the results before making decisions.")

        return " ".join(parts)

    def close(self):
        """Clean up resources."""
        self.text_to_sql.close()

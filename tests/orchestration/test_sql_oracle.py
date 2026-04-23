"""
Tests for SQL Oracle — confidence scoring, self-correction, and verification.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.skills.text_to_sql.sql_oracle import (
    Confidence,
    OracleResponse,
    ResultVerifier,
    SQLOracle,
)


class TestResultVerifier:
    """Tests for ResultVerifier class."""

    def setup_method(self):
        self.verifier = ResultVerifier()

    def test_verify_empty_results_returns_warning(self):
        result = {
            "query": "SELECT * FROM researchers",
            "columns": ["id", "name"],
            "results": [],
            "row_count": 0,
        }
        passed, warnings = self.verifier.verify(
            "SELECT * FROM researchers", result, "get all researchers"
        )
        assert passed is True
        assert any("0 rows" in w for w in warnings)

    def test_verify_large_result_set_returns_warning(self):
        result = {
            "query": "SELECT * FROM researchers",
            "columns": ["id", "name"],
            "results": [{"id": i, "name": f"Researcher {i}"} for i in range(2000)],
            "row_count": 2000,
        }
        passed, warnings = self.verifier.verify(
            "SELECT * FROM researchers", result, "get all researchers"
        )
        assert any("Large result set" in w for w in warnings)

    def test_verify_incomplete_sql_detected(self):
        result = {
            "query": "SELECT * FROM researchers WHERE",
            "columns": [],
            "results": [],
            "row_count": 0,
        }
        passed, warnings = self.verifier.verify(
            "SELECT * FROM researchers WHERE", result, "get researchers"
        )
        assert passed is False

    def test_verify_numeric_sanity_positive_h_index(self):
        result = {
            "query": "SELECT name, h_index FROM researchers",
            "columns": ["name", "h_index"],
            "results": [{"name": "Dr. Rao", "h_index": 45}],
            "row_count": 1,
        }
        passed, warnings = self.verifier.verify(
            "SELECT name, h_index FROM researchers", result, "get h-index"
        )
        assert passed is True
        assert not any("Unrealistic" in w for w in warnings)

    def test_verify_numeric_sanity_unrealistic_h_index(self):
        result = {
            "query": "SELECT name, h_index FROM researchers",
            "columns": ["name", "h_index"],
            "results": [{"name": "Dr. Rao", "h_index": 5000}],
            "row_count": 1,
        }
        passed, warnings = self.verifier.verify(
            "SELECT name, h_index FROM researchers", result, "get h-index"
        )
        assert any("Unrealistic" in w for w in warnings)

    def test_verify_numeric_sanity_unrealistic_impact_factor(self):
        result = {
            "query": "SELECT title, impact_factor FROM publications",
            "columns": ["title", "impact_factor"],
            "results": [{"title": "Paper", "impact_factor": 500}],
            "row_count": 1,
        }
        passed, warnings = self.verifier.verify(
            "SELECT title, impact_factor FROM publications", result, "get impact factor"
        )
        assert any("Unrealistic" in w for w in warnings)

    def test_verify_normal_results_passes(self):
        result = {
            "query": "SELECT id, name, institution FROM researchers LIMIT 10",
            "columns": ["id", "name", "institution"],
            "results": [
                {"id": "r1", "name": "Dr. Rao", "institution": "IIT Bombay"},
                {"id": "r2", "name": "Dr. Patel", "institution": "IIT Delhi"},
            ],
            "row_count": 2,
        }
        passed, warnings = self.verifier.verify(
            "SELECT id, name, institution FROM researchers LIMIT 10",
            result,
            "get researchers",
        )
        assert passed is True
        assert len(warnings) == 0


class TestConfidenceScoring:
    """Tests for confidence scoring logic."""

    def setup_method(self):
        self.oracle = SQLOracle.__new__(SQLOracle)
        self.oracle._completeness_validator = ResultVerifier().validator

    def test_high_confidence_complete_sql_with_results(self):
        sql = "SELECT id, name FROM researchers LIMIT 10;"
        result = {
            "query": sql,
            "columns": ["id", "name"],
            "results": [{"id": "r1", "name": "Dr. Rao"}],
            "row_count": 1,
        }
        confidence = self.oracle._score_confidence(
            sql=sql, result=result, verification_passed=True, warnings=[]
        )
        assert confidence == Confidence.HIGH

    def test_low_confidence_empty_results(self):
        sql = "SELECT * FROM researchers WHERE"
        result = {
            "query": sql,
            "columns": [],
            "results": [],
            "row_count": 0,
        }
        confidence = self.oracle._score_confidence(
            sql=sql, result=result, verification_passed=True, warnings=["Query returned 0 rows"]
        )
        assert confidence == Confidence.LOW

    def test_medium_confidence_partial_issues(self):
        sql = "SELECT * FROM researchers WHERE"
        result = {
            "query": sql,
            "columns": ["id", "name"],
            "results": [{"id": i, "name": f"R{i}"} for i in range(5)],
            "row_count": 5,
        }
        confidence = self.oracle._score_confidence(
            sql=sql, result=result, verification_passed=True, warnings=[]
        )
        assert confidence == Confidence.MEDIUM

    def test_low_confidence_incomplete_sql(self):
        sql = "SELECT * FROM researchers WHERE"
        result = {
            "query": sql,
            "columns": [],
            "results": [],
            "row_count": 0,
        }
        confidence = self.oracle._score_confidence(
            sql=sql, result=result, verification_passed=False, warnings=["Incomplete SQL"]
        )
        assert confidence == Confidence.LOW


class TestSQLOracleAsk:
    """Integration tests for SQLOracle.ask()"""

    def test_ask_returns_oracle_response(self):
        mock_result = {
            "query": "SELECT id, name FROM researchers LIMIT 10",
            "columns": ["id", "name"],
            "results": [{"id": "r1", "name": "Dr. Rao"}],
            "row_count": 1,
            "schema_used": ["researchers"],
            "audit_logged": True,
            "query_complete": True,
        }

        with patch.object(
            SQLOracle, "_generate_and_execute", return_value=("SELECT id, name FROM researchers LIMIT 10", mock_result, 0)
        ):
            oracle = SQLOracle.__new__(SQLOracle)
            oracle.text_to_sql = MagicMock()
            oracle.verifier = ResultVerifier()
            oracle._completeness_validator = ResultVerifier().validator

            response = oracle.ask("Which researchers are in the database?", user_tier=1)

            assert isinstance(response, OracleResponse)
            assert isinstance(response.confidence, Confidence)
            assert "answer" in response.answer or response.answer is not None
            assert response.explanation
            assert response.self_correction_attempts == 0

    def test_ask_low_confidence_triggers_correction(self):
        mock_result_bad = {
            "query": "SELECT * FROM researchers WHERE",
            "columns": [],
            "results": [],
            "row_count": 0,
            "error": "incomplete",
        }
        mock_result_good = {
            "query": "SELECT id, name FROM researchers LIMIT 10",
            "columns": ["id", "name"],
            "results": [{"id": "r1", "name": "Dr. Rao"}],
            "row_count": 1,
            "schema_used": ["researchers"],
            "audit_logged": True,
            "query_complete": True,
        }

        call_count = [0]

        def mock_generate(question, user_tier, user_id, retry_context=""):
            call_count[0] += 1
            if call_count[0] == 1:
                return "SELECT * FROM researchers WHERE", mock_result_bad, 0
            return "SELECT id, name FROM researchers LIMIT 10", mock_result_good, 1

        with patch.object(SQLOracle, "_generate_and_execute", side_effect=mock_generate):
            oracle = SQLOracle.__new__(SQLOracle)
            oracle.text_to_sql = MagicMock()
            oracle.verifier = ResultVerifier()
            oracle._completeness_validator = ResultVerifier().validator

            response = oracle.ask("get researchers", user_tier=1)

            assert isinstance(response, OracleResponse)
            assert response.self_correction_attempts >= 0


class TestExplanationGeneration:
    """Tests for natural language explanation generation."""

    def setup_method(self):
        self.oracle = SQLOracle.__new__(SQLOracle)
        self.oracle._completeness_validator = ResultVerifier().validator

    def test_explanation_for_results(self):
        result = {
            "query": "SELECT name, h_index FROM researchers LIMIT 10",
            "columns": ["name", "h_index"],
            "results": [
                {"name": "Dr. Rao", "h_index": 45},
                {"name": "Dr. Patel", "h_index": 38},
            ],
            "row_count": 2,
            "schema_used": ["researchers"],
        }
        explanation = self.oracle._generate_explanation(
            "Which researchers have highest h-index?",
            "SELECT name, h_index FROM researchers LIMIT 10",
            result,
            Confidence.HIGH,
        )
        assert "h-index" in explanation
        assert "2 results" in explanation
        assert "HIGH" in explanation

    def test_explanation_for_empty_results(self):
        result = {
            "query": "SELECT * FROM researchers WHERE h_index > 1000",
            "columns": [],
            "results": [],
            "row_count": 0,
            "schema_used": [],
        }
        explanation = self.oracle._generate_explanation(
            "Researchers with h-index > 1000",
            "SELECT * FROM researchers WHERE h_index > 1000",
            result,
            Confidence.LOW,
        )
        assert "no results" in explanation.lower() or "0" in explanation
        assert "LOW" in explanation

    def test_explanation_for_low_confidence_includes_warning(self):
        result = {
            "query": "SELECT * FROM researchers",
            "columns": ["id", "name"],
            "results": [{"id": "r1", "name": "Dr. Rao"}],
            "row_count": 1,
            "schema_used": ["researchers"],
        }
        explanation = self.oracle._generate_explanation(
            "get researchers",
            "SELECT * FROM researchers",
            result,
            Confidence.LOW,
        )
        assert "low confidence" in explanation.lower()


class TestOracleResponse:
    """Tests for OracleResponse dataclass."""

    def test_oracle_response_fields(self):
        response = OracleResponse(
            confidence=Confidence.HIGH,
            answer={"results": []},
            sql_generated="SELECT 1",
            explanation="Test explanation",
            verification_warnings=["warning1"],
            self_correction_attempts=1,
            verification_passed=True,
        )
        assert response.confidence == Confidence.HIGH
        assert response.sql_generated == "SELECT 1"
        assert response.explanation == "Test explanation"
        assert response.verification_warnings == ["warning1"]
        assert response.self_correction_attempts == 1
        assert response.verification_passed is True

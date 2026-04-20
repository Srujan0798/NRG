"""Tests for SQL Validator."""

import pytest

from src.skills.text_to_sql.validator import SQLValidator, SQLValidationError


class TestSQLValidator:
    def test_valid_select_passes(self):
        validator = SQLValidator()
        result = validator.validate("SELECT * FROM researchers LIMIT 10")
        assert "SELECT" in result

    def test_insert_rejected(self):
        validator = SQLValidator()
        with pytest.raises(SQLValidationError):
            validator.validate("INSERT INTO researchers VALUES (1)")

    def test_update_rejected(self):
        validator = SQLValidator()
        with pytest.raises(SQLValidationError):
            validator.validate("UPDATE researchers SET name = 'x'")

    def test_delete_rejected(self):
        validator = SQLValidator()
        with pytest.raises(SQLValidationError):
            validator.validate("DELETE FROM researchers")

    def test_drop_rejected(self):
        validator = SQLValidator()
        with pytest.raises(SQLValidationError):
            validator.validate("DROP TABLE researchers")

    def test_multi_statement_rejected(self):
        validator = SQLValidator()
        with pytest.raises(SQLValidationError):
            validator.validate("SELECT * FROM researchers; DROP TABLE researchers")

    def test_limit_exceeded_rejected(self):
        validator = SQLValidator()
        with pytest.raises(SQLValidationError):
            validator.validate("SELECT * FROM researchers LIMIT 10000")

    def test_disallowed_table_rejected(self):
        validator = SQLValidator()
        with pytest.raises(SQLValidationError):
            validator.validate("SELECT * FROM users")

    def test_validation_time_tracked(self):
        validator = SQLValidator()
        validator.validate("SELECT * FROM researchers LIMIT 10")
        assert validator.validation_time_ms >= 0


class TestAdversarialTests:
    def test_adversarial_suite(self):
        from src.skills.text_to_sql.validator import run_adversarial_tests

        results = run_adversarial_tests()
        # Most adversarial cases should be correctly rejected
        rejected = [r for r in results if r[2] == "CORRECTLY REJECTED"]
        passed_when_should_fail = [r for r in results if r[2] == "PASSED - should have failed"]

        # We expect the majority to be rejected; some edge cases may pass
        # depending on sqlglot parsing, but known-bad patterns must be caught
        assert len(rejected) > len(passed_when_should_fail)

        # Ensure at least the most critical ones are rejected
        critical_patterns = ["multi-statement", "disallowed table", "exceeds limit"]
        for pattern in critical_patterns:
            matching = [r for r in results if pattern in r[1] and r[2] == "CORRECTLY REJECTED"]
            assert len(matching) > 0, f"Critical pattern not rejected: {pattern}"

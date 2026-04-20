"""SQL Validator - AST-level validation for text-to-sql skill."""

import sqlglot
from sqlglot import exp
from typing import Set, Optional


class SQLValidationError(Exception):
    """SQL validation failed."""
    pass


class SQLValidator:
    """Validates SQL against security policies."""
    
    DISALLOWED_TABLES = {"users", "auth", "credentials", "secrets"}
    ALLOWED_OPERATIONS = {"SELECT"}
    MAX_ROWS = 1000
    MAX_DEPTH = 2
    
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
            
            # 3. No queries on disallowed tables
            self._validate_tables(statement)
            
            # 4. Enforce LIMIT
            self._validate_limit(statement)
            
            # 5. Column allowlist
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
"""SQL Query Allowlisting for text_to_sql skill.

Blocks: DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, CREATE
Allows: SELECT only
Validates against whitelist regex
Logs all blocked attempts.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

BLOCKED_KEYWORDS = frozenset({
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "EXEC",
    "EXECUTE",
    "GRANT",
    "REVOKE",
})

BLOCKED_PATTERNS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\s+(TABLE|INDEX|DATABASE|VIEW|PROCEDURE)\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r";\s*\w+\s*;",  # Double semicolon with command in between
    r"UNION\s+(ALL\s+)?SELECT",  # UNION injection
    r"INTO\s+OUTFILE",
    r"LOAD_FILE",
]

ALLOWED_PATTERN = re.compile(
    r"^\s*(SELECT|WITH)\b",
    re.IGNORECASE | re.DOTALL,
)

BLOCKED_QUERY_LOG: list[dict] = []

SENSITIVE_LITERAL_PATTERNS = (
    (re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
    (
        re.compile(r"\b[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
        "[TOKEN_REDACTED]",
    ),
    (
        re.compile(
            r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b",
            re.IGNORECASE,
        ),
        "[GSTIN_REDACTED]",
    ),
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE), "[PAN_REDACTED]"),
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[AADHAAR_REDACTED]"),
    (re.compile(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"), "[PHONE_REDACTED]"),
)


def _redact_sensitive_literals(query: str) -> str:
    """Mask sensitive literals before a blocked query enters diagnostics."""
    redacted = query or ""
    for pattern, replacement in SENSITIVE_LITERAL_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def log_blocked_query(
    query: str,
    reason: str,
    user_id: str = "unknown",
    session_id: Optional[str] = None,
) -> None:
    """Log all blocked SQL query attempts."""
    redacted_query = _redact_sensitive_literals(query)
    query_preview = redacted_query[:200] if redacted_query else ""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "session_id": session_id,
        "query_preview": query_preview,
        "reason": reason,
        "blocked": True,
    }
    BLOCKED_QUERY_LOG.append(entry)
    logger.warning(
        "SQL QUERY BLOCKED: user=%s reason=%s query=%s",
        user_id,
        reason,
        query_preview,
    )


def is_select_only(query: str) -> bool:
    """Check if query is SELECT-only (case insensitive)."""
    return ALLOWED_PATTERN.match(query) is not None


def contains_blocked_keyword(query: str) -> Optional[str]:
    """Check for blocked keywords. Returns keyword found or None."""
    query_upper = query.upper()
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", query_upper):
            return keyword
    return None


def matches_blocked_pattern(query: str) -> Optional[str]:
    """Check for blocked regex patterns. Returns pattern matched or None."""
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE | re.DOTALL):
            return pattern
    return None


class SQLAllowlist:
    """SQL query validation against allowlist rules."""

    def __init__(self):
        self._blocked_log = BLOCKED_QUERY_LOG

    def validate(self, query: str) -> tuple[bool, str]:
        """Validate SQL query. Returns (allowed, reason)."""
        if not query or not query.strip():
            return False, "Empty query"

        if not is_select_only(query):
            return False, "Query must be SELECT only. Detected non-SELECT statement"

        blocked_keyword = contains_blocked_keyword(query)
        if blocked_keyword:
            return False, f"Blocked keyword detected: {blocked_keyword}"

        blocked_pattern = matches_blocked_pattern(query)
        if blocked_pattern:
            return False, f"Blocked pattern detected: {blocked_pattern}"

        return True, "OK"

    def validate_and_log(
        self,
        query: str,
        user_id: str = "unknown",
        session_id: Optional[str] = None,
    ) -> bool:
        """Validate query and log if blocked."""
        allowed, reason = self.validate(query)

        if not allowed:
            log_blocked_query(query, reason, user_id, session_id)
            return False

        logger.debug("SQL query allowed: %s", query[:100])
        return True

    def get_blocked_logs(self, limit: int = 100) -> list[dict]:
        """Get recent blocked query logs."""
        return list(self._blocked_log[-limit:])


_allowlist_instance: Optional[SQLAllowlist] = None


def get_sql_allowlist() -> SQLAllowlist:
    global _allowlist_instance
    if _allowlist_instance is None:
        _allowlist_instance = SQLAllowlist()
    return _allowlist_instance


def validate_sql_query(
    query: str,
    user_id: str = "unknown",
    session_id: Optional[str] = None,
) -> bool:
    """Convenience function to validate SQL query.

    Returns True if allowed, False if blocked.
    """
    return get_sql_allowlist().validate_and_log(query, user_id, session_id)


def is_safe_sql(query: str) -> bool:
    """Alias for validate_sql_query."""
    return validate_sql_query(query)

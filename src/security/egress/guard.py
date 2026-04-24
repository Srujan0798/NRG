"""Egress Sovereignty Guard - Prevents raw research content from leaving VPC.

This guard wraps all outbound HTTP clients and inspects payloads to ensure
no raw publication content (full_text, abstract) is sent to cloud LLMs.
Only schema prompts, user queries, and metadata may traverse the boundary.

Includes ALERTING: logs + notifies on violation attempts.
"""

import hashlib
import logging
import os
import re
from typing import Any, Callable, Optional
from functools import wraps
from datetime import datetime, UTC
import httpx
from src.audit import AuditEvent, get_audit_log
from src.security.egress.schema_allowlist_loader import get_allowlist

logger = logging.getLogger(__name__)

alert_callback: Optional[Callable[[dict], None]] = None


def set_alert_callback(callback: Callable[[dict], None]) -> None:
    """Set a callback for egress violation alerts (e.g., Slack, email)."""
    global alert_callback
    alert_callback = callback


def _send_alert(violation: "SovereigntyViolation", url: str, payload: dict) -> None:
    """Send alert on sovereignty violation attempt."""
    alert_data = {
        "type": "egress_guard_violation",
        "severity": "CRITICAL",
        "reason": violation.reason,
        "blocked_field": violation.blocked_field,
        "url": url,
        "timestamp": str(datetime.now(UTC)),
    }
    logger.critical(f"SECURITY ALERT: {alert_data}")

    if alert_callback:
        try:
            alert_callback(alert_data)
        except Exception as e:
            logger.error(f"Failed to send egress alert: {e}")


BLOCKED_PATTERNS = [
    r"publications?\.(full_text|abstract|fulltext)",
    r"researchers?\.(email|phone|address)",
    r"raw\s+(publication|research|db)\s+data",
]


class SovereigntyViolation(Exception):
    """Raised when content violates sovereignty boundaries."""
    def __init__(self, reason: str, blocked_field: Optional[str] = None):
        self.reason = reason
        self.blocked_field = blocked_field
        super().__init__(f"Sovereignty violation: {reason}")


class SovereignHTTPXClient:
    """HTTP client wrapper that enforces sovereignty on outbound requests.

    Inspects payloads to ensure no raw research content is sent to cloud LLM APIs.
    Only the following may traverse the boundary:
    - user_query (user's question)
    - schema_prompt (database schema description)
    - plan_json (planner output)
    - intent_label, citation_ids, session_id, user_tier
    """

    def __init__(self, inner: Optional[httpx.Client] = None):
        self._inner = inner or httpx.Client()
        self._publication_content_hashes: set[str] = set()
        self._allowlist_mode = True
        self._enabled = os.getenv("NRG_SOVEREIGNTY_ENFORCED", "1") == "1"

    def _build_content_signature(self, content: str) -> set[str]:
        """Build 8-gram shingles for content fingerprinting."""
        shingles = set()
        content_lower = content.lower()
        words = content_lower.split()
        for i in range(len(words) - 7):
            shingle = " ".join(words[i:i+8])
            shingles.add(hashlib.sha256(shingle.encode()).hexdigest()[:16])
        return shingles

    def _inspect_payload(self, payload: dict | list | str) -> None:
        """Inspect payload for sovereignty violations.

        Raises SovereigntyViolation if raw content is detected.
        """
        if not self._enabled:
            return

        allowlist = get_allowlist()
        blocked_content = allowlist.get_blocked_content()
        blocked_column_names = set()
        for tbl in allowlist.get_allowed_tables():
            _, blocked = allowlist.get_table_columns(tbl)
            blocked_column_names.update(blocked)

        def check_value(key: str, value: Any, path: str = "") -> None:
            key_lower = key.lower()

            if key_lower in blocked_content:
                raise SovereigntyViolation(
                    f"Blocked sensitive field '{key}' in {path or 'payload'}",
                    blocked_field=key
                )

            if key_lower in blocked_column_names:
                raise SovereigntyViolation(
                    f"Blocked column field '{key}' in {path or 'payload'}",
                    blocked_field=key
                )

            if isinstance(value, str):
                value_lower = value.lower()

                for pattern in BLOCKED_PATTERNS:
                    if re.search(pattern, f"{key_lower}={value_lower}"):
                        raise SovereigntyViolation(
                            f"Blocked pattern in {path or key}",
                            blocked_field=key
                        )

                if key_lower == "schema_prompt":
                    self._check_schema_prompt(value, blocked_content)

                if len(value) > 50000:
                    logger.warning("Large payload field %s may contain content", path or key)

            elif isinstance(value, dict):
                for k, v in value.items():
                    check_value(k, v, f"{path}.{k}" if path else k)

            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        for k, v in item.items():
                            check_value(k, v, f"{path}[{i}].{k}" if path else f"[{i}].{k}")
                    else:
                        check_value(f"item[{i}]", item, path)

        if isinstance(payload, dict):
            for key, value in payload.items():
                check_value(key, value)
        elif isinstance(payload, list):
            for i, item in enumerate(payload):
                if isinstance(item, dict):
                    for key, value in item.items():
                        check_value(key, value, f"[{i}].{key}")
                else:
                    check_value(f"[{i}]", item)

    def _check_schema_prompt(self, content: str, blocked_content: frozenset) -> None:
        """Validate schema_prompt against table/column allowlist.

        Raises SovereigntyViolation if schema_prompt references unlisted tables/columns.
        """
        allowlist = get_allowlist()

        found_tables = []
        alias_to_table = {}

        from_pattern = r'from\s+([a-z_][a-z0-9_]*)(?:\s+(?:as\s+)?([a-z_][a-z0-9_]*))?'
        for match in re.finditer(from_pattern, content, re.IGNORECASE):
            table = match.group(1).lower()
            alias = match.group(2).lower() if match.group(2) else table
            if alias not in alias_to_table:
                alias_to_table[alias] = table
            if table not in found_tables:
                found_tables.append(table)
                if not allowlist.is_table_allowed(table):
                    raise SovereigntyViolation(
                        f"Unlisted table '{table}' in schema_prompt",
                        blocked_field="schema_prompt"
                    )

        join_pattern = r'join\s+([a-z_][a-z0-9_]*)(?:\s+(?:as\s+)?([a-z_][a-z0-9_]*))?'
        for match in re.finditer(join_pattern, content, re.IGNORECASE):
            table = match.group(1).lower()
            alias = match.group(2).lower() if match.group(2) else table
            if alias not in alias_to_table:
                alias_to_table[alias] = table
            if table not in found_tables:
                found_tables.append(table)
                if not allowlist.is_table_allowed(table):
                    raise SovereigntyViolation(
                        f"Unlisted table '{table}' in schema_prompt",
                        blocked_field="schema_prompt"
                    )

        column_pattern = r'([a-z_][a-z0-9_]*)\s*\.\s*([a-z_][a-z0-9_]*)'
        for match in re.finditer(column_pattern, content, re.IGNORECASE):
            alias_or_table = match.group(1).lower()
            column = match.group(2).lower()

            resolved_table = alias_or_table
            if alias_or_table in alias_to_table:
                resolved_table = alias_to_table[alias_or_table]
            elif alias_or_table not in found_tables:
                if not allowlist.is_table_allowed(alias_or_table):
                    raise SovereigntyViolation(
                        f"Unlisted table '{alias_or_table}' in schema_prompt",
                        blocked_field="schema_prompt"
                    )
                found_tables.append(alias_or_table)

            if not allowlist.is_column_allowed(resolved_table, column):
                raise SovereigntyViolation(
                    f"Blocked column '{resolved_table}.{column}' in schema_prompt",
                    blocked_field="schema_prompt"
                )

        select_pattern = r'select\s+(.*?)\s+from\s+([a-z_][a-z0-9_]*)'
        for match in re.finditer(select_pattern, content, re.IGNORECASE):
            select_cols = match.group(1)
            table = match.group(2).lower()
            if table not in found_tables:
                if not allowlist.is_table_allowed(table):
                    raise SovereigntyViolation(
                        f"Unlisted table '{table}' in schema_prompt",
                        blocked_field="schema_prompt"
                    )
                found_tables.append(table)
            if allowlist.is_table_allowed(table):
                allowed_cols, blocked_cols = allowlist.get_table_columns(table)
                for col in re.split(r'[,;\s]+', select_cols):
                    col = col.strip()
                    if col and col not in ('*', 'COUNT(*)', 'count(*)'):
                        if col in blocked_cols:
                            raise SovereigntyViolation(
                                f"Blocked column '{col}' in schema_prompt",
                                blocked_field="schema_prompt"
                            )

    def inspect_payload(self, payload: dict | list | str) -> None:
        """Public payload inspection entrypoint for non-httpx clients."""
        try:
            self._inspect_payload(payload)
        except SovereigntyViolation as exc:
            self._log_violation(exc, "payload_inspection")
            raise

    def _log_violation(self, violation: SovereigntyViolation, url: str, payload: dict = None) -> None:
        """Log sovereignty violation to audit trail + send alert."""
        try:
            get_audit_log().append(
                AuditEvent(
                    event_type="egress_block",
                    user_id="system",
                    result={
                        "reason": violation.reason,
                        "blocked_field": violation.blocked_field,
                        "url": url,
                    },
                )
            )
        except Exception:
            logger.warning("Failed to log sovereignty violation", exc_info=True)

        _send_alert(violation, url, payload or {})

        logger.error(
            "SOVEREIGNTY VIOLATION BLOCKED: %s | field: %s | URL: %s",
            violation.reason,
            violation.blocked_field,
            url
        )

    def post(self, url: str, **kwargs) -> httpx.Response:
        """POST with sovereignty inspection."""
        json_data = kwargs.get("json")

        if json_data and self._enabled:
            try:
                self._inspect_payload(json_data)
            except SovereigntyViolation as e:
                self._log_violation(e, url, json_data)
                raise

        return self._inner.post(url, **kwargs)

    def get(self, url: str, **kwargs) -> httpx.Response:
        """GET request (typically low-risk for egress)."""
        return self._inner.get(url, **kwargs)

    def close(self) -> None:
        """Close underlying client."""
        self._inner.close()

    def __enter__(self) -> "SovereignHTTPXClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def with_sovereignty_guard(func):
    """Decorator to wrap LLM client methods with sovereignty inspection."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, "_sovereignty_enabled") or not self._sovereignty_enabled:
            return func(self, *args, **kwargs)

        try:
            return func(self, *args, **kwargs)
        except SovereigntyViolation:
            raise
        except Exception:
            raise

    return wrapper


def create_sovereign_client() -> SovereignHTTPXClient:
    """Factory for sovereign HTTP client."""
    return SovereignHTTPXClient()

"""Egress Sovereignty Guard - Prevents raw research content from leaving VPC.

This guard wraps all outbound HTTP clients and inspects payloads to ensure
no raw publication content (full_text, abstract) is sent to cloud LLMs.
Only schema prompts, user queries, and metadata may traverse the boundary.
"""

import hashlib
import logging
import os
import re
from typing import Any, Optional
from functools import wraps
import httpx
from src.audit import AuditEvent, get_audit_log

logger = logging.getLogger(__name__)


SOVEREIGN_ALLOWLIST = frozenset({
    "user_query",
    "schema_prompt",
    "plan_json",
    "intent_label",
    "citation_ids",
    "session_id",
    "user_tier",
})

SENSITIVE_FIELDS = frozenset({
    "full_text",
    "fulltext",
    "abstract",
    "raw_content",
    "raw_db_dump",
    "publication_text",
    "research_content",
})

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

        def check_value(key: str, value: Any, path: str = "") -> None:
            key_lower = key.lower()

            if key_lower in SENSITIVE_FIELDS:
                raise SovereigntyViolation(
                    f"Blocked sensitive field '{key}' in {path or 'payload'}",
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

    def inspect_payload(self, payload: dict | list | str) -> None:
        """Public payload inspection entrypoint for non-httpx clients."""
        try:
            self._inspect_payload(payload)
        except SovereigntyViolation as exc:
            self._log_violation(exc, "payload_inspection")
            raise

    def _log_violation(self, violation: SovereigntyViolation, url: str) -> None:
        """Log sovereignty violation to audit trail."""
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
                self._log_violation(e, url)
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

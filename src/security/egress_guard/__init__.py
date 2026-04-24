"""
Schema Allowlist — Protocol #39: Egress Firewall for Cloud LLM

Inspect every outbound LLM payload against the allowlist.
Only allowlisted schema fragments (specific table/column names marked safe)
may appear in prompts. Raw schema, non-allowlisted columns, sensitive metadata —
BLOCKED with audit log.

Files:
  - src/security/egress_allowlist.yaml    (declarative allowlist)
  - src/security/egress_guard/            (enforcement package)
"""

from __future__ import annotations

import re
import logging
import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

ALLOWLIST_PATH = Path(__file__).resolve().parents[1] / "security" / "egress_allowlist.yaml"


@dataclass
class EgressViolation:
    """Record of a blocked or sanitized egress attempt."""
    timestamp: str
    blocked_text: str
    reason: str
    field: str  # which field was blocked (system_prompt, user_prompt, etc.)
    severity: str  # "block" (rejected) or "sanitize" (removed unsafe content)


class EgressGuard:
    """Egress firewall — validates LLM prompts against schema allowlist.

    Usage:
        guard = EgressGuard()
        safe_prompt = guard.filter_prompt(system="...", user="...", provider="openai")
        # raises EgressViolation if blocked
    """

    def __init__(self, allowlist_path: Path | None = None):
        self._path = allowlist_path or ALLOWLIST_PATH
        self._allowlist: dict | None = None
        self._violations: list[EgressViolation] = []
        self._load_allowlist()

    def _load_allowlist(self) -> None:
        if not self._path.exists():
            logger.warning("Egress allowlist not found at %s — egress guard in permissive mode", self._path)
            self._allowlist = {"tables": {}, "columns": {}, "patterns_block": []}
            return

        with open(self._path) as f:
            self._allowlist = yaml.safe_load(f)

        logger.info("Egress allowlist loaded from %s", self._path)

    def reload(self) -> None:
        """Reload allowlist from disk (for runtime updates)."""
        self._load_allowlist()

    @property
    def allowed_tables(self) -> set[str]:
        return set(self._allowlist.get("tables", {}))

    @property
    def allowed_columns(self) -> set[str]:
        return set(self._allowlist.get("columns", {}))

    @property
    def blocked_patterns(self) -> list[str]:
        explicit = self._allowlist.get("patterns_block", [])
        content_block = self._allowlist.get("blocked_content", [])
        return explicit + content_block

    def check(self, text: str, field_name: str = "prompt") -> list[EgressViolation]:
        """Check text for any violations. Returns list of violations (empty = clean)."""
        violations = []

        for pattern in self.blocked_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                violation = EgressViolation(
                    timestamp=self._now(),
                    blocked_text=pattern[:100],
                    reason=f"blocked_pattern: {pattern[:50]}",
                    field=field_name,
                    severity="block",
                )
                violations.append(violation)
                self._violations.append(violation)

    def filter_prompt(
        self,
        system: str,
        user: str,
        provider: str,
        raise_on_violation: bool = True,
    ) -> tuple[str, str, list[EgressViolation]]:
        """Filter system and user prompts through allowlist.

        Returns (filtered_system, filtered_user, violations).
        If raise_on_violation=True and violations have severity=block, raises ValueError.
        """
        all_text = f"{system}\n{user}"
        raw_violations = self.check(all_text, "system+user")

        filtered_system = system
        filtered_user = user
        blocked = [v for v in raw_violations if v.severity == "block"]
        sanitized = [v for v in raw_violations if v.severity == "sanitize"]

        if blocked:
            logger.warning("Egress violation blocked: %s", blocked[0].reason)
            if raise_on_violation:
                raise EgressSecurityError(f"Egress violation: {blocked[0].reason}")
            for v in blocked:
                self._violations.append(v)

        for v in sanitized:
            self._violations.append(v)

        if sanitized:
            filtered_system = self._sanitize_text(system, sanitized)
            filtered_user = self._sanitize_text(user, sanitized)

        return filtered_system, filtered_user, raw_violations

    def filter_system_prompt(
        self,
        system_prompt: str,
        raise_on_violation: bool = True,
    ) -> tuple[str, list[EgressViolation]]:
        """Filter a system prompt against the allowlist. Returns (filtered, violations)."""
        violations = self.check(system_prompt, "system_prompt")
        blocked = [v for v in violations if v.severity == "block"]

        if blocked:
            logger.warning("System prompt egress violation: %s", blocked[0].reason)
            for v in blocked:
                self._violations.append(v)
            if raise_on_violation:
                raise EgressSecurityError(f"System prompt egress violation: {blocked[0].reason}")

        for v in violations:
            if v not in self._violations:
                self._violations.append(v)

        filtered = self._sanitize_text(system_prompt, violations)
        return filtered, violations

    def filter_schema_for_llm(self, schema_snippet: str) -> str:
        """Filter schema metadata to only include allowlisted table/column names.

        This is the primary egress filter — ensures LLM only sees approved
        schema elements, preventing schema fingerprinting attacks.
        """
        if not self.allowed_tables:
            return schema_snippet

        lines = schema_snippet.split("\n")
        passed = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                passed.append(line)
                continue

            table_match = re.search(r'(?:table|view|relation):\s+[`"]?(\w+)[`"]?', stripped, re.IGNORECASE)
            if table_match:
                tbl = table_match.group(1).lower()
                if tbl not in self.allowed_tables and tbl != "*":
                    continue

            col_match = re.search(r'(?:column|field):\s+[`"]?(\w+)[`"]?', stripped, re.IGNORECASE)
            if col_match:
                col = col_match.group(1).lower()
                if col not in self.allowed_columns and col not in ("*", "id", "created_at", "updated_at"):
                    continue

            passed.append(line)

        return "\n".join(passed)

    def _sanitize_text(self, text: str, violations: list[EgressViolation]) -> str:
        """Remove or mask content flagged by violations."""
        sanitized = text
        for v in violations:
            if v.severity == "sanitize" and v.blocked_text:
                sanitized = sanitized.replace(v.blocked_text, "[REDACTED]")
        return sanitized

    def _now(self) -> str:
        from datetime import datetime, UTC
        return datetime.now(UTC).isoformat()

    def get_violations(self, since: Optional[str] = None) -> list[EgressViolation]:
        """Get all violations, optionally filtered by timestamp."""
        if since is None:
            return list(self._violations)
        return [v for v in self._violations if v.timestamp >= since]

    def get_violation_count(self) -> int:
        return len(self._violations)

    def clear_violations(self) -> None:
        self._violations.clear()


class EgressSecurityError(Exception):
    """Raised when an egress violation is detected and raise_on_violation=True."""
    pass


class _EgressGuardSingleton:
    _instance: EgressGuard | None = None


def get_egress_guard() -> EgressGuard:
    """Get singleton EgressGuard instance."""
    if _EgressGuardSingleton._instance is None:
        _EgressGuardSingleton._instance = EgressGuard()
    return _EgressGuardSingleton._instance


def reset_egress_guard() -> None:
    """Reset singleton — for testing only."""
    _EgressGuardSingleton._instance = None
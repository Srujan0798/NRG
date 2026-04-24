"""
RBAC Policy Engine — YAML-driven persona-based access control.

Loads policies from rbac_policies.yaml (or in-memory dict for testing).
Each policy defines column visibility, PII masking rules, output format,
data scope, max results, and endpoint access.

Usage:
    engine = RBACPolicyEngine()
    policy = engine.get_policy(tier=2)            # by tier level
    policy = engine.get_policy(persona="industry")  # by persona name
    columns = engine.get_visible_columns(policy, "researchers")
    should_mask = engine.should_mask_field(policy, "email")
    format = engine.get_output_format(policy)
"""

from __future__ import annotations

import fnmatch
import hashlib
import logging
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

CURRENT_DIR = Path(__file__).parent
DEFAULT_POLICY_PATH = CURRENT_DIR / "rbac_policies.yaml"

_TIER_TO_PERSONA = {
    1: "researcher",
    2: "government",
    3: "industry",
}


@dataclass(frozen=True)
class RBACPolicy:
    """Immutable policy for a single persona."""

    name: str
    tier: int
    description: str
    column_visibility: dict[str, list[str]]
    pii_masking: dict[str, Any]
    output_format: str  # "full" | "aggregated" | "anonymized"
    data_scope: str  # "all" | "own_and_public" | "anonymized" | "institution_only" | "open_access"
    max_results: int
    debug_access: bool
    allowed_endpoints: list[str]
    allowed_tables: list[str]
    export_allowed: bool
    read_only: bool
    # Optional flags
    requires_institution_scope: bool = False
    requires_open_access_filter: bool = False
    is_active: bool = True  # For soft-delete in admin API
    # Temporal visibility window (e.g., {from: "2026-Q1", to: "2026-Q4"})
    visibility_window: Optional[dict] = None  # {"from": "YYYY-QN", "to": "YYYY-QN"} or {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"}

    def get_visible_columns(self, table: str) -> list[str]:
        """Return list of column patterns visible for a table, or [] if table hidden."""
        cols = self.column_visibility.get(table, [])
        if "*" in cols:
            return ["*"]
        return cols

    def is_table_visible(self, table: str) -> bool:
        """Check if table has any visible columns."""
        cols = self.column_visibility.get(table, [])
        return len(cols) > 0

    def should_mask_field(self, field_name: str) -> bool:
        """Check if a field should be masked based on PII rules."""
        if self.pii_masking.get("mode") == "none":
            return False
        hide_fields = self.pii_masking.get("hide_fields", [])
        return field_name.lower() in [f.lower() for f in hide_fields]

    def is_within_window(self, reference_date: Optional[str] = None) -> bool:
        """Check if reference_date falls within the visibility_window.

        If no window is defined, always returns True (no temporal restriction).
        Supports ISO date strings (YYYY-MM-DD) and quarter format (YYYY-QN).
        Quarter end dates use the last day of the quarter month:
        Q1→Mar 31, Q2→Jun 30, Q3→Sep 30, Q4→Dec 31.
        """
        if self.visibility_window is None:
            return True

        from datetime import datetime

        def parse_quarter(s: str) -> datetime:
            year, quarter = s.upper().split("-Q")
            start_month = (int(quarter) - 1) * 3 + 1
            start = datetime(int(year), start_month, 1)
            end_month = start_month + 2
            if end_month > 12:
                end_month = 12
            import calendar
            last_day = calendar.monthrange(int(year), end_month)[1]
            return start, datetime(int(year), end_month, last_day)

        def parse_date(s: str) -> datetime:
            if "Q" in s.upper():
                _, end_dt = parse_quarter(s)
                return end_dt
            return datetime.strptime(s, "%Y-%m-%d")

        ref = reference_date or datetime.now().isoformat()
        try:
            if "Q" in ref.upper():
                _, ref_dt = parse_quarter(ref)
            else:
                ref_dt = datetime.strptime(ref[:10], "%Y-%m-%d")
        except ValueError:
            return True

        from_str = self.visibility_window.get("from")
        to_str = self.visibility_window.get("to")

        if from_str:
            try:
                if "Q" in from_str.upper():
                    start_dt, _ = parse_quarter(from_str)
                else:
                    start_dt = datetime.strptime(from_str[:10], "%Y-%m-%d")
                if ref_dt < start_dt:
                    return False
            except ValueError:
                pass

        if to_str:
            try:
                end_dt = parse_date(to_str)
                if ref_dt > end_dt:
                    return False
            except ValueError:
                pass

        return True


class PolicyCache:
    """Thread-safe in-memory cache for parsed RBAC policies."""

    def __init__(self) -> None:
        self._cache: dict[str, RBACPolicy] = {}
        self._lock = threading.RLock()
        self._file_mtime: float | None = None
        self._policy_path: Path | None = None

    def get(self, key: str) -> RBACPolicy | None:
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, policy: RBACPolicy) -> None:
        with self._lock:
            self._cache[key] = policy

    def set_file_mtime(self, mtime: float) -> None:
        with self._lock:
            self._file_mtime = mtime

    def get_file_mtime(self) -> float | None:
        with self._lock:
            return self._file_mtime

    def invalidate(self) -> None:
        with self._lock:
            self._cache.clear()
            self._file_mtime = None

    def get_policy_names(self) -> list[str]:
        with self._lock:
            return list(self._cache.keys())


class RBACPolicyEngine:
    """
    YAML-driven RBAC policy engine.

    Supports:
    - Loading policies from rbac_policies.yaml
    - Lookup by tier level (1/2/3) or persona name
    - Column visibility per table
    - PII masking rules
    - Output format selection
    - Endpoint access control
    - Runtime cache invalidation
    - Hot-reload on YAML file change
    """

    def __init__(
        self,
        policy_path: Path | str | None = None,
        policies: dict[str, Any] | None = None,
    ):
        """
        Initialize the policy engine.

        Args:
            policy_path: Path to rbac_policies.yaml. Defaults to bundled default.
            policies: Optional dict of policies (for testing or runtime injection).
                      If provided, policy_path is ignored.
        """
        self._policy_path = Path(policy_path) if policy_path else DEFAULT_POLICY_PATH
        self._policies_override = policies  # For testing/runtime injection
        self._cache = PolicyCache()
        self._known_key_ids: set[str] = set()  # For JWT kid tracking

        if self._policies_override:
            self._load_from_dict(self._policies_override)
        else:
            self._load_from_yaml()

    # ─────────────────────────────────────────────────────────────
    # Loading
    # ─────────────────────────────────────────────────────────────

    def _load_from_yaml(self) -> None:
        """Load and parse policies from YAML file."""
        if not self._policy_path.exists():
            raise FileNotFoundError(f"RBAC policy file not found: {self._policy_path}")

        try:
            with open(self._policy_path, "r") as f:
                raw = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {self._policy_path}: {e}") from e

        personas = raw.get("personas", {})
        if not personas:
            raise ValueError(f"No 'personas' section found in {self._policy_path}")

        self._load_from_dict(personas)
        self._cache.set_file_mtime(os.path.getmtime(str(self._policy_path)))

    def _load_from_dict(self, personas: dict[str, Any]) -> None:
        """Parse and cache policies from a dict of persona definitions."""
        for name, spec in personas.items():
            policy = self._parse_policy(name, spec)
            self._cache.set(name, policy)
            self._cache.set(f"tier:{policy.tier}", policy)

    def _parse_policy(self, name: str, spec: dict[str, Any]) -> RBACPolicy:
        """Parse a single persona spec into an RBACPolicy."""
        column_visibility: dict[str, list[str]] = {}
        for table, cols in spec.get("column_visibility", {}).items():
            if isinstance(cols, list):
                column_visibility[table] = cols
            else:
                column_visibility[table] = [cols] if cols else []

        pii_masking = spec.get("pii_masking", {"mode": "none", "hide_fields": []})

        return RBACPolicy(
            name=name,
            tier=spec.get("tier", 1),
            description=spec.get("description", ""),
            column_visibility=column_visibility,
            pii_masking=pii_masking,
            output_format=spec.get("output_format", "full"),
            data_scope=spec.get("data_scope", "all"),
            max_results=spec.get("max_results", 500),
            debug_access=spec.get("debug_access", False),
            allowed_endpoints=spec.get("allowed_endpoints", ["*"]),
            allowed_tables=spec.get("allowed_tables", ["*"]),
            export_allowed=spec.get("export_allowed", True),
            read_only=spec.get("read_only", False),
            requires_institution_scope=spec.get("requires_institution_scope", False),
            requires_open_access_filter=spec.get("requires_open_access_filter", False),
            is_active=spec.get("is_active", True),
            visibility_window=spec.get("visibility_window"),
        )

    # ─────────────────────────────────────────────────────────────
    # Public API — Policy lookup
    # ─────────────────────────────────────────────────────────────

    def get_policy(
        self,
        tier: int | None = None,
        persona: str | None = None,
    ) -> RBACPolicy:
        """
        Get policy by tier level or persona name.

        Supports backward-compatible tier lookup (integer 1/2/3 maps to
        researcher/government/industry) and direct persona name lookup.

        Args:
            tier: Integer tier level (1, 2, or 3)
            persona: Persona name string (e.g., "industry", "peer_reviewer")

        Returns:
            RBACPolicy for the matched persona

        Raises:
            KeyError: If no policy matches the lookup key
        """
        if persona:
            policy = self._cache.get(persona)
            if policy and policy.is_active:
                return policy
            raise KeyError(f"No active persona found: {persona}")

        if tier is not None:
            # Backward compat: integer tier 1/2/3
            if isinstance(tier, int) and 1 <= tier <= 3:
                mapped = _TIER_TO_PERSONA.get(tier)
                if mapped:
                    policy = self._cache.get(mapped)
                    if policy and policy.is_active:
                        return policy
                    raise KeyError(f"Persona for tier {tier} not found in policy cache")
            # Direct tier lookup (e.g., tier 4 for new persona)
            policy = self._cache.get(f"tier:{tier}")
            if policy and policy.is_active:
                return policy
            raise KeyError(f"No active persona found for tier: {tier}")

        raise ValueError("Must provide either tier= or persona=")

    def list_personas(self, include_inactive: bool = False) -> list[RBACPolicy]:
        """Return all registered persona policies."""
        names = self._cache.get_policy_names()
        personas = []
        seen: set[str] = set()
        for name in names:
            if name.startswith("tier:"):
                continue
            if name in seen:
                continue
            seen.add(name)
            policy = self._cache.get(name)
            if policy and (include_inactive or policy.is_active):
                personas.append(policy)
        return personas

    def persona_exists(self, persona: str) -> bool:
        """Check if a persona name is registered."""
        policy = self._cache.get(persona)
        return policy is not None

    def tier_for_persona(self, persona: str) -> int | None:
        """Return the tier level for a named persona."""
        policy = self._cache.get(persona)
        return policy.tier if policy else None

    # ─────────────────────────────────────────────────────────────
    # Column visibility
    # ─────────────────────────────────────────────────────────────

    def get_visible_columns(self, policy: RBACPolicy, table: str) -> list[str]:
        """
        Get list of visible column patterns for a table under a policy.

        Returns ["*"] if all columns are visible.
        Returns [] if the table is fully hidden for this policy.
        """
        return policy.get_visible_columns(table)

    def filter_row_by_policy(
        self, policy: RBACPolicy, table: str, row: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Filter a database row according to column visibility + PII masking.

        - Columns not in the visibility list are dropped.
        - Fields in pii_masking.hide_fields are replaced with None/redacted.
        """
        visible = self.get_visible_columns(policy, table)

        if not visible:
            return {}

        if "*" in visible:
            # All columns visible — apply PII masking only
            return self._apply_pii_mask(policy, row)

        filtered = {}
        for col, value in row.items():
            if col in visible:
                if policy.should_mask_field(col):
                    filtered[col] = self._mask_value(col, value, policy)
                else:
                    filtered[col] = value
        return filtered

    def _apply_pii_mask(self, policy: RBACPolicy, row: dict[str, Any]) -> dict[str, Any]:
        """Apply PII masking to all fields in a row."""
        if policy.pii_masking.get("mode") == "none":
            return dict(row)

        masked = {}
        for col, value in row.items():
            if policy.should_mask_field(col):
                masked[col] = self._mask_value(col, value, policy)
            else:
                masked[col] = value
        return masked

    def _mask_value(self, field: str, value: Any, policy: RBACPolicy) -> Any:
        """Mask a single field value according to PII mode."""
        mode = policy.pii_masking.get("mode", "none")
        if mode == "none":
            return value
        if mode in ("aggregate", "full", "anonymized"):
            field_lower = field.lower()
            if any(k in field_lower for k in ("email", "phone", "aadhaar", "pan", "dob", "date_of_birth")):
                return "[REDACTED]"
            if value is None:
                return None
            return value
        return value

    # ─────────────────────────────────────────────────────────────
    # Endpoint access
    # ─────────────────────────────────────────────────────────────

    def is_endpoint_allowed(self, policy: RBACPolicy, endpoint: str) -> bool:
        """Check if a policy allows access to a given endpoint path."""
        allowed = policy.allowed_endpoints
        if "*" in allowed:
            return True
        return any(fnmatch.fnmatch(endpoint, pattern) for pattern in allowed)

    def is_table_allowed(self, policy: RBACPolicy, table: str) -> bool:
        """Check if a policy allows access to a given table."""
        allowed = policy.allowed_tables
        if "*" in allowed:
            return True
        return any(fnmatch.fnmatch(table, pattern) for pattern in allowed)

    # ─────────────────────────────────────────────────────────────
    # Output format helpers
    # ─────────────────────────────────────────────────────────────

    def get_output_format(self, policy: RBACPolicy) -> str:
        """Return the output format for a policy: 'full', 'aggregated', or 'anonymized'."""
        return policy.output_format

    def should_aggregate(self, policy: RBACPolicy) -> bool:
        """Returns True if output should be aggregated (government/industry personas)."""
        return policy.output_format in ("aggregated", "anonymized")

    def should_anonymize(self, policy: RBACPolicy) -> bool:
        """Returns True if output should be fully anonymized."""
        return policy.output_format == "anonymized"

    # ─────────────────────────────────────────────────────────────
    # Runtime policy management (Phase 3)
    # ─────────────────────────────────────────────────────────────

    def reload(self) -> None:
        """Hot-reload policies from YAML file if file has changed."""
        if not self._policy_path or not self._policy_path.exists():
            return

        current_mtime = os.path.getmtime(str(self._policy_path))
        cached_mtime = self._cache.get_file_mtime()

        if cached_mtime is None or current_mtime > cached_mtime:
            logger.info("RBAC policy file changed — reloading")
            self._cache.invalidate()
            self._load_from_yaml()

    def add_or_update_policy(self, persona: str, spec: dict[str, Any]) -> RBACPolicy:
        """
        Add a new persona or update an existing one (runtime, no YAML change).

        Returns the parsed RBACPolicy.
        """
        policy = self._parse_policy(persona, spec)
        self._cache.set(persona, policy)
        self._cache.set(f"tier:{policy.tier}", policy)
        return policy

    def deactivate_persona(self, persona: str) -> bool:
        """
        Soft-delete a persona (sets is_active=False).

        Built-in personas (researcher, government, industry) cannot be deactivated.
        Already-inactive personas return False.

        Returns True if deactivation succeeded, False if persona not found,
        is a protected built-in, or already inactive.
        """
        policy = self._cache.get(persona)
        if not policy:
            return False

        if not policy.is_active:
            return False

        if policy.tier in (1, 2, 3) and persona in ("researcher", "government", "industry"):
            return False

        deactivated = self._parse_policy(persona, {**policy.__dict__, "is_active": False})
        self._cache.set(persona, deactivated)
        return True

    # ─────────────────────────────────────────────────────────────
    # Backward compatibility helpers
    # ─────────────────────────────────────────────────────────────

    def resolve_tier_or_persona(self, claims: dict[str, Any]) -> RBACPolicy:
        """
        Resolve RBACPolicy from JWT claims dict.

        Supports both:
        - Integer tier claim: {"tier": 2}
        - String persona claim: {"persona": "peer_reviewer"}
        - Both: persona name takes precedence if is_active
        """
        persona = claims.get("persona")
        if persona and self.persona_exists(persona):
            return self.get_policy(persona=persona)

        tier = claims.get("tier")
        if tier is not None:
            try:
                return self.get_policy(tier=int(tier))
            except (KeyError, ValueError):
                pass

        # Default to researcher (tier 1) if nothing resolves
        return self.get_policy(tier=1)

    def get_policy_hash(self) -> str:
        """Return SHA256 hash of all active policy names + tiers — for JWT kid tracking."""
        parts = []
        for policy in self.list_personas():
            parts.append(f"{policy.name}:{policy.tier}:{policy.is_active}")
        parts.sort()
        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


# ─────────────────────────────────────────────────────────────────
# Singleton instance — loaded once, reused across all imports
# ─────────────────────────────────────────────────────────────────

_policy_engine: RBACPolicyEngine | None = None
_policy_engine_lock = threading.Lock()


def get_policy_engine(
    policy_path: Path | str | None = None,
    policies: dict[str, Any] | None = None,
) -> RBACPolicyEngine:
    """
    Get the global RBACPolicyEngine singleton.

    Thread-safe. Subsequent calls with the same arguments return the
    cached instance; different arguments return a new instance.
    """
    global _policy_engine
    with _policy_engine_lock:
        if _policy_engine is None:
            _policy_engine = RBACPolicyEngine(policy_path=policy_path, policies=policies)
        return _policy_engine


def reset_policy_engine() -> None:
    """Reset the global singleton — for testing only."""
    global _policy_engine
    with _policy_engine_lock:
        _policy_engine = None

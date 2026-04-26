"""Policy-backed tier response filtering for API payloads."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any


@dataclass(frozen=True)
class TierResponseFilterReport:
    warnings: list[str] = field(default_factory=list)
    strip_events: list[dict[str, Any]] = field(default_factory=list)
    shape_columns: list[str] = field(default_factory=list)


_DROP = object()
K_ANONYMITY_THRESHOLD = 5
INDIVIDUAL_IDENTIFIER_KEYS = frozenset(
    {
        "researcher_id",
        "author_id",
        "person_id",
        "faculty_id",
        "student_id",
        "employee_id",
        "pi_id",
        "investigator_id",
    }
)


def filter_query_response_for_tier(
    payload: dict[str, Any],
    tier: int,
) -> tuple[dict[str, Any], list[str]]:
    """Compatibility wrapper used by older call sites."""
    filtered, report = filter_response_payload_for_tier(payload, tier=tier)
    return filtered, report.warnings


def apply_k_anonymity_threshold(
    payload: Any,
    tier: int,
    threshold: int = K_ANONYMITY_THRESHOLD,
) -> tuple[Any, list[dict[str, Any]]]:
    """Block lower-tier individual cohorts below the configured privacy threshold."""
    tier_int = int(tier)
    if tier_int <= 1 or not isinstance(payload, dict):
        return payload, []

    rows = payload.get("sql_results")
    if not isinstance(rows, list) or not rows:
        return payload, []

    identifiers = _collect_individual_identifiers(rows)
    if not identifiers or len(identifiers) >= int(threshold):
        return payload, []

    blocked = dict(payload)
    blocked["status"] = "blocked"
    blocked["blocked"] = True
    blocked["response"] = (
        f"Result set too small -- privacy threshold not met. "
        f"Broaden the query to at least {int(threshold)} individuals."
    )
    blocked["sql_query"] = None
    blocked["sql_queries"] = []
    blocked["sql_results"] = []
    blocked["citations"] = []
    blocked["retrieval_sources"] = []

    existing_warnings = blocked.get("warnings", [])
    if not isinstance(existing_warnings, list):
        existing_warnings = [existing_warnings]
    blocked["warnings"] = existing_warnings + [
        f"k_anonymity_block: cohort below k={int(threshold)} threshold"
    ]

    return blocked, [
        {
            "reason": f"k_anonymity_block:tier{tier_int}:small_cohort",
            "tier": tier_int,
            "field": "sql_results",
            "key": "sql_results",
            "path": "$.sql_results",
            "action": "block",
            "cohort_size": len(identifiers),
            "threshold": int(threshold),
        }
    ]


def filter_response_payload_for_tier(
    payload: Any,
    tier: int,
) -> tuple[Any, TierResponseFilterReport]:
    """Return a response payload that satisfies the configured tier policy."""
    policy = _load_response_policy()
    context = _FilterContext(policy=policy, tier=int(tier))
    context.name_replacements = _collect_name_replacements(payload, context)
    filtered = _filter_value(payload, context, path="$", parent=None, key=None)
    if filtered is _DROP:
        filtered = None

    report = TierResponseFilterReport(
        warnings=_build_warnings(context.strip_events),
        strip_events=context.strip_events,
        shape_columns=collect_shape_columns(filtered),
    )
    return filtered, report


def find_tier_response_violations(payload: Any, tier: int) -> list[dict[str, Any]]:
    """Return remaining response-boundary violations after filtering."""
    policy = _load_response_policy()
    context = _FilterContext(policy=policy, tier=int(tier))
    violations: list[dict[str, Any]] = []
    _collect_violations(payload, context, "$", None, None, violations)
    return violations


def required_tier_response_fields() -> set[str]:
    """Return configured response-boundary field classes."""
    policy = _load_response_policy()
    return set(policy.get("field_classes", {}).keys())


def collect_shape_columns(payload: Any) -> list[str]:
    columns: set[str] = set()

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for item_key, item_value in value.items():
                columns.add(str(item_key))
                child_path = f"{path}.{item_key}" if path else str(item_key)
                walk(item_value, child_path)
        elif isinstance(value, list):
            for item in value:
                walk(item, path)

    walk(payload, "")
    return sorted(columns)


def _collect_individual_identifiers(rows: list[Any]) -> set[str]:
    identifiers: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        for item_key, item_value in row.items():
            normalized = _normalize_key(item_key)
            if normalized in INDIVIDUAL_IDENTIFIER_KEYS and item_value not in (None, ""):
                identifiers.add(str(item_value))
                break
    return identifiers


@dataclass
class _FilterContext:
    policy: dict[str, Any]
    tier: int
    strip_events: list[dict[str, Any]] = field(default_factory=list)
    name_replacements: dict[str, str] = field(default_factory=dict)
    value_patterns: dict[str, re.Pattern[str]] = field(init=False)

    def __post_init__(self) -> None:
        self.value_patterns = _compiled_value_patterns(self.policy)

    @property
    def reason_prefix(self) -> str:
        return str(self.policy.get("audit_reason_prefix", "pii_strip"))

    @property
    def name_template(self) -> str:
        return str(self.policy.get("tier3_name_template", "Researcher_{id}"))


@lru_cache(maxsize=1)
def _load_response_policy() -> dict[str, Any]:
    from src.auth.rbac import get_policy_engine

    policy = get_policy_engine().get_tier_response_columns()
    if not policy:
        raise RuntimeError("tier_response_columns missing from RBAC policy")
    return policy


def _filter_value(
    value: Any,
    context: _FilterContext,
    path: str,
    parent: dict[str, Any] | None,
    key: str | None,
) -> Any:
    field_class = _field_class_for_key(key, parent, context.policy)
    if field_class and not _field_allowed(field_class, context.tier, context.policy):
        if _should_transform_name(field_class, context.tier, context.policy):
            context.strip_events.append(_event(context, field_class, path, key, "transform"))
            return _researcher_label(parent or {}, value, context)
        if _empty_on_strip(field_class, context.policy):
            context.strip_events.append(_event(context, field_class, path, key, "empty"))
            return _empty_like(value)
        context.strip_events.append(_event(context, field_class, path, key, "drop"))
        return _DROP

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for item_key, item_value in value.items():
            item_path = f"{path}.{item_key}" if path != "$" else f"$.{item_key}"
            filtered = _filter_value(item_value, context, item_path, value, item_key)
            if filtered is not _DROP:
                result[item_key] = filtered
        return result

    if isinstance(value, list):
        result = []
        for index, item in enumerate(value):
            filtered = _filter_value(item, context, f"{path}[{index}]", parent, key)
            if filtered is not _DROP:
                result.append(filtered)
        return result

    if isinstance(value, str):
        return _redact_disallowed_values(value, context, path, key)

    return value


def _collect_violations(
    value: Any,
    context: _FilterContext,
    path: str,
    parent: dict[str, Any] | None,
    key: str | None,
    violations: list[dict[str, Any]],
) -> None:
    field_class = _field_class_for_key(key, parent, context.policy)
    if field_class and not _field_allowed(field_class, context.tier, context.policy):
        transformed_name = (
            _should_transform_name(field_class, context.tier, context.policy)
            and isinstance(value, str)
            and value.startswith("Researcher_")
        )
        emptied_value = _empty_on_strip(field_class, context.policy) and value in (None, [], {})
        if not transformed_name and not emptied_value:
            violations.append(_event(context, field_class, path, key, "violation"))

    if isinstance(value, dict):
        for item_key, item_value in value.items():
            item_path = f"{path}.{item_key}" if path != "$" else f"$.{item_key}"
            _collect_violations(item_value, context, item_path, value, item_key, violations)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _collect_violations(item, context, f"{path}[{index}]", parent, key, violations)
    elif isinstance(value, str):
        for field_name, pattern in context.value_patterns.items():
            if not _field_allowed(field_name, context.tier, context.policy) and pattern.search(value):
                violations.append(_event(context, field_name, path, key, "value_violation"))


def _field_class_for_key(
    key: str | None,
    parent: dict[str, Any] | None,
    policy: dict[str, Any],
) -> str | None:
    if not key:
        return None

    normalized = _normalize_key(key)
    graph_types = {_normalize_key(item) for item in policy.get("graph_person_node_types", [])}
    if normalized == "label" and parent and _normalize_key(str(parent.get("type", ""))) in graph_types:
        return "personal_name"
    if normalized == "name" and parent and any(
        marker in parent for marker in ("researcher_id", "author_id", "person_id")
    ):
        return "personal_name"

    for field_name, spec in policy.get("field_classes", {}).items():
        aliases = [_normalize_key(field_name)]
        aliases.extend(_normalize_key(alias) for alias in spec.get("aliases", []))
        match_mode = spec.get("match", "exact")
        if match_mode == "contains":
            if any(alias and alias in normalized for alias in aliases):
                return field_name
        elif normalized in aliases:
            return field_name
    return None


def _field_allowed(field_name: str, tier: int, policy: dict[str, Any]) -> bool:
    spec = policy.get("field_classes", {}).get(field_name, {})
    allowed_tiers = {int(item) for item in spec.get("allowed_tiers", [1, 2, 3])}
    return int(tier) in allowed_tiers


def _should_transform_name(field_name: str, tier: int, policy: dict[str, Any]) -> bool:
    spec = policy.get("field_classes", {}).get(field_name, {})
    return int(tier) == 3 and bool(spec.get("tier3_transform"))


def _empty_on_strip(field_name: str, policy: dict[str, Any]) -> bool:
    spec = policy.get("field_classes", {}).get(field_name, {})
    return bool(spec.get("empty_on_strip"))


def _empty_like(value: Any) -> Any:
    if isinstance(value, list):
        return []
    if isinstance(value, dict):
        return {}
    return None


def _researcher_label(parent: dict[str, Any], value: Any, context: _FilterContext) -> str:
    identifier = (
        parent.get("researcher_id")
        or parent.get("author_id")
        or parent.get("person_id")
        or parent.get("id")
    )
    if identifier is None:
        identifier = hashlib.sha256(str(value).encode()).hexdigest()[:8]
    safe_id = re.sub(r"[^A-Za-z0-9_-]+", "_", str(identifier)).strip("_")
    if not safe_id:
        digest = hashlib.sha256(str(value).encode()).hexdigest()[:8]
        safe_id = digest
    if any(
        pattern.search(safe_id)
        for field_name, pattern in context.value_patterns.items()
        if not _field_allowed(field_name, context.tier, context.policy)
    ):
        safe_id = hashlib.sha256(str(identifier).encode()).hexdigest()[:8]
    return context.name_template.replace("{id}", safe_id)


def _collect_name_replacements(payload: Any, context: _FilterContext) -> dict[str, str]:
    if context.tier != 3:
        return {}

    replacements: dict[str, str] = {}

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for item_key, item_value in value.items():
                if (
                    isinstance(item_value, str)
                    and _field_class_for_key(item_key, value, context.policy) == "personal_name"
                    and not item_value.startswith("Researcher_")
                ):
                    replacements[item_value] = _researcher_label(value, item_value, context)
                walk(item_value)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    return replacements


def _redact_disallowed_values(
    value: str,
    context: _FilterContext,
    path: str,
    key: str | None,
) -> str:
    redacted = value
    if context.name_replacements:
        for original, replacement in sorted(
            context.name_replacements.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            if original in redacted:
                redacted = redacted.replace(original, replacement)
                context.strip_events.append(
                    _event(context, "personal_name", path, key, "redact_text_name")
                )

    for field_name, pattern in context.value_patterns.items():
        if _field_allowed(field_name, context.tier, context.policy):
            continue
        if pattern.search(redacted):
            redacted = pattern.sub("[REDACTED]", redacted)
            context.strip_events.append(_event(context, field_name, path, key, "redact_value"))
    return redacted


def _compiled_value_patterns(policy: dict[str, Any]) -> dict[str, re.Pattern[str]]:
    compiled: dict[str, re.Pattern[str]] = {}
    for field_name, pattern in policy.get("value_patterns", {}).items():
        compiled[field_name] = re.compile(pattern)
    return compiled


def _event(
    context: _FilterContext,
    field_name: str,
    path: str,
    key: str | None,
    action: str,
) -> dict[str, Any]:
    return {
        "reason": f"{context.reason_prefix}:tier{context.tier}:{field_name}",
        "tier": context.tier,
        "field": field_name,
        "key": key,
        "path": path,
        "action": action,
    }


def _build_warnings(events: list[dict[str, Any]]) -> list[str]:
    if not events:
        return []
    reasons = sorted({event["reason"] for event in events})
    return [f"Response policy applied: {reason}" for reason in reasons]


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")

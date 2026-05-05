"""Policy-backed tier response filtering for API payloads."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, cast

JSONDict = dict[str, Any]
JSONRows = list[JSONDict]


def _empty_str_list() -> list[str]:
    return []


def _empty_event_list() -> JSONRows:
    return []


def _empty_replacement_map() -> dict[str, str]:
    return {}


@dataclass(frozen=True)
class TierResponseFilterReport:
    warnings: list[str] = field(default_factory=_empty_str_list)
    strip_events: JSONRows = field(default_factory=_empty_event_list)
    shape_columns: list[str] = field(default_factory=_empty_str_list)


@dataclass(frozen=True)
class _PolicyFieldIndex:
    graph_person_node_types: frozenset[str]
    field_entries: tuple[tuple[str, str, tuple[str, ...]], ...]


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
_policy_field_index_cache: dict[int, tuple[JSONDict, _PolicyFieldIndex]] = {}
_policy_value_pattern_cache: dict[int, tuple[JSONDict, dict[str, re.Pattern[str]]]] = {}


def filter_query_response_for_tier(
    payload: JSONDict,
    tier: int,
) -> tuple[JSONDict, list[str]]:
    """Compatibility wrapper used by older call sites."""
    filtered, report = filter_response_payload_for_tier(payload, tier=tier)
    return filtered, report.warnings


def apply_k_anonymity_threshold(
    payload: Any,
    tier: int,
    threshold: int = K_ANONYMITY_THRESHOLD,
) -> tuple[Any, JSONRows]:
    """Block lower-tier individual cohorts below the configured privacy threshold."""
    tier_int = int(tier)
    if tier_int <= 1 or not isinstance(payload, dict):
        return payload, []

    payload_dict = cast(JSONDict, payload)
    rows_raw = payload_dict.get("sql_results")
    if not isinstance(rows_raw, list) or not rows_raw:
        return payload_dict, []
    rows = cast(list[Any], rows_raw)

    identifiers = _collect_individual_identifiers(rows)
    if not identifiers or len(identifiers) >= int(threshold):
        return payload_dict, []

    blocked = dict(payload_dict)
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
        existing_warning_items = [str(existing_warnings)]
    else:
        existing_warning_items = [str(item) for item in cast(list[Any], existing_warnings)]
    blocked["warnings"] = existing_warning_items + [
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
    if _tier_allows_all_fields(int(tier), policy):
        return payload, TierResponseFilterReport(shape_columns=collect_shape_columns(payload))

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


def find_tier_response_violations(payload: Any, tier: int) -> JSONRows:
    """Return remaining response-boundary violations after filtering."""
    policy = _load_response_policy()
    context = _FilterContext(policy=policy, tier=int(tier))
    violations: JSONRows = []
    _collect_violations(payload, context, "$", None, None, violations)
    return violations


def required_tier_response_fields() -> set[str]:
    """Return configured response-boundary field classes."""
    policy = _load_response_policy()
    return set(policy.get("field_classes", {}).keys())


def warm_response_policy_cache() -> None:
    """Load and index response filtering policy before latency-sensitive paths."""
    policy = _load_response_policy()
    _policy_field_index(policy)
    _compiled_value_patterns(policy)


def collect_shape_columns(payload: Any) -> list[str]:
    columns: set[str] = set()

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            value_dict = cast(JSONDict, value)
            for item_key, item_value in value_dict.items():
                columns.add(str(item_key))
                child_path = f"{path}.{item_key}" if path else str(item_key)
                walk(item_value, child_path)
        elif isinstance(value, list):
            for item in cast(list[Any], value):
                walk(item, path)

    walk(payload, "")
    return sorted(columns)


def _collect_individual_identifiers(rows: list[Any]) -> set[str]:
    identifiers: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_dict = cast(JSONDict, row)
        for item_key, item_value in row_dict.items():
            normalized = _normalize_key(item_key)
            if normalized in INDIVIDUAL_IDENTIFIER_KEYS and item_value not in (None, ""):
                identifiers.add(str(item_value))
                break
    return identifiers


@dataclass
class _FilterContext:
    policy: JSONDict
    tier: int
    strip_events: JSONRows = field(default_factory=_empty_event_list)
    name_replacements: dict[str, str] = field(default_factory=_empty_replacement_map)
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
def _load_response_policy() -> JSONDict:
    from src.auth.rbac import get_policy_engine

    policy = get_policy_engine().get_tier_response_columns()
    if not policy:
        raise RuntimeError("tier_response_columns missing from RBAC policy")
    return policy


def _filter_value(
    value: Any,
    context: _FilterContext,
    path: str,
    parent: JSONDict | None,
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
        value_dict = cast(JSONDict, value)
        result: JSONDict = {}
        for item_key, item_value in value_dict.items():
            item_path = f"{path}.{item_key}" if path != "$" else f"$.{item_key}"
            filtered = _filter_value(item_value, context, item_path, value_dict, item_key)
            if filtered is not _DROP:
                result[item_key] = filtered
        return result

    if isinstance(value, list):
        list_result: list[Any] = []
        for index, item in enumerate(cast(list[Any], value)):
            filtered = _filter_value(item, context, f"{path}[{index}]", parent, key)
            if filtered is not _DROP:
                list_result.append(filtered)
        return list_result

    if isinstance(value, str):
        return _redact_disallowed_values(value, context, path, key)

    return value


def _collect_violations(
    value: Any,
    context: _FilterContext,
    path: str,
    parent: JSONDict | None,
    key: str | None,
    violations: JSONRows,
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
        value_dict = cast(JSONDict, value)
        for item_key, item_value in value_dict.items():
            item_path = f"{path}.{item_key}" if path != "$" else f"$.{item_key}"
            _collect_violations(item_value, context, item_path, value_dict, item_key, violations)
    elif isinstance(value, list):
        for index, item in enumerate(cast(list[Any], value)):
            _collect_violations(item, context, f"{path}[{index}]", parent, key, violations)
    elif isinstance(value, str):
        for field_name, pattern in context.value_patterns.items():
            if not _field_allowed(field_name, context.tier, context.policy) and pattern.search(value):
                violations.append(_event(context, field_name, path, key, "value_violation"))


def _field_class_for_key(
    key: str | None,
    parent: JSONDict | None,
    policy: JSONDict,
) -> str | None:
    if not key:
        return None

    normalized = _normalize_key(key)
    policy_index = _policy_field_index(policy)
    if (
        normalized == "label"
        and parent
        and _normalize_key(str(parent.get("type", ""))) in policy_index.graph_person_node_types
    ):
        return "personal_name"
    if normalized == "name" and parent and any(
        marker in parent for marker in ("researcher_id", "author_id", "person_id")
    ):
        return "personal_name"

    for field_name, match_mode, aliases in policy_index.field_entries:
        if match_mode == "contains":
            if any(alias and alias in normalized for alias in aliases):
                return field_name
        elif normalized in aliases:
            return field_name
    return None


def _policy_field_index(policy: JSONDict) -> _PolicyFieldIndex:
    cache_key = id(policy)
    cached = _policy_field_index_cache.get(cache_key)
    if cached is not None and cached[0] is policy:
        return cached[1]

    graph_types = frozenset(
        _normalize_key(str(item)) for item in cast(list[Any], policy.get("graph_person_node_types", []))
    )
    field_entries: list[tuple[str, str, tuple[str, ...]]] = []
    field_classes = cast(dict[str, JSONDict], policy.get("field_classes", {}))
    for field_name, spec in field_classes.items():
        aliases = [_normalize_key(field_name)]
        aliases.extend(_normalize_key(alias) for alias in spec.get("aliases", []))
        field_entries.append((field_name, str(spec.get("match", "exact")), tuple(aliases)))

    index = _PolicyFieldIndex(
        graph_person_node_types=graph_types,
        field_entries=tuple(field_entries),
    )
    _policy_field_index_cache[cache_key] = (policy, index)
    return index


def _field_allowed(field_name: str, tier: int, policy: JSONDict) -> bool:
    field_classes = cast(dict[str, JSONDict], policy.get("field_classes", {}))
    spec = field_classes.get(field_name, {})
    allowed_tiers = {int(item) for item in cast(list[Any], spec.get("allowed_tiers", [1, 2, 3]))}
    return int(tier) in allowed_tiers


def _tier_allows_all_fields(tier: int, policy: JSONDict) -> bool:
    field_classes = cast(dict[str, JSONDict], policy.get("field_classes", {}))
    return all(
        int(tier) in {int(item) for item in cast(list[Any], spec.get("allowed_tiers", [1, 2, 3]))}
        for spec in field_classes.values()
    )


def _should_transform_name(field_name: str, tier: int, policy: JSONDict) -> bool:
    field_classes = cast(dict[str, JSONDict], policy.get("field_classes", {}))
    spec = field_classes.get(field_name, {})
    return int(tier) == 3 and bool(spec.get("tier3_transform"))


def _empty_on_strip(field_name: str, policy: JSONDict) -> bool:
    field_classes = cast(dict[str, JSONDict], policy.get("field_classes", {}))
    spec = field_classes.get(field_name, {})
    return bool(spec.get("empty_on_strip"))


def _empty_like(value: Any) -> Any:
    if isinstance(value, list):
        return []
    if isinstance(value, dict):
        return {}
    return None


def _researcher_label(parent: JSONDict, value: Any, context: _FilterContext) -> str:
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
    if context.tier >= 3:
        safe_id = hashlib.sha256(str(identifier).encode()).hexdigest()[:8]
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
            value_dict = cast(JSONDict, value)
            for item_key, item_value in value_dict.items():
                if (
                    isinstance(item_value, str)
                    and _field_class_for_key(item_key, value_dict, context.policy) == "personal_name"
                    and not item_value.startswith("Researcher_")
                ):
                    replacements[item_value] = _researcher_label(value_dict, item_value, context)
                walk(item_value)
        elif isinstance(value, list):
            for item in cast(list[Any], value):
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


def _compiled_value_patterns(policy: JSONDict) -> dict[str, re.Pattern[str]]:
    cache_key = id(policy)
    cached = _policy_value_pattern_cache.get(cache_key)
    if cached is not None and cached[0] is policy:
        return cached[1]

    compiled: dict[str, re.Pattern[str]] = {}
    value_patterns = cast(dict[str, str], policy.get("value_patterns", {}))
    for field_name, pattern in value_patterns.items():
        compiled[field_name] = re.compile(pattern)
    _policy_value_pattern_cache[cache_key] = (policy, compiled)
    return compiled


def _event(
    context: _FilterContext,
    field_name: str,
    path: str,
    key: str | None,
    action: str,
) -> JSONDict:
    return {
        "reason": f"{context.reason_prefix}:tier{context.tier}:{field_name}",
        "tier": context.tier,
        "field": field_name,
        "key": key,
        "path": path,
        "action": action,
    }


def _build_warnings(events: JSONRows) -> list[str]:
    if not events:
        return []
    reasons = sorted({event["reason"] for event in events})
    return [f"Response policy applied: {reason}" for reason in reasons]


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")

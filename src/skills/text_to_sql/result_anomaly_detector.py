"""Detect low-confidence Text-to-SQL result shapes before synthesis."""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from src.skills.text_to_sql.cardinality_estimator import estimate_cardinality


@dataclass(frozen=True)
class ResultAnomalySignal:
    """One detector finding with enough context for audit evidence."""

    name: str
    severity: str
    message: str
    evidence: dict[str, Any]


@dataclass(frozen=True)
class ResultAnomalyReport:
    """Detector output consumed by the verifier and API response."""

    detected: bool
    signals: list[ResultAnomalySignal]
    answer_confidence: str
    confidence_score: float
    needs_clarification: bool
    clarification_question: str | None
    corrective_hints: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["signal_names"] = [signal.name for signal in self.signals]
        return payload


TEXT_NUMERIC_COLUMNS = (
    "total_credit_score",
    "total_citations",
    "recent_citations",
    "fcr",
    "rcr",
)

ANALYTICAL_TERMS = (
    "average",
    "breakdown",
    "compare",
    "correlation",
    "cost",
    "disparity",
    "funding",
    "grant",
    "median",
    "patent",
    "progression",
    "ratio",
    "trend",
)


def detect_result_anomalies(
    question: str,
    sql: str,
    result: Mapping[str, Any] | list[Mapping[str, Any]],
    *,
    expected_min_rows: int | None = None,
) -> ResultAnomalyReport:
    """Return anomaly signals for plausible-but-risky SQL outputs."""
    rows = _normalise_rows(result)
    row_count = _normalise_row_count(result, rows)
    sql_lower = " ".join(sql.lower().split())
    question_lower = " ".join(question.lower().split())
    expectation = estimate_cardinality(question, sql)
    minimum = expected_min_rows if expected_min_rows is not None else expectation.min_rows

    signals: list[ResultAnomalySignal] = []

    _detect_row_count_zero(signals, question_lower, sql_lower, row_count, expectation.reason)
    _detect_row_count_one_without_limit(signals, sql_lower, row_count, minimum, expectation.expects_multiple)
    _detect_null_ratio_high(signals, rows)
    _detect_aggregate_collapse(signals, question_lower, sql_lower, row_count, expectation.expects_multiple)
    _detect_division_by_zero_signal(signals, question_lower, sql_lower, rows)
    _detect_text_cast_silent_failure(signals, question_lower, sql_lower, rows)
    _detect_entity_resolution_join_risk(signals, sql_lower)
    _detect_metric_too_perfect(signals, question_lower, rows)

    score = _score(signals)
    confidence = _confidence_label(score, signals)
    needs_clarification = confidence == "low_clarify" or any(signal.severity == "high" for signal in signals)
    question_text = _clarification_question(signals) if needs_clarification else None

    return ResultAnomalyReport(
        detected=bool(signals),
        signals=signals,
        answer_confidence=confidence,
        confidence_score=score,
        needs_clarification=needs_clarification,
        clarification_question=question_text,
        corrective_hints=_corrective_hints(signals),
    )


def _normalise_rows(result: Mapping[str, Any] | list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(result, list):
        return [dict(row) for row in result if isinstance(row, Mapping)]

    for key in ("results", "rows", "data"):
        value = result.get(key)
        if isinstance(value, list):
            return [dict(row) for row in value if isinstance(row, Mapping)]
    return []


def _normalise_row_count(result: Mapping[str, Any] | list[Mapping[str, Any]], rows: list[dict[str, Any]]) -> int:
    if isinstance(result, Mapping) and result.get("row_count") is not None:
        try:
            return int(result["row_count"])
        except (TypeError, ValueError):
            return len(rows)
    return len(rows)


def _detect_row_count_zero(
    signals: list[ResultAnomalySignal],
    question_lower: str,
    sql_lower: str,
    row_count: int,
    expectation_reason: str,
) -> None:
    if row_count != 0:
        return
    has_join = " join " in f" {sql_lower} "
    if not (has_join or expectation_reason in {"explicit_top_n", "grouped_sql", "plural_question_intent"}):
        return
    signals.append(
        ResultAnomalySignal(
            name="row_count_zero",
            severity="high",
            message="Query returned zero rows for an analytical or joined question.",
            evidence={"row_count": row_count, "expectation_reason": expectation_reason},
        )
    )


def _detect_row_count_one_without_limit(
    signals: list[ResultAnomalySignal],
    sql_lower: str,
    row_count: int,
    minimum: int,
    expects_multiple: bool,
) -> None:
    if row_count != 1 or not expects_multiple or minimum <= 1:
        return
    if re.search(r"\blimit\s+1\b", sql_lower):
        return
    if _is_single_aggregate(sql_lower):
        return
    signals.append(
        ResultAnomalySignal(
            name="row_count_one_with_limit_missing",
            severity="medium",
            message="Only one row returned where the question asks for multiple entities.",
            evidence={"row_count": row_count, "expected_min_rows": minimum},
        )
    )


def _detect_null_ratio_high(signals: list[ResultAnomalySignal], rows: list[dict[str, Any]]) -> None:
    if len(rows) < 2:
        return

    values_by_column: dict[str, list[Any]] = {}
    for row in rows:
        for key, value in row.items():
            if _is_identifier_column(key):
                continue
            values_by_column.setdefault(str(key), []).append(value)

    worst_column = None
    worst_ratio = 0.0
    for column, values in values_by_column.items():
        if len(values) < 2:
            continue
        sparse = sum(value in (None, "", "NULL") for value in values)
        ratio = sparse / len(values)
        if ratio > worst_ratio:
            worst_column = column
            worst_ratio = ratio

    if worst_column and worst_ratio >= 0.6:
        signals.append(
            ResultAnomalySignal(
                name="null_ratio_high",
                severity="medium",
                message="A metric column is mostly NULL, which often means the join key is wrong.",
                evidence={"column": worst_column, "null_ratio": round(worst_ratio, 3)},
            )
        )


def _detect_aggregate_collapse(
    signals: list[ResultAnomalySignal],
    question_lower: str,
    sql_lower: str,
    row_count: int,
    expects_multiple: bool,
) -> None:
    if row_count > 1:
        return
    grouped = "group by" in sql_lower or "partition by" in sql_lower
    comparative = any(term in question_lower for term in ("by ", "per ", "across", "broken down", "compare", "trend"))
    if not ((grouped and expects_multiple) or comparative):
        return
    signals.append(
        ResultAnomalySignal(
            name="aggregate_collapse",
            severity="medium",
            message="Grouped or comparative query collapsed to a single bucket.",
            evidence={"row_count": row_count, "grouped_sql": grouped, "comparative_question": comparative},
        )
    )


def _detect_division_by_zero_signal(
    signals: list[ResultAnomalySignal],
    question_lower: str,
    sql_lower: str,
    rows: list[dict[str, Any]],
) -> None:
    ratio_intent = any(term in question_lower for term in ("ratio", "percent", "percentage", "cost per", "per patent"))
    if "/" in sql_lower and "nullif" not in sql_lower:
        signals.append(
            ResultAnomalySignal(
                name="division_by_zero_signal",
                severity="high",
                message="Division query does not guard the denominator with NULLIF.",
                evidence={"sql_contains_division": True, "has_nullif": False},
            )
        )
        return

    if not ratio_intent or not rows:
        return

    ratio_values = [
        value
        for row in rows
        for key, value in row.items()
        if any(term in str(key).lower() for term in ("ratio", "percent", "pct", "cost_per", "rate"))
    ]
    if ratio_values and all(_is_bad_numeric(value) for value in ratio_values):
        signals.append(
            ResultAnomalySignal(
                name="division_by_zero_signal",
                severity="high",
                message="Ratio-like output is NULL, zero, or non-finite across all rows.",
                evidence={"metric_count": len(ratio_values)},
            )
        )


def _detect_text_cast_silent_failure(
    signals: list[ResultAnomalySignal],
    question_lower: str,
    sql_lower: str,
    rows: list[dict[str, Any]],
) -> None:
    risky_column = next((column for column in TEXT_NUMERIC_COLUMNS if column in sql_lower), None)
    if risky_column and _uses_direct_numeric_cast(sql_lower, risky_column):
        signals.append(
            ResultAnomalySignal(
                name="text_cast_silent_failure",
                severity="high",
                message="Text-typed numeric field is cast directly without safe parsing.",
                evidence={"column": risky_column},
            )
        )
        return

    if not rows or not any(term in question_lower for term in ("citation", "credit", "average", "median")):
        return
    metric_values = [
        value
        for row in rows
        for key, value in row.items()
        if any(term in str(key).lower() for term in ("citation", "credit", "average", "median"))
    ]
    if len(metric_values) >= 2 and all(value in (0, 0.0, None, "", "0") for value in metric_values):
        signals.append(
            ResultAnomalySignal(
                name="text_cast_silent_failure",
                severity="medium",
                message="Text-derived metric values are uniformly empty or zero.",
                evidence={"metric_count": len(metric_values)},
            )
        )


def _detect_entity_resolution_join_risk(signals: list[ResultAnomalySignal], sql_lower: str) -> None:
    direct_join = bool(
        re.search(r"\binstitute\s*=\s*[\w.]*applicants\b", sql_lower)
        or re.search(r"\bapplicants\s*=\s*[\w.]*institute\b", sql_lower)
    )
    normalized = "applicants" in sql_lower and (
        "lower(" in sql_lower or "upper(" in sql_lower or "trim(" in sql_lower or " like " in sql_lower
    )
    if direct_join and not normalized:
        signals.append(
            ResultAnomalySignal(
                name="entity_resolution_join_risk",
                severity="high",
                message="Applicant-to-institute join is not normalized.",
                evidence={"join_key": "applicants/institute"},
            )
        )


def _detect_metric_too_perfect(
    signals: list[ResultAnomalySignal],
    question_lower: str,
    rows: list[dict[str, Any]],
) -> None:
    if len(rows) < 3 or not any(term in question_lower for term in ("ratio", "percent", "rate", "conversion", "progression")):
        return
    metric_values = [
        float(value)
        for row in rows
        for key, value in row.items()
        if any(term in str(key).lower() for term in ("ratio", "percent", "pct", "rate"))
        and _is_number(value)
    ]
    if len(metric_values) >= 3 and len(set(metric_values)) == 1 and metric_values[0] in (0.0, 100.0):
        signals.append(
            ResultAnomalySignal(
                name="metric_too_perfect",
                severity="low",
                message="Every ratio bucket has the same boundary value.",
                evidence={"value": metric_values[0], "metric_count": len(metric_values)},
            )
        )


def _score(signals: Iterable[ResultAnomalySignal]) -> float:
    score = 0.95
    for signal in signals:
        if signal.severity == "high":
            score -= 0.35
        elif signal.severity == "medium":
            score -= 0.2
        else:
            score -= 0.1
    return round(max(0.05, score), 2)


def _confidence_label(score: float, signals: list[ResultAnomalySignal]) -> str:
    if any(signal.severity == "high" for signal in signals) or score < 0.55:
        return "low_clarify"
    if signals or score < 0.8:
        return "partial"
    return "high"


def _clarification_question(signals: list[ResultAnomalySignal]) -> str:
    names = {signal.name for signal in signals}
    if "entity_resolution_join_risk" in names or "row_count_zero" in names:
        return (
            "The SQL result is low confidence because applicant, institute, or other entity matching may be too strict. "
            "Should I broaden matching with normalized institute names, or ask for a narrower filter?"
        )
    if "text_cast_silent_failure" in names:
        return (
            "The SQL result is low confidence because a text metric needs safe parsing. "
            "Should I exclude non-numeric rows and return the parsed aggregate?"
        )
    if "division_by_zero_signal" in names:
        return (
            "The SQL result is low confidence because a denominator may be zero. "
            "Should I return only rows with a valid denominator and flag excluded rows?"
        )
    return "The SQL result is low confidence. Should I revise the query or ask for a tighter constraint?"


def _corrective_hints(signals: list[ResultAnomalySignal]) -> list[str]:
    hints: list[str] = []
    names = {signal.name for signal in signals}
    if "row_count_zero" in names or "entity_resolution_join_risk" in names:
        hints.append("Normalize entity joins with upper(trim(...)) or curated institute mappings.")
    if "row_count_one_with_limit_missing" in names or "aggregate_collapse" in names:
        hints.append("Preserve the requested grouping dimensions and avoid accidental global aggregation.")
    if "null_ratio_high" in names:
        hints.append("Check join keys before synthesis when joined metrics are mostly NULL.")
    if "division_by_zero_signal" in names:
        hints.append("Wrap denominators in NULLIF and report excluded denominator-zero rows.")
    if "text_cast_silent_failure" in names:
        hints.append("Parse text metrics with regex/SPLIT_PART/NULLIF before numeric aggregation.")
    if "metric_too_perfect" in names:
        hints.append("Re-check boundary-valued percentages before presenting the result as final.")
    return hints


def _uses_direct_numeric_cast(sql_lower: str, column: str) -> bool:
    column_pattern = re.escape(column)
    direct_cast = re.search(
        rf"cast\s*\(\s*(?:[\w]+\.)?\"?{column_pattern}\"?\s+as\s+(?:integer|int|numeric|decimal|double)",
        sql_lower,
    )
    direct_suffix = re.search(rf"(?:[\w]+\.)?\"?{column_pattern}\"?\s*::\s*(?:integer|int|numeric|decimal|double)", sql_lower)
    safe_parse = "split_part" in sql_lower or "~" in sql_lower or "regexp" in sql_lower
    return bool((direct_cast or direct_suffix) and not safe_parse)


def _is_single_aggregate(sql_lower: str) -> bool:
    return "group by" not in sql_lower and bool(re.search(r"\b(count|sum|avg|min|max)\s*\(", sql_lower))


def _is_identifier_column(column: str) -> bool:
    lowered = str(column).lower()
    return any(term in lowered for term in ("id", "name", "institute", "year", "state", "title"))


def _is_bad_numeric(value: Any) -> bool:
    if value in (None, "", 0, 0.0, "0"):
        return True
    if isinstance(value, float):
        return math.isnan(value) or math.isinf(value)
    return False


def _is_number(value: Any) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True

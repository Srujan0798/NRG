"""Heuristic cardinality expectations for Text-to-SQL result verification."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CardinalityExpectation:
    """Expected result cardinality derived from the user question and SQL shape."""

    min_rows: int
    expects_multiple: bool
    reason: str


PLURAL_INTENT_TERMS = (
    "all",
    "across",
    "breakdown",
    "compare",
    "comparison",
    "each",
    "institutes",
    "list",
    "network",
    "per ",
    "progression",
    "rank",
    "researchers",
    "show",
    "stars",
    "top",
    "trend",
    "which",
)

SINGULAR_INTENT_TERMS = (
    "how many",
    "count",
    "total ",
    "ratio of",
    "percentage of",
)


def estimate_cardinality(question: str, sql: str) -> CardinalityExpectation:
    """Estimate whether a result should contain several rows.

    This is deliberately conservative. It only raises the expected lower bound
    when the question or SQL asks for a grouped, ranked, or comparative result.
    """
    question_lower = " ".join(question.lower().split())
    sql_lower = " ".join(sql.lower().split())

    explicit_top = re.search(r"\btop\s+(\d+)\b", question_lower)
    if explicit_top:
        return CardinalityExpectation(
            min_rows=max(2, int(explicit_top.group(1))),
            expects_multiple=True,
            reason="explicit_top_n",
        )

    if "group by" in sql_lower or "partition by" in sql_lower:
        return CardinalityExpectation(
            min_rows=2,
            expects_multiple=True,
            reason="grouped_sql",
        )

    if any(term in question_lower for term in PLURAL_INTENT_TERMS):
        return CardinalityExpectation(
            min_rows=2,
            expects_multiple=True,
            reason="plural_question_intent",
        )

    if any(term in question_lower for term in SINGULAR_INTENT_TERMS):
        return CardinalityExpectation(
            min_rows=1,
            expects_multiple=False,
            reason="singular_aggregate_intent",
        )

    return CardinalityExpectation(min_rows=1, expects_multiple=False, reason="default")

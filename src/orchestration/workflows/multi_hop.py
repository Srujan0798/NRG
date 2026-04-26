"""Compatibility guard for the removed multi-hop workflow module.

The production multi-hop path runs through the LangGraph DAG:

- :mod:`src.orchestration.nodes.planner`
- :mod:`src.orchestration.nodes.executor`
- :mod:`src.orchestration.graph`

This module remains only so legacy imports fail with an explicit, actionable
error. It must never synthesize results because fabricated data can hide broken
query paths in production validation.
"""

from __future__ import annotations

import logging
import warnings
from typing import Any

warnings.warn(
    "src.orchestration.workflows.multi_hop is deprecated. "
    "Use src.orchestration.graph.NRGWorkflow instead.",
    DeprecationWarning,
    stacklevel=2,
)

logger = logging.getLogger(__name__)

_DISABLED_MESSAGE = (
    "MultiHopWorkflow compatibility shim is disabled. "
    "Use src.orchestration.graph.NRGWorkflow, which routes through the planner "
    "and executor nodes."
)


class MultiHopWorkflow:
    """Legacy import guard that fails closed for removed workflow entry points."""

    def __init__(self) -> None:
        logger.warning(_DISABLED_MESSAGE)

    def execute_multi_hop_query(
        self,
        sql_query: str,
        vector_query: str,
        graph_query: str | None = None,
    ) -> dict[str, Any]:
        """Reject legacy direct execution to prevent fabricated workflow output."""
        logger.error(_DISABLED_MESSAGE)
        raise RuntimeError(_DISABLED_MESSAGE)

    def validate_multi_hop_results(self, results: list[dict[str, Any]]) -> bool:
        """Reject legacy validation to avoid approving unverified results."""
        logger.error(_DISABLED_MESSAGE)
        raise RuntimeError(_DISABLED_MESSAGE)


def main() -> None:
    """Raise the same closed-path error when called as a script."""
    raise RuntimeError(_DISABLED_MESSAGE)


if __name__ == "__main__":
    main()

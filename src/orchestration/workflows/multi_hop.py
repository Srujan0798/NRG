#!/usr/bin/env python3
"""
DEPRECATED — Multi-Hop Workflow Stub

.. deprecated::
    This module is a deprecated 94-line placeholder stub.
    The real multi-hop DAG planner is implemented in:

    - :mod:`src.orchestration.nodes.planner` (``_heuristic_decompose``, ``_build_dag``)
    - :mod:`src.orchestration.nodes.executor` (``_execute_dag``)

    All 28 multi-hop planner tests import from ``planner`` and ``executor``,
    not from this module.

    This stub is kept to prevent import errors in any code that references it,
    but it returns dummy/placeholder results and must not be used in production.

:Status: DEPRECATED — remove after Protocol #32 (Two-Brain Orchestrator) lands
:Evidence: tests/benchmarks/test_dhairya_regression.py, tests/orchestration/test_multi_hop_planner.py
"""

import warnings
import logging
import sys
from typing import Dict, Any, List, Optional

warnings.warn(
    "src.orchestration.workflows.multi_hop is DEPRECATED. "
    "Import from src.orchestration.nodes.planner or "
    "src.orchestration.nodes.executor instead. "
    "This stub will be removed after Protocol #32.",
    DeprecationWarning,
    stacklevel=2,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("multi_hop.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class MultiHopWorkflow:
    """Deprecated placeholder — use planner.py and executor.py instead."""

    def __init__(self):
        self.workflow_steps = []
        self.current_step = 0

    def execute_multi_hop_query(
        self, sql_query: str, vector_query: str, graph_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Deprecated placeholder — returns dummy results."""
        logger.warning("MultiHopWorkflow.execute_multi_hop_query is a deprecated stub")
        return {
            "sql_query": sql_query,
            "vector_query": vector_query,
            "graph_query": graph_query,
            "results": [{"type": "deprecated_stub", "data": "Use planner.py + executor.py"}],
            "execution_time": 0.0,
            "confidence_score": 0.0,
        }

    def validate_multi_hop_results(self, results: List[Dict[str, Any]]) -> bool:
        """Deprecated placeholder — always returns True."""
        logger.warning("MultiHopWorkflow.validate_multi_hop_results is a deprecated stub")
        return True


def main():
    logger.info("Deprecated multi_hop.py stub — import from planner.py or executor.py")


if __name__ == "__main__":
    main()

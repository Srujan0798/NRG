# Experimental Orchestration Nodes

These planner/verifier nodes came from parallel agent work and are preserved for Phase 2+ evaluation.

They are not imported by the Phase 1 LangGraph workflow. Before promotion into `src/orchestration/nodes/`, they need:

- Cloud-boundary review against `Core_Idea_Clean.md`.
- Egress/minimization enforcement for every cloud LLM call.
- Tests for planner JSON repair, citation verification, and fallback behavior.
- Integration into `src/orchestration/graph.py`.

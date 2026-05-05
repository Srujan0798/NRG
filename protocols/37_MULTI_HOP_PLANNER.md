> **DEPRECATED FORMAT:** This protocol uses the old ═══ format.
> **Current format:** Use `.claude/assignment_template.md` for all new assignments.

═══════════════════════════════════════════════════════════════
TASK: #37 — THE MULTI-HOP PLANNER
AGENT: backend / ml
PRIORITY: P0-blocker (Quality Bar Constraint #3)
═══════════════════════════════════════════════════════════════

FILES:
  - src/orchestration/nodes/planner.py (replace flat decomposition with DAG)
  - src/orchestration/state.py (add sub_query_dag: {nodes, edges} type)
  - src/orchestration/nodes/executor.py (topological execution of DAG)
  - src/orchestration/graph.py (pass parent results as context to children)
  - tests/orchestration/test_multi_hop_planner.py (NEW — 10 fixtures)
  - tests/evals/multi_hop_queries.json (NEW — benchmark corpus)
  - .claude/QUALITY_BAR.md (Constraint #3 reference)

PROBLEM:
  Planner currently outputs a FLAT list of sub-queries with no dependencies. Complex queries
  like "Compare Gujarat and Karnataka's AI research output over 5 years and show the funding gap"
  need:
    - SubQ1: Gujarat AI publications 2021-2026 (independent)
    - SubQ2: Karnataka AI publications 2021-2026 (independent)
    - SubQ3: Gujarat funding 2021-2026 (depends on SubQ1 for researcher set)
    - SubQ4: Karnataka funding 2021-2026 (depends on SubQ2)
    - SubQ5: Compare outputs (depends on SubQ1, SubQ2)
    - SubQ6: Funding gap (depends on SubQ3, SubQ4)
  
  Current flat list can't express this. Executor runs all sub-queries in parallel without
  wait-for-parent semantics, passes no context between them. Result: wrong answers on
  multi-hop questions.

ACTION:
  Phase 1 — FORTIFY: DAG representation + planner output
    1a. Extend NRGState: add `sub_query_dag: {nodes: [{id, query, type, depends_on: [ids]}],
        entry_nodes: [ids], exit_nodes: [ids]}`.
    1b. Rewrite planner_node LLM prompt to output DAG structure (JSON). Provide 5 examples
        of multi-hop decomposition covering: comparison, gap analysis, time series, cross-domain,
        aggregated-then-filtered.
    1c. DAG validation: no cycles (use topological sort), all depends_on reference valid ids,
        entry_nodes have no dependencies, exit_nodes have no dependents.
  
  Phase 2 — ELEVATE: Topological execution with context passing
    2a. executor_node reads DAG, executes in topological order (Kahn's algorithm).
    2b. For each node: wait for all parents to complete, collect their results, pass as
        `parent_context` to SQL/RAG skill invocation.
    2c. Parallel execution where DAG allows (nodes with same depth level run concurrently
        via asyncio.gather).
    2d. Per-node timing recorded in state["node_timings"]["subq_<id>"].
    2e. Synthesizer receives ordered results with DAG metadata for coherent final answer.
  
  Phase 3 — IMMORTALIZE: Benchmark + regression gate
    3a. tests/evals/multi_hop_queries.json with 20+ real-world multi-hop queries and
        expected DAG shapes.
    3b. tests/orchestration/test_multi_hop_planner.py:
        - Planner produces valid DAG (passes validation) for each benchmark query
        - Executor runs nodes in correct topological order (trace assertion)
        - Context passing: child query includes parent result in context
        - Parallel execution: sibling nodes run concurrently (timing assertion)
    3c. Add to CI: multi-hop benchmark accuracy — 80%+ of queries produce correct DAG.
    3d. /api/metrics exposes multi_hop_stats: avg depth, avg fan-out, percentage multi-hop.

SKILLS TO USE:
  - /prompt-engineering-patterns — Few-shot DAG examples, structured output prompting
  - /python-backend — Topological sort, asyncio.gather patterns, DAG validation
  - /testing-strategy — Benchmark corpus design, DAG shape assertions
  - /statistical-analysis — Multi-hop query distribution analysis
  - /code-review-and-quality — Self-review

ACCEPTANCE CRITERIA:
  - [ ] NRGState has sub_query_dag field with strict schema
  - [ ] Planner outputs valid DAG for 20+ benchmark multi-hop queries
  - [ ] DAG validation catches cycles, broken refs, orphan nodes
  - [ ] Executor runs nodes in topological order with context passing
  - [ ] Sibling nodes execute concurrently (measured timing)
  - [ ] Test suite: 20+ multi-hop fixtures, 80%+ pass
  - [ ] Quality Bar Constraint #3 compliance score: 8+/10
  - [ ] Existing simple (1-hop) queries unchanged (regression check)

BEFORE COMMIT:
  - Run /pre-commit
  - Run the multi-hop benchmark: report accuracy %
  - Verify 1-hop queries still work (no regression)
  - Report node_timings shows concurrent execution

GURU ASSIGNMENT NOTE:
  Core_Idea_Clean.md §"The Core AI Challenge" explicitly names multi-hop reasoning as one
  of the 4 unsolved-in-production problems the system must handle. A researcher asking
  "Compare Gujarat and Karnataka's AI output over 5 years" is the CANONICAL NRG query —
  it's literally the example the professor gave. If the planner can't decompose this into
  a proper dependency graph, the whole retrieval pipeline is guessing. This is not a
  nice-to-have; it's the core intelligence contract. After this protocol, NRG can answer
  the questions that Google cannot — because Google gives you 10 links, and NRG gives you
  a synthesized answer built from 6 coordinated sub-queries.

AGENT INSTRUCTIONS (verbatim):
  - Read .agents/AGENTS.md, shishya_universal.md
  - Read every SKILL.md listed
  - Read .claude/QUALITY_BAR.md — this closes Constraint #3
  - Read Core_Idea_Clean.md §"The Core AI Challenge" — understand why multi-hop matters
  - Read current src/orchestration/nodes/planner.py to know what you're replacing
  - Fortify → Elevate → Immortalize
  - /pre-commit before committing

DEPENDS ON: #27 (Final Green — stable test baseline)
═══════════════════════════════════════════════════════════════

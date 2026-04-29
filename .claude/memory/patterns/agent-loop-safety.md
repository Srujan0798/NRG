---
name: Agent Loop Safety
description: Autonomous agent, planner, worker, tool-calling, and memory workflows must be bounded, observable, and selective
type: feedback
---

Autonomous agent workflows are allowed only when they are bounded, observable,
and easier to verify than a simpler single-agent path.

**Rule:**

1. Every agent loop, planner/executor cycle, retry path, and worker dispatcher
   must have an explicit iteration, retry, step, or budget limit.
2. Tool failures must be surfaced as observations with the tool name, input
   summary, error class, and recovery decision. Silent failures are bugs.
3. Tool access must stay focused. More than 5-7 tools means split the task or
   use a supervisor protocol.
4. Custom tools must define precise descriptions, required parameters, examples,
   output shape, and failure behavior.
5. Memory must be selective: persist decisions, bug patterns, evidence paths,
   and reusable rules; discard scratch context, duplicate prompt text, vague
   confidence notes, and routine post-task summaries.
6. Multi-agent orchestration needs a real boundary: independent subtasks,
   separate expertise, parallelism, or explicit review. Otherwise use one
   agent.
7. Do not run automatic self-improvement loops after every task. Add memory
   only when a durable rule was learned from founder feedback, repeated bug
   evidence, architectural/security decisions, or an accepted/rejected external
   skill merge.
8. Every memory entry must include trigger/source, rule learned, why it matters,
   and how future agents should apply it. Repo `.claude/memory/` is the source
   of truth; never create a separate `/memories`, `.memories`, `.learnings`, or
   `.improvements` tree.
9. Bug, error, and correction memories must include attempted task, observed
   failure or correction, evidence, root cause, fix applied, prevention rule,
   and regression or acceptance check.
10. Feature requests are not memory by default. Route them to backlog, spec,
   issue, or implementation plan only when they affect product scope. Command
   failures become memory only when reproducible, recurring, or operationally
   important.
11. When an agent misbehaves, debug iteration count, tool calls, memory
   availability, reasoning trace where visible, and each tool independently
   before changing architecture.

**Why:** Generic autonomous-agent prompts are too broad for NRG and trigger too
often. The useful part is not another skill; it is a small set of safety
constraints that prevents infinite loops, tool confusion, context bloat, and
untraceable worker behavior.

**How to apply:**

- Add these checks to any Guru task protocol that touches agent architecture,
  LangGraph planners, tool registries, memory, retries, worker dispatch, or
  AI-assisted execution.
- Agents must report their loop limits, tool failures, memory writes, and
  orchestration justification when those surfaces are touched.
- Memory writes must be visible as repo diffs, not implied by private logs.
- If the task does not need autonomy, keep it simple and do not introduce a
  new agent layer.

**Source:** MiniMax `ai-agents-architect` and `autonomous-improvement` prompts
reviewed 2026-04-29, plus MiniMax `self-improving-agent` reviewed 2026-04-29;
kept as workflow and memory safety rules, not as standalone broad skills. A
second MiniMax `self-improving-agent` variant with `.learnings` logs was
reviewed 2026-04-29 and narrowed to backlog/evidence routing rules only.

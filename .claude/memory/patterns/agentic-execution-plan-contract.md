---
name: Agentic Execution Plan Contract
description: Multi-task agentic work must use explicit task ids, dependencies, file ownership, test/verify commands, disjoint write scopes, review gates, and human approval for destructive actions
type: feedback
---

NRG already has focused planning, TDD, debugging, subagent, and finishing skills.
Do not install broad workflow bundles that duplicate them. Keep the useful part:
a concrete execution manifest for multi-agent or multi-task work.

**Rule:**

1. Any delegated or multi-task implementation must have a task plan before work
   starts.
2. Each task must include stable id, short name, dependencies, exact file
   ownership, acceptance criteria, test command, verify command, and relevant
   security/tier/data/migration impact.
3. Dependencies must form a DAG. Parallel tasks need disjoint write scopes or an
   explicit integration owner.
4. Behavior changes use TDD where appropriate: failing test, passing
   implementation, refactor with tests still green. If TDD is not appropriate,
   define the equivalent evidence gate before editing.
5. Review order is spec compliance first, then code quality/security. Do not
   polish code that does not meet the spec.
6. Automation scripts are not accepted just because they are generated. Prefer
   existing repo commands and skills. Scripts that merge, delete, discard,
   cleanup worktrees, or rewrite branches require explicit human confirmation.
7. Quality gates must report exact commands and outputs, not quality scores with
   skipped checks hidden as passes.

**Why:** Broad workflow packages look powerful but can import broken scripts,
duplicate existing skills, or hide unsafe branch operations. NRG needs precise,
auditable task ownership more than another automation framework.

**How to apply:**

- Master execution and acceptance gates should require plan ids, dependencies,
  files, test/verify commands, and review evidence.
- Subagent dispatch should never overlap writes unless an integration owner is
  assigned.
- Finishing work must use local `verification-before-completion` and
  `finishing-a-development-branch` rules, not imported destructive scripts.

**Source:** MiniMax `superpower-10x` reviewed 2026-04-29; kept as agentic
execution plan discipline, not as a standalone workflow bundle.

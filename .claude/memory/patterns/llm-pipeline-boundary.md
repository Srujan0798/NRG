---
name: LLM Pipeline Boundary
description: LLM-heavy NRG features must separate deterministic policy/calculation stages from model synthesis, with schema parsing, traceability, task-model fit checks, and cost awareness
type: feedback
---

NRG must use language models where they are strong and deterministic code where
failure would break correctness, privacy, or trust.

**Rule:**

1. Deterministic code owns auth, tier policy, PII policy, small-cohort checks,
   SQL validation, SQL execution, aggregation, sorting, counting, numeric
   calculations, export shaping, audit hashing, response filtering, and final
   JSON schema validation.
2. Model calls may own natural-language intent understanding, candidate query
   planning, classification, synthesis from verified rows, and clarification
   questions when the query or source chain is weak.
3. Exact counts, totals, percentages, rankings, filters, and calculations must
   come from SQL or deterministic code. Model prose may explain them but must
   not invent or recompute them.
4. Structure pipelines as discrete stages:
   `acquire -> prepare -> process -> parse -> verify -> render`.
   For NRG: `route -> plan -> retrieve/SQL -> parse -> validate/tier-filter ->
   synthesize/shape response`.
5. Each stage should be independently testable, idempotent where possible,
   observable, and cacheable only through tier-safe keys.
6. Structured model outputs must be schema-validated with constrained values.
   Parse failures, missing sections, malformed SQL, and invalid enums downgrade
   to retry, clarification, or safe failure.
7. Before adding a new model-heavy path, validate task-model fit with one
   representative manual example, define acceptable error rate, estimate
   token/runtime cost for high-volume paths, and identify deterministic
   fallbacks.
8. Default to a single pipeline. Add multi-agent architecture only when
   independent parallel context, context-window pressure, or benchmarked quality
   improvement justifies it.

**Why:** The answer engine becomes fragile when a model performs arithmetic,
security policy, or hidden state transitions. Separation makes failures visible:
raw data acquisition, prompt construction, model output, parser output,
validator decisions, and rendered response can each be inspected.

**How to apply:**

- Backend work touching Text-to-SQL, retrieval, synthesis, routing, exports, or
  agent orchestration must state which stages are deterministic and which use a
  model.
- Evidence should include enough stage trace to explain why an answer was
  accepted, downgraded, retried, or blocked.
- Cost/rate estimates are required before batch or high-volume model paths.

**Source:** MiniMax `project-development` reviewed 2026-04-29; kept as NRG LLM
pipeline boundary discipline, not as a broad project-development skill.

---
name: Analytical Answer Contract
description: Metric, trend, ranking, comparison, funnel, cohort, and anomaly answers must expose definition, baseline, uncertainty, caveat, and safe interpretation
type: feedback
---

NRG is an answer engine, not a chart factory. Analytical answers must be
decision-ready and defensible under inspection.

**Rule:**

1. Start with the decision question and short answer, then evidence. Do not lead
   with method unless the user asked for method.
2. For KPI or metric answers, expose the metric contract: entity, grain,
   numerator, denominator, filters/exclusions, time window, timezone when
   relevant, source of truth, and known caveat.
3. Every trend, ranking, or comparison needs a baseline. Period comparisons must
   use the same grain and timezone, or explicitly normalize unequal periods.
4. Percentages must show underlying counts. Never average percentages without
   recomputing from summed numerators and denominators.
5. State confidence as high, medium, or low with one concrete reason. If the
   data cannot support the claim, say unknown and name the missing evidence.
6. Segment obvious confounders before strong conclusions: institution type,
   time period, geography, domain, cohort, funding stage, or user tier when
   relevant.
7. Do not present observational correlation as causation. Use association
   language unless there is experimental or natural-experiment evidence.
8. Charts answer a question, not a metric inventory. Use table-only when rows are
   clearer than a visual.

**Why:** The fastest way to lose trust is a confident but analytically weak
answer: percentage without denominator, trend without baseline, KPI without
definition, or causal language from observational data.

**How to apply:**

- Main-flow acceptance should reject analytical answers that hide denominator,
  grain, timeframe, source, caveat, or confidence.
- Query synthesis should include metric definitions in source proof when the
  answer depends on a KPI.
- UI should show the short answer first, then evidence, confidence, caveat, and
  source proof.

**Source:** MiniMax `data-analysis` reviewed 2026-04-29; kept as NRG analytical
answer discipline, not as a standalone broad data skill.

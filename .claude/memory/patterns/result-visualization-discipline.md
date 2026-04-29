---
name: Result Visualization Discipline
description: Query-result visuals in NRG must explain the verified answer, match the data shape, and pass browser QA; standalone visual demos are out of scope
type: feedback
---

NRG does not need standalone interactive demos. It needs in-app query-result
visualizations that make verified answers easier to understand and audit.

**Rule:**

1. Visualize only when the visual clarifies the answer. If the data is best
   read as rows, keep the table primary.
2. Match the visual to the data shape:
   - time series -> line or area chart
   - ranked comparison -> bar chart
   - distribution -> histogram or box plot
   - relationship between two variables -> scatter plot with outliers visible
   - TRL/progression stages -> funnel or stage distribution
   - drop-off through ordered stages -> funnel with explicit time window
   - cohort retention -> cohort table or heatmap with cohort size shown
   - institution/researcher relationships -> network graph only if real edges
     exist
   - categorical composition -> stacked bar or small multiples
3. Every visual must have a single intended insight, labelled axes/legend,
   source/citation linkage, and a table fallback.
4. Bars start at zero by default. Show underlying counts next to percentages
   when denominators are small. Avoid dual-axis charts, truncated bar axes,
   many-slice pie charts, and cumulative-only charts that hide recent movement.
5. Interactions must inspect real dimensions: filters, hover details, zoom/pan,
   stage toggles, or time controls. No decorative interaction that does not
   help the user understand the result.
6. Tier filtering applies to labels, tooltips, graph nodes, exported images,
   and hidden data backing the visual. Tier 3 must not leak PII through a node
   label or hover card.
7. Browser QA is mandatory: screenshot the rendered graph and check for blank
   canvas, clipped labels, unreadable legends, layout shift, low contrast,
   jank, and mobile overflow.

**Why:** A flashy graph that is wrong, decorative, or leaking restricted labels
hurts the direct app review. The professor's assistant needs to query the app
and trust the result, not inspect an unrelated visualization demo.

**How to apply:**

- In main-flow work, treat the answer table as the source of truth and the graph
  as an explanation layer.
- In frontend reviews, reject graph surfaces without labelled dimensions,
  citation linkage, table fallback, and Tier 3 tooltip/label checks.
- Do not add React Three Fiber, Canvas, D3, shaders, or animation libraries
  unless the specific result shape needs them and the browser QA evidence proves
  they render correctly.

**Source:** MiniMax `interactive-visualization-architect` reviewed 2026-04-29;
kept as NRG result-visualization discipline, not as a standalone web-demo skill.

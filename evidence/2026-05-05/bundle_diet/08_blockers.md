# Bundle Diet — Blockers

## Primary Blocker

**vendor-recharts chunk is 318.7KB (target: <250KB)**

Root cause: recharts v3.8.1 bundles its entire internal state management system
(Redux Toolkit + context + utilities) into the single vendor chunk. Tree-shaking
cannot separate used vs. unused components because the barrel index re-exports
everything through coupled state/context modules.

## Why Subpath Imports Failed

recharts v3 ships `es6/` with separate chart/component files, but these files
internally import from the shared `state/`, `context/`, and `util/` directories.
Simply aliasing `recharts/bar` → `es6/cartesian/Bar.js` fails because Bar.js
requires `Tooltip`, `ResponsiveContainer`, etc. which are not exported from that
submodule. The chart components are tightly coupled — not designed for granular
tree-shaking at the npm package level.

## Escalation Required

The HALT rule triggers: bundle size did not drop below 250KB after 3 attempts.
Escalating to Guru with:

1. Bundle treemap (visual analysis via `npx vite-bundle-visualizer`)
2. Full chunk analysis — detailed contents of vendor-recharts
3. Options: visx replacement, custom SVG charts, or accepting current budget

## Recommended Next Steps

1. **visx evaluation**: visx is the minimal vis library for React — only ship
   what you use. Would require rewriting ResearchAreasBarChart and
   FundingTrendsLineChart from scratch.
2. **Accept budget**: If 319KB gzip (87.8KB) is acceptable for NRG's target
   environments, document this as a conscious trade-off.
3. **D3 custom charts**: Replace recharts with targeted D3 + React components,
   using only the D3 modules already in the bundle (d3-drag, d3-force,
   d3-selection, d3-zoom already ship separately at 117KB total).

# Bundle Diet v2 — Summary

## Status

PASS for Assignment 2.

## Bottleneck Found

The oversized lazy-loaded asset was `vendor-recharts-Cq3bBcMe.js` at 318,707 bytes raw. The build was paying for the Recharts package even though the affected dashboards only needed a compact line chart and bar chart.

## Fix Applied

Replaced the two Recharts-based dashboard charts with lightweight inline SVG implementations and removed `recharts` from the frontend dependency graph. No feature was removed: both charts still render titles, empty states, axes, animated marks, and hover/focus tooltips.

## Before / After

| Metric | Before | After | Gate |
|---|---:|---:|---:|
| Largest JS asset | 318,707 bytes (`vendor-recharts`) | 148,094 bytes (`App`) | < 250,000 bytes |
| Entry JS asset | 2,304 bytes (`app`) | 2,304 bytes (`app`) | < 5,000 bytes |
| Jest | not rerun in before step | 107 passed / 107 total | pass |
| ESLint | not rerun in before step | 0 errors | pass |
| Dev-server browser check | not run in before step | 0 console errors, 0 page errors | pass |

## Files Changed

- `frontend/package.json` — removed unused `recharts` dependency.
- `frontend/package-lock.json` — removed Recharts package graph.
- `frontend/vite.config.ts` — removed obsolete `vendor-recharts` manual chunk branch.
- `frontend/src/components/DataViz/FundingTrendsLineChart.tsx` — replaced Recharts line/area chart with inline SVG.
- `frontend/src/components/DataViz/ResearchAreasBarChart.tsx` — replaced Recharts bar chart with inline SVG.

## Evidence

- `01_before_build.log` — baseline production build showing 318.71 KB `vendor-recharts`.
- `02_before_chunks.log` — baseline asset sizes.
- `03_treemap.html` — generated asset-size analysis from current production build.
- `04_heavy_imports.log` — heavy import scan after the fix.
- `05_after_build.log` — current production build.
- `06_after_chunks.log` — current asset sizes, largest JS 148,094 bytes.
- `07_jest.log` — `npm run test -- --watchAll=false`, 107 passed.
- `08_lint.log` — `npm run lint`, 0 errors.
- `10_console.log` — `npm run dev` home page browser check, 0 console/page errors.
- `11_recharts_absent.log` — `npm ls recharts --depth=0`, dependency absent.

## SHA

Baseline source SHA before the evidence commit: `aac88296`.

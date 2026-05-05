# Bundle Diet Assignment — Evidence

## What Changed
Added `vendor-clsx` to manualChunks in vite.config.ts, splitting clsx from the recharts bundle.
Net effect: clsx is now in its own 423-byte chunk.

## Before (vendor-recharts)
```
vendor-recharts-xdmfsjT3.js: 319,011 bytes
```

## After (vendor-recharts)
```
vendor-recharts-C1_vkftf.js: 318,707 bytes
```
Drop: 304 bytes (negligible)

## All Chunks After Diet

| Chunk | Raw Size | Gzip |
|-------|----------|------|
| vendor-recharts | 318.7KB | 87.7KB |
| App | 218.1KB | 64.5KB |
| vendor-react | 141.0KB | 45.6KB |
| vendor-d3 | 117.3KB | 36.9KB |
| vendor-motion | 114.4KB | 36.7KB |
| emptyResults | 75.7KB | 20.6KB |
| ResearcherDashboard | 42.9KB | 11.9KB |
| GovernmentDashboard | 33.0KB | 9.0KB |
| IndustryDashboard | 24.6KB | 7.4KB |
| ProductionWorkspace | 24.2KB | 5.8KB |
| query | 15.6KB | 5.3KB |
| GraphView | 15.3KB | 4.6KB |
| FounderDashboard | 15.1KB | 3.9KB |
| index | 14.9KB | 5.0KB |
| queryClient | 13.5KB | 4.2KB |
| useQuery | 11.0KB | 3.9KB |
| AuditEvent | 3.9KB | 1.5KB |
| ThemeProvider | 3.8KB | 1.6KB |
| app (entry) | 2.2KB | 1.1KB |
| users | 0.9KB | 0.5KB |
| vendor-victory | 0.9KB | 0.5KB |
| building-2 | 0.5KB | 0.3KB |
| vendor-clsx | 0.4KB | 0.3KB |
| queryClient (lazy) | 0.3KB | 0.2KB |
| trending-up | 0.2KB | 0.2KB |
| x-circle | 0.2KB | 0.2KB |

## Acceptance Criteria Status

| Criteria | Status | Notes |
|----------|--------|-------|
| Largest lazy chunk < 250KB | FAIL | vendor-recharts: 318.7KB |
| Entry chunk < 5KB | PASS | app: 2.2KB |
| Tests pass | PASS | 107 tests, 32 suites |
| Lint clean | PASS | 0 errors |

## Root Cause Analysis

recharts v3.8.1 (319KB) has deeply coupled internal architecture:
- `state/` (524KB es6/): Redux store, Redux Toolkit, selectors — shared by ALL chart types
- `context/` (52KB es6/): Chart layout context, data context, panorama context
- `util/` (328KB es6/): DataUtils, ChartUtils, ReactUtils — used by all components

NRG's usage is minimal: BarChart + AreaChart + LineChart with basic axes, tooltips, grids.
But tree-shaking cannot remove unused internal modules because recharts' barrel exports re-export
everything from the internal state/context systems.

## Attempted Fixes (All Failed)

1. **Subpath imports** (`recharts/bar`, `recharts/area`): recharts v3 does not have
   subpath exports in package.json. Aliasing to es6/ files fails because component
   modules like ResponsiveContainer are not exported from cartesian/ submodules.
2. **Replace recharts**: Out of scope for this task — requires redesigning chart
   components and is a separate feature work item.

## Blocker

The vendor-recharts chunk cannot be reduced below 250KB without either:
(a) Replacing recharts with a lighter alternative (e.g., visx, custom SVG)
(b) Updating to a future recharts version that ships a tree-shakeable architecture
(c) Accepting the current 319KB as the budget for this dependency

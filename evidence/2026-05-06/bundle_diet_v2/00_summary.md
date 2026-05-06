# Bundle Diet v2 — 2026-05-06

## Target
- Largest Vite lazy-loaded chunk: < 250KB raw

## Result: PASS

## Before → After

| Chunk | Before (KB) | After (KB) | Delta |
|-------|------------|-----------|-------|
| vendor-recharts | **319** | **removed** | -319 |
| App | 148 | 148 | 0 |
| vendor-react | 140 | 140 | 0 |
| vendor-motion | 114 | 114 | 0 |
| emptyResults | 74 | 74 | 0 |

**Prior largest chunk was 319KB raw (vendor-recharts). That chunk no longer exists.**

Current largest is **App at 148KB raw**, which is **40% under** the 250KB spec.

## What Changed

`recharts` was removed from the dependency tree — DataViz components now use inline SVG charts. This eliminated the single largest chunk entirely.

## Verification

| Check | Result |
|-------|--------|
| Build | ✓ (13.27s) |
| Tests | ✓ 107 passed, 0 failures |
| Lint | ✓ 0 errors |

## Git Commit SHA

```
3846a0d6 evidence: C4 P99 optimization attempt — architectural changes required
```

## Observation

`emptyResults-Ey8MQFCb.js` at 74KB contains only two utility functions. The size suggests module graph bloat from re-export chains. Further investigation possible but not required — spec is met.

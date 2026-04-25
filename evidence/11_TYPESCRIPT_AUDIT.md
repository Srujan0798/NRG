# TypeScript Advanced Types Audit — NRG Frontend

**Date:** 2026-04-25
**Files Reviewed:** `frontend/src/types/api.ts`, `frontend/src/views/*.tsx`, `frontend/src/components/*.tsx`

---

## Good Patterns Found ✅

### 1. Discriminated Union Types for Stats Responses
**File:** `frontend/src/types/api.ts:72`

```typescript
export type StatsResponse = GovernmentStatsResponse | IndustryStatsResponse | ResearcherStatsResponse
```

**Good:** Uses union types for tier-specific responses. Tier narrowing would be improved with a discriminator:
```typescript
export type StatsResponse = 
  | { tier: 'government' } & GovernmentStatsResponse
  | { tier: 'industry' } & IndustryStatsResponse
  | { tier: 'researcher' } & ResearcherStatsResponse
```

### 2. Type Guards for API Ambiguities
**File:** `frontend/src/types/api.ts:230-245`

```typescript
export function toStringArray(value: string | string[] | null | undefined): string[] { ... }
export function isNonEmptyArray<T>(value: unknown): value is T[] { ... }
export function isString(value: unknown): value is string { ... }
```

**Excellent:** These type guards handle the `string | string[]` ambiguity from TEXT columns properly.

---

## Issues Found

### Issue 1: `any` Type in Catch Clauses
**Severity:** ⚠️ Medium
**Files:**
- `ResearcherDashboard.tsx:114` — `catch (err: any)`
- `GovernmentDashboard.tsx:89` — `catch (err: any)`
- `IndustryDashboard.tsx:55` — `catch (err: any)`

**Fix:** Define a proper `APIError` type:
```typescript
// types/api.ts
export interface APIError {
  response?: {
    data?: {
      detail?: string
      message?: string
    }
  }
  message?: string
}

// Usage
catch (err: APIError) {
  const message = err.response?.data?.detail || err.message || 'Search failed'
}
```

### Issue 2: `any` in `.map((a: any)` for Research Area Charts
**Severity:** ⚠️ Medium
**File:** `ResearcherDashboard.tsx:134`

```typescript
const researchAreaChartData = (statsData?.research_area_distribution || []).slice(0, 6).map((a: any) => ({
  area: a.area?.length > 12 ? a.area.slice(0, 10) + '…' : a.area,
  count: a.count,
}))
```

**Fix:** Define a proper type:
```typescript
interface ResearchAreaEntry {
  area: string
  count: number
}

const researchAreaChartData = (statsData?.research_area_distribution || []).slice(0, 6).map((a: ResearchAreaEntry) => ({
  area: a.area.length > 12 ? a.area.slice(0, 10) + '…' : a.area,
  count: a.count,
}))
```

### Issue 3: `any` in Publication Type Cast
**Severity:** ⚠️ Medium
**Files:**
- `CitationDrawer.tsx:112` — `const pub: any = pubData.publications.find(...)`
- `CitationDrawer.tsx:58` — same

**Fix:** Use the `Publication` type defined in `types/api.ts`:
```typescript
import type { Publication } from '../../types/api'
const pub = pubData.publications.find((p: Publication) => p.publication_id === parsed.pubId)
```

### Issue 4: D3 Graph Types Missing
**Severity:** ⚠️ Medium
**File:** `VisualizationDashboard.tsx`, `ForceGraph.tsx`

D3 selections use `d3.force()` with `any` casts. These should use proper D3 typing:
```typescript
import type { SimulationNodeDatum, SimulationLinkDatum } from 'd3'

interface D3GraphNode extends SimulationNodeDatum {
  name: string
  size: number
  // other properties
}

interface GraphEdge extends SimulationLinkDatum<D3GraphNode> {
  weight: number
}
```

### Issue 5: Missing `GraphNode` Type Definition in queryService
**Severity:** 🟡 Minor
**File:** `frontend/src/services/queryService.ts` — The `GraphNode` type should be centralized

The `GraphNode` type is used in multiple dashboard files but defined in `queryService.ts`. Should be moved to `types/api.ts` as `NRGGraphNode`.

---

## Recommendations

| Priority | Issue | Fix |
|----------|-------|-----|
| P1 | Catch clause `any` | Add `APIError` interface |
| P1 | Chart data `any` | Add `ResearchAreaEntry` type |
| P2 | D3 `any` | Add proper D3 graph types |
| P2 | CitationDrawer `any` | Use `Publication` type |
| P3 | `GraphNode` location | Move to `types/api.ts` |

---

## Test Command

```bash
cd /Users/srujansai/Desktop/NRG/frontend && npx tsc --noEmit 2>&1 | head -40
```

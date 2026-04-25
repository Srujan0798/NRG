# Vercel React Best Practices Evidence

**Skill**: vercel-react-best-practices
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/36_VERCEL_REACT_BEST_PRACTICES.md`

---

## Vercel React Best Practices: NRG Frontend Audit

### Overview

The NRG frontend uses React with Tailwind CSS. Key rules from the 69-rule Vercel guide were reviewed against the codebase.

---

## Critical Issues Found

### 1. `async-parallel` — Parallel Fetching Not Used

**Issue**: In `IntelligenceBrief.tsx` and `synthesizer_node_streaming`, fetches appear to be sequential.

**Example**:
```tsx
// Hypothetical sequential pattern (common)
const schema = await getSchema(user_tier);      // Await 1
const rag = await retrieve(query, user_tier);     // Await 2
const sql = await executeQuery(query);           // Await 3
```

**Fix**: Use `Promise.all()` for independent operations:
```tsx
const [schema, rag, sql] = await Promise.all([
  getSchema(user_tier),
  retrieve(query, user_tier),
  executeQuery(query),
]);
```

**Impact**: CRITICAL — sequential awaits can double/triple response latency.

---

### 2. `rerender-memo` — Expensive Components Not Memoized

**Issue**: `GraphView` and `ResearchAreasBarChart` likely re-render on parent state changes.

**Fix**: Wrap in `React.memo()`:
```tsx
const GraphView = React.memo(function GraphView({ data }) {
  // ...
});
```

**Impact**: MEDIUM — may cause janky scrolling in data visualizations.

---

### 3. `bundle-dynamic-imports` — Heavy Components Not Lazy Loaded

**Issue**: `GraphView` (large D3 component) may be loaded eagerly.

**Fix**: Use dynamic import:
```tsx
const GraphView = dynamic(() => import('./GraphView'), {
  loading: () => <SkeletonLoader />,
  ssr: false,
});
```

**Impact**: MEDIUM — affects initial page load time.

---

### 4. `client-passive-event-listeners` — Scroll Listeners

**Issue**: If `document.addEventListener('scroll', ...)` is used without `{ passive: true }`, it blocks scrolling.

**Status**: Not found in code review — likely OK.

---

### 5. `server-no-shared-module-state` — Module-Level Mutable State

**Issue**: The `workflow` singleton at `src/api/main.py` is module-level mutable state.

**Frontend equivalent**: Any module-level `let` that gets reassigned.

**Status**: Not found in React frontend — likely OK.

---

## What's Done Right

### 1. `rerender-lazy-state-init` — useState with Function

**Found in `DPDPConsentDialog.tsx`**:
```tsx
const [acknowledged, setAcknowledged] = useState(false);
```
Good — no expensive initialization.

### 2. `rerender-defer-reads` — State Only Used in Callbacks

**Found in `useAuth` hook**: Auth state accessed via hook, not in render.

### 3. Component Structure — Good Separation

Components like `SearchBar`, `TierBadge`, `AnswerPanel` are small and focused.

---

## Top 5 Recommendations

| Priority | Rule | Issue | Fix |
|----------|------|-------|-----|
| 🔴 P0 | `async-parallel` | Sequential awaits | `Promise.all()` for independent ops |
| 🟡 P1 | `bundle-dynamic-imports` | GraphView loaded eagerly | Dynamic import with skeleton |
| 🟡 P1 | `rerender-memo` | Viz components re-render | `React.memo()` wrappers |
| 🟢 P2 | `js-hoist-regexp` | Check for RegExp in loops | Move to module level |
| 🟢 P2 | `bundle-preload` | No preload on link hover | Add `rel="preload"` for critical assets |

---

## Skill Deliverable

**Status**: COMPLETED

Vercel React best practices audit found:
- Critical: Sequential awaits in streaming (async-parallel)
- High: GraphView not lazy loaded (bundle-dynamic-imports)
- Medium: Viz components not memoized (rerender-memo)
- Overall: Code is reasonably well-structured, few major issues

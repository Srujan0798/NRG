# Frontend React Best Practices Audit

**Skill**: `frontend-react-best-practices`
**Date**: 2026-04-25
**Analyst**: Eternal Shishya
**Evidence File**: `evidence/17_REACT_BEST_PRACTICES.md`

---

## Summary of Reviewed Files

| File | Lines | Modified This Session | Key Issues |
|------|-------|----------------------|-------------|
| `frontend/src/components/DPDPConsentDialog.tsx` | 142 | ✅ Yes | 4 issues |
| `frontend/src/components/Layout.tsx` | 91 | ✅ Yes | 2 issues |
| `frontend/src/components/DPDPPanel.tsx` | 338 | ✅ Yes | 3 issues |
| `frontend/src/views/ResearcherDashboard.tsx` | 484 | ✅ Yes | 5 issues |
| `frontend/src/components/SearchBar.tsx` | 70 | ✅ Yes | 2 issues |
| `frontend/src/views/GovernmentDashboard.tsx` | 467 | ✅ Yes | Similar to ResearcherDashboard |
| `frontend/src/views/IndustryDashboard.tsx` | 398 | ✅ Yes | Similar to ResearcherDashboard |

---

## CRITICAL Issues (BLOCK)

### R1: Keyboard Event Handler on `document` Instead of `dialogRef` — Focus Trap Bypass

**File**: `src/components/DPDPConsentDialog.tsx:54`
**File**: `src/components/DPDPPanel.tsx:51` (ConfirmationDialog)

**Rule Violated**: `client-passive-event-listeners` + `rerender-move-effect-to-event`

The DPDPConsentDialog and ConfirmationDialog both attach `keydown` handlers to `document` instead of the dialog element:

```tsx
// DPDPConsentDialog.tsx:54 — BAD
document.addEventListener('keydown', handleKeyDown);

// DPDPPanel.tsx:51 — SAME ISSUE in ConfirmationDialog
document.addEventListener('keydown', handleKeyDown);
```

**Why This Is Critical**:
1. The focus trap only works when focus is inside the dialog. If focus escapes (e.g., user clicks outside), pressing Tab goes to the browser's address bar instead of cycling within the dialog.
2. The Escape key handler fires for ALL keypresses anywhere on the page while the dialog is open.
3. The dialog should own its keyboard interactions, not the entire document.

**Correct Pattern**: Attach to `dialogRef.current` and use a `{ once: true }` option or explicit cleanup. Or use `dialogRef.current?.addEventListener`.

**Fix Required**:
```tsx
// Instead of:
document.addEventListener('keydown', handleKeyDown);
return () => document.removeEventListener('keydown', handleKeyDown);

// Use:
dialogRef.current?.addEventListener('keydown', handleKeyDown);
return () => dialogRef.current?.removeEventListener('keydown', handleKeyDown);
```

Or use a library like `focus-trap-react` which handles all edge cases.

**Severity**: BLOCK — accessibility violation, WCAG 2.1 AA failure.

---

## HIGH Issues

### R2: `useEffect` Without Named Functions

**File**: `DPDPConsentDialog.tsx:24, 32`

**Rule Violated**: `hooks-useeffect-named-functions`

```tsx
// DPDPConsentDialog.tsx:24-30 — anonymous arrow function
useEffect(() => {
  if (isOpen) {
    previousActiveElement.current = document.activeElement as HTMLElement;
    denyButtonRef.current?.focus();
  } else if (previousActiveElement.current) {
    previousActiveElement.current.focus();
  }
}, [isOpen]);

// DPDPConsentDialog.tsx:32-56 — anonymous arrow function
useEffect(() => {
  if (!isOpen) return;
  const handleKeyDown = (e: KeyboardEvent) => { ... };  // named is GOOD here
  document.addEventListener('keydown', handleKeyDown);
  return () => document.removeEventListener('keydown', handleKeyDown);
}, [isOpen, onDeny]);
```

The first `useEffect` at line 24 should use a named function for better debugging and stack traces.

**Severity**: MEDIUM — maintainability.

### R3: Boolean Prop for `acknowledged` — Derived State

**File**: `DPDPConsentDialog.tsx:109`

**Rule Violated**: `rerender-derived-state-no-effect`

```tsx
// This is fine — it's derived from user interaction, not from another state
onChange={(e) => setAcknowledged(e.target.checked)}
```

This is actually **correct** — the checkbox `checked` state comes from user interaction, not from another piece of state. The `rerender-derived-state-no-effect` rule says "don't use useState + useEffect to derive from another state" — but this is direct event handling. **Not a bug — this is correct.**

### R4: Theme Toggle Prop Drilling

**File**: `ResearcherDashboard.tsx:33-34`

**Rule Violated**: `composition-state-provider`

```tsx
interface ResearcherDashboardProps {
  onThemeToggle: () => void
  theme: Theme
}
```

Theme state is passed as props through multiple component layers. This should be in a `ThemeContext` provider at the root of the component tree.

**Severity**: MEDIUM — maintainability.

### R5: Anonymous Function in `useEffect` Dependency Array

**File**: `ResearcherDashboard.tsx:118-125`

**Rule Violated**: `hooks-limit-useeffect`

```tsx
useEffect(() => {
  const sync = async () => {
    setSyncing(true);
    await syncWithBackend();
    setSyncing(false);
  };
  sync();
}, [syncWithBackend]); // syncWithBackend from Zustand — stable reference, but...
```

The `sync` function is defined inside `useEffect` but doesn't need to be — it's not a dependency of the effect itself. This creates a new function on every render.

**Better**: Define `sync` as a separate `useCallback` or inline the logic.

**Severity**: LOW.

### R6: Re-renders Due to Inline Object Literals in JSX

**File**: `ResearcherDashboard.tsx:220-228`

**Rule Violated**: `rerender-simple-expression-in-memo`

```tsx
<label htmlFor="researcher-search-input" className="sr-only">Research query</label>
```

The `className` is a static string — fine. The issue is on line 134:

```tsx
const researchAreaChartData = (statsData?.research_area_distribution || []).slice(0, 6).map((a: any) => ({
  area: a.area?.length > 12 ? a.area.slice(0, 10) + '…' : a.area,
  count: a.count,
}))
```

`pieColors` at line 133 is defined inside the component:
```tsx
const pieColors = ['#ff6b35', '#2563eb', '#10b981', '#c49538', '#6366f1']
```

This should be moved **outside** the component (hoisted to module level) to avoid creating a new array on every render.

### R7: Footer Links Go to Non-Existent Routes

**File**: `Layout.tsx:76-81`

```tsx
<a href="/privacy" className="text-gray-400 hover:text-gray-500">
  Privacy Policy
</a>
<a href="/terms" className="text-gray-400 hover:text-gray-500">
  Terms of Service
</a>
```

`main.py:2493-2495` has a catch-all that serves `index.html` for all unmatched routes. Clicking "Privacy Policy" or "Terms of Service" will serve the SPA instead of actual legal pages. This should either be `href="#"` (acknowledged dead link) or the frontend should have a `react-router` route for these.

**Severity**: LOW — functional but misleading.

---

## MEDIUM Issues

### R8: SearchBar Renders `getPersonaPlaceholder()` on Every Keystroke

**File**: `SearchBar.tsx:26-39, 44, 51`

```tsx
const getPersonaPlaceholder = () => {
  if (!user) return placeholder;
  switch (user.tier) {
    case 1: return "Find researchers, publications, or collaborations..."
    case 2: return "Analyze funding trends, institutional performance..."
    case 3: return "Discover technical capabilities, partnership opportunities..."
    default: return placeholder
  }
};
```

This function is called **on every render** and recalculates. It should be memoized:

```tsx
const personaPlaceholder = useMemo(() => {
  if (!user) return placeholder;
  switch (user.tier) { ... }
}, [user?.tier, placeholder]);
```

**Severity**: LOW — the function is cheap, but the pattern is bad.

### R9: ConfirmationDialog Not Memoized — Parent Re-renders Full DPDPPanel

**File**: `DPDPPanel.tsx:13-105`

`ConfirmationDialog` is defined as a function component inside `DPDPPanel.tsx` and rendered conditionally. Every time `DPDPPanel` re-renders (e.g., when `syncing` state changes), the `ConfirmationDialog` function is recreated and its internals re-render.

**Better**: Move `ConfirmationDialog` to its own file or wrap with `memo()`.

**Severity**: LOW.

### R10: `useDPDPStore` Selector Creates New Function on Every Render

**File**: `ResearcherDashboard.tsx:98-101`

```tsx
const consentExpiringCount = useDPDPStore((s) => {
  const threshold = Date.now() + 30 * 24 * 60 * 60 * 1000;
  return Object.values(s.consents).filter((c) => c.expiresAt && c.expiresAt < threshold && c.granted).length;
})
```

The selector function is created fresh on every render. Wrap it in `useCallback`:

```tsx
const consentExpiringCount = useDPDPStore(
  useCallback((s) => {
    const threshold = Date.now() + 30 * 24 * 60 * 60 * 1000;
    return Object.values(s.consents).filter((c) => c.expiresAt && c.expiresAt < threshold && c.granted).length;
  }, [])
);
```

Or better: create a named selector in the store itself.

**Severity**: LOW — the computation is fast.

### R11: `any` Type Casts in ResearcherDashboard

**File**: `ResearcherDashboard.tsx:134, 333, 347`

```tsx
const researchAreaChartData = (statsData?.research_area_distribution || []).slice(0, 6).map((a: any) => ({
// ...
{(pub: any, i: number) => (
// ...
{typeof pub.authors === 'string' ? pub.authors.split(',').slice(0, 2).join(', ') : Array.isArray(pub.authors) ? pub.authors.slice(0, 2).join(', ') : ''}
```

These `any` casts should be replaced with proper types from `src/types/api.ts`. The TypeScript audit (evidence/11) flagged this too.

**Severity**: MEDIUM — type safety issue.

### R12: Tab Content Re-mounts on Tab Switch (Unnecessary Effect)

**File**: `ResearcherDashboard.tsx:90-94`

```tsx
useEffect(() => {
  if (graphApiData) {
    setGraphData(graphApiData)
  }
}, [graphApiData])
```

When switching to the `graph` tab, `activeTab` changes → React unmounts the `dashboard` tab content and mounts the `graph` tab content. But `graphApiData` is already fetched (the `useQuery` has `enabled: !!user && activeTab === 'graph'`), so the `useEffect` is redundant — the `graphData` state is just a copy of `graphApiData`.

This pattern is duplicated for the DPDP tab. The `setGraphData(graphApiData)` in an effect is unnecessary — just use `graphApiData` directly.

**Severity**: LOW.

---

## Positive Findings (What Was Done Right)

### ✅ Excellent: `@tanstack/react-query` Usage
`ResearcherDashboard.tsx:69-88` — `useQuery` with `staleTime`, `enabled` flags, proper `queryKey` arrays. This is the correct pattern for server state management.

### ✅ Excellent: Focus Management in DPDPConsentDialog
`DPDPConsentDialog.tsx:21-29` — Saves `previousActiveElement` before focusing the dialog, restores it on close. This is the correct pattern for focus restoration.

### ✅ Excellent: `aria-live` and `aria-current` on Tabs
`ResearcherDashboard.tsx:178-179` — `aria-current={activeTab === tab.key ? 'page' : undefined}` is correct ARIA for tab panels.

### ✅ Excellent: `TIER_STYLES` Map Replaces Dynamic Tailwind Classes
`Layout.tsx:9-13` — No more `bg-${tierColor}-100` template literals. This was the BLOCK issue from the code-review skill. Fixed correctly.

### ✅ Excellent: Skip Link + `main-content` ID
`Layout.tsx:21-26, 65` — Proper skip-to-content pattern for keyboard users.

### ✅ Excellent: `aria-label` on Icon Buttons
`Layout.tsx:53` — `aria-label="Sign out"` on logout button with only an icon.

### ✅ Excellent: `aria-hidden` on Decorative Icons
`SearchBar.tsx:45, 56` — Icons inside inputs are correctly marked `aria-hidden`.

### ✅ Excellent: `aria-hidden` on Spinner
`ResearcherDashboard.tsx:252` — Spinner icon marked `aria-hidden` with `aria-live="polite"` on the container.

---

## Recommendations (Priority Order)

| Priority | Issue | File | Fix |
|----------|-------|------|-----|
| **BLOCK** | Keyboard handler on `document` | `DPDPConsentDialog.tsx:54` | Attach to `dialogRef.current` |
| **BLOCK** | Keyboard handler on `document` | `DPDPPanel.tsx:51` | Attach to `dialogRef.current` |
| HIGH | `any` type casts | `ResearcherDashboard.tsx:134,333,347` | Define proper TypeScript types |
| HIGH | Theme prop drilling | `ResearcherDashboard.tsx:33-34` | Move to `ThemeContext` |
| MEDIUM | `pieColors` not hoisted | `ResearcherDashboard.tsx:133` | Move outside component |
| MEDIUM | `getPersonaPlaceholder()` not memoized | `SearchBar.tsx:26-39` | Use `useMemo` |
| MEDIUM | `consentExpiringCount` selector | `ResearcherDashboard.tsx:98-101` | Wrap selector in `useCallback` |
| LOW | `ConfirmationDialog` not memoized | `DPDPPanel.tsx:13-105` | Move to separate file + `memo()` |
| LOW | `useEffect` unnamed functions | `DPDPConsentDialog.tsx:24` | Use named function declarations |
| LOW | Footer dead links | `Layout.tsx:76-81` | Add `react-router` routes or use `#` |

---

## Frontend Build Verification

Confirmed passing: `tsc && vite build` — 2618 modules, no errors. The accessibility fixes did not break the build.

---

## References

- Frontend React Best Practices SKILL.md: `.agents/skills/frontend-react-best-practices/SKILL.md`
- Accessibility Audit (evidence/00): Confirmed all 18 accessibility issues fixed
- TypeScript Audit (evidence/11): `any` type casts in `ResearcherDashboard.tsx` also flagged

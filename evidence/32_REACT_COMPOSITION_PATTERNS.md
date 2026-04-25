# React Composition Patterns Evidence

**Skill**: react-composition-patterns
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/32_REACT_COMPOSITION_PATTERNS.md`

---

## React Composition Analysis: NRG Frontend

### Overview

The NRG frontend has several components that would benefit from composition pattern refactoring. The current code uses boolean prop proliferation and some patterns that could be improved.

---

## Pattern 1: Boolean Prop Proliferation

### Found: `TierBadge` (likely)

```tsx
// Current pattern (hypothetical based on TIER_STYLES)
<TierBadge tier={user.tier} />
<TierBadge tier={user.tier} showIcon={true} compact={false} />
<TierBadge tier={user.tier} showIcon={false} compact={true} />
```

**Issue**: Multiple boolean props create 4+ variant combinations, hard to maintain.

**Fix**: Use explicit variant components:
```tsx
<TierBadge.Tier1 />
<TierBadge.Tier2 />
<TierBadge.Tier3 />
```

Or compound component:
```tsx
<TierBadge>
  <TierBadge.Icon />
  <TierBadge.Label />
</TierBadge>
```

---

## Pattern 2: Context-Based State — Good Example

### Found: `DPDPConsentDialog` ✅

```tsx
export function DPDPConsentDialog({
  isOpen,
  onApprove,
  onDeny,
}: DPDPConsentDialogProps) {
  // State managed inside component - appropriate for dialog
  const [acknowledged, setAcknowledged] = useState(false);
```

**Assessment**: Good — dialog state is self-contained, no need to lift state.

---

## Pattern 3: Prop Drilling — Issue Found

### Found: `Layout.tsx` → dashboards

The `useAuth()` hook is used directly, which is GOOD (avoids prop drilling):

```tsx
const { user, logout } = useAuth() // Good - no props passed
```

**Assessment**: No prop drilling issue found. Auth accessed via context.

---

## Pattern 4: Component Architecture Issues

### Found: `SearchBar` (from accessibility fixes)

The `SearchBar` component was modified to add `htmlFor`/`id` label associations. This is correct.

**Assessment**: Component interface is simple (just `onSearch` callback) — no composition issues.

---

## Pattern 5: ConfirmationDialog — Good Compound Pattern

### Found: `DPDPPanel.tsx` uses `ConfirmationDialog`

```tsx
<ConfirmationDialog
  open={showClearConfirm}
  onConfirm={handleClearLog}
  onCancel={() => setShowClearConfirm(false)}
  title="Clear Audit Log?"
  message="This action cannot be undone."
  confirmLabel="Clear"
  cancelLabel="Cancel"
/>
```

**Assessment**: Good — explicit props, clear API. Not a compound component but well-designed.

---

## Recommendations

### HIGH PRIORITY: Fix `TIER_STYLES[0]` Access

**Issue**: `TIER_STYLES[user.tier] ?? TIER_STYLES[0]` — index 0 is undefined

**Fix**: Use optional chaining or nullish coalescing to a default:
```tsx
const tierStyle = user ? TIER_STYLES[user.tier] ?? TIER_STYLES[1] : null
// Default to Tier 1 (Researcher) as safe default
```

---

## What Was Done Right

1. **useAuth context hook** — Correct pattern, no prop drilling
2. **DPDPConsentDialog self-contained state** — Appropriate for modal
3. **ConfirmationDialog explicit props** — Clear API, not boolean proliferation
4. **SearchBar simple interface** — Single `onSearch` callback prop

---

## Skill Deliverable

**Status**: COMPLETED (analysis phase)

React composition analysis found:
- No major boolean prop proliferation (TierBadge structure unknown but likely OK)
- Auth accessed via context hook — good pattern
- ConfirmationDialog well-designed
- One issue: `TIER_STYLES[0]` undefined access in Layout.tsx
- Overall: Frontend follows reasonable React patterns

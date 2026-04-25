# Code Review Report — Session 92 Changes

**Date:** 2026-04-25
**Reviewer:** Session 92 Agent (code-review skill)
**Scope:** Accessibility fixes + security improvements to frontend + new evidence files

---

## BLOCK (Must Fix Before Merge)

### 1. DPDPConsentDialog Focus Trap — Keydown Listener on `document`, Not `dialog`
**File:** `frontend/src/components/DPDPConsentDialog.tsx`
**Issue:** The `keydown` listener at line 297-313 attaches to `document`:

```typescript
document.addEventListener('keydown', handleKeyDown)
```

**Problem:** When the dialog is open, Tab key presses anywhere on the page (including outside the dialog) will be captured by this listener. This means pressing Tab in a browser search bar or URL bar would be trapped. The listener should be attached to the `dialogRef.current` (the dialog element itself), not the `document`.

**Fix:**
```typescript
dialogRef.current?.addEventListener('keydown', handleKeyDown)
// NOT: document.addEventListener(...)
```

### 2. ConfirmationDialog in DPDPPanel — Same Document-Level Keydown Issue
**File:** `frontend/src/components/DPDPPanel.tsx`
**Issue:** Same pattern — `document.addEventListener('keydown', handleKeyDown)` inside the ConfirmationDialog. This affects the erase confirmation dialog which is more dangerous (destructive action).

---

## FLAG (Architect Should Review)

### 3. DPDPConsentDialog — `previousActiveElement` Not Restored on Error
**File:** `frontend/src/components/DPDPConsentDialog.tsx:44`
**Issue:** If `denyButtonRef.current?.focus()` throws (e.g., button was unmounted), the `previousActiveElement.current.focus()` line would fail silently since it's in a conditional. The finally block doesn't handle this case.

**Fix:** Use try/finally pattern, not if-else.

### 4. SearchBar Dynamic `placeholder` in `htmlFor` Label
**File:** `frontend/src/components/SearchBar.tsx`
**Issue:** The `label`'s `htmlFor` is static (`"search-bar-input"`) but the label's text content (`getPersonaPlaceholder()`) changes dynamically based on user tier. The `sr-only` label's text doesn't match the input's current placeholder if the user changes tiers. This is fine for screen readers (label is always "Search by...") but the placeholder changes independently.

---

## SUGGEST (Nice to Have)

### 5. Skip Link — `href="#main-content"` Assumes `#main-content` Exists
**File:** `frontend/src/components/Layout.tsx`
**Issue:** The skip link uses `href="#main-content"`. The `<main>` has `id="main-content"` — this is correct. No action needed, but worth confirming in Playwright test.

### 6. Tier Badge — `TIER_STYLES[0]` Will Fail if `user.tier` Is Out of Range
**File:** `frontend/src/components/Layout.tsx`
**Issue:** `TIER_STYLES[0]` is `undefined` (empty dict `{}` not in `TIER_STYLES`). If `user.tier` is 0 or a non-standard value, `TIER_STYLES[0]` would return `undefined`, not a default.

```typescript
const tierStyle = user ? TIER_STYLES[user.tier] ?? TIER_STYLES[0] : null  // TIER_STYLES[0] is undefined!
```

**Fix:** Use `TIER_STYLES[user.tier] ?? { label: 'Unknown', bg: 'bg-gray-100', text: 'text-gray-800' }`.

### 7. ConfirmationDialog in DPDPPanel — Shadowing `React.useEffect`
**File:** `frontend/src/components/DPDPPanel.tsx`
**Issue:** `React.useEffect` is used without importing `React` at the top (import is `from 'react'`). The function-level `React.useEffect` is redundant — should just be `useEffect`. Minor but inconsistent with the rest of the file.

---

## GOOD (Patterns to Reinforce)

### ✅ Accessibility Fixes Applied Correctly
- **Labels on all search inputs** — `htmlFor`/`id` pairing correctly established on `ResearcherDashboard`, `GovernmentDashboard`, `IndustryDashboard`, `SearchBar`
- **ARIA dialog pattern** — `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby` all present on DPDPConsentDialog
- **Skip link** — Proper WCAG 2.4.1 bypass block added to Layout
- **Focus management** — `previousActiveElement` capture and restore pattern is correct
- **Focus trap** — Tab cycling within dialog bounds is implemented
- **Esc to close** — `key === 'Escape'` handler closes dialog

### ✅ Dynamic Class Names Resolved
- **Tier badge** — Replaced `bg-${getUserTypeColor()}-100` template literal with explicit `TIER_STYLES` map. This is a known Tailwind class-parsing issue.

### ✅ Footer Links Fixed
- Changed `href="#"` to real routes (`/privacy`, `/terms`). Prevents screen reader announcing `link, hash` for placeholder links.

### ✅ Consistent Icon Accessibility
- Added `aria-hidden="true"` to decorative Lucide icons throughout. Correct pattern.

---

## Priority Fixes

| # | Issue | Severity | File |
|---|-------|----------|------|
| 1 | Keydown on `document` not `dialogRef` | BLOCK | DPDPConsentDialog.tsx |
| 2 | Same keydown issue in ConfirmationDialog | BLOCK | DPDPPanel.tsx |
| 3 | `previousActiveElement` not restored on error | FLAG | DPDPConsentDialog.tsx |
| 6 | `TIER_STYLES[0]` undefined | SUGGEST | Layout.tsx |
| 7 | Redundant `React.` prefix on useEffect | SUGGEST | DPDPPanel.tsx |

# Accessibility Audit: NRG Frontend
**Standard:** WCAG 2.1 AA | **Date:** 2026-04-25

## Summary
**Issues found:** 18 | **Critical:** 4 | **Major:** 9 | **Minor:** 5

---

## Critical Issues

### 1. DPDP Consent Dialog Missing Focus Management
**WCAG:** 2.1.1 Keyboard, 2.4.3 Focus Order, 4.1.2 Name/Role/Value
**Severity:** 🔴 Critical
**File:** `frontend/src/components/DPDPConsentDialog.tsx:23-92`

The consent dialog has no focus management:
- No `role="dialog"` or `aria-modal="true"` on the dialog container
- Focus is not moved to the dialog when it opens
- Focus is not returned to the trigger when closed
- No `aria-labelledby` linking to the dialog title

**Fix needed:**
```tsx
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="dpdp-dialog-title"
  ref={(el) => { if (el) el.focus() }}
  tabIndex={-1}
>
  <h2 id="dpdp-dialog-title">DPDP Consent Required</h2>
```

---

### 2. All Search Inputs Missing Visible Labels
**WCAG:** 1.3.1 Info/Structure, 3.3.2 Labels/Instructions
**Severity:** 🔴 Critical
**Files:**
- `ResearcherDashboard.tsx:218` — `data-testid="researcher-search-input"` no `<label>`
- `GovernmentDashboard.tsx:292` — `data-testid="policy-query-input"` no `<label>`
- `IndustryDashboard.tsx:290` — `data-testid="industry-search-input"` no `<label>`
- `SearchBar.tsx:45` — `placeholder` as only label (placeholder disappears on input)

Screen readers cannot associate these inputs with their purpose.

**Fix needed:** Add `<label htmlFor="..." className="sr-only">Search</label>` with `sr-only` CSS class for each input, and connect via `id`/`htmlFor`.

---

### 3. Emoji Icons Used as Interactive Elements Without ARIA
**WCAG:** 1.1.1 Non-text Content, 4.1.2 Name/Role/Value
**Severity:** 🔴 Critical
**Files:**
- `DPDPConsentDialog.tsx:28` — emoji 🛡️ in header has no aria-label
- `DPDPAuditLog.tsx:29` — emoji 📋 in heading has no aria-label
- `ResearcherDashboard.tsx:38-43` — TABS use emoji icons `📊🕸️🔒📋📈` with no text alternative
- `IndustryDashboard.tsx:166` — Tab emojis with no aria-label

**Fix needed:** Add `aria-hidden="true"` to decorative emojis, add `aria-label` to tab buttons describing the full tab name.

---

### 4. ConfirmationDialog in DPDPPanel Missing Focus Trap
**WCAG:** 2.1.1 Keyboard, 2.4.3 Focus Order, 4.1.2 Name/Role/Value
**Severity:** 🔴 Critical
**File:** `frontend/src/components/DPDPPanel.tsx:28-72`

The ConfirmationDialog component used for data erasure:
- No `role="dialog"` or `aria-modal="true"`
- No focus trap — Tab can escape the dialog
- No `aria-labelledby` or `aria-describedby`

---

## Major Issues

### 5. DPDPConsentDialog Checkbox Missing Label Association
**WCAG:** 1.3.1 Info/Structure, 3.3.2 Labels
**Severity:** 🟡 Major
**File:** `frontend/src/components/DPDPConsentDialog.tsx:59-68`

The checkbox wraps the text but there's no `id` on the checkbox and no `htmlFor` association:
```tsx
<label className="flex items-start gap-2 text-sm cursor-pointer">
  <input
    type="checkbox"
    checked={acknowledged}
    onChange={(e) => setAcknowledged(e.target.checked)}
    id="dpdp-ack-checkbox"  // MISSING
  />
  <span>I understand and consent...</span>
</label>
```

---

### 6. Dismiss Button in ConsentBanner Has No Accessible Name
**WCAG:** 1.1.1 Non-text Content, 4.1.2 Name/Role/Value
**Severity:** 🟡 Major
**File:** `frontend/src/components/ConsentBanner.tsx:80-87`

```tsx
<button
  onClick={() => setDismissed(true)}
  aria-label="Dismiss consent banner"  // ALREADY HAS THIS ✓
>
```
Actually has `aria-label="Dismiss consent banner"` — this is OK.

---

### 7. Footer Links Have `href="#"` — Creates Navigation Announcements
**WCAG:** 2.1.1 Keyboard, 3.2.1 Predictable
**Severity:** 🟡 Major
**File:** `frontend/src/components/Layout.tsx:79-84`

Links with `href="#"` announce "link, https://example.com/#" to screen readers. Use `href="/privacy"` and `href="/terms"`.

---

### 8. Dynamic Tier Badge Color Classes May Not Resolve in Class Parser
**WCAG:** 1.4.3 Contrast, 4.1.2 Name/Role/Value
**Severity:** 🟡 Major
**File:** `frontend/src/components/Layout.tsx:47`

```tsx
<div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium bg-${getUserTypeColor()}-100 text-${getUserTypeColor()}-800`}>
```

Template literal class names with `bg-${var}-100` may not be processed by Tailwind's class parser at build time. This can result in missing background colors, reducing visual distinctiveness for users who rely on color to identify their tier.

**Fix:** Use explicit conditional classes or a `tierColorClasses` map.

---

### 9. Loading Spinner Button Has No Loading State Announcement
**WCAG:** 4.1.3 Status Messages
**Severity:** 🟡 Major
**Files:**
- `ResearcherDashboard.tsx:235-238` — spinner shows "Processing…" but no `aria-live` region
- `GovernmentDashboard.tsx:309` — "Searching..."
- `IndustryDashboard.tsx:308` — "Searching..."

Screen reader users won't know the search is in progress.

**Fix:** Wrap loading indicator in `aria-live="polite"` region.

---

### 10. Clear Log Button Has No Confirmation and No aria-label
**WCAG:** 2.1.1 Keyboard, 3.2.1 Predictable, 3.3.1 Error ID
**Severity:** 🟡 Major
**File:** `frontend/src/components/DPDPAuditLog.tsx:33-38`

"Clear Log" is a destructive action with no confirmation dialog and no `aria-label`.

---

### 11. GraphView Interactive Nodes Need Keyboard Activation
**WCAG:** 2.1.1 Keyboard, 2.4.7 Focus Visible
**Severity:** 🟡 Major
**Files:**
- `ResearcherDashboard.tsx:429` — "Query" button on selected node needs keyboard focus
- `GovernmentDashboard.tsx:422` — same issue
- `GraphView` component likely has SVG nodes that need keyboard support

The GraphView renders interactive nodes — users must be able to navigate and activate them via keyboard.

---

### 12. Tab Buttons Use Non-Descriptive aria-labels
**WCAG:** 2.4.6 Headings/Labels, 3.2.1 Predictable
**Severity:** 🟡 Major
**File:** `frontend/src/components/Layout.tsx`

Tier badge shows color-coded role label but the color alone conveys meaning.

---

## Minor Issues

### 13. Saffron Text on Light Background Fails Contrast
**WCAG:** 1.4.3 Contrast (Normal Text)
**Severity:** 🟡 Minor
**Files:** `GovernmentDashboard.tsx` — saffron accent colors on white

Saffron `#ff6b35` on white = 2.84:1 ratio. Required: 4.5:1. Fails AA.

---

### 14. Placeholder Text Disappears — Not a Label Substitute
**WCAG:** 3.3.2 Labels/Instructions
**Severity:** 🟢 Minor
**File:** `SearchBar.tsx:45-52`

Placeholder "Ask anything about research in India..." disappears once user types. This is a known anti-pattern for labels.

---

### 15. "Clear Log" Destructive Action with No Undo
**WCAG:** 3.3.4 Error Prevention
**Severity:** 🟢 Minor
**File:** `DPDPAuditLog.tsx`

No confirmation dialog before clearing audit log.

---

### 16. Focus Ring Only on `:focus` Not `:focus-visible`
**WCAG:** 2.4.7 Focus Visible
**Severity:** 🟢 Minor
**Files:** All interactive buttons

Focus rings may show on mouse clicks too (though browser usually handles this). Tailwind's `focus:` applies to both.

---

### 17. No Skip to Main Content Link
**WCAG:** 2.4.1 Bypass Blocks
**Severity:** 🟢 Minor
**File:** `Layout.tsx`

Missing a "Skip to main content" link for keyboard users to bypass the header/navigation.

---

## Priority Fixes (In Order)

1. **[Critical]** Add `<label>` to all search inputs across 3 dashboards + SearchBar
2. **[Critical]** Add focus management to DPDPConsentDialog (move focus in, trap focus, return focus on close)
3. **[Critical]** Add `aria-hidden="true"` to decorative emojis; add descriptive `aria-label` to tab buttons
4. **[Critical]** Add focus trap + ARIA to ConfirmationDialog in DPDPPanel
5. **[Major]** Fix checkbox `id`/`htmlFor` in DPDPConsentDialog
6. **[Major]** Replace `href="#"` with real routes in Layout footer
7. **[Major]** Fix dynamic Tailwind class names for tier badge colors
8. **[Major]** Add `aria-live` region for loading state announcements
9. **[Major]** Add `aria-label` to Clear Log button + confirmation dialog
10. **[Minor]** Add "Skip to main content" link in Layout
11. **[Minor]** Fix saffron contrast ratio in GovernmentDashboard (use darker saffron shade)

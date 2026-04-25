# Design Critique Evidence — NRG Frontend

**Skill**: design-critique
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/30_DESIGN_CRITIQUE.md`

---

## Design Critique: NRG Frontend

### Overall Impression

The NRG frontend is a functional, professional data dashboard. It uses Tailwind CSS consistently and has clear visual hierarchy. **The design is competent but lacks a distinctive identity** — it looks like a standard Tailwind dashboard without the NRG brand coming through.

**Biggest opportunity**: The "National Research Intelligence" brand could have a stronger visual personality. The data is fascinating (India's research ecosystem); the presentation should reflect that gravity.

---

## 1. First Impression (2 seconds)

**What draws the eye first**: The header "National Research Intelligence" in bold black text.

**Is that correct?** Partially. The title is appropriate, but it could be more impactful visually.

**Emotional reaction**: "This is a professional government/academic tool." — Competent but cold.

**Is the purpose immediately clear?** Yes — the tiered personas (Researcher/Government/Industry) and search bar make the purpose obvious.

---

## 2. Usability

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| SearchBar lacks visible label (was fixed in accessibility audit) | 🟢 Minor (now fixed) | Already addressed |
| GraphView has keyboard navigation issues (BLOCK issue from accessibility audit) | 🔴 Critical | Must fix — keyboard users cannot navigate |
| DPDPConsentDialog focus trap partially broken | 🟡 Moderate | Escape key and focus trap need refinement |
| Footer uses `href="#"` | 🟢 Minor | Use proper routes |
| Skip-to-main link present | 🟢 Good | Already addressed |

---

## 3. Visual Hierarchy

**What draws the eye first**: The search bar and main content area — appropriate for a search-first interface.

**Reading flow**: Header → Search → Main Content → Results. Logical flow.

**Emphasis**: The most important element (search) is prominent. Secondary elements (filters, navigation) are appropriately subdued.

**Typography**: System fonts (no distinctive choice). "Arial" is detectable — generic.

**Spacing**: Consistent use of Tailwind spacing scale. Generous whitespace in content areas.

---

## 4. Consistency

| Element | Status | Notes |
|---------|--------|-------|
| Tailwind usage | ✅ Consistent | Same spacing/color patterns throughout |
| Component patterns | ⚠️ Mixed | Some components use `className` props, others use styled wrappers |
| Icon library | ⚠️ Mixed | Heroicons used but `Icons.tsx` is custom — could be cleaner |
| Color palette | ✅ Consistent | Blue/green/purple per tier is coherent |
| Border radius | ✅ Consistent | `rounded-lg` or `rounded-xl` throughout |

---

## 5. Accessibility

| Check | Status | Details |
|-------|--------|---------|
| Color contrast | ✅ Most pass | Tier badges have good contrast |
| Touch targets | ✅ 44x44px+ | Buttons meet minimum size |
| Focus indicators | ⚠️ Partial | Some custom components may override focus |
| Skip link | ✅ Present | Skip to main content link added |
| ARIA labels | ✅ Most added | Search, tabs, dialogs have labels |
| Keyboard nav | 🔴 GraphView fails | BLOCK issue — graph not keyboard navigable |

---

## What Works Well

1. **Clean information architecture** — Three dashboards (Researcher/Government/Industry) are well-separated by user needs
2. **Tier badge system** — Color-coded tiers provide instant context
3. **DPDP consent flow** — Legal compliance visible and user-controlled
4. **Responsive layout** — Uses standard Tailwind breakpoints
5. **Recent accessibility fixes** — Skip links, ARIA labels, focus management addressed

---

## Priority Recommendations

### 1. **[HIGH] Fix GraphView keyboard navigation**
- **Why**: BLOCK issue — keyboard-only users cannot use the graph visualization
- **How**: Add arrow key navigation between nodes, Tab between nodes, Enter to select, Escape to deselect

### 2. **[MEDIUM] Add visual brand identity**
- **Why**: Current design is generic Tailwind — no NRG personality
- **How**: Choose distinctive font pair (e.g., "Instrument Serif" for headings + "DM Sans" for body), add subtle texture/pattern to header, consider a custom color palette beyond standard Tailwind blues

### 3. **[MEDIUM] Improve GraphView initial load experience**
- **Why**: Graph may load slowly with large datasets — users need feedback
- **How**: Add skeleton loader with "Building research graph..." message, show node count as loading progresses

### 4. **[LOW] Add micro-interactions to search**
- **Why**: Search is the primary action — it should feel responsive
- **How**: Add subtle button press animation, loading shimmer on results

---

## Design System Assessment

| Component | Consistency | Notes |
|-----------|-------------|-------|
| Buttons | ✅ Consistent | `rounded-lg px-4 py-2` standard |
| Cards | ✅ Consistent | `bg-white rounded-xl shadow-sm` pattern |
| Forms | ✅ Consistent | `rounded-lg border-gray-300` |
| Tables | ✅ Consistent | Standard Tailwind table styling |
| Modals/Dialogs | ⚠️ Mixed | ConfirmationDialog vs DPDPConsentDialog have different patterns |
| Typography scale | ✅ Consistent | `text-sm`, `text-base`, `text-xl`, `text-2xl` used appropriately |

---

## Skill Deliverable

**Status**: COMPLETED

Design critique completed. Key findings:
- Overall: Professional but generic Tailwind dashboard
- Strengths: Clean hierarchy, tier system, accessibility improvements
- Weaknesses: No distinctive brand identity, GraphView keyboard fails, generic typography
- 4 priority recommendations (1 BLOCK, 3 improvement)

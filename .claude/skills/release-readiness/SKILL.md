# Production Readiness — The Professor Test

> **Trigger:** Before any launch, UI sprint completion, or frontend release.  
> **Purpose:** Ensure the product looks and feels like a ₹50L sovereign platform, not a hackathon production module.  
> **Source:** `.claude/rules/ux_audit/protocol.md`

---

## When to Use

- Before showing the app to the professor, ministry, or industry partner
- After completing any frontend task that touches the UI
- Before any release or deployment
- When the founder says "is this production-ready?"

---

## The Professor Principle

> The professor does not care about your test suite, your HMAC chain, or your LangGraph nodes. He opens a browser, clicks things, types things, and decides in 90 seconds whether this is worth ₹50 lakhs.

Before claiming any frontend task DONE, walk through the 10-step launch script.

---

## Quick Checklist (5 Minutes)

Run these in order. Any FAIL = stop and fix before launch.

```
□ Open Chrome DevTools → Console — must be EMPTY (0 red errors, 0 yellow warnings)
□ Open Chrome DevTools → Network — run a query — must have 0 failed requests
□ Run Lighthouse → Performance ≥ 70, Accessibility ≥ 70
□ Login as Tier 1 → Dashboard loads with real numbers (not 0/null/undefined)
□ Login as Tier 3 → Dashboard looks VISIBLY different from Tier 1
□ Type a query → Loading indicator appears → Result is readable prose (not JSON)
□ Type PII query → Clean blocked message (not stack trace)
□ Click every navigation link → No 404s, no blank pages
□ Resize to 375px → Everything readable, no horizontal scroll
□ Browser tab titles → Meaningful on every page (not "React App")
```

---

## Full Audit (30 Minutes)

Follow `.claude/rules/ux_audit/protocol.md` Section 1–12:

1. **First Impressions** — Login screen + Dashboard (L1-L10, D1-D10)
2. **Search / Query** — Input behavior, results, multi-turn (S1-S10, R1-R10, FU1-FU5)
3. **Standalone Search** — If applicable (SR1-SR10)
4. **Navigation** — Click every link (N1-N10)
5. **Loading & Empty States** — Every screen that can be empty (E1-E10)
6. **Error Handling** — Trigger each error type gracefully (ER1-ER10)
7. **Mobile** — Chrome DevTools 375px, test all pages (M1-M10)
8. **Performance** — Lighthouse, console, network (P1-P10)
9. **Content & Copy** — No placeholders, consistent formatting (C1-C10)
10. **Acceptance Test Script** — Walk through the exact 10-step professor sequence
11. **Embarrassment Check** — Review Section 11 of ux_audit/protocol.md
12. **Report** — Fill the UI/UX Audit Report template

---

## Red Flags (Fix Immediately)

| Red Flag | What To Do |
|----------|-----------|
| Console shows red errors | Fix the source. Do not suppress. |
| "undefined" / "NaN" / "null" visible | Add null-checking on every data field before render |
| Raw JSON shown to user | Parse and format before rendering. Never show raw API response. |
| Spinner never stops | Add timeout + error state to every async call |
| No visual feedback on button click | Add loading state or immediate visual confirmation |
| Page title is "React App" | Set `<title>` dynamically per route |
| Horizontal scroll on desktop | Check overflow, max-width, and table layouts |
| Tier 1 and Tier 3 look identical | Verify RBAC is filtering data AND changing the UI |
| `alert()` anywhere in code | Replace with custom toast/modal component |
| Placeholder text ("Lorem ipsum", "TODO") | `grep -ri "TODO\|FIXME\|lorem" frontend/src/` → must be 0 |

---

## Evidence Required

Before claiming production-ready, produce:

1. **Screen recording** of the 10-step launch script (Section 10 of ux_audit/protocol.md)
2. **Lighthouse report** screenshot (Performance + Accessibility scores)
3. **Clean Console** screenshot (0 errors during normal use)
4. **Clean Network** screenshot (0 failed requests during a query)
5. **UI/UX Audit Report** filled using Section 12 template

Save all to `evidence/<date>/ui_ux_audit/`.

---

## The Rule

> A backend agent can claim DONE with passing tests. A frontend agent cannot claim DONE without walking through the launch script in a real browser. The professor sees UI. Not tests.

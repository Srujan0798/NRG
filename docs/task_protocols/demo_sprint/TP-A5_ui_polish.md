# TP-A5 — UI Polish: Warnings, Mobile, Empty States

**Owner:** FRONTEND  
**Estimated Duration:** 2–3 hours  
**Blockers:** None  
**Reference:** `.claude/rules/ux_audit_protocol.md` Sections 5, 7, 8, 9

---

## Objective

Clean up the frontend so it looks and feels like a ₹50L product. Fix ESLint warnings, verify mobile responsive, ensure empty states exist, clean console errors, and pass Lighthouse ≥ 70/70.

---

## Fortify Phase (Audit Current State)

1. Run ESLint and count warnings:
   ```bash
   cd frontend && npm run lint 2>&1 | tail -20
   ```

2. Run Lighthouse in Chrome DevTools:
   - Performance score: ___
   - Accessibility score: ___

3. Check for placeholder text:
   ```bash
   grep -ri "TODO\|FIXME\|lorem\|placeholder\|dummy\|test data" frontend/src/ 2>/dev/null | grep -v node_modules
   ```

4. Check browser tab titles:
   - Open login page → tab title should be meaningful
   - Open dashboard → tab title should be meaningful
   - Open query page → tab title should be meaningful

5. Open Chrome DevTools → Console during normal use:
   - Count red errors: ___
   - Count yellow warnings: ___

6. Test mobile at 375px (Chrome DevTools → iPhone SE):
   - Login page readable?
   - Dashboard readable?
   - Query box usable?
   - No horizontal scroll?

---

## Elevate Phase (Fix)

### Fix 1: ESLint Warnings (Target: 0 warnings)

Common warning categories:
- Unused imports → remove or use
- Missing hook dependencies → add to dependency array or suppress with comment + justification
- `any` types → replace with proper TypeScript types
- Console.log statements → remove or replace with proper logging

Run after each fix:
```bash
cd frontend && npm run lint
```

### Fix 2: Mobile Responsive (Target: usable at 375px)

- Tables must scroll horizontally, not break layout
- Buttons must be ≥44×44px touch target
- Text must be readable without zooming
- Search box must be full-width, not covered by keyboard
- Navigation must collapse to hamburger

### Fix 3: Empty States (Target: every empty widget has a message)

For every component that displays data:
- If data array is empty → show "No data found" message
- If chart has no data → show "No data available" placeholder
- If stats are 0 → show "0" explicitly

Example pattern:
```tsx
{data?.length > 0 ? (
  <DataTable data={data} />
) : (
  <EmptyState message="No researchers found for this query." />
)}
```

### Fix 4: Console Errors (Target: 0 red errors)

- Fix every red error that appears during normal use
- Common causes: undefined property access, missing key in list, CORS issues, failed API calls

### Fix 5: Browser Tab Titles

Set dynamic `<title>` per route:
```tsx
useEffect(() => {
  document.title = "Dashboard | NRG";
}, []);
```

### Fix 6: Lighthouse ≥ 70/70

- Performance: optimize images, lazy load, code split
- Accessibility: add alt text, proper labels, color contrast

---

## Immortalize Phase (Evidence)

1. ESLint report:
   ```
   evidence/2026-04-25/demo_sprint/A5_eslint_report.log
   ```
   Before/after warning count.

2. Lighthouse report:
   ```
   evidence/2026-04-25/demo_sprint/A5_lighthouse_report.json
   ```
   Screenshot of Lighthouse scores.

3. Mobile screenshots:
   ```
   evidence/2026-04-25/demo_sprint/A5_mobile_login.png
   evidence/2026-04-25/demo_sprint/A5_mobile_dashboard.png
   evidence/2026-04-25/demo_sprint/A5_mobile_query.png
   ```

4. Console screenshot:
   ```
   evidence/2026-04-25/demo_sprint/A5_clean_console.png
   ```
   Must show 0 red errors.

---

## Acceptance Criteria

- [ ] `npm run lint` shows ≤10 warnings (or 0 if achievable in time)
- [ ] Lighthouse Performance ≥ 70
- [ ] Lighthouse Accessibility ≥ 70
- [ ] Mobile (375px): login, dashboard, query all readable and usable
- [ ] 0 red console errors during normal use
- [ ] Every empty widget has a message (not blank)
- [ ] Browser tab titles are meaningful on every route
- [ ] `npm run build` passes with 0 errors

---

## Rollback Plan

If any fix breaks the build, revert that specific file. Keep `git stash` or branch backup before major changes.

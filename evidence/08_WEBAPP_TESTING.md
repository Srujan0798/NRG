# Webapp Testing Report — NRG Frontend

**Date:** 2026-04-25
**Status:** Frontend not running — tests cannot be executed locally

---

## Playwright Test Inventory

### `tests/` (Frontend integration tests)
| Test File | What It Tests | Status |
|-----------|--------------|--------|
| `login.spec.ts` | Login page + auth flow | ⚠️  Needs frontend running |
| `role-access.spec.ts` | Tier-based access (T1/T2/T3) | ⚠️  Needs frontend running |
| `consent.spec.ts` | DPDP consent banner + dialog | ⚠️  Needs frontend running |
| `audit-log.spec.ts` | Audit log panel | ⚠️  Needs frontend running |
| `graph-visualization.spec.ts` | GraphView component | ⚠️  Needs frontend running |
| `responsive.spec.ts` | Mobile responsiveness | ⚠️  Needs frontend running |

### `e2e/` (Full E2E tests)
| Test File | What It Tests | Status |
|-----------|--------------|--------|
| `basic.spec.ts` | Basic navigation | ⚠️  Needs frontend running |
| `login.spec.ts` | Login flow | ⚠️  Needs frontend running |
| `role-access.spec.ts` | Tier access enforcement | ⚠️  Needs frontend running |
| `researcher-dashboard.spec.ts` | Researcher dashboard | ⚠️  Needs frontend running |
| `government-dashboard.spec.ts` | Government dashboard | ⚠️  Needs frontend running |
| `industry-dashboard.spec.ts` | Industry dashboard | ⚠️  Needs frontend running |
| `full-journey.spec.ts` | Full researcher journey | ⚠️  Needs frontend running |
| `cross-cutting-security.spec.ts` | Security (XSS, CSRF) | ⚠️  Needs frontend running |
| `fixtures.ts` | Test fixtures (users) | ✅  Ready |

---

## Critical Gaps Found

### Gap 1: No DPDPConsentDialog Accessibility Tests
**Severity:** 🔴 High

The consent dialog has no Playwright tests for:
- Focus is moved to dialog on open
- Focus returns to trigger on close
- Escape key closes dialog
- Tab cycles within dialog (focus trap)
- aria-modal is set

**Test needed:**
```typescript
test('consent dialog focus management', async ({ page }) => {
  await page.goto('/');
  // Trigger consent dialog
  await page.click('[data-testid="manage-consent-btn"]');
  // Check focus moved to dialog
  await expect(page.locator('[role="dialog"]')).toBeFocused();
  // Check Tab cycles within dialog
  await page.keyboard.press('Tab');
  // ...verify focus stays in dialog
  // Check Escape closes
  await page.keyboard.press('Escape');
  await expect(page.locator('[role="dialog"]')).not.toBeVisible();
});
```

### Gap 2: No Keyboard Navigation Tests for GraphView
**Severity:** 🟡 Medium

The knowledge graph has no keyboard navigation tests — critical for accessibility compliance.

### Gap 3: No Accessibility (axe-core) Scan in Playwright
**Severity:** 🟡 Medium

No automated WCAG 2.1 AA scanning as part of the test suite.

**Add to `playwright.config.ts`:**
```typescript
import { defineConfig } from '@playwright/test';
import axe from 'axe-playwright';

export default defineConfig({
  // ...
});
// In test:
test('accessibility scan', async ({ page }) => {
  await page.goto('/researcher');
  const results = await new axe({ page }).analyze();
  expect(results.violations).toHaveLength(0);
});
```

---

## To Run Tests

```bash
# Start frontend
cd frontend && npm run dev &

# Run Playwright tests
npx playwright test

# Run with UI
npx playwright test --ui

# Run specific test
npx playwright test tests/consent.spec.ts

# Run accessibility scan only
npx playwright test --grep "a11y"
```

---

## Evidence That Tests Exist

```
frontend/tests/
  login.spec.ts
  role-access.spec.ts
  consent.spec.ts        ← Needs DPDPConsentDialog focus tests
  audit-log.spec.ts
  graph-visualization.spec.ts  ← Needs keyboard nav tests
  responsive.spec.ts

frontend/e2e/
  basic.spec.ts
  login.spec.ts
  role-access.spec.ts
  researcher-dashboard.spec.ts
  government-dashboard.spec.ts
  industry-dashboard.spec.ts
  full-journey.spec.ts
  cross-cutting-security.spec.ts ← Good: security tests exist
```

# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: persona.spec.ts >> Government Persona >> should login as government
- Location: tests/e2e/persona.spec.ts:28:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('[name="email"]')

```

# Page snapshot

```yaml
- generic [ref=e2]: "{\"detail\":\"Method Not Allowed\"}"
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Researcher Persona', () => {
  4  |   test('should login as researcher', async ({ page }) => {
  5  |     await page.goto('http://localhost:3000/login');
  6  |     await page.fill('[name="email"]', 'researcher@example.com');
  7  |     await page.fill('[name="password"]', 'researcher123');
  8  |     await page.click('[type="submit"]');
  9  |     await expect(page).toHaveURL(/dashboard/);
  10 |   });
  11 | 
  12 |   test('should query and see citations', async ({ page }) => {
  13 |     await page.goto('http://localhost:3000');
  14 |     await page.fill('[name="query"]', 'robotics researchers');
  15 |     await page.click('[type="submit"]');
  16 |     await expect(page.locator('.citation')).toBeVisible();
  17 |   });
  18 | 
  19 |   test('should access all data tiers', async ({ page }) => {
  20 |     await page.goto('http://localhost:3000');
  21 |     await page.fill('[name="query"]', 'list all researchers');
  22 |     await page.click('[type="submit"]');
  23 |     await expect(page.locator('.result-row')).toHaveCount({ gte: 10 });
  24 |   });
  25 | });
  26 | 
  27 | test.describe('Government Persona', () => {
  28 |   test('should login as government', async ({ page }) => {
  29 |     await page.goto('http://localhost:3000/login');
> 30 |     await page.fill('[name="email"]', 'gov@example.com');
     |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
  31 |     await page.fill('[name="password"]', 'gov123');
  32 |     await page.click('[type="submit"]');
  33 |     await expect(page).toHaveURL(/dashboard/);
  34 |   });
  35 | 
  36 |   test('should see aggregated data only', async ({ page }) => {
  37 |     await page.goto('http://localhost:3000');
  38 |     await page.fill('[name="query"]', 'funding by state');
  39 |     await page.click('[type="submit"]');
  40 |     await expect(page.locator('.result-row')).toHaveCount({ lte: 20 });
  41 |   });
  42 | 
  43 |   test('should be denied PII access', async ({ page }) => {
  44 |     await page.goto('http://localhost:3000');
  45 |     await page.fill('[name="query"]', 'researcher emails');
  46 |     await page.click('[type="submit"]');
  47 |     await expect(page.locator('.denial')).toBeVisible();
  48 |   });
  49 | });
  50 | 
  51 | test.describe('Industry Persona', () => {
  52 |   test('should login as industry', async ({ page }) => {
  53 |     await page.goto('http://localhost:3000/login');
  54 |     await page.fill('[name="email"]', 'industry@example.com');
  55 |     await page.fill('[name="password"]', 'ind123');
  56 |     await page.click('[type="submit"]');
  57 |     await expect(page).toHaveURL(/dashboard/);
  58 |   });
  59 | 
  60 |   test('should see public metadata only', async ({ page }) => {
  61 |     await page.goto('http://localhost:3000');
  62 |     await page.fill('[name="query"]', 'publications');
  63 |     await page.click('[type="submit"]');
  64 |     await expect(page.locator('.result-row')).toHaveCount({ lte: 10 });
  65 |   });
  66 | 
  67 |   test('should be denied funding details', async ({ page }) => {
  68 |     await page.goto('http://localhost:3000');
  69 |     await page.fill('[name="query"]', 'grant amounts');
  70 |     await page.click('[type="submit"]');
  71 |     await expect(page.locator('.denial')).toBeVisible();
  72 |   });
  73 | });
  74 | 
  75 | test.describe('Error States', () => {
  76 |   test('should show empty state', async ({ page }) => {
  77 |     await page.goto('http://localhost:3000');
  78 |     await page.fill('[name="query"]', '');
  79 |     await page.click('[type="submit"]');
  80 |     await expect(page.locator('.empty-state')).toBeVisible();
  81 |   });
  82 | 
  83 |   test('should show error state', async ({ page }) => {
  84 |     await page.goto('http://localhost:3000');
  85 |     await page.fill('[name="query"]', 'INVALID_QUERY');
  86 |     await page.click('[type="submit"]');
  87 |     await expect(page.locator('.error-state')).toBeVisible();
  88 |   });
  89 | });
```
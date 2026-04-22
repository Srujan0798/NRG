# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: persona.spec.ts >> Government Persona >> should be denied PII access
- Location: tests/e2e/persona.spec.ts:43:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('[name="query"]')

```

# Page snapshot

```yaml
- generic [ref=e4]:
  - generic [ref=e5]:
    - paragraph [ref=e6]: National Research Graph
    - heading "Kong-backed access for researchers, ministries, and industry partners." [level=1] [ref=e7]
    - paragraph [ref=e8]: "Each persona now signs in against the real JWT API, queries through Kong on port `8000`, and sees data scoped to its assigned access tier."
    - generic [ref=e9]:
      - button "Select Researcher persona" [ref=e10] [cursor=pointer]:
        - generic [ref=e11]:
          - img [ref=e12]
          - generic [ref=e15]: Researcher
        - generic [ref=e16]:
          - paragraph [ref=e17]: researcher_user
          - paragraph [ref=e18]: researcher-pass
      - button "Select Government persona" [ref=e19] [cursor=pointer]:
        - generic [ref=e20]:
          - img [ref=e21]
          - generic [ref=e23]: Government
        - generic [ref=e24]:
          - paragraph [ref=e25]: gov_user
          - paragraph [ref=e26]: government-pass
      - button "Select Industry persona" [ref=e27] [cursor=pointer]:
        - generic [ref=e28]:
          - img [ref=e29]
          - generic [ref=e32]: Industry
        - generic [ref=e33]:
          - paragraph [ref=e34]: industry_user
          - paragraph [ref=e35]: industry-pass
  - generic [ref=e36]:
    - generic [ref=e37]:
      - img [ref=e39]
      - generic [ref=e42]:
        - heading "Sign in" [level=2] [ref=e43]
        - paragraph [ref=e44]: Use a seeded persona account to enter the platform.
    - generic [ref=e45]:
      - generic [ref=e46]:
        - generic [ref=e47]: Username
        - textbox "Username" [ref=e48]: researcher_user
      - generic [ref=e49]:
        - generic [ref=e50]: Password
        - textbox "Password" [ref=e51]: researcher-pass
      - button "Continue as Researcher" [ref=e52] [cursor=pointer]
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
  30 |     await page.fill('[name="email"]', 'gov@example.com');
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
> 45 |     await page.fill('[name="query"]', 'researcher emails');
     |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
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
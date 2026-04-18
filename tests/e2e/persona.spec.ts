import { test, expect } from '@playwright/test';

test.describe('Researcher Persona', () => {
  test('should login as researcher', async ({ page }) => {
    await page.goto('http://localhost:3000/login');
    await page.fill('[name="email"]', 'researcher@example.com');
    await page.fill('[name="password"]', 'researcher123');
    await page.click('[type="submit"]');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('should query and see citations', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('[name="query"]', 'robotics researchers');
    await page.click('[type="submit"]');
    await expect(page.locator('.citation')).toBeVisible();
  });

  test('should access all data tiers', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('[name="query"]', 'list all researchers');
    await page.click('[type="submit"]');
    await expect(page.locator('.result-row')).toHaveCount({ gte: 10 });
  });
});

test.describe('Government Persona', () => {
  test('should login as government', async ({ page }) => {
    await page.goto('http://localhost:3000/login');
    await page.fill('[name="email"]', 'gov@example.com');
    await page.fill('[name="password"]', 'gov123');
    await page.click('[type="submit"]');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('should see aggregated data only', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('[name="query"]', 'funding by state');
    await page.click('[type="submit"]');
    await expect(page.locator('.result-row')).toHaveCount({ lte: 20 });
  });

  test('should be denied PII access', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('[name="query"]', 'researcher emails');
    await page.click('[type="submit"]');
    await expect(page.locator('.denial')).toBeVisible();
  });
});

test.describe('Industry Persona', () => {
  test('should login as industry', async ({ page }) => {
    await page.goto('http://localhost:3000/login');
    await page.fill('[name="email"]', 'industry@example.com');
    await page.fill('[name="password"]', 'ind123');
    await page.click('[type="submit"]');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('should see public metadata only', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('[name="query"]', 'publications');
    await page.click('[type="submit"]');
    await expect(page.locator('.result-row')).toHaveCount({ lte: 10 });
  });

  test('should be denied funding details', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('[name="query"]', 'grant amounts');
    await page.click('[type="submit"]');
    await expect(page.locator('.denial')).toBeVisible();
  });
});

test.describe('Error States', () => {
  test('should show empty state', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('[name="query"]', '');
    await page.click('[type="submit"]');
    await expect(page.locator('.empty-state')).toBeVisible();
  });

  test('should show error state', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('[name="query"]', 'INVALID_QUERY');
    await page.click('[type="submit"]');
    await expect(page.locator('.error-state')).toBeVisible();
  });
});
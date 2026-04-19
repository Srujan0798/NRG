import { test, expect } from '@playwright/test';

test.describe('Natural Language Query Flows', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('input[type="text"]', 'researcher_user');
    await page.fill('input[type="password"]', 'researcher-pass');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Researcher Dashboard')).toBeVisible();
  });

  test('Query: Find robotics researchers', async ({ page }) => {
    await page.fill('input[placeholder="Ask about research..."]', 
      'find robotics researchers in Gujarat');
    await page.click('button:has-text("Search")');
    await expect(page.locator('text=researchers')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="citation"]')).toBeVisible();
  });

  test('Query: Publications by year', async ({ page }) => {
    await page.fill('input[placeholder="Ask about research..."]', 
      'publications from 2023');
    await page.click('button:has-text("Search")');
    await expect(page.locator('text=2023')).toBeVisible({ timeout: 10000 });
  });

  test('Query: Funding records', async ({ page }) => {
    await page.fill('input[placeholder="Ask about research..."]', 
      'DST grants for IIT Bombay');
    await page.click('button:has-text("Search")');
    await expect(page.locator('text=funding')).toBeVisible({ timeout: 10000 });
  });

  test('Query with graph view', async ({ page }) => {
    await page.fill('input[placeholder="Ask about research..."]', 
      'machine learning researchers');
    await page.click('button:has-text("Visualize")');
    await expect(page.locator('canvas')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('.graph-node')).toHaveCount({ min: 5 });
  });
});

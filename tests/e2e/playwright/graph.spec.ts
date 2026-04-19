import { test, expect } from '@playwright/test';

test.describe('Graph View Flows', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('input[type="text"]', 'researcher_user');
    await page.fill('input[type="password"]', 'researcher-pass');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Researcher Dashboard')).toBeVisible();
  });

  test('Graph renders for machine learning topic', async ({ page }) => {
    await page.fill('input[placeholder="Enter topic..."]', 'machine learning');
    await page.click('button:has-text("Visualize")');
    await expect(page.locator('canvas')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=machine learning')).toBeVisible();
  });

  test('Graph renders for renewable energy topic', async ({ page }) => {
    await page.fill('input[placeholder="Enter topic..."]', 'renewable energy');
    await page.click('button:has-text("Visualize")');
    await expect(page.locator('canvas')).toBeVisible({ timeout: 10000 });
  });

  test('Node click filters answer panel', async ({ page }) => {
    await page.fill('input[placeholder="Enter topic..."]', 'AI');
    await page.click('button:has-text("Visualize")');
    await page.locator('canvas').click({ position: { x: 400, y: 300 } });
    await expect(page.locator('.node-details')).toBeVisible();
  });
});

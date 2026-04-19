import { test, expect } from '@playwright/test';

test.describe('Login Flows', () => {
  test('Researcher can login', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('input[type="text"]', 'researcher_user');
    await page.fill('input[type="password"]', 'researcher-pass');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Researcher Dashboard')).toBeVisible();
  });

  test('Government can login', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.click('text=Government');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Government Dashboard')).toBeVisible();
  });

  test('Industry can login', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.click('text=Industry');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Industry Dashboard')).toBeVisible();
  });
});

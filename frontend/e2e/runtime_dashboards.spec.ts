import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:4173';

async function login(page, username: string, password: string) {
  await page.goto(`${FRONTEND_URL}/login`);
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL(/.*dashboard.*/, { timeout: 10000 });
}

async function runQuery(page, query: string) {
  await page.fill('input[placeholder*="Ask"], textarea[placeholder*="Ask"], [data-testid="query-input"]', query);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(8000);
}

test.describe('NRG Dashboard Runtime', () => {
  test('Researcher persona — login + query', async ({ page }) => {
    await login(page, 'researcher_user', 'researcher-pass');
    await expect(page.locator('text=Researcher').or(page.locator('text=Dashboard'))).toBeVisible();
    await runQuery(page, 'machine learning researchers in Gujarat');
    const responseText = await page.locator('body').textContent();
    expect(responseText).toContain('IIT');
  });

  test('Government persona — login + query', async ({ page }) => {
    await login(page, 'gov_user', 'government-pass');
    await expect(page.locator('text=Government').or(page.locator('text=Dashboard'))).toBeVisible();
    await runQuery(page, 'total funding by state');
    const responseText = await page.locator('body').textContent();
    expect(responseText?.length).toBeGreaterThan(50);
  });

  test('Industry persona — login + query', async ({ page }) => {
    await login(page, 'industry_user', 'industry-pass');
    await expect(page.locator('text=Industry').or(page.locator('text=Dashboard'))).toBeVisible();
    await runQuery(page, 'top research areas');
    const responseText = await page.locator('body').textContent();
    expect(responseText?.length).toBeGreaterThan(50);
  });
});

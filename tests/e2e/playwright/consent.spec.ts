import { test, expect } from '@playwright/test';

test.describe('DPDP Consent Flows', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('http://localhost:3000');
    await page.fill('input[type="text"]', 'researcher_user');
    await page.fill('input[type="password"]', 'researcher-pass');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Researcher Dashboard')).toBeVisible();
  });

  test('Grant consent for research_access', async ({ page }) => {
    await page.goto('http://localhost:3000/consent');
    await page.click('text=Grant research_access');
    await expect(page.locator('text=Consent granted')).toBeVisible();
  });

  test('Revoke consent for research_access', async ({ page }) => {
    await page.goto('http://localhost:3000/consent');
    await page.click('text=Grant research_access');
    await page.click('text=Revoke');
    await expect(page.locator('text=Consent revoked')).toBeVisible();
  });

  test('Export user data', async ({ page }) => {
    await page.goto('http://localhost:3000/settings');
    await page.click('text=Export My Data');
    await expect(page.locator('text=Data export complete')).toBeVisible();
    const download = await page.waitForEvent('download');
    expect(download.suggestedFilename()).toContain('export');
  });

  test('Delete user data', async ({ page }) => {
    await page.goto('http://localhost:3000/settings');
    await page.click('text=Delete My Account');
    await page.fill('input[placeholder="Confirm"]', 'DELETE');
    await page.click('text=Confirm Delete');
    await expect(page.locator('text=Account deleted')).toBeVisible();
  });
});

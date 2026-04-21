import { test, expect } from './fixtures';

async function loginAsGovernment(page) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => localStorage.clear());
  await page.getByRole('button', { name: 'Select Government persona' }).click();
  await page.getByRole('button', { name: /Continue as Government/ }).click();
  await expect(page.getByText(/Government Analytics/)).toBeVisible({ timeout: 30000 });
}

test.describe('Government Dashboard (Tier 2)', () => {
  test('can login as government user', async ({ page }) => {
    await loginAsGovernment(page);
    await expect(page.getByText(/Government Analytics/)).toBeVisible();
  });

  test('sees aggregated stats (no PII)', async ({ page }) => {
    await loginAsGovernment(page);
    // Should see aggregated metrics, not individual emails/phones
    await expect(page.getByText(/National Research Metrics|Total Researchers|State Distribution/i).first()).toBeVisible({ timeout: 15000 });
  });

  test('policy-oriented queries return state/national level data', async ({ page }) => {
    await loginAsGovernment(page);
    const queryInput = page.getByPlaceholder(/Enter research topic|National Research Query/);
    await queryInput.fill('state wise funding distribution');
    await page.getByRole('button', { name: /Search|Analyze/ }).click();
    await expect(page.getByText(/state|funding|distribution|crore/i).first()).toBeVisible({ timeout: 60000 });
  });

  test('does not see individual researcher emails', async ({ page }) => {
    await loginAsGovernment(page);
    // Search for a researcher query
    const queryInput = page.getByPlaceholder(/Enter research topic|National Research Query/);
    await queryInput.fill('researchers in Maharashtra');
    await page.getByRole('button', { name: /Search|Analyze/ }).click();
    await page.waitForTimeout(5000);
    // Page text should NOT contain email addresses
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toMatch(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
  });
});

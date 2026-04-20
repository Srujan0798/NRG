import { test, expect } from './fixtures';

test.describe('DLP and Security Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.evaluate(() => localStorage.clear());
  });

  test('PII/DLP violation shows safe error message', async ({ page }) => {
    test.setTimeout(60000);
    await page.getByRole('button', { name: 'Select Researcher persona' }).click();
    await page.getByRole('button', { name: /Continue as Researcher/ }).click();
    await expect(page.getByText(/Researcher Workspace/)).toBeVisible({ timeout: 30000 });

    const queryInput = page.getByPlaceholder('Enter research topic, author, or DOI...');
    await queryInput.fill('Researcher with Aadhar 1234-5678-9012');
    await page.getByRole('button', { name: /Search/ }).click();
    // Frontend should surface security message; backend may block or process
    await expect(page.getByText(/Security Message|🛡️|blocked|PII/i)).toBeVisible({ timeout: 30000 });
  });
});

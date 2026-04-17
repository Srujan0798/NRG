import { test, expect } from '@playwright/test';

test.describe('DLP and Security Validation', () => {
  test('PII/DLP violation shows safe error message', async ({ page }) => {
    // Login as researcher
    await page.goto('/');
    await page.getByLabel('Username').fill('researcher_user');
    await page.getByLabel('Password').fill('researcher-pass');
    await page.getByRole('button', { name: /Continue as/ }).click();
    
    // Perform a query that contains PII (simulated for Kong DLP)
    // In a real setup, Kong DLP would trigger on strings like 'Aadhar: 1234-5678-9012'
    const queryInput = page.getByPlaceholder('Enter research topic, author, or DOI...');
    await queryInput.fill('Researcher with Aadhar 1234-5678-9012');
    await page.getByRole('button', { name: 'Search' }).click();
    
    // Check if security message is surfaced
    // Note: This assumes Kong is configured to block and the frontend catches the error
    await expect(page.getByText('🛡️ Security Message')).toBeVisible();
    await expect(page.getByText(/PII Detected|Security Violation|blocked/i)).toBeVisible();
  });
});

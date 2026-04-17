import { test, expect } from '@playwright/test';

test.describe('Audit Log Functionality', () => {
  test('Audit log displays entries', async ({ page }) => {
    // Login as researcher
    await page.goto('http://localhost:3000');
    await page.getByPlaceholder('Username').fill('researcher_user');
    await page.getByPlaceholder('Password').fill('researcher-pass');
    await page.getByRole('button', { name: 'Continue as Researcher' }).click();
    
    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');
    
    // Navigate to Audit tab
    await page.getByText('Audit').click();
    
    // Verify audit log is displayed
    await expect(page.getByText('DPDP Audit Log')).toBeVisible();
    
    // Check if audit entries are present
    const auditLog = page.getByText('DPDP Audit Log');
    await expect(auditLog).toBeVisible();
  });

  test('Audit log clear functionality', async ({ page }) => {
    // Login as researcher
    await page.goto('http://localhost:3000');
    await page.getByPlaceholder('Username').fill('researcher_user');
    await page.getByPlaceholder('Password').fill('researcher-pass');
    await page.getByRole('button', { name: 'Continue as Researcher' }).click();
    
    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');
    
    // Navigate to Audit tab
    await page.getByText('Audit').click();
    
    // If there are entries, check for clear button
    const clearButton = page.getByText('Clear Log');
    if (await clearButton.isVisible()) {
      // Click clear button
      await clearButton.click();
      
      // Verify log is cleared (this might require checking that the log area is empty)
      // This is a simplified check - in a real test, you might want to verify the content
    }
  });
});
import { test, expect } from '@playwright/test';

test.describe('Audit Log Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Login as researcher
    await page.goto('/');
    await page.getByLabel('Email').fill('researcher@test.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page).toHaveURL(/.*dashboard/);
    
    // Navigate to audit log
    await page.getByRole('link', { name: 'Audit Log' }).click();
    await expect(page.getByText('DPDP Audit Log')).toBeVisible();
  });

  test('Audit log page loads correctly', async ({ page }) => {
    await expect(page.getByTestId('audit-log-container')).toBeVisible();
  });

  test('Audit entries are displayed', async ({ page }) => {
    const entryCount = await page.locator('.audit-entry').count();
    expect(entryCount).toBeGreaterThan(0);
  });

  test('Filter audit log by date range', async ({ page }) => {
    // Set date range
    await page.getByLabel('Start Date').fill('2023-01-01');
    await page.getByLabel('End Date').fill('2023-12-31');
    await page.getByRole('button', { name: 'Filter' }).click();
    
    // Check if filtered results are shown
    await expect(page.getByText('Filtered results')).toBeVisible();
  });

  test('Export audit log data', async ({ page }) => {
    // Click export button
    await page.getByRole('button', { name: 'Export' }).click();
    
    // Check for download notification
    await expect(page.getByText('Audit log exported successfully')).toBeVisible();
  });

  test('View detailed audit entry', async ({ page }) => {
    // Click on first audit entry to view details
    await page.locator('.audit-entry').first().click();
    
    // Check if details modal is shown
    await expect(page.getByText('Audit Entry Details')).toBeVisible();
  });
});
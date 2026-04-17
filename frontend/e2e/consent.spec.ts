import { test, expect } from '@playwright/test';

test.describe('DPDP Consent Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Login as researcher
    await page.goto('/');
    await page.getByLabel('Email').fill('researcher@test.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('User can view consent management page', async ({ page }) => {
    await page.getByRole('link', { name: 'Consent Management' }).click();
    await expect(page.getByText('Consent Management')).toBeVisible();
  });

  test('User can open consent dialog', async ({ page }) => {
    await page.getByRole('link', { name: 'Consent Management' }).click();
    await page.getByRole('button', { name: 'Manage Consent' }).click();
    await expect(page.getByText('DPDP Consent Dialog')).toBeVisible();
  });

  test('User can accept consent terms', async ({ page }) => {
    await page.getByRole('link', { name: 'Consent Management' }).click();
    await page.getByRole('button', { name: 'Manage Consent' }).click();
    await page.getByRole('button', { name: 'Accept' }).click();
    await expect(page.getByText('Consent updated successfully')).toBeVisible();
  });

  test('User can withdraw consent', async ({ page }) => {
    await page.getByRole('link', { name: 'Consent Management' }).click();
    await page.getByRole('button', { name: 'Withdraw Consent' }).click();
    await expect(page.getByText('Consent withdrawn')).toBeVisible();
  });

  test('User sees error with invalid consent action', async ({ page }) => {
    await page.getByRole('link', { name: 'Consent Management' }).click();
    
    // Try to perform an invalid action
    await page.route('**/api/consent/**', route => {
      route.fulfill({
        status: 400,
        body: JSON.stringify({ error: 'Invalid consent action' })
      });
    });
    
    await page.getByRole('button', { name: 'Invalid Action' }).click();
    await expect(page.getByText('Invalid consent action')).toBeVisible();
  });
});
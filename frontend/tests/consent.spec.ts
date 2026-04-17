import { test, expect } from '@playwright/test';

test.describe('DPDP Consent Functionality', () => {
  test('Researcher can grant DPDP consent', async ({ page }) => {
    // Login as researcher
    await page.goto('http://localhost:3000');
    await page.getByPlaceholder('Username').fill('researcher_user');
    await page.getByPlaceholder('Password').fill('researcher-pass');
    await page.getByRole('button', { name: 'Continue as Researcher' }).click();
    
    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');
    
    // Navigate to DPDP tab
    await page.getByText('DPDP').click();
    
    // Click grant consent button
    await page.getByText('Grant New Consent for Data Access').click();
    
    // In the consent dialog, click approve
    await page.getByText('I approve').click();
    
    // Verify consent was granted
    await expect(page.getByText('Consent Status')).toBeVisible();
    await expect(page.getByText('Your data access is managed per India\'s DPDP Act 2023')).toBeVisible();
  });

  test('Researcher can withdraw DPDP consent', async ({ page }) => {
    // Login as researcher
    await page.goto('http://localhost:3000');
    await page.getByPlaceholder('Username').fill('researcher_user');
    await page.getByPlaceholder('Password').fill('researcher-pass');
    await page.getByRole('button', { name: 'Continue as Researcher' }).click();
    
    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');
    
    // Navigate to DPDP tab
    await page.getByText('DPDP').click();
    
    // Click grant consent button
    await page.getByText('Grant New Consent for Data Access').click();
    
    // In the consent dialog, click deny
    await page.getByText('I do not approve').click();
    
    // Verify consent was not granted
    await expect(page.getByText('Consent Status')).toBeVisible();
    await expect(page.getByText('Your data access is managed per India\'s DPDP Act 2023')).toBeVisible();
  });
});
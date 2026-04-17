import { test, expect } from '@playwright/test';

// Test all user roles can login
test.describe('Login Functionality', () => {
  test('Researcher can login', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Login as researcher
    await page.getByPlaceholder('Username').fill('researcher_user');
    await page.getByPlaceholder('Password').fill('researcher-pass');
    await page.getByRole('button', { name: 'Continue as Researcher' }).click();
    
    // Verify login success
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.getByText('National Research Intelligence Platform')).toBeVisible();
  });

  test('Government can login', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Login as government
    await page.getByPlaceholder('Username').fill('gov_user');
    await page.getByPlaceholder('Password').fill('government-pass');
    await page.getByRole('button', { name: 'Continue as Government' }).click();
    
    // Verify login success
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.getByText('Government Analytics')).toBeVisible();
  });

  test('Industry can login', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Login as industry
    await page.getByPlaceholder('Username').fill('industry_user');
    await page.getByPlaceholder('Password').fill('industry-pass');
    await page.getByRole('button', { name: 'Continue as Industry' }).click();
    
    // Verify login success
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.getByText('Industry Innovation')).toBeVisible();
  });
});
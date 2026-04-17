import { test, expect } from '@playwright/test';

test.describe('Login Functionality', () => {
  test('should login as researcher', async ({ page }) => {
    await page.goto('/');
    
    // Fill in login form with researcher credentials
    await page.getByPlaceholder('Username').fill('researcher_user');
    await page.getByPlaceholder('Password').fill('researcher-pass');
    
    // Click the login button
    await page.getByRole('button', { name: 'Continue as Researcher' }).click();
    
    // Check if we're redirected to the dashboard
    await page.waitForURL(/.*dashboard/);
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/');
    
    // Fill in login form with invalid credentials
    await page.getByPlaceholder('Username').fill('invalid_user');
    await page.getByPlaceholder('Password').fill('wrong_password');
    
    // Click the login button
    await page.getByRole('button', { name: 'Continue as Researcher' }).click();
    
    // Check that we stay on the login page
    await expect(page).toHaveURL('/');
  });
});
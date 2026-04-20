import { test, expect } from './fixtures';

test.describe('Login Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.evaluate(() => localStorage.clear());
  });

  test('should login as researcher', async ({ page }) => {
    await page.getByRole('button', { name: 'Select Researcher persona' }).click();
    await page.getByRole('button', { name: /Continue as Researcher/ }).click();
    await expect(page.getByText(/Researcher Workspace/)).toBeVisible({ timeout: 30000 });
  });

  test('should login as government', async ({ page }) => {
    await page.getByRole('button', { name: 'Select Government persona' }).click();
    await page.getByRole('button', { name: /Continue as Government/ }).click();
    await expect(page.getByText(/Government Analytics/)).toBeVisible({ timeout: 30000 });
  });

  test('should login as industry', async ({ page }) => {
    await page.getByRole('button', { name: 'Select Industry persona' }).click();
    await page.getByRole('button', { name: /Continue as Industry/ }).click();
    await expect(page.getByText(/Industry Innovation/)).toBeVisible({ timeout: 30000 });
  });
});

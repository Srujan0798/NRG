import { test, expect } from './fixtures';

test('should load page', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  expect(page.isClosed()).toBeFalsy();
  await expect(page.getByText(/National Research Graph/)).toBeVisible();
});

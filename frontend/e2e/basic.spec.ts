import { test, expect } from '@playwright/test';

test('should load page', async ({ page }) => {
  await page.goto('/');
  // Simple test to check if page loads without error
  expect(page.isClosed()).toBeFalsy();
});
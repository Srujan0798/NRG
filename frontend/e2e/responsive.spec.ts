import { test, expect } from '@playwright/test';

test.describe('Responsive Design Tests', () => {
  test('Desktop layout', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    
    // Check desktop-specific elements
    await expect(page.getByTestId('desktop-layout')).toBeVisible();
  });

  test('Tablet layout', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    
    // Check tablet-specific elements
    await expect(page.getByTestId('tablet-layout')).toBeVisible();
  });

  test('Mobile layout', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // Check mobile-specific elements
    await expect(page.getByTestId('mobile-layout')).toBeVisible();
  });

  test('Navigation adapts to screen size', async ({ page }) => {
    // Test mobile navigation
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // Mobile menu should be visible
    await expect(page.getByRole('button', { name: 'Menu' })).toBeVisible();
  });

  test('Form elements adapt to screen size', async ({ page }) => {
    // Test form responsiveness
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/login');
    
    // Form should adapt to mobile view
    await expect(page.getByTestId('mobile-form')).toBeVisible();
  });
});
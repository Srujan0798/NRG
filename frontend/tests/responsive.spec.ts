import { test, expect } from '@playwright/test';

test.describe('Responsive Design', () => {
  test('Application is responsive on different screen sizes', async ({ page }) => {
    // Test on desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('http://localhost:3000');
    
    // Login as researcher
    await page.getByPlaceholder('Username').fill('researcher_user');
    await page.getByPlaceholder('Password').fill('researcher-pass');
    await page.getByRole('button', { name: 'Continue as Researcher' }).click();
    
    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');
    
    // Verify layout elements are present
    await expect(page.getByText('National Research Intelligence Platform')).toBeVisible();
    
    // Test on tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Verify layout elements are still present
    await expect(page.getByText('National Research Intelligence Platform')).toBeVisible();
    
    // Test on mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Verify layout elements are still present
    await expect(page.getByText('National Research Intelligence Platform')).toBeVisible();
  });
});
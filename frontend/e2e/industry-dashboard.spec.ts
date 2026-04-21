import { test, expect } from './fixtures';

async function loginAsIndustry(page) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => localStorage.clear());
  await page.getByRole('button', { name: 'Select Industry persona' }).click();
  await page.getByRole('button', { name: /Continue as Industry/ }).click();
  await expect(page.getByText(/Industry Innovation/)).toBeVisible({ timeout: 30000 });
}

test.describe('Industry Dashboard (Tier 3)', () => {
  test('can login as industry user', async ({ page }) => {
    await loginAsIndustry(page);
    await expect(page.getByText(/Industry Innovation/)).toBeVisible();
  });

  test('sees anonymized data only', async ({ page }) => {
    await loginAsIndustry(page);
    await expect(page.getByText(/Research Partner Discovery/)).toBeVisible({ timeout: 15000 });
    // Should see research areas and names but not contact details
    await expect(page.getByText(/research area|expertise|domain/i).first()).toBeVisible({ timeout: 15000 });
  });

  test('cannot access researcher emails or phone', async ({ page }) => {
    await loginAsIndustry(page);
    const queryInput = page.getByPlaceholder(/Enter research topic|Research Partner Discovery/);
    await queryInput.fill('robotics researchers');
    await page.getByRole('button', { name: /Search|Discover/ }).click();
    await page.waitForTimeout(5000);
    const bodyText = await page.locator('body').textContent();
    // No email patterns
    expect(bodyText).not.toMatch(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
    // No phone patterns
    expect(bodyText).not.toMatch(/\+?\d[\d\s().-]{8,}\d/);
  });

  test('cannot access tier 1 routes or data', async ({ page }) => {
    await loginAsIndustry(page);
    await expect(page.getByText(/Knowledge Graph Query/)).not.toBeVisible();
    await expect(page.getByText(/Government Analytics/)).not.toBeVisible();
  });
});

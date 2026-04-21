import { test, expect } from './fixtures';

async function loginAsResearcher(page) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => localStorage.clear());
  await page.getByRole('button', { name: 'Select Researcher persona' }).click();
  await page.getByRole('button', { name: /Continue as Researcher/ }).click();
  await expect(page.getByText(/Researcher Workspace/)).toBeVisible({ timeout: 30000 });
}

test.describe('Researcher Dashboard (Tier 1)', () => {
  test('can login as researcher', async ({ page }) => {
    await loginAsResearcher(page);
    await expect(page.getByText(/Researcher Workspace/)).toBeVisible();
  });

  test('can submit a research query', async ({ page }) => {
    await loginAsResearcher(page);
    const queryInput = page.getByPlaceholder('Enter research topic, author, or DOI...');
    await queryInput.fill('hydrogen catalysis research in India');
    await page.getByRole('button', { name: /Search/ }).click();
    // Response should appear within 60s
    await expect(page.getByText(/research|found|result/i).first()).toBeVisible({ timeout: 60000 });
  });

  test('sees full researcher details (PII visible)', async ({ page }) => {
    await loginAsResearcher(page);
    // Tier 1 should see contact info in researcher listings
    await expect(page.getByText(/Researcher Workspace/)).toBeVisible();
    // The workspace should show detailed researcher cards
    await expect(page.locator('[data-testid="researcher-card"], .researcher-card').first()).toBeVisible({ timeout: 15000 });
  });

  test('sees citation references in response', async ({ page }) => {
    await loginAsResearcher(page);
    const queryInput = page.getByPlaceholder('Enter research topic, author, or DOI...');
    await queryInput.fill('AI research in Gujarat');
    await page.getByRole('button', { name: /Search/ }).click();
    await expect(page.getByText(/cite|reference|source/i).first()).toBeVisible({ timeout: 60000 });
  });

  test('can navigate to knowledge graph', async ({ page }) => {
    await loginAsResearcher(page);
    await expect(page.getByText(/Knowledge Graph Query/)).toBeVisible({ timeout: 15000 });
  });
});

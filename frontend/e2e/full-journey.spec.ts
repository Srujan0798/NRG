import { test, expect } from './fixtures';

const mockQueryResponse = {
  query_id: 'test-query-1',
  response: '**Researchers:** 200\n\n**Publications:** 500',
  status: 'success',
  tier: 1,
  verification_status: true,
  citations: [],
  provenance: { synth: 'sql_formatter', cloud_synthesis_used: false },
  conversation_history: [],
};

test.describe('Full User Journeys', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.evaluate(() => localStorage.clear());
  });

  test('researcher: login → dashboard → query → results', async ({ page }) => {
    test.setTimeout(60000);
    // Mock the query endpoint to return instantly
    await page.route('/query', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockQueryResponse) });
    });

    await page.getByRole('button', { name: 'Select Researcher persona' }).click();
    await page.getByRole('button', { name: /Continue as Researcher/ }).click();
    await expect(page.getByText(/Researcher Workspace/)).toBeVisible({ timeout: 30000 });

    const queryInput = page.getByPlaceholder('Enter research topic, author, or DOI...');
    await expect(queryInput).toBeVisible({ timeout: 15000 });
    await queryInput.fill('machine learning');
    await page.getByRole('button', { name: /Search/ }).click();

    await expect(page.getByText(/Researchers.*200|Publications.*500/)).toBeVisible({ timeout: 15000 });
  });

  test('government: login → dashboard → query → results', async ({ page }) => {
    test.setTimeout(60000);
    await page.route('/query', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockQueryResponse, tier: 2 }) });
    });

    await page.getByRole('button', { name: 'Select Government persona' }).click();
    await page.getByRole('button', { name: /Continue as Government/ }).click();
    await expect(page.getByText(/Government Analytics/)).toBeVisible({ timeout: 30000 });

    const queryInput = page.getByPlaceholder(/Enter query/);
    await expect(queryInput).toBeVisible({ timeout: 15000 });
    await queryInput.fill('Gujarat research trends');
    await page.getByRole('button', { name: /Query/ }).click();

    await expect(page.getByText(/Researchers.*200|Publications.*500/)).toBeVisible({ timeout: 15000 });
  });

  test('industry: login → dashboard → query → results', async ({ page }) => {
    test.setTimeout(60000);
    await page.route('/query', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockQueryResponse, tier: 3 }) });
    });

    await page.getByRole('button', { name: 'Select Industry persona' }).click();
    await page.getByRole('button', { name: /Continue as Industry/ }).click();
    await expect(page.getByText(/Industry Innovation/)).toBeVisible({ timeout: 30000 });

    const queryInput = page.getByPlaceholder(/Enter query/);
    await expect(queryInput).toBeVisible({ timeout: 15000 });
    await queryInput.fill('AI researchers in Maharashtra');
    await page.getByRole('button', { name: /Discover/ }).click();

    await expect(page.getByText(/Researchers.*200|Publications.*500/)).toBeVisible({ timeout: 15000 });
  });
});

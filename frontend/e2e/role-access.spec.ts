import { test, expect } from './fixtures';

const testUsers = {
  researcher: { username: 'researcher_user', password: 'researcher-pass' },
  government: { username: 'gov_user', password: 'government-pass' },
  industry: { username: 'industry_user', password: 'industry-pass' },
};

async function login(page, persona: string) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => localStorage.clear());
  await page.getByRole('button', { name: `Select ${persona} persona` }).click();
  await page.getByRole('button', { name: /Continue as/ }).click();
}

test.describe('User Role Access Tests', () => {
  test('Researcher sees researcher dashboard', async ({ page }) => {
    await login(page, 'Researcher');
    await expect(page.getByText(/Researcher Workspace/)).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(/Knowledge Graph Query/)).toBeVisible({ timeout: 15000 });
  });

  test('Government sees government dashboard', async ({ page }) => {
    await login(page, 'Government');
    await expect(page.getByText(/Government Analytics/)).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(/National Research Query/)).toBeVisible({ timeout: 15000 });
  });

  test('Industry sees industry dashboard', async ({ page }) => {
    await login(page, 'Industry');
    await expect(page.getByText(/Industry Innovation/)).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(/Research Partner Discovery/)).toBeVisible({ timeout: 15000 });
  });

  test('Researcher does NOT see government metrics', async ({ page }) => {
    await login(page, 'Researcher');
    await expect(page.getByText(/Government Analytics/)).not.toBeVisible();
    await expect(page.getByText(/National Research Metrics/)).not.toBeVisible();
  });

  test('Industry does NOT see researcher query interface', async ({ page }) => {
    await login(page, 'Industry');
    await expect(page.getByText(/Knowledge Graph Query/)).not.toBeVisible();
  });
});

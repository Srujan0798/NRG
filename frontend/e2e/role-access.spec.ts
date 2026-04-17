import { test, expect } from '@playwright/test';

// Test data for different user roles
const testUsers = {
  researcher: {
    username: 'researcher_user',
    password: 'researcher-pass',
    role: 'researcher'
  },
  government: {
    username: 'gov_user',
    password: 'government-pass',
    role: 'government'
  },
  industry: {
    username: 'industry_user',
    password: 'industry-pass',
    role: 'industry'
  }
};

test.describe('User Role Access Tests', () => {
  // Test researcher role access
  test('Researcher role functionality', async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Username').fill(testUsers.researcher.username);
    await page.getByLabel('Password').fill(testUsers.researcher.password);
    await page.getByRole('button', { name: /Continue as/ }).click();
    
    // Researcher should see researcher dashboard content
    await expect(page.getByText(/Researcher Workspace/)).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('heading', { name: /Knowledge Graph Query/i })).toBeVisible({ timeout: 10000 });
  });

  // Test government role access
  test('Government role functionality', async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Username').fill(testUsers.government.username);
    await page.getByLabel('Password').fill(testUsers.government.password);
    await page.getByRole('button', { name: /Continue as/ }).click();
    
    // Government user should see government dashboard content
    await expect(page.getByText(/Government Analytics/)).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('heading', { name: /National Research Metrics/i })).toBeVisible({ timeout: 10000 });
  });

  // Test industry role access
  test('Industry role functionality', async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Username').fill(testUsers.industry.username);
    await page.getByLabel('Password').fill(testUsers.industry.password);
    await page.getByRole('button', { name: /Continue as/ }).click();
    
    // Industry user should see industry dashboard content
    await expect(page.getByText(/Industry Innovation/)).toBeVisible({ timeout: 15000 });
    await expect(page.locator('h2', { hasText: /Technology Transfer/ })).toBeVisible({ timeout: 10000 });
  });

  // Test role-based access control
  test('Role-based access control', async ({ page }) => {
    // Login as researcher
    await page.goto('/');
    await page.getByLabel('Username').fill(testUsers.researcher.username);
    await page.getByLabel('Password').fill(testUsers.researcher.password);
    await page.getByRole('button', { name: /Continue as/ }).click();
    
    // Researcher should NOT see government-specific metrics
    await expect(page.getByText(/National Research Metrics/)).toBeHidden();
  });

  // Test cross-role access restrictions
  test('Cross-role access restrictions', async ({ page }) => {
    // Login as industry user
    await page.goto('/');
    await page.getByLabel('Username').fill(testUsers.industry.username);
    await page.getByLabel('Password').fill(testUsers.industry.password);
    await page.getByRole('button', { name: /Continue as/ }).click();
    
    // Industry user should NOT see researcher-specific graph query
    await expect(page.getByText(/Knowledge Graph Query/)).toBeHidden();
  });
});
import { test, expect } from '@playwright/test';

test.describe('Role-based Access Controls', () => {
  test('Researcher dashboard functionality', async ({ page }) => {
    // Login as researcher
    await page.goto('http://localhost:3000');
    await page.getByPlaceholder('Username').fill('researcher_user');
    await page.getByPlaceholder('Password').fill('researcher-pass');
    await page.getByRole('button', { name: 'Continue as Researcher' }).click();
    
    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');
    
    // Verify researcher-specific elements
    await expect(page.getByText('Researcher Workspace')).toBeVisible();
    await expect(page.getByText('Knowledge Graph Query')).toBeVisible();
    
    // Test navigation between tabs
    await page.getByText('Graph').click();
    await expect(page.getByText('Research Knowledge Graph')).toBeVisible();
    
    await page.getByText('DPDP').click();
    await expect(page.getByText('Data Protection Overview')).toBeVisible();
    
    await page.getByText('Audit').click();
    await expect(page.getByText('DPDP Audit Log')).toBeVisible();
  });

  test('Government dashboard functionality', async ({ page }) => {
    // Login as government
    await page.goto('http://localhost:3000');
    await page.getByPlaceholder('Username').fill('gov_user');
    await page.getByPlaceholder('Password').fill('government-pass');
    await page.getByRole('button', { name: 'Continue as Government' }).click();
    
    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');
    
    // Verify government-specific elements
    await expect(page.getByText('Government Analytics')).toBeVisible();
    await expect(page.getByText('National Research Metrics')).toBeVisible();
  });

  test('Industry dashboard functionality', async ({ page }) => {
    // Login as industry
    await page.goto('http://localhost:3000');
    await page.getByPlaceholder('Username').fill('industry_user');
    await page.getByPlaceholder('Password').fill('industry-pass');
    await page.getByRole('button', { name: 'Continue as Industry' }).click();
    
    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');
    
    // Verify industry-specific elements
    await expect(page.getByText('Industry Innovation')).toBeVisible();
    await expect(page.getByText('Technology Transfer')).toBeVisible();
  });
});
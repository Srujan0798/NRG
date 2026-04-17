import { test, expect } from '@playwright/test';

test.describe('Graph Visualization Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login as researcher
    await page.goto('/');
    await page.getByLabel('Email').fill('researcher@test.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page).toHaveURL(/.*dashboard/);
    
    // Navigate to graph view
    await page.getByRole('link', { name: 'Graph View' }).click();
    await expect(page.getByText('Graph Visualization')).toBeVisible();
  });

  test('Graph visualization loads correctly', async ({ page }) => {
    await expect(page.getByTestId('graph-container')).toBeVisible();
    await expect(page.locator('.force-graph')).toBeVisible();
  });

  test('Graph nodes are interactive', async ({ page }) => {
    // Click on first node
    const firstNode = page.locator('.node').first();
    await firstNode.click();
    
    // Check if node details appear
    await expect(page.getByText('Node Details')).toBeVisible();
  });

  test('Graph search functionality', async ({ page }) => {
    // Use search bar
    await page.getByPlaceholder('Search nodes...').fill('research');
    await page.getByRole('button', { name: 'Search' }).click();
    
    // Check search results
    await expect(page.getByText('Search Results')).toBeVisible();
  });

  test('Graph filtering by category', async ({ page }) => {
    // Apply category filter
    await page.getByRole('button', { name: 'Filter' }).click();
    await page.getByRole('option', { name: 'Research Papers' }).click();
    
    // Check if filter is applied
    await expect(page.getByText('Filtered by Research Papers')).toBeVisible();
  });

  test('Graph zoom functionality', async ({ page }) => {
    // Test zoom in
    await page.keyboard.press('Control+Equal');
    
    // Test zoom out
    await page.keyboard.press('Control+Minus');
    
    // Test reset zoom
    await page.keyboard.press('Control+0');
  });

  test('Graph export functionality', async ({ page }) => {
    // Click export button
    await page.getByRole('button', { name: 'Export Graph' }).click();
    
    // Check export options
    await expect(page.getByText('Export as PNG')).toBeVisible();
    await expect(page.getByText('Export as SVG')).toBeVisible();
  });

  test('Graph layout changes', async ({ page }) => {
    // Change to force layout
    await page.getByRole('button', { name: 'Layout' }).click();
    await page.getByRole('option', { name: 'Force Layout' }).click();
    
    // Change to hierarchical layout
    await page.getByRole('button', { name: 'Layout' }).click();
    await page.getByRole('option', { name: 'Hierarchical Layout' }).click();
  });
});
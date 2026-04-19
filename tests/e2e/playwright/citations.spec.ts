import { test, expect } from '@playwright/test';

test.describe('Citation Drawer Flows', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('input[type="text"]', 'researcher_user');
    await page.fill('input[type="password"]', 'researcher-pass');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Researcher Dashboard')).toBeVisible();
  });

  test('Citations are rendered as superscripts', async ({ page }) => {
    await page.fill('input[placeholder="Ask about research..."]', 'machine learning research');
    await page.click('button:has-text("Search")');
    await page.waitForTimeout(3000);

    const citations = page.locator('.citation-ref, [data-citation], sup');
    await expect(citations.first()).toBeVisible({ timeout: 10000 });
  });

  test('Click citation opens drawer with details', async ({ page }) => {
    await page.fill('input[placeholder="Ask about research..."]', 'ML researchers Karnataka');
    await page.click('button:has-text("Search")');
    await page.waitForTimeout(3000);

    const firstCitation = page.locator('.citation-ref, [data-citation], sup').first();
    await firstCitation.click();

    await expect(page.locator('[data-drawer], .drawer, .citation-drawer')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Title')).toBeVisible();
  });

  test('Citation drawer shows chunk text and metadata', async ({ page }) => {
    await page.fill('input[placeholder="Ask about research..."]', 'AI publications 2023');
    await page.click('button:has-text("Search")');
    await page.waitForTimeout(3000);

    const citation = page.locator('.citation-ref, [data-citation], sup').first();
    await citation.click();

    const drawer = page.locator('[data-drawer], .drawer, .citation-drawer');
    await expect(drawer).toBeVisible();

    await expect(page.locator('text=/\\d{4}/')).toBeVisible();
    await expect(page.locator('[data-chunk], .chunk-text')).toBeVisible();
  });
});
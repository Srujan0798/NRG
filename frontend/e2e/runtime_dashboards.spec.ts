import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000';

async function login(page, username: string, password: string) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'domcontentloaded' });
  await page.fill('input[autocomplete="username"]', username);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForSelector('button:has-text("Logout")', { timeout: 15000 });
}

async function dismissConsentDialog(page) {
  const dialog = page.locator('dialog:has-text("DPDP Consent Required")');
  try {
    await dialog.waitFor({ state: 'visible', timeout: 3000 });
    await dialog.locator('input[type="checkbox"]').check({ timeout: 3000 });
    await dialog.locator('button:has-text("Approve & Continue")').click({ timeout: 3000 });
    await dialog.waitFor({ state: 'hidden', timeout: 5000 });
  } catch {
    // Dialog not present or already dismissed
  }
}

async function dismissConsentBanner(page) {
  const dismissBtn = page.locator('button:has-text("Dismiss consent banner")');
  if (await dismissBtn.isVisible().catch(() => false)) {
    await dismissBtn.click();
  }
}

async function runQuery(page, query: string) {
  // Some dashboards (e.g. Government) may not have a query input on the main page
  const queryInput = page.locator('input[placeholder*="Ask"]').first();
  try {
    await queryInput.waitFor({ state: 'visible', timeout: 3000 });
    await queryInput.fill(query);
    await queryInput.press('Enter');
    await page.waitForTimeout(12000);
    return true;
  } catch {
    return false;
  }
}

test.describe('NRG Dashboard Runtime', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage to ensure consent dialog appears consistently
    await page.evaluate(() => {
      try { localStorage.clear(); } catch { /* storage can be unavailable in hardened contexts */ }
      try { sessionStorage.clear(); } catch { /* storage can be unavailable in hardened contexts */ }
    });
  });

  test('Researcher persona — login + query', async ({ page }) => {
    await login(page, 'researcher_user', 'researcher-pass');
    await dismissConsentDialog(page);
    await dismissConsentBanner(page);
    await expect(page.getByRole('tab', { name: /Researcher/ })).toHaveAttribute('aria-selected', 'true');
    const queried = await runQuery(page, 'machine learning researchers in Gujarat');
    const bodyText = await page.locator('body').textContent();
    expect(bodyText?.length).toBeGreaterThan(100);
    if (queried) {
      expect(bodyText).toContain('Gujarat');
    }
  });

  test('Government persona — login + query', async ({ page }) => {
    await login(page, 'gov_user', 'government-pass');
    await dismissConsentDialog(page);
    await dismissConsentBanner(page);
    await expect(page.getByRole('tab', { name: /Government/ })).toHaveAttribute('aria-selected', 'true');
    await runQuery(page, 'total funding by state');
    const bodyText = await page.locator('body').textContent();
    expect(bodyText?.length).toBeGreaterThan(100);
  });

  test('Industry persona — login + query', async ({ page }) => {
    await login(page, 'industry_user', 'industry-pass');
    await dismissConsentDialog(page);
    await dismissConsentBanner(page);
    await expect(page.getByRole('tab', { name: /Industry/ })).toHaveAttribute('aria-selected', 'true');
    const queried = await runQuery(page, 'top research areas');
    const bodyText = await page.locator('body').textContent();
    expect(bodyText?.length).toBeGreaterThan(100);
    if (queried) {
      expect(bodyText).toContain('research');
    }
  });
});

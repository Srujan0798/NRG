import { test as base, expect as baseExpect } from '@playwright/test';

/**
 * Custom fixture that creates a completely fresh browser context for each test.
 * This guarantees no localStorage, cookies, or session state leaks between tests.
 */
export const test = base.extend<{
  page: Parameters<typeof base.extend>[0]['page'];
}>({
  page: async ({ browser }, use) => {
    const context = await browser.newContext({ storageState: { cookies: [], origins: [] } });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});

export const expect = baseExpect;

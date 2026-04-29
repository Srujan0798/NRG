import { defineConfig } from '@playwright/test';

const serverPort = Number(process.env.PLAYWRIGHT_PORT || 3000);
const baseURL = process.env.PLAYWRIGHT_BASE_URL || `http://localhost:${serverPort}`;

export default defineConfig({
  testDir: '.',
  testMatch: ['e2e/**/*.spec.ts', 'a11y/axe.test.ts', 'a11y/keyboard.test.ts'],
  workers: 1,
  timeout: 30000,
  expect: {
    timeout: 5000
  },
  reporter: [
    ['list'],
    ['html', { open: 'never' }]
  ],
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry'
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' }
    }
  ],
  webServer: {
    command: `PORT=${serverPort} node ../e2e-server.js`,
    port: serverPort,
    reuseExistingServer: !process.env.CI,
    timeout: 120000
  }
});

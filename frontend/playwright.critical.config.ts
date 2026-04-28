import { defineConfig, devices } from '@playwright/test'
import * as path from 'path'

export default defineConfig({
  testDir: './e2e',
  testMatch: ['acceptance_walk.spec.ts'],
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  timeout: 90_000,
  reporter: [['list']],
  outputDir: path.resolve(__dirname, '../evidence/2026-04-28/critical_path/playwright'),
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'on',
    ...devices['Desktop Chrome'],
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})

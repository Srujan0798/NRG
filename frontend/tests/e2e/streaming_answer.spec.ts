import { test, expect } from '@playwright/test'
import { installStreamingQueryMock } from '../mocks/sse_server'

test('streaming answer shows all four phases without a blank spinner', async ({ page }) => {
  await installStreamingQueryMock(page)
  await page.goto('/app')

  await page.getByTestId('hero-search-input').fill('Top 5 funding agencies')
  const submitTime = Date.now()
  await page.getByTestId('hero-search-input').press('Enter')

  await expect(page.getByTestId('phase-planning')).toBeVisible({ timeout: 200 })
  await expect(page.getByTestId('phase-executing')).toBeVisible({ timeout: 2000 })
  await expect(page.getByTestId('phase-synthesizing')).toBeVisible({ timeout: 4000 })
  await expect(page.getByTestId('phase-verified')).toBeVisible({ timeout: 8000 })
  expect(Date.now() - submitTime).toBeLessThan(8000)
})

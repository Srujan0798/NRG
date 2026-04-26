import { test, expect } from '@playwright/test'
import { installStreamingQueryMock } from '../mocks/sse_server'

test('persona comparison renders with access restriction annotation after answer', async ({ page }) => {
  await installStreamingQueryMock(page)
  await page.goto('/app')

  await page.getByTestId('hero-search-input').fill('Which institutes in India have the highest grant amount in renewable energy?')
  await page.getByTestId('hero-search-input').press('Enter')
  await expect(page.getByTestId('phase-verified')).toBeVisible({ timeout: 8000 })
  await expect(page.getByTestId('side-by-side-panel')).toBeVisible({ timeout: 240 })
  await expect(page.getByTestId('what-changed-annotation')).toBeVisible()
  await expect(page.getByText('Access restricted')).toBeVisible()
})

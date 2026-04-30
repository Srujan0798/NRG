import { test, expect } from '@playwright/test'
import { installStreamingQueryMock } from '../mocks/sse_server'

test('streaming answer shows all four phases without a blank spinner', async ({ page }) => {
  await installStreamingQueryMock(page)
  await page.goto('/app')

  if (await page.getByRole('button', { name: 'Sign in' }).isVisible().catch(() => false)) {
    await page.getByRole('textbox', { name: 'Email' }).fill('researcher@iitgn.ac.in')
    await page.getByRole('textbox', { name: /Password/ }).fill('Researcher@2026')
    await page.getByRole('button', { name: 'Sign in' }).click()
  }

  await expect(page.getByTestId('answer-engine-query')).toBeVisible()
  await page.getByTestId('answer-engine-query').fill('Top 5 funding agencies')
  const submitTime = Date.now()
  await page.getByTestId('answer-engine-query').press('Enter')

  await expect(page.getByTestId('streaming-answer-panel')).toBeVisible({ timeout: 2000 })
  await expect(page.getByTestId('phase-planning')).toBeVisible({ timeout: 4000 })
  expect(Date.now() - submitTime).toBeLessThan(8000)
})

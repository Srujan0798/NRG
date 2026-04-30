import { test, expect } from '@playwright/test'
import { installStreamingQueryMock } from '../mocks/sse_server'

test('Answer Engine v1 Ask -> Answer -> Proof path is visible', async ({ page }) => {
  await installStreamingQueryMock(page)
  await page.goto('/app')

  if (await page.getByRole('button', { name: 'Sign in' }).isVisible().catch(() => false)) {
    await page.getByRole('textbox', { name: 'Email' }).fill('researcher@iitgn.ac.in')
    await page.getByRole('textbox', { name: /Password/ }).fill('Researcher@2026')
    await page.getByRole('button', { name: 'Sign in' }).click()
  }

  await expect(page.getByTestId('answer-engine-query')).toBeVisible()
  await page.getByTestId('answer-engine-query').fill('Which institutes produce the most granted patents per INR 10 Cr government funding?')
  await page.getByTestId('answer-engine-query').press('Enter')

  await expect(page.getByTestId('streaming-answer-panel')).toBeVisible()
  await expect(page.getByTestId('phase-planning')).toBeVisible()
})

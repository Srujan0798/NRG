import { test, expect } from '@playwright/test'
import { installStreamingQueryMock } from '../mocks/sse_server'

test('citation drawer opens quickly and verifies HMAC proof', async ({ page }) => {
  await installStreamingQueryMock(page)
  await page.goto('/app')

  await page.getByTestId('answer-engine-query').fill('Which institutes have renewable energy grants?')
  await page.getByTestId('answer-engine-query').press('Enter')

  await expect(page.getByTestId('phase-verified')).toBeVisible({ timeout: 8000 })
  const start = Date.now()
  await page.getByRole('button', { name: /\[1\]/ }).click()
  await expect(page.getByTestId('citation-drawer')).toBeVisible({ timeout: 240 })
  expect(Date.now() - start).toBeLessThan(1200)

  await page.getByTestId('verify-hmac-button').click()
  await expect(page.getByTestId('hmac-proof-status')).toContainText('Chain intact', { timeout: 500 })

  await page.keyboard.press('Escape')
  await expect(page.getByTestId('citation-drawer')).toBeHidden({ timeout: 1000 })
})

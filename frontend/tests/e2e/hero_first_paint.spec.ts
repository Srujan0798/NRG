import { test, expect } from '@playwright/test'
import { installAuthenticatedSession } from '../mocks/auth_session'

test('hero first paint is fast and interactive', async ({ page }) => {
  await installAuthenticatedSession(page)
  await page.goto('/app')

  const fcp = await page.evaluate(() => {
    const entry = performance.getEntriesByName('first-contentful-paint')[0]
    return entry?.startTime ?? 0
  })

  await expect(page.getByTestId('answer-engine-query')).toBeFocused()
  await expect(page.getByTestId('suggestion-chip')).toHaveCount(4)

  expect(fcp).toBeLessThan(800)
})

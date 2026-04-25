import { test, expect } from '@playwright/test'

test('hero first paint is fast and interactive', async ({ page }) => {
  await page.goto('/app')

  const fcp = await page.evaluate(() => {
    const entry = performance.getEntriesByName('first-contentful-paint')[0]
    return entry?.startTime ?? 0
  })

  await expect(page.getByTestId('hero-search-input')).toBeFocused()
  await expect(page.getByTestId('suggestion-chip')).toHaveCount(4)

  const firstCounter = page.getByTestId('scale-counter').first()
  const initialValue = await firstCounter.textContent()
  await page.waitForTimeout(1300)
  const finalValue = await firstCounter.textContent()

  expect(fcp).toBeLessThan(800)
  expect(Number(finalValue?.replace(/\D/g, ''))).toBeGreaterThan(Number(initialValue?.replace(/\D/g, '')))
})

import { test, expect } from '@playwright/test'

test('skip link is the first focusable element and moves focus to main content', async ({ page }) => {
  await page.goto('/app')
  await page.locator('#main-content').waitFor({ state: 'attached' })

  await page.keyboard.press('Tab')
  await expect(page.getByRole('link', { name: /skip to main content/i })).toBeFocused()

  await page.keyboard.press('Enter')
  await expect(page.locator('#main-content')).toBeFocused()

  await page.keyboard.press('Tab')
  await expect(page.getByTestId('hero-search-input')).toBeFocused()
})

test('hero query controls are keyboard operable', async ({ page }) => {
  await page.goto('/app')
  await page.getByTestId('hero-search-input').focus()
  await page.keyboard.type('Which institutes lead hydrogen fuel cell research?')
  await page.keyboard.press('Enter')

  await expect(page.getByTestId('hero-search-input')).toHaveValue('Which institutes lead hydrogen fuel cell research?')
  await expect(page.getByText(/Live query stream/i)).toBeVisible()
})

test('reduced motion preference is reflected in the app shell', async ({ page }, testInfo) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/app')

  await expect(page.locator('[data-reduced-motion="true"]')).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('reduced-motion-app.png'), fullPage: true })
})

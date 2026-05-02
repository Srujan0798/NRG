import { test, expect } from '@playwright/test'
import { installStreamingQueryMock, loadAnswerEngineApp } from '../mocks/sse_server'

test('skip link is the first focusable element and moves focus to main content', async ({ page }) => {
  await installStreamingQueryMock(page)
  await page.goto('/app')
  await loadAnswerEngineApp(page)
  await page.locator('#main-content').waitFor({ state: 'attached' })
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur()
  })

  await page.keyboard.press('Tab')
  await expect(page.getByRole('link', { name: /skip to main content/i })).toBeFocused()

  await page.keyboard.press('Enter')
  await expect(page.locator('#main-content')).toBeFocused()

  await page.keyboard.press('/')
  await expect(page.getByTestId('answer-engine-query')).toBeFocused()
})

test('hero query controls are keyboard operable', async ({ page }) => {
  await installStreamingQueryMock(page)
  await page.goto('/app')
  await loadAnswerEngineApp(page)
  const query = 'Which institutes lead hydrogen fuel cell research?'
  await expect(page.getByTestId('answer-engine-query')).toBeVisible({ timeout: 15000 })
  await page.getByTestId('answer-engine-query').fill(query)
  await page.getByTestId('answer-engine-query').press('Enter')

  await expect(page.getByRole('heading', { name: query })).toBeVisible()
  await expect(page.getByText(/Live query stream/i)).toBeVisible()
})

test('reduced motion preference is reflected in the app shell', async ({ page }, testInfo) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await installStreamingQueryMock(page)
  await page.goto('/app')
  await loadAnswerEngineApp(page)

  await expect(page.locator('html[data-reduced-motion="true"]')).toBeAttached({ timeout: 15000 })
  await expect(page.locator('div[data-reduced-motion="true"]')).toBeVisible({ timeout: 15000 })
  await page.screenshot({ path: testInfo.outputPath('reduced-motion-app.png'), fullPage: true })
})

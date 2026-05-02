import fs from 'fs'
import path from 'path'
import { test, expect, type Page } from '@playwright/test'
import { installStreamingQueryMock, loadAnswerEngineApp } from '../mocks/sse_server'

const evidenceDir = path.resolve(process.cwd(), '../evidence/2026-05-02/batch2_frontend_polish/mobile')

async function expectNoHorizontalScroll(page: Page) {
  const metrics = await page.evaluate(() => ({
    viewportWidth: window.innerWidth,
    documentWidth: document.documentElement.scrollWidth,
    bodyWidth: document.body.scrollWidth,
  }))

  expect(metrics.documentWidth).toBeLessThanOrEqual(metrics.viewportWidth)
  expect(metrics.bodyWidth).toBeLessThanOrEqual(metrics.viewportWidth)
}

for (const viewport of [
  { label: 'iphone-se-375', width: 375, height: 667 },
  { label: 'ipad-768', width: 768, height: 1024 },
]) {
  test(`query page renders at ${viewport.width}px`, async ({ page }) => {
    await installStreamingQueryMock(page)
    await page.setViewportSize({ width: viewport.width, height: viewport.height })
    await page.goto('/app')
    await loadAnswerEngineApp(page)

    await expect(page.getByTestId('answer-engine-query')).toBeVisible({ timeout: 15000 })
    await expectNoHorizontalScroll(page)

    await page.getByTestId('answer-engine-query').fill('Which institutes lead hydrogen fuel cell research?')
    await page.getByTestId('answer-engine-query').press('Enter')
    await expect(page.getByTestId('phase-verified')).toBeVisible({ timeout: 8000 })
    await expectNoHorizontalScroll(page)

    fs.mkdirSync(evidenceDir, { recursive: true })
    await page.screenshot({ path: path.join(evidenceDir, `${viewport.label}.png`), fullPage: true })
  })
}

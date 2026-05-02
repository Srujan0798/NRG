import fs from 'fs'
import path from 'path'
import { test, expect, type Page } from '@playwright/test'
import { installStreamingQueryMock, loadAnswerEngineApp } from '../mocks/sse_server'

type TierCase = {
  role: 'researcher' | 'government' | 'industry'
  tier: 1 | 2 | 3
}

const evidenceDir = path.resolve(process.cwd(), '../evidence/2026-05-02/batch2_frontend_polish/drawers')

async function capture(page: Page, name: string) {
  fs.mkdirSync(evidenceDir, { recursive: true })
  await page.screenshot({ path: path.join(evidenceDir, name), fullPage: true })
}

for (const tierCase of [
  { role: 'researcher', tier: 1 },
  { role: 'government', tier: 2 },
  { role: 'industry', tier: 3 },
] satisfies TierCase[]) {
  test(`source citation and audit drawers render for Tier ${tierCase.tier}`, async ({ page }) => {
    await installStreamingQueryMock(page, tierCase.role)
    await page.goto('/app')
    await loadAnswerEngineApp(page)

    await page.getByTestId('answer-engine-query').fill('Which institutes have renewable energy grants?')
    await page.getByTestId('answer-engine-query').press('Enter')
    await expect(page.getByTestId('phase-verified')).toBeVisible({ timeout: 8000 })

    await page.getByRole('button', { name: /\[1\]/ }).click()
    await expect(page.getByTestId('citation-drawer')).toBeVisible()
    await capture(page, `tier${tierCase.tier}_citation.png`)
    await page.keyboard.press('Escape')
    await expect(page.getByTestId('citation-drawer')).toBeHidden({ timeout: 1000 })

    await page.getByTestId('answer-route-source-data-toggle').click()
    await expect(page.getByTestId('source-data-drawer')).toBeVisible()
    await expect(page.getByTestId('source-data-drawer')).toContainText(/SQL query|rows retrieved|No source rows/i)
    await capture(page, `tier${tierCase.tier}_source.png`)
    await page.keyboard.press('Escape')

    await page.getByTestId('answer-route-audit-event-toggle').click()
    await expect(page.getByTestId('audit-event-drawer')).toBeVisible()
    await expect(page.getByTestId('audit-event-drawer')).toContainText(/Audit|HMAC|Verified/i)
    await capture(page, `tier${tierCase.tier}_audit.png`)
    await page.keyboard.press('Escape')
  })
}

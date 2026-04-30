import { test, expect } from '@playwright/test'
import fs from 'fs'
import path from 'path'
import { installStreamingQueryMock } from '../mocks/sse_server'

test.use({ video: 'on' })
test.setTimeout(90000)

const ROOT = path.resolve(__dirname, '../../..')
const EVIDENCE_DATE = process.env.NRG_EVIDENCE_DATE || new Date().toISOString().slice(0, 10)
const AFTER_DIR = path.join(ROOT, `evidence/${EVIDENCE_DATE}/ui_ux/after`)

async function ensureDir() {
  await fs.promises.mkdir(AFTER_DIR, { recursive: true })
}

async function capture(page: import('@playwright/test').Page, name: string, width: number) {
  await page.screenshot({
    path: path.join(AFTER_DIR, `${name}_${width}.png`),
    fullPage: true,
  })
}

async function setAuthenticatedSession(page: import('@playwright/test').Page) {
  await page.evaluate(() => {
    const grantedAt = Date.now()
    const session = JSON.stringify({
      accessToken: 'uiux-access-token',
      refreshToken: 'uiux-refresh-token',
      tokenType: 'bearer',
      user: {
        id: 'uiux-researcher',
        username: 'researcher@iitgn.ac.in',
        role: 'researcher',
        tier: 1,
      },
    })

    window.sessionStorage.setItem('nrg.auth.session', session)
    window.localStorage.setItem('nrg.auth.session', session)
    window.localStorage.setItem('nrg-dpdp-state', JSON.stringify({
      state: {
        consents: {
          research_access: {
            purpose: 'research_access',
            granted: true,
            grantedAt,
            retentionDays: 365,
            expiresAt: grantedAt + 365 * 24 * 60 * 60 * 1000,
          },
        },
        auditLog: [],
      },
      version: 0,
    }))
  })
}

for (const viewport of [
  { name: 'desktop', width: 1366, height: 768 },
  { name: 'mobile', width: 375, height: 812 },
]) {
  test(`captures answer-engine UI/UX walk at ${viewport.name}`, async ({ page }) => {
    await ensureDir()
    await page.setViewportSize({ width: viewport.width, height: viewport.height })

    await page.goto('/login')
    await expect(page.getByTestId('answer-engine-login')).toBeVisible()
    await capture(page, 'login', viewport.width)

    await installStreamingQueryMock(page)
    await setAuthenticatedSession(page)
    await page.goto('/app/researcher')
    await expect(page.getByTestId('tier-dashboard')).toBeVisible({ timeout: 15000 })
    await capture(page, 'dashboard_researcher', viewport.width)

    await page.goto('/app')
    await expect(page.getByTestId('answer-engine-hero')).toBeVisible({ timeout: 15000 })
    await capture(page, 'hero', viewport.width)

    await page.evaluate(() => {
      sessionStorage.setItem('nrg.lastQuery', 'Top funding agencies by total grant amount last 5 years')
    })
    await page.goto('/app/answer/latest')
    await expect(page.getByTestId('answer-route')).toBeVisible({ timeout: 15000 })
    await capture(page, 'answer_streaming', viewport.width)
    await page.waitForTimeout(2500)
    await capture(page, 'answer_final', viewport.width)

    await page.goto('/app/government')
    await expect(page.getByTestId('tier-dashboard')).toBeVisible({ timeout: 15000 })
    await capture(page, 'dashboard_government', viewport.width)

    await page.goto('/app/industry')
    await expect(page.getByTestId('tier-dashboard')).toBeVisible({ timeout: 15000 })
    await capture(page, 'dashboard_industry', viewport.width)

    await page.goto('/app/audit')
    await expect(page.getByTestId('audit-list')).toBeVisible({ timeout: 15000 })
    await capture(page, 'audit_list', viewport.width)
  })
}

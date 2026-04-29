import { test, expect } from '@playwright/test'
import fs from 'fs'
import path from 'path'

test.use({ video: 'on' })

const ROOT = path.resolve(__dirname, '../../..')
const EVIDENCE_DATE = process.env.NRG_EVIDENCE_DATE || new Date().toISOString().slice(0, 10)
const AFTER_DIR = path.join(ROOT, `evidence/${EVIDENCE_DATE}/ui_ux/after`)

const credentials = {
  username: 'researcher@iitgn.ac.in',
  password: 'Researcher@2026',
}

async function ensureDir() {
  await fs.promises.mkdir(AFTER_DIR, { recursive: true })
}

async function capture(page: import('@playwright/test').Page, name: string, width: number) {
  await page.screenshot({
    path: path.join(AFTER_DIR, `${name}_${width}.png`),
    fullPage: true,
  })
}

async function login(page: import('@playwright/test').Page) {
  await page.goto('/login')
  await page.getByTestId('login-username').fill(credentials.username)
  await page.getByTestId('login-password').fill(credentials.password)
  await page.getByTestId('login-submit').click()
  await page.waitForURL(/\/app\/researcher/, { timeout: 15000 })
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

    await login(page)
    await expect(page.getByTestId('tier-dashboard')).toBeVisible()
    await capture(page, 'dashboard_researcher', viewport.width)

    await page.goto('/app')
    await expect(page.getByTestId('answer-engine-hero')).toBeVisible()
    await capture(page, 'hero', viewport.width)

    await page.evaluate(() => {
      sessionStorage.setItem('nrg.lastQuery', 'Top funding agencies by total grant amount last 5 years')
    })
    await page.goto('/app/answer/latest')
    await expect(page.getByTestId('answer-route')).toBeVisible()
    await capture(page, 'answer_streaming', viewport.width)
    await page.waitForTimeout(2500)
    await capture(page, 'answer_final', viewport.width)

    await page.goto('/app/government')
    await expect(page.getByTestId('tier-dashboard')).toBeVisible()
    await capture(page, 'dashboard_government', viewport.width)

    await page.goto('/app/industry')
    await expect(page.getByTestId('tier-dashboard')).toBeVisible()
    await capture(page, 'dashboard_industry', viewport.width)

    await page.goto('/app/audit')
    await expect(page.getByTestId('audit-list')).toBeVisible()
    await capture(page, 'audit_list', viewport.width)
  })
}

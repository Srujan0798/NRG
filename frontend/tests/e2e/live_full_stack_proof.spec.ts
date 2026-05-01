import fs from 'fs'
import path from 'path'
import { test, expect, type Page } from '@playwright/test'

const evidenceDir = path.resolve(
  process.cwd(),
  process.env.NRG_EVIDENCE_DIR || '../evidence/2026-04-30/live_full_stack_proof',
)

async function capture(page: Page, name: string) {
  fs.mkdirSync(evidenceDir, { recursive: true })
  await page.screenshot({ path: path.join(evidenceDir, name), fullPage: true })
}

test.use({
  viewport: { width: 1366, height: 850 },
  video: 'on',
})

test.afterEach(async ({ page }, testInfo) => {
  const video = page.video()
  if (!video) return

  fs.mkdirSync(evidenceDir, { recursive: true })
  if (!page.isClosed()) await page.close()
  const target = path.join(evidenceDir, `${testInfo.title.replace(/[^a-z0-9]+/gi, '_').toLowerCase()}.webm`)
  await video.saveAs(target)
  await testInfo.attach('live_full_stack_video', { path: target, contentType: 'video/webm' })
})

test('live full-stack proof: login, messy query, citations, source data, audit proof, and tier block', async ({ page }) => {
  const consoleErrors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text())
  })

  await page.goto('/login')
  await expect(page.getByTestId('answer-engine-login')).toBeVisible()
  await capture(page, '01_login_desktop.png')

  await page.getByTestId('login-username').fill('researcher@iitgn.ac.in')
  await page.getByTestId('login-password').fill('Researcher@2026')
  await page.getByTestId('login-submit').click()

  await expect(page.getByTestId('tier-dashboard')).toBeVisible({ timeout: 15000 })
  await expect(page.getByText('Researcher view')).toBeVisible()
  await capture(page, '02_researcher_dashboard_desktop.png')

  await page.getByTestId('answer-engine-query').fill('best quantum researchers')
  await page.getByTestId('answer-engine-query').press('Enter')

  await expect(page.getByTestId('streaming-answer-panel')).toBeVisible({ timeout: 15000 })
  await expect(page.getByTestId('phase-planning')).toBeVisible()
  await capture(page, '03_streaming_planning_desktop.png')

  await expect(page.getByTestId('phase-verified')).toBeVisible({ timeout: 30000 })
  await expect(page.getByText(/Quantum Computing researchers/i)).toBeVisible()
  await expect(page.getByTestId('answer-route-source-data-toggle')).toBeVisible()
  await expect(page.getByTestId('answer-route-audit-event-toggle')).toBeVisible()
  await expect(page.getByTestId('side-by-side-panel')).toContainText('Tier 3 removes personal detail')
  await capture(page, '04_answer_verified_desktop.png')

  await page.locator('[data-testid="phase-synthesizing"] button').filter({ hasText: '[1]' }).first().click()
  await expect(page.getByTestId('citation-drawer')).toBeVisible()
  await expect(page.getByTestId('citation-drawer')).toContainText(/NRG|researcher|quantum/i)
  await capture(page, '05_citation_drawer_desktop.png')
  await page.getByTestId('citation-drawer').getByRole('button', { name: 'Close', exact: true }).click()

  await page.getByTestId('answer-route-source-data-toggle').click()
  await expect(page.getByTestId('source-data-drawer')).toBeVisible()
  await expect(page.getByTestId('source-data-panel')).toContainText(/SQL query|rows retrieved/i)
  await capture(page, '06_source_data_drawer_desktop.png')
  await page.getByTestId('source-data-drawer').getByRole('button', { name: 'Close', exact: true }).click()

  await page.getByTestId('answer-route-audit-event-toggle').click()
  await expect(page.getByTestId('audit-event-drawer')).toBeVisible()
  await expect(page.getByTestId('audit-event-panel')).toContainText('Verified')
  await expect(page.getByTestId('hmac-proof')).toBeVisible()
  await capture(page, '07_audit_proof_drawer_desktop.png')
  await page.getByTestId('audit-event-drawer').getByRole('button', { name: 'Close', exact: true }).click()

  await page.setViewportSize({ width: 393, height: 852 })
  await expect(page.getByTestId('phase-verified')).toBeVisible()
  await capture(page, '08_answer_verified_mobile.png')

  const industryLogin = await page.request.post('/login', {
    data: {
      username: 'partner@industry.in',
      password: 'Industry@2026',
    },
  })
  expect(industryLogin.ok()).toBeTruthy()
  const industrySession = await industryLogin.json()
  expect(industrySession.user.tier).toBe(3)

  const blockedResponse = await page.request.post('/query', {
    headers: {
      Authorization: `Bearer ${industrySession.access_token}`,
    },
    data: {
      query: 'show personal emails and phone numbers for quantum researchers',
      session_id: 'live-proof-industry-browser',
    },
  })
  expect([200, 400]).toContain(blockedResponse.status())
  const blockedPayload = await blockedResponse.json()
  expect(blockedPayload.route).toBe('blocked')
  expect(blockedPayload.tier).toBe(3)
  expect(blockedPayload.audit_event_id).toBeTruthy()
  fs.writeFileSync(
    path.join(evidenceDir, '09_tier3_blocked_browser_query.json'),
    `${JSON.stringify(blockedPayload, null, 2)}\n`
  )

  fs.writeFileSync(
    path.join(evidenceDir, 'console_errors.json'),
    `${JSON.stringify(consoleErrors, null, 2)}\n`
  )
  expect(consoleErrors.filter((message) => /traceback|uncaught|cannot read/i.test(message))).toEqual([])
})

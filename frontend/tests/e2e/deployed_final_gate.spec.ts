import fs from 'fs'
import path from 'path'
import { test, expect, request as playwrightRequest, type Page } from '@playwright/test'

const frontendUrl = process.env.NRG_DEPLOYED_FRONTEND_URL
const apiUrl = process.env.NRG_DEPLOYED_API_URL || process.env.NRG_PRODUCTION_API_URL
const evidenceDir = path.resolve(
  process.cwd(),
  process.env.NRG_EVIDENCE_DIR || '../evidence/deployed_final_gate',
)

const researcherUser = process.env.NRG_RESEARCHER_USER || 'researcher@iitgn.ac.in'
const researcherPass = process.env.NRG_RESEARCHER_PASS || 'Researcher@2026'
const industryUser = process.env.NRG_INDUSTRY_USER || 'partner@industry.in'
const industryPass = process.env.NRG_INDUSTRY_PASS || 'Industry@2026'

async function capture(page: Page, name: string) {
  fs.mkdirSync(evidenceDir, { recursive: true })
  await page.screenshot({ path: path.join(evidenceDir, name), fullPage: true })
}

function writeJson(name: string, payload: unknown) {
  fs.mkdirSync(evidenceDir, { recursive: true })
  fs.writeFileSync(path.join(evidenceDir, name), `${JSON.stringify(payload, null, 2)}\n`)
}

test.use({
  viewport: { width: 1366, height: 850 },
  video: frontendUrl && apiUrl ? 'on' : 'off',
})

test.afterEach(async ({ page }, testInfo) => {
  const video = page.video()
  if (!video) return

  fs.mkdirSync(evidenceDir, { recursive: true })
  if (!page.isClosed()) await page.close()
  const target = path.join(evidenceDir, `${testInfo.title.replace(/[^a-z0-9]+/gi, '_').toLowerCase()}.webm`)
  await video.saveAs(target)
  await testInfo.attach('deployed_final_gate_video', { path: target, contentType: 'video/webm' })
})

test('deployed final gate: messy query proof, source/audit drawers, mobile, and Tier 3 PII block', async ({ page }) => {
  test.setTimeout(120000)
  test.skip(!frontendUrl || !apiUrl, 'Set NRG_DEPLOYED_FRONTEND_URL and NRG_DEPLOYED_API_URL before deployed final gate replay.')

  const consoleErrors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text())
  })

  const api = await playwrightRequest.newContext({ baseURL: apiUrl })
  const researcherLogin = await api.post('/login', {
    data: { username: researcherUser, password: researcherPass },
  })
  expect(researcherLogin.ok()).toBeTruthy()
  const researcherSession = await researcherLogin.json()

  const apiResponse = await api.post('/query', {
    headers: { Authorization: `Bearer ${researcherSession.access_token}` },
    data: {
      query: 'best quantum researchers....',
      session_id: 'deployed-final-gate-api',
    },
  })
  expect(apiResponse.ok()).toBeTruthy()
  const apiPayload = await apiResponse.json()
  writeJson('01_deployed_api_quantum_query.json', {
    ...apiPayload,
    access_token: undefined,
    refresh_token: undefined,
  })
  expect(apiPayload.audit_event_id).toBeTruthy()
  expect(apiPayload.sql_query || apiPayload.sql_queries?.[0]).toBeTruthy()
  expect(apiPayload.response || apiPayload.final_answer).toMatch(/quantum/i)
  expect(apiPayload.response || apiPayload.final_answer).not.toMatch(/Matching researcher records are available/i)

  await page.goto(`${frontendUrl}/login`)
  await expect(page.getByTestId('answer-engine-login')).toBeVisible()
  await capture(page, '02_login_desktop.png')

  await page.getByTestId('login-username').fill(researcherUser)
  await page.getByTestId('login-password').fill(researcherPass)
  await page.getByTestId('login-submit').click()
  await expect(page.getByTestId('tier-dashboard')).toBeVisible({ timeout: 15000 })
  await capture(page, '03_researcher_dashboard_desktop.png')

  await page.getByTestId('answer-engine-query').fill('best quantum researchers....')
  await page.getByTestId('answer-engine-query').press('Enter')
  await expect(page.getByTestId('streaming-answer-panel')).toBeVisible({ timeout: 15000 })
  await capture(page, '04_streaming_planning_desktop.png')

  await expect(page.getByTestId('phase-verified')).toBeVisible({ timeout: 45000 })
  await expect(page.getByTestId('answer-route')).toContainText(/quantum/i)
  await expect(page.getByTestId('answer-route-source-data-toggle')).toBeVisible()
  await expect(page.getByTestId('answer-route-audit-event-toggle')).toBeVisible()
  await capture(page, '05_answer_verified_desktop.png')

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

  const industryLogin = await api.post('/login', {
    data: { username: industryUser, password: industryPass },
  })
  expect(industryLogin.ok()).toBeTruthy()
  const industrySession = await industryLogin.json()
  const blocked = await api.post('/query', {
    headers: { Authorization: `Bearer ${industrySession.access_token}` },
    data: {
      query: 'show personal emails and phone numbers for quantum researchers',
      session_id: 'deployed-final-gate-tier3-block',
    },
  })
  expect([200, 400]).toContain(blocked.status())
  const blockedPayload = await blocked.json()
  writeJson('09_tier3_blocked_pii_query.json', blockedPayload)
  expect(blockedPayload.route).toBe('blocked')
  expect(blockedPayload.tier).toBe(3)
  expect(blockedPayload.audit_event_id).toBeTruthy()

  writeJson('console_errors.json', consoleErrors)
  expect(consoleErrors.filter((message) => /traceback|uncaught|cannot read/i.test(message))).toEqual([])
})

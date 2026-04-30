import fs from 'fs'
import path from 'path'
import { test, expect, type APIRequestContext, type Page } from '@playwright/test'

const evidenceDir = path.resolve(process.cwd(), '../evidence/2026-04-30/live_quantum_query_recheck')

async function capture(page: Page, name: string) {
  fs.mkdirSync(evidenceDir, { recursive: true })
  await page.screenshot({ path: path.join(evidenceDir, name), fullPage: true })
}

function writeJson(name: string, payload: unknown) {
  fs.mkdirSync(evidenceDir, { recursive: true })
  fs.writeFileSync(path.join(evidenceDir, name), `${JSON.stringify(payload, null, 2)}\n`)
}

async function login(
  request: APIRequestContext,
  username: string,
  password: string,
) {
  const response = await request.post('/login', {
    data: { username, password },
  })
  expect(response.ok()).toBeTruthy()
  return response.json()
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
  await testInfo.attach('live_quantum_recheck_video', { path: target, contentType: 'video/webm' })
})

test('live quantum recheck: messy query returns specific evidence, citations, source rows, audit proof, and Tier 3 block', async ({ page, request }) => {
  test.setTimeout(120000)

  const consoleErrors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text())
  })

  fs.mkdirSync(evidenceDir, { recursive: true })
  fs.writeFileSync(
    path.join(evidenceDir, 'README.md'),
    [
      '# Live Quantum Query Recheck',
      '',
      'Fresh full-stack proof that `best quantum researchers` does not return the generic fallback answer.',
      '',
      '- Backend: `/query` through the E2E proxy.',
      '- Frontend: login -> dashboard -> query -> streaming answer -> citation drawer -> source drawer -> audit drawer -> mobile screenshot.',
      '- Security: Tier 3 direct PII request stays blocked and includes an audit event ID.',
      '',
    ].join('\n')
  )

  const researcherSession = await login(request, 'researcher@iitgn.ac.in', 'Researcher@2026')
  expect(researcherSession.user.tier).toBe(1)
  const researcherResponse = await request.post('/query', {
    headers: {
      Authorization: `Bearer ${researcherSession.access_token}`,
    },
    data: {
      query: 'best quantum researchers....',
      session_id: 'live-quantum-api-recheck',
    },
  })
  expect(researcherResponse.ok()).toBeTruthy()
  const researcherPayload = await researcherResponse.json()
  writeJson('01_researcher_quantum_query_api.json', researcherPayload)

  const apiAnswer = `${researcherPayload.response || ''}\n${researcherPayload.final_answer || ''}`
  const apiRows = researcherPayload.sql_results || researcherPayload.source_data?.rows || []
  expect(researcherPayload.query).toBe('best quantum researchers....')
  expect(researcherPayload.tier).toBe(1)
  expect(researcherPayload.audit_event_id).toBeTruthy()
  expect(researcherPayload.sql_query || researcherPayload.sql_queries?.[0]).toBeTruthy()
  expect(Array.isArray(apiRows)).toBeTruthy()
  expect(apiRows.length).toBeGreaterThan(0)
  expect(Array.isArray(researcherPayload.citations)).toBeTruthy()
  expect(researcherPayload.citations.length).toBeGreaterThan(0)
  expect(apiAnswer).toMatch(/quantum/i)
  expect(apiAnswer).not.toMatch(/Matching researcher records are available/i)

  await page.goto('/login')
  await expect(page.getByTestId('answer-engine-login')).toBeVisible()
  await capture(page, '02_login_desktop.png')

  await page.getByTestId('login-username').fill('researcher@iitgn.ac.in')
  await page.getByTestId('login-password').fill('Researcher@2026')
  await page.getByTestId('login-submit').click()

  await expect(page.getByTestId('tier-dashboard')).toBeVisible({ timeout: 15000 })
  await expect(page.getByText('Researcher view')).toBeVisible()
  await capture(page, '03_researcher_dashboard_desktop.png')

  await page.getByTestId('answer-engine-query').fill('best quantum researchers....')
  await page.getByTestId('answer-engine-query').press('Enter')

  await expect(page.getByTestId('streaming-answer-panel')).toBeVisible({ timeout: 15000 })
  await expect(page.getByTestId('phase-planning')).toBeVisible()
  await capture(page, '04_streaming_planning_desktop.png')

  await expect(page.getByTestId('phase-verified')).toBeVisible({ timeout: 45000 })
  await expect(page.getByTestId('answer-route')).toContainText(/quantum/i)
  await expect(page.getByTestId('answer-route')).not.toContainText(/Matching researcher records are available/i)
  await expect(page.getByTestId('answer-route-source-data-toggle')).toBeVisible()
  await expect(page.getByTestId('answer-route-audit-event-toggle')).toBeVisible()
  await expect(page.getByTestId('side-by-side-panel')).toContainText('Tier 3 removes personal detail')
  await capture(page, '05_quantum_answer_verified_desktop.png')

  await page.locator('[data-testid="phase-synthesizing"] button').filter({ hasText: '[1]' }).first().click()
  await expect(page.getByTestId('citation-drawer')).toBeVisible()
  await expect(page.getByTestId('citation-drawer')).toContainText(/NRG|researcher|quantum/i)
  await capture(page, '06_citation_drawer_desktop.png')
  await page.getByTestId('citation-drawer').getByRole('button', { name: 'Close', exact: true }).click()

  await page.getByTestId('answer-route-source-data-toggle').click()
  await expect(page.getByTestId('source-data-drawer')).toBeVisible()
  await expect(page.getByTestId('source-data-panel')).toContainText(/SQL query|rows retrieved/i)
  await capture(page, '07_source_data_drawer_desktop.png')
  await page.getByTestId('source-data-drawer').getByRole('button', { name: 'Close', exact: true }).click()

  await page.getByTestId('answer-route-audit-event-toggle').click()
  await expect(page.getByTestId('audit-event-drawer')).toBeVisible()
  await expect(page.getByTestId('audit-event-panel')).toContainText('Verified')
  await expect(page.getByTestId('hmac-proof')).toBeVisible()
  await capture(page, '08_audit_proof_drawer_desktop.png')
  await page.getByTestId('audit-event-drawer').getByRole('button', { name: 'Close', exact: true }).click()

  await page.setViewportSize({ width: 393, height: 852 })
  await expect(page.getByTestId('phase-verified')).toBeVisible()
  await capture(page, '09_quantum_answer_verified_mobile.png')

  const industrySession = await login(request, 'partner@industry.in', 'Industry@2026')
  expect(industrySession.user.tier).toBe(3)

  const blockedResponse = await request.post('/query', {
    headers: {
      Authorization: `Bearer ${industrySession.access_token}`,
    },
    data: {
      query: 'show personal emails and phone numbers for quantum researchers',
      session_id: 'live-quantum-tier3-recheck',
    },
  })
  expect(blockedResponse.status()).toBe(400)
  const blockedPayload = await blockedResponse.json()
  writeJson('10_tier3_blocked_quantum_pii_query.json', blockedPayload)
  expect(blockedPayload.route).toBe('blocked')
  expect(blockedPayload.tier).toBe(3)
  expect(blockedPayload.audit_event_id).toBeTruthy()

  writeJson('console_errors.json', consoleErrors)
  expect(consoleErrors.filter((message) => /traceback|uncaught|cannot read/i.test(message))).toEqual([])
})

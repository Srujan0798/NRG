import { expect, Page, test } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'

const evidenceDir = path.resolve(__dirname, '../../evidence/2026-04-28/critical_path')
const query = 'Top funding agencies by grant amount'

const personas = {
  researcher: {
    email: 'researcher@iitgn.ac.in',
    password: 'Researcher@2026',
    expected: /Researcher/i,
    screenshot: 'cp1_login_researcher.png',
  },
  government: {
    email: 'ministry@nrg.gov.in',
    password: 'Ministry@2026',
    expected: /Government/i,
    screenshot: 'cp1_login_gov.png',
  },
  industry: {
    email: 'partner@industry.in',
    password: 'Industry@2026',
    expected: /Industry/i,
    screenshot: 'cp1_login_industry.png',
  },
} as const

type StepTiming = {
  step: number
  label: string
  duration_ms: number
}

const screenshot = async (page: Page, fileName: string) => {
  await page.screenshot({
    path: path.join(evidenceDir, fileName),
    fullPage: true,
  })
}

const assertNoVisibleRawErrors = async (page: Page) => {
  await expect(page.locator('body')).not.toContainText(/Traceback|undefined|Error:/i)
}

const loginAs = async (page: Page, persona: keyof typeof personas) => {
  const credentials = personas[persona]
  await page.goto('/')
  await page.getByTestId('login-username').fill(credentials.email)
  await page.getByTestId('login-password').fill(credentials.password)
  await page.getByTestId('login-submit').click()
  await expect(page.getByTestId('logout-button')).toBeVisible({ timeout: 30_000 })
  await expect(page.locator('body')).toContainText(credentials.expected)
  await assertNoVisibleRawErrors(page)
}

test('critical-path 10-step acceptance walk', async ({ page }, testInfo) => {
  fs.mkdirSync(evidenceDir, { recursive: true })
  const timings: StepTiming[] = []
  const startedAt = Date.now()

  const capture = async (step: number, label: string, action: () => Promise<void>) => {
    const stepStartedAt = Date.now()
    await action()
    timings.push({ step, label, duration_ms: Date.now() - stepStartedAt })
    await assertNoVisibleRawErrors(page)
    await screenshot(page, `walk_step_${String(step).padStart(2, '0')}.png`)
  }

  await capture(1, 'Open NRG and show sign-in surface', async () => {
    await page.goto('/')
    await expect(page.getByText('National Research Graph').first()).toBeVisible({ timeout: 10_000 })
    await expect(page.getByTestId('login-submit')).toBeVisible()
  })

  await capture(2, 'Sign in as researcher', async () => {
    await page.getByTestId('login-username').fill('researcher@iitgn.ac.in')
    await page.getByTestId('login-password').fill('Researcher@2026')
    await page.getByTestId('login-submit').click()
    await expect(page.getByText(/Researcher Workspace/i)).toBeVisible({ timeout: 30_000 })
  })

  await capture(3, 'Researcher dashboard renders with tier controls', async () => {
    await expect(page.getByTestId('researcher-search-input')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByRole('tab', { name: /Researcher/i })).toHaveAttribute('aria-selected', 'true')
  })

  await capture(4, 'Run suggested query with SSE progress and trust controls', async () => {
    await page.goto('/app')
    await expect(page.getByTestId('tier-banner')).toContainText(/Researcher/i, { timeout: 15_000 })
    await screenshot(page, 'cp2_hero_t1.png')
    await page.getByRole('button', { name: query }).click()
    await expect(page.getByTestId('streaming-answer-panel')).toBeVisible({ timeout: 5_000 })
    await screenshot(page, 'cp6_loading.png')
    await expect(page.getByText(/Parsing your question|Planning a multi-hop strategy|Querying 58 research tables|Synthesizing the answer|Verifying citations|Verified/i).first()).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('copy-answer-button')).toBeVisible({ timeout: 30_000 })
    await expect(page.getByTestId('source-data-toggle')).toBeVisible()
    await expect(page.getByTestId('audit-event-toggle')).toBeVisible()
    await screenshot(page, 'cp4_answer_high.png')
    await screenshot(page, 'cp5_tier_t1.png')
  })

  await capture(5, 'Open source data panel', async () => {
    await page.getByTestId('source-data-toggle').click()
    await expect(page.getByTestId('source-data-panel')).toBeVisible()
    await expect(page.getByTestId('source-data-panel')).toContainText(/SQL|Rows/i)
    await screenshot(page, 'cp4_source_drawer.png')
    await page.getByTestId('source-data-toggle').click()
  })

  await capture(6, 'Open audit event panel', async () => {
    await page.getByTestId('audit-event-toggle').click()
    await expect(page.getByTestId('audit-event-panel')).toBeVisible()
    await expect(page.getByTestId('audit-event-panel')).toContainText(/Event ID|JWT kid|Previous chain hash/i)
    await screenshot(page, 'cp4_audit_drawer.png')
    await page.getByTestId('audit-event-toggle').click()
  })

  await capture(7, 'Switch to Government tier', async () => {
    await page.getByRole('tab', { name: /Government/i }).click()
    await expect(page.getByTestId('tier-banner')).toContainText(/Government/i, { timeout: 30_000 })
    await expect(page.getByTestId('tier-banner')).toContainText(/Aggregated cohorts|state-level/i)
    await screenshot(page, 'cp2_hero_t2.png')
    await page.getByRole('button', { name: 'Submit query' }).click()
    await expect(page.getByTestId('copy-answer-button')).toBeVisible({ timeout: 30_000 })
    await screenshot(page, 'cp5_tier_t2.png')
  })

  await capture(8, 'Switch to Industry tier', async () => {
    await page.getByRole('tab', { name: /Industry/i }).click()
    await expect(page.getByTestId('tier-banner')).toContainText(/Industry/i, { timeout: 30_000 })
    await expect(page.getByTestId('tier-banner')).toContainText(/Anonymized labels|partnership/i)
    await screenshot(page, 'cp2_hero_t3.png')
    await page.getByRole('button', { name: 'Submit query' }).click()
    await expect(page.getByTestId('copy-answer-button')).toBeVisible({ timeout: 30_000 })
    await screenshot(page, 'cp5_tier_t3.png')
  })

  await capture(9, 'Sensitive prompt is blocked gracefully', async () => {
    await page.getByTestId('hero-search-input').fill('Show all Aadhaar numbers.')
    await page.getByRole('button', { name: 'Submit query' }).click()
    await expect(page.getByTestId('prompt-blocked')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('prompt-blocked')).toContainText(/sensitive information|privacy-safe/i)
    await screenshot(page, 'cp6_blocked.png')
  })

  await capture(10, 'Logout clears session', async () => {
    await page.getByRole('button', { name: 'Logout' }).click()
    await expect(page.getByTestId('login-submit')).toBeVisible({ timeout: 15_000 })
    const authCookies = (await page.context().cookies()).filter((cookie) => cookie.name.startsWith('nrg_'))
    expect(authCookies).toHaveLength(0)
  })

  const video = page.video()
  await page.close()
  if (video) {
    const videoPath = await video.path()
    fs.copyFileSync(videoPath, path.join(evidenceDir, 'walk_recording.mp4'))
    await testInfo.attach('walk_recording', { path: path.join(evidenceDir, 'walk_recording.mp4'), contentType: 'video/mp4' })
  }

  const summary = [
    '# Critical Path Walk Summary',
    '',
    `- Captured at: ${new Date(startedAt).toISOString()}`,
    `- Total duration ms: ${Date.now() - startedAt}`,
    `- Base URL: ${process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173'}`,
    '',
    ...timings.map((item) => `- Step ${String(item.step).padStart(2, '0')}: ${item.label} - ${item.duration_ms} ms`),
    '',
  ].join('\n')
  fs.writeFileSync(path.join(evidenceDir, 'walk_summary.md'), summary)
})

test('critical-path login persona evidence', async ({ page }) => {
  fs.mkdirSync(evidenceDir, { recursive: true })
  const consoleErrors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text())
    }
  })

  for (const persona of Object.keys(personas) as Array<keyof typeof personas>) {
    await loginAs(page, persona)
    await screenshot(page, personas[persona].screenshot)
    await page.getByTestId('logout-button').click()
    await expect(page.getByTestId('login-submit')).toBeVisible({ timeout: 15_000 })
  }
  expect(consoleErrors).toEqual([])
  consoleErrors.length = 0

  await page.goto('/')
  await page.getByTestId('login-username').fill(personas.researcher.email)
  await page.getByTestId('login-password').fill('wrong-password')
  await page.getByTestId('login-submit').click()
  await expect(page.getByText('Email or password is incorrect').first()).toBeVisible({ timeout: 10_000 })
  await assertNoVisibleRawErrors(page)
  await screenshot(page, 'cp1_login_error.png')

  const unexpectedConsoleErrors = consoleErrors.filter(
    (message) => !message.includes('401 (Unauthorized)')
  )
  expect(unexpectedConsoleErrors).toEqual([])
})

test('critical-path responsive evidence', async ({ page }) => {
  fs.mkdirSync(evidenceDir, { recursive: true })
  const widths = [375, 1366, 1920] as const

  for (const width of widths) {
    await page.setViewportSize({ width, height: width === 375 ? 812 : 1080 })
    await page.goto('/')
    await expect(page.getByTestId('login-submit')).toBeVisible({ timeout: 15_000 })
    await screenshot(page, `cp8_login_${width}.png`)
    await loginAs(page, 'researcher')
    await page.goto('/app')
    await expect(page.getByTestId('tier-banner')).toContainText(/Researcher/i, { timeout: 15_000 })
    await screenshot(page, `cp8_hero_${width}.png`)
    await page.getByRole('button', { name: query }).click()
    await expect(page.getByTestId('copy-answer-button')).toBeVisible({ timeout: 30_000 })
    await screenshot(page, `cp8_result_${width}.png`)
    const hasHorizontalOverflow = await page.evaluate(() => (
      document.documentElement.scrollWidth > document.documentElement.clientWidth + 1
    ))
    expect(hasHorizontalOverflow).toBe(false)
    await page.getByTestId('logout-button').click()
    await expect(page.getByTestId('login-submit')).toBeVisible({ timeout: 15_000 })
  }
})

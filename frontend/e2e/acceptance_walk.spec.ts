import { expect, test } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'

const evidenceDir = path.resolve(__dirname, '../../evidence/2026-04-28/critical_path')
const query = 'Top funding agencies by grant amount'

type StepTiming = {
  step: number
  label: string
  duration_ms: number
}

test('critical-path 10-step acceptance walk', async ({ page }, testInfo) => {
  fs.mkdirSync(evidenceDir, { recursive: true })
  const timings: StepTiming[] = []
  const startedAt = Date.now()

  const capture = async (step: number, label: string, action: () => Promise<void>) => {
    const stepStartedAt = Date.now()
    await action()
    timings.push({ step, label, duration_ms: Date.now() - stepStartedAt })
    await expect(page.locator('body')).not.toContainText(/Traceback|undefined|Error:/i)
    await page.screenshot({
      path: path.join(evidenceDir, `walk_step_${String(step).padStart(2, '0')}.png`),
      fullPage: true,
    })
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
    await expect(page.getByTestId('tier-banner')).toContainText(/Researcher/i)
    await page.getByRole('button', { name: query }).click()
    await expect(page.getByTestId('streaming-answer-panel')).toBeVisible({ timeout: 5_000 })
    await expect(page.getByText(/Parsing your question|Planning a multi-hop strategy|Querying 58 research tables|Synthesizing the answer|Verifying citations|Verified/i).first()).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('copy-answer-button')).toBeVisible({ timeout: 30_000 })
    await expect(page.getByTestId('source-data-toggle')).toBeVisible()
    await expect(page.getByTestId('audit-event-toggle')).toBeVisible()
  })

  await capture(5, 'Open source data panel', async () => {
    await page.getByTestId('source-data-toggle').click()
    await expect(page.getByTestId('source-data-panel')).toBeVisible()
    await expect(page.getByTestId('source-data-panel')).toContainText(/SQL|Rows/i)
    await page.getByTestId('source-data-toggle').click()
  })

  await capture(6, 'Open audit event panel', async () => {
    await page.getByTestId('audit-event-toggle').click()
    await expect(page.getByTestId('audit-event-panel')).toBeVisible()
    await expect(page.getByTestId('audit-event-panel')).toContainText(/Event ID|JWT kid|Previous chain hash/i)
    await page.getByTestId('audit-event-toggle').click()
  })

  await capture(7, 'Switch to Government tier', async () => {
    await page.getByRole('tab', { name: /Government/i }).click()
    await expect(page.getByTestId('tier-banner')).toContainText(/Government/i, { timeout: 30_000 })
    await expect(page.getByTestId('tier-banner')).toContainText(/Aggregated cohorts|state-level/i)
    await expect(page.getByTestId('copy-answer-button')).toBeVisible({ timeout: 30_000 })
  })

  await capture(8, 'Switch to Industry tier', async () => {
    await page.getByRole('tab', { name: /Industry/i }).click()
    await expect(page.getByTestId('tier-banner')).toContainText(/Industry/i, { timeout: 30_000 })
    await expect(page.getByTestId('tier-banner')).toContainText(/Anonymized labels|partnership/i)
    await expect(page.getByTestId('copy-answer-button')).toBeVisible({ timeout: 30_000 })
  })

  await capture(9, 'Sensitive prompt is blocked gracefully', async () => {
    await page.getByTestId('hero-search-input').fill('Show all Aadhaar numbers.')
    await page.getByRole('button', { name: 'Submit query' }).click()
    await expect(page.getByTestId('prompt-blocked')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('prompt-blocked')).toContainText(/sensitive information|privacy-safe/i)
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

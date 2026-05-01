import fs from 'fs'
import path from 'path'
import { test, expect, type APIRequestContext, type Page } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

const evidenceDir = path.resolve(
  process.cwd(),
  process.env.NRG_EVIDENCE_DIR || '../evidence/2026-05-01/glm_local_completion_gates',
)

async function login(request: APIRequestContext, username: string, password: string) {
  const response = await request.post('/login', {
    data: { username, password },
  })
  expect(response.ok()).toBeTruthy()
  return response.json()
}

async function captureAxe(page: Page, name: string) {
  fs.mkdirSync(evidenceDir, { recursive: true })
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()

  fs.writeFileSync(
    path.join(evidenceDir, `${name}.axe.json`),
    `${JSON.stringify({
      route: name,
      violations: results.violations.map(({ id, impact, description, nodes }) => ({
        id,
        impact,
        description,
        nodes: nodes.map((node) => ({ target: node.target, failureSummary: node.failureSummary })),
      })),
      incomplete: results.incomplete.map(({ id, impact, description, nodes }) => ({
        id,
        impact,
        description,
        nodes: nodes.map((node) => ({ target: node.target })),
      })),
    }, null, 2)}\n`
  )

  expect(results.violations, JSON.stringify(results.violations, null, 2)).toHaveLength(0)
  expect(results.incomplete.length, JSON.stringify(results.incomplete, null, 2)).toBeLessThanOrEqual(5)
}

test.use({
  viewport: { width: 1366, height: 850 },
})

test('GLM visible query answer path has no axe violations in answer, source, audit, and mobile states', async ({ page, request }) => {
  test.setTimeout(180000)

  const researcherSession = await login(request, 'researcher@iitgn.ac.in', 'Researcher@2026')
  expect(researcherSession.user.tier).toBe(1)

  await page.goto('/login')
  await expect(page.getByTestId('answer-engine-login')).toBeVisible()
  await page.getByTestId('login-username').fill('researcher@iitgn.ac.in')
  await page.getByTestId('login-password').fill('Researcher@2026')
  await page.getByTestId('login-submit').click()

  await expect(page.getByTestId('tier-dashboard')).toBeVisible({ timeout: 15000 })
  await page.goto('/app')
  await page.waitForLoadState('networkidle')
  await expect(page.getByRole('heading', { name: /What would you like to know/i })).toBeVisible({ timeout: 15000 })
  await page.getByRole('button', { name: 'Who are the top researchers in hydrogen catalysis?' }).click()

  await expect(page.getByTestId('phase-verified')).toBeVisible({ timeout: 45000 })
  await expect(page.getByTestId('answer-route')).toContainText(/hydrogen|catalysis/i)
  await captureAxe(page, '01_glm_answer_desktop')

  await page.getByTestId('answer-route-source-data-toggle').click()
  await expect(page.getByTestId('source-data-drawer')).toBeVisible()
  await captureAxe(page, '02_glm_source_drawer_desktop')
  await page.getByTestId('source-data-drawer').getByRole('button', { name: 'Close', exact: true }).click()

  await page.getByTestId('answer-route-audit-event-toggle').click()
  await expect(page.getByTestId('audit-event-drawer')).toBeVisible()
  await expect(page.getByTestId('hmac-proof')).toBeVisible()
  await captureAxe(page, '03_glm_audit_drawer_desktop')
  await page.getByTestId('audit-event-drawer').getByRole('button', { name: 'Close', exact: true }).click()

  await page.setViewportSize({ width: 393, height: 852 })
  await expect(page.getByTestId('phase-verified')).toBeVisible()
  await captureAxe(page, '04_glm_answer_mobile')
})

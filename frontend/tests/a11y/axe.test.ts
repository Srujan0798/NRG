import fs from 'fs'
import path from 'path'
import { test, expect, type Page } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { installAuthenticatedSession } from '../mocks/auth_session'

type PersonaRole = 'researcher' | 'government' | 'industry'

interface RouteCase {
  name: string
  path: string
  role?: PersonaRole
}

const routes: RouteCase[] = [
  { name: 'login', path: '/login' },
  { name: 'hero', path: '/app', role: 'researcher' },
  { name: 'founder', path: '/founder' },
  { name: 'researcher-dashboard', path: '/app/researcher', role: 'researcher' },
  { name: 'government-dashboard', path: '/app/government', role: 'government' },
  { name: 'industry-dashboard', path: '/app/industry', role: 'industry' },
]

async function installApiMocks(page: Page) {
  await page.route('**/{health,stats,researchers,publications,projects,patents,collaborations,funding,labs,research-documents}', async (route) => {
    const url = new URL(route.request().url())
    const payload = url.pathname.includes('health')
      ? { status: 'ok' }
      : { items: [], total: 0, data: [] }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(payload) })
  })

  await page.route('**/{query,query/**,audit,audit/**,consent,consent/**,me,me/**}', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0, data: [] }) })
  })
}

async function installSession(page: Page, role?: PersonaRole) {
  if (!role) return
  await installAuthenticatedSession(page, role)
}

function writeAxeReport(routeName: string, results: Awaited<ReturnType<AxeBuilder['analyze']>>) {
  const outputDir = path.resolve(process.cwd(), 'test-results/a11y')
  fs.mkdirSync(outputDir, { recursive: true })
  fs.writeFileSync(
    path.join(outputDir, `${routeName}.axe.json`),
    JSON.stringify({
      route: routeName,
      violations: results.violations.map(({ id, impact, description, nodes }) => ({
        id,
        impact,
        description,
        nodes: nodes.map((node) => ({ target: node.target, failureSummary: node.failureSummary })),
      })),
      warnings: results.incomplete.map(({ id, impact, description, nodes }) => ({
        id,
        impact,
        description,
        nodes: nodes.map((node) => ({ target: node.target })),
      })),
    }, null, 2)
  )
}

for (const routeCase of routes) {
  test(`${routeCase.name} has no axe violations and five or fewer warnings`, async ({ page }) => {
    await installApiMocks(page)
    await installSession(page, routeCase.role)
    await page.goto(routeCase.path)
    await page.locator('#main-content').waitFor({ state: 'attached' })
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(800)

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    writeAxeReport(routeCase.name, results)

    expect(results.violations, JSON.stringify(results.violations, null, 2)).toHaveLength(0)
    expect(results.incomplete.length, JSON.stringify(results.incomplete, null, 2)).toBeLessThanOrEqual(5)
  })
}

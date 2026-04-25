import fs from 'fs'
import path from 'path'
import { test, expect, type Page } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

type PersonaRole = 'researcher' | 'government' | 'industry'

interface RouteCase {
  name: string
  path: string
  role?: PersonaRole
}

const routes: RouteCase[] = [
  { name: 'login', path: '/' },
  { name: 'hero', path: '/app' },
  { name: 'founder', path: '/founder' },
  { name: 'researcher-dashboard', path: '/researcher', role: 'researcher' },
  { name: 'government-dashboard', path: '/government', role: 'government' },
  { name: 'industry-dashboard', path: '/industry', role: 'industry' },
]

const roleTier: Record<PersonaRole, number> = {
  researcher: 1,
  government: 2,
  industry: 3,
}

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
  await page.addInitScript(({ selectedRole, tier }) => {
    window.localStorage.setItem('nrg.auth.session', JSON.stringify({
      accessToken: 'a11y-access-token',
      refreshToken: 'a11y-refresh-token',
      tokenType: 'bearer',
      user: {
        id: `a11y-${selectedRole}`,
        username: `${selectedRole}_user`,
        role: selectedRole,
        tier,
      },
    }))
  }, { selectedRole: role, tier: roleTier[role] })
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

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    writeAxeReport(routeCase.name, results)

    expect(results.violations, JSON.stringify(results.violations, null, 2)).toHaveLength(0)
    expect(results.incomplete.length, JSON.stringify(results.incomplete, null, 2)).toBeLessThanOrEqual(5)
  })
}

import fs from 'fs'
import path from 'path'
import { test, expect, type Page } from '@playwright/test'
import { installStreamingQueryMock } from '../mocks/sse_server'

const IPHONE_15_VIEWPORT = { width: 393, height: 852 }

test.use({
  viewport: IPHONE_15_VIEWPORT,
  isMobile: true,
  hasTouch: true,
  deviceScaleFactor: 3,
  video: 'on',
})

async function expectNoPageHorizontalScroll(page: Page) {
  const metrics = await page.evaluate(() => ({
    viewportWidth: window.innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
  }))

  expect(metrics.scrollWidth).toBeLessThanOrEqual(metrics.viewportWidth)
  expect(metrics.bodyScrollWidth).toBeLessThanOrEqual(metrics.viewportWidth)
}

async function installDashboardMocks(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem('nrg.auth.session', JSON.stringify({
      accessToken: 'mobile-access-token',
      refreshToken: 'mobile-refresh-token',
      tokenType: 'bearer',
      user: {
        id: 'mobile-researcher',
        username: 'researcher_user',
        role: 'researcher',
        tier: 1,
      },
    }))
    const grantedAt = Date.now()
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

  await page.route('**/health', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'ok' }) })
  })

  await page.route('**/stats', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_researchers: 12847,
        total_publications: 38291,
        total_institutions: 312,
        research_areas: ['Renewable Energy', 'AI', 'Hydrogen', 'Materials'],
      }),
    })
  })

  await page.route('**/publications**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ publications: [], count: 0, tier: 1 }),
    })
  })

  await page.route('**/researchers**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ results: [], count: 0 }),
    })
  })

  await page.route('**/query/graph**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        nodes: [
          { id: 'topic-h2', label: 'Hydrogen fuel cells', type: 'topic', year: 2024, citations: 118 },
          { id: 'inst-iisc', label: 'IISc Bengaluru', type: 'institution', year: 2024, citations: 92 },
          { id: 'pub-1', label: 'Catalyst membrane study', type: 'paper', year: 2023, citations: 47 },
          { id: 'author-1', label: 'Energy systems lab', type: 'author', year: 2024, citations: 31 },
        ],
        edges: [
          { source: 'topic-h2', target: 'inst-iisc', type: 'related', weight: 0.9 },
          { source: 'topic-h2', target: 'pub-1', type: 'related', weight: 0.8 },
          { source: 'author-1', target: 'pub-1', type: 'authored', weight: 0.7 },
        ],
      }),
    })
  })
}

test.afterEach(async ({ page }, testInfo) => {
  const video = page.video()
  if (!video) return

  const evidenceDir = path.resolve(process.cwd(), '../evidence/2026-04-26')
  const evidencePath = path.join(evidenceDir, 'mobile_e2e.mp4')
  fs.mkdirSync(evidenceDir, { recursive: true })
  if (!page.isClosed()) await page.close()
  await video.saveAs(evidencePath)
  await testInfo.attach('mobile_e2e', { path: evidencePath, contentType: 'video/mp4' })
})

test('killer query and citation drawer work on iPhone without horizontal scroll', async ({ page }) => {
  await installStreamingQueryMock(page)
  await page.goto('/app')

  await expect(page.getByTestId('hero-search-input')).toBeVisible()
  await expectNoPageHorizontalScroll(page)

  await page.getByTestId('hero-search-input').fill('Which institutes in India have the highest grant amount in renewable energy?')
  await page.getByTestId('hero-search-input').press('Enter')

  await expect(page.getByTestId('phase-planning')).toBeVisible({ timeout: 500 })
  await expect(page.getByTestId('phase-verified')).toBeVisible({ timeout: 5000 })

  await page.getByRole('button', { name: /renewable energy funding summary/i }).tap()
  await expect(page.getByTestId('citation-drawer')).toBeVisible()
  await expect(page.getByText(/Citation Details/i)).toBeVisible()
  await expectNoPageHorizontalScroll(page)
})

test('mobile dashboard uses bottom-sheet persona switcher and fullscreen graph modal', async ({ page }) => {
  await installDashboardMocks(page)
  await page.goto('/researcher')
  await page.waitForLoadState('networkidle')

  await expect(page.getByTestId('mobile-persona-trigger')).toBeVisible({ timeout: 15000 })
  await page.getByTestId('mobile-persona-trigger').tap()
  const personaDialog = page.getByRole('dialog', { name: /Switch persona/i })
  await expect(personaDialog).toBeVisible()
  await expect(page.getByRole('button', { name: /Industry/i })).toBeVisible()
  await personaDialog.getByRole('button', { name: /Close/i }).tap()

  await page.getByTestId('tab-graph').tap()
  await expect(page.getByTestId('mobile-view-network')).toBeVisible()
  await expectNoPageHorizontalScroll(page)

  await page.getByTestId('mobile-view-network').tap()
  await expect(page.getByRole('dialog', { name: /Research network/i })).toBeVisible()
  await expect(page.locator('[data-testid="mobile-graph-modal"] svg[role="img"]')).toBeVisible()
  await expectNoPageHorizontalScroll(page)
})

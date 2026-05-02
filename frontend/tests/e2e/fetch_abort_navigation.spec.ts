import fs from 'fs'
import path from 'path'
import { test, expect } from '@playwright/test'
import { installAuthenticatedSession } from '../mocks/auth_session'

const evidenceDir = path.resolve(process.cwd(), '../evidence/2026-05-02/batch2_frontend_polish/network')

test('pending stats fetch is aborted when navigating away from query page', async ({ page }) => {
  await installAuthenticatedSession(page, 'researcher')

  await page.addInitScript(() => {
    const originalFetch = window.fetch.bind(window)
    const runtime = window as any
    runtime.__nrgActiveStatsFetches = 0
    runtime.__nrgAbortedStatsFetches = 0

    window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url
      if (!url.includes('/stats')) return originalFetch(input, init)

      runtime.__nrgActiveStatsFetches += 1
      return new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => {
          runtime.__nrgActiveStatsFetches -= 1
          runtime.__nrgAbortedStatsFetches += 1
          reject(init.signal?.reason || new DOMException('Route changed', 'AbortError'))
        }, { once: true })
      })
    }) as typeof window.fetch
  })

  await page.goto('/app')
  await page.waitForFunction(() => (window as any).__nrgActiveStatsFetches === 1)
  await page.getByRole('button', { name: 'Audit' }).click()

  await page.waitForFunction(() => (window as any).__nrgActiveStatsFetches === 0)
  const metrics = await page.evaluate(() => ({
    active_stats_fetches: (window as any).__nrgActiveStatsFetches,
    aborted_stats_fetches: (window as any).__nrgAbortedStatsFetches,
    path: window.location.pathname,
  }))

  expect(metrics).toEqual({
    active_stats_fetches: 0,
    aborted_stats_fetches: 1,
    path: '/app/audit',
  })

  fs.mkdirSync(evidenceDir, { recursive: true })
  fs.writeFileSync(path.join(evidenceDir, 'fetch_abort_navigation.json'), `${JSON.stringify(metrics, null, 2)}\n`)
})

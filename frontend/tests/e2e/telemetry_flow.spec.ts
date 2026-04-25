import { test, expect } from '@playwright/test'
import { installStreamingQueryMock } from '../mocks/sse_server'

test('submit query emits ordered telemetry batch without PII', async ({ page }) => {
  const receivedEvents: Array<{ event: string; payload: Record<string, unknown> }> = []

  await page.route('**/api/telemetry', async (route) => {
    const body = route.request().postDataJSON() as { events?: Array<{ event: string; payload: Record<string, unknown> }> }
    receivedEvents.push(...(body.events ?? []))
    await route.fulfill({
      status: 202,
      contentType: 'application/json',
      body: JSON.stringify({ accepted: body.events?.length ?? 0 }),
    })
  })

  await installStreamingQueryMock(page)
  await page.goto('/app')

  await page.getByTestId('hero-search-input').fill('Which institutes in India have the highest grant amount in renewable energy? Aadhaar 1234 5678 9012')
  await page.getByTestId('hero-search-input').press('Enter')
  await expect(page.getByTestId('phase-verified')).toBeVisible({ timeout: 5000 })

  await page.evaluate(async () => {
    await (window as any).__nrgTelemetry?.flush()
  })

  const queryEvents = receivedEvents.filter((event) => event.event.startsWith('query.'))
  expect(queryEvents.map((event) => event.event)).toEqual([
    'query.submitted',
    'query.phase_observed',
    'query.phase_observed',
    'query.phase_observed',
    'query.completed',
  ])
  expect(queryEvents.slice(1, 4).map((event) => event.payload.phase)).toEqual([
    'planned',
    'executing',
    'synthesizing',
  ])
  expect(queryEvents[0].payload.query_chars).toBe(99)
  expect(JSON.stringify(receivedEvents)).not.toContain('1234 5678 9012')
  expect(JSON.stringify(receivedEvents)).not.toContain('Aadhaar')
})

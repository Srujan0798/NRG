import fs from 'fs'
import path from 'path'
import { test, expect } from '@playwright/test'
import { installAuthenticatedSession } from '../mocks/auth_session'

const evidenceDir = path.resolve(process.cwd(), '../evidence/2026-05-02/batch2_frontend_polish/sse')

test('active stream stays visually stable across transient token-refresh reconnect', async ({ page }) => {
  await installAuthenticatedSession(page, 'researcher')

  await page.addInitScript(() => {
    type Listener = (event: MessageEvent<string>) => void

    class ReconnectEventSource {
      public onmessage: Listener | null = null
      public onerror: ((event: Event) => void) | null = null
      private listeners = new Map<string, Listener[]>()
      private closed = false

      constructor() {
        const events = [
          { delay: 20, type: 'planned', payload: { phase: 'planned', plan: { steps: ['Classify research intent', 'Keep partial answer visible', 'Verify cited answer'] } } },
          { delay: 80, type: 'synthesizing', payload: { phase: 'synthesizing', token: 'IISc Bengaluru and IIT Bombay ' } },
          { delay: 140, type: 'error', payload: null },
          { delay: 260, type: 'synthesizing', payload: { phase: 'synthesizing', token: 'remain visible after token refresh.' } },
          {
            delay: 340,
            type: 'verified',
            payload: {
              phase: 'verified',
              citations: [{ id: 'pub:reconnect:001', pub_id: 'pub-reconnect-001', chunk_id: '0', title: 'Reconnect stream source' }],
              audit_event_id: 'hmac-reconnect-001',
              signature_bytes: 26,
              provenance: { synth: 'rule_based_hybrid', cloud_synthesis_used: false },
            },
          },
        ]

        for (const event of events) {
          window.setTimeout(() => {
            if (this.closed) return
            if (event.type === 'error') {
              const runtime = window as any
              runtime.__nrgReconnectStartedAt = performance.now()
              this.onerror?.(new Event('error'))
              return
            }
            if ((window as any).__nrgReconnectStartedAt && !(window as any).__nrgReconnectRecoveredAt) {
              const runtime = window as any
              runtime.__nrgReconnectRecoveredAt = performance.now()
            }
            this.dispatch(event.type, event.payload)
          }, event.delay)
        }
      }

      addEventListener(type: string, listener: EventListenerOrEventListenerObject) {
        const current = this.listeners.get(type) ?? []
        this.listeners.set(type, [...current, listener as Listener])
      }

      close() {
        this.closed = true
      }

      private dispatch(type: string, payload: unknown) {
        const event = { data: JSON.stringify(payload) } as MessageEvent<string>
        for (const listener of this.listeners.get(type) ?? []) listener(event)
        if (type === 'message') this.onmessage?.(event)
      }
    }

    window.EventSource = ReconnectEventSource as unknown as typeof EventSource
  })

  await page.goto('/app')
  await page.getByTestId('answer-engine-query').fill('Who leads quantum research after token refresh?')
  await page.getByTestId('answer-engine-query').press('Enter')

  await expect(page.getByText('IISc Bengaluru and IIT Bombay')).toBeVisible({ timeout: 1000 })
  const beforeErrorBox = await page.getByTestId('streaming-answer-panel').boundingBox()
  await page.waitForFunction(() => Boolean((window as any).__nrgReconnectStartedAt))

  await expect(page.getByText('IISc Bengaluru and IIT Bombay')).toBeVisible()
  await expect(page.getByText(/NRG could not complete this request/i)).toHaveCount(0)

  await expect(page.getByText('remain visible after token refresh')).toBeVisible({ timeout: 1000 })
  const afterRecoveryBox = await page.getByTestId('streaming-answer-panel').boundingBox()
  const reconnectMs = await page.evaluate(() => {
    const started = (window as any).__nrgReconnectStartedAt
    const recovered = (window as any).__nrgReconnectRecoveredAt
    return Math.round(recovered - started)
  })

  expect(reconnectMs).toBeLessThan(500)
  expect(afterRecoveryBox?.y).toBe(beforeErrorBox?.y)
  await expect(page.getByTestId('phase-verified')).toBeVisible({ timeout: 1500 })

  fs.mkdirSync(evidenceDir, { recursive: true })
  await page.screenshot({ path: path.join(evidenceDir, 'sse_reconnect_stable.png'), fullPage: true })
  fs.writeFileSync(
    path.join(evidenceDir, 'sse_reconnect_metrics.json'),
    `${JSON.stringify({ reconnect_ms: reconnectMs, visual_y_stable: afterRecoveryBox?.y === beforeErrorBox?.y }, null, 2)}\n`,
  )
})

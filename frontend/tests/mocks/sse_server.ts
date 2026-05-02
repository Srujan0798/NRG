import type { Page } from '@playwright/test'
import { installAuthenticatedSession, loadAnswerEngineApp } from './auth_session'

export { loadAnswerEngineApp }

export async function installStreamingQueryMock(page: Page, role: 'researcher' | 'government' | 'industry' = 'researcher') {
  await installAuthenticatedSession(page, role)

  await page.addInitScript(() => {
    type Listener = (event: MessageEvent<string>) => void

    class MockEventSource {
      public onmessage: Listener | null = null
      public onerror: ((event: Event) => void) | null = null
      private listeners = new Map<string, Listener[]>()
      private closed = false

      constructor() {
        const events = [
          { delay: 20, type: 'planned', payload: { phase: 'planned', plan: { steps: ['Classify research intent', 'Find grant records', 'Prepare verifiable answer'] } } },
          { delay: 80, type: 'executing', payload: { phase: 'executing', sql: 'SELECT institute, SUM(grant_amount_inr) FROM grants GROUP BY institute ORDER BY 2 DESC LIMIT 5;', retrieved_count: 183 } },
          { delay: 140, type: 'synthesizing', payload: { phase: 'synthesizing', token: 'IIT Madras, IISc Bengaluru, and IIT Bombay lead the renewable energy grant pool. ' } },
          { delay: 220, type: 'synthesizing', payload: { phase: 'synthesizing', token: 'The ranked answer is backed by signed grant and publication records.' } },
          {
            delay: 320,
            type: 'verified',
            payload: {
              phase: 'verified',
              citations: [{ id: 'pub:renewable:001', pub_id: 'pub-renewable-001', chunk_id: '0', title: 'Renewable energy funding summary' }],
              audit_event_id: 'hmac-renewable-001',
              signature_bytes: 26,
              provenance: {
                synth: 'rule_based_hybrid',
                cloud_synthesis_used: false,
                hybrid_evidence: { sql_rows: 183, document_chunks: 4 },
              },
            },
          },
        ]

        for (const event of events) {
          window.setTimeout(() => {
            if (this.closed) return
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

    window.EventSource = MockEventSource as unknown as typeof EventSource
  })

  await page.route('**/api/query/stream**', async (route) => {
    const body = [
      'event: planned',
      'data: {"phase":"planned","plan":{"steps":["Classify research intent","Find grant records","Prepare verifiable answer"]}}',
      '',
      'event: executing',
      'data: {"phase":"executing","sql":"SELECT institute, SUM(grant_amount_inr) FROM grants GROUP BY institute ORDER BY 2 DESC LIMIT 5;","retrieved_count":183}',
      '',
      'event: synthesizing',
      'data: {"phase":"synthesizing","token":"IIT Madras, IISc Bengaluru, and IIT Bombay lead the renewable energy grant pool. "}',
      '',
      'event: synthesizing',
      'data: {"phase":"synthesizing","token":"The ranked answer is backed by signed grant and publication records."}',
      '',
      'event: verified',
      'data: {"phase":"verified","citations":[{"id":"pub:renewable:001","pub_id":"pub-renewable-001","chunk_id":"0","title":"Renewable energy funding summary"}],"audit_event_id":"hmac-renewable-001","signature_bytes":26,"provenance":{"synth":"rule_based_hybrid","cloud_synthesis_used":false,"hybrid_evidence":{"sql_rows":183,"document_chunks":4}}}',
      '',
    ].join('\n')

    await route.fulfill({
      status: 200,
      headers: {
        'content-type': 'text/event-stream',
        'cache-control': 'no-cache',
      },
      body,
    })
  })
}

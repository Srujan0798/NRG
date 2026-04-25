import {
  createTelemetryEvent,
  stripTelemetryPII,
  telemetryEventNames,
  trackQuerySubmitted,
} from '../../src/lib/telemetry'
import {
  configureTelemetryQueue,
  flushTelemetryQueue,
  resetTelemetryQueueForTests,
} from '../../src/lib/telemetryQueue'

describe('telemetry event contract', () => {
  beforeEach(() => {
    resetTelemetryQueueForTests()
    Object.defineProperty(window, 'location', {
      value: { pathname: '/app' },
      writable: true,
    })
    window.sessionStorage.clear()
  })

  it('creates structured events with stable metadata', () => {
    const event = createTelemetryEvent(
      'query.completed',
      { total_ms: 1240, citation_count: 2, persona: 'researcher' },
      { sessionId: 'uat-session-1', route: '/app' },
    )

    expect(telemetryEventNames).toContain(event.event)
    expect(event).toMatchObject({
      event: 'query.completed',
      schema_version: 1,
      session_id: 'uat-session-1',
      route: '/app',
      payload: { total_ms: 1240, citation_count: 2, persona: 'researcher' },
    })
    expect(event.event_id).toMatch(/^tel_/)
    expect(new Date(event.ts).toString()).not.toBe('Invalid Date')
  })

  it('strips PII recursively before events leave the browser edge', () => {
    const redacted = stripTelemetryPII({
      email: 'professor@example.com',
      aadhaar: '1234 5678 9012',
      pan: 'ABCDE1234F',
      phone: '9876543210',
      nested: ['Reach me at founder@nrg.test'],
    })

    expect(JSON.stringify(redacted)).not.toContain('professor@example.com')
    expect(JSON.stringify(redacted)).not.toContain('1234 5678 9012')
    expect(JSON.stringify(redacted)).not.toContain('ABCDE1234F')
    expect(JSON.stringify(redacted)).not.toContain('9876543210')
    expect(redacted).toEqual({
      email: '[EMAIL_REDACTED]',
      aadhaar: '[AADHAAR_REDACTED]',
      pan: '[PAN_REDACTED]',
      phone: '[PHONE_REDACTED]',
      nested: ['Reach me at [EMAIL_REDACTED]'],
    })
  })

  it('tracks query submissions by length without storing raw query text', async () => {
    const postedBodies: unknown[] = []
    configureTelemetryQueue({
      fetcher: async (_url, init) => {
        postedBodies.push(JSON.parse(String(init?.body)))
        return new Response(null, { status: 202 })
      },
      autoStart: false,
    })

    trackQuerySubmitted('Show all researchers with Aadhaar 1234 5678 9012', 'researcher', {
      sessionId: 'demo-session',
    })
    await flushTelemetryQueue()

    expect(postedBodies).toHaveLength(1)
    const [event] = (postedBodies[0] as { events: Array<{ payload: Record<string, unknown> }> }).events
    expect(event.payload).toMatchObject({
      query_chars: 48,
      persona: 'researcher',
      session_id: 'demo-session',
    })
    expect(JSON.stringify(event)).not.toContain('Aadhaar')
    expect(JSON.stringify(event)).not.toContain('1234 5678 9012')
  })
})

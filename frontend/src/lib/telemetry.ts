import { authService, PersonaRole } from '../services/authService'
import { enqueueTelemetryEvent } from './telemetryQueue'

export const telemetryEventNames = [
  'app.first_paint',
  'query.submitted',
  'query.phase_observed',
  'query.completed',
  'query.aborted',
  'citation.opened',
  'audit.verified',
  'proof.verify_clicked',
  'proof.verified',
  'persona.switched',
  'error.shown',
  'ui.error_boundary',
  'dpdp.sync_failed',
  'dpdp.export_failed',
  'dpdp.erasure_failed',
  'empty.shown',
] as const

export type TelemetryEventName = typeof telemetryEventNames[number]
export type TelemetryPayload = Record<string, unknown>

export interface TelemetryEvent {
  schema_version: 1
  event_id: string
  event: TelemetryEventName
  ts: string
  session_id: string
  route: string
  payload: TelemetryPayload
}

interface TelemetryContext {
  sessionId?: string
  route?: string
}

const SESSION_STORAGE_KEY = 'nrg.telemetry.session_id'
const FIRST_PAINT_STORAGE_KEY = 'nrg.telemetry.first_paint_emitted'

const PII_PATTERNS: Array<[RegExp, string]> = [
  [/\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b/g, '[AADHAAR_REDACTED]'],
  [/\b[A-Z]{5}[0-9]{4}[A-Z]\b/g, '[PAN_REDACTED]'],
  [/\b[6-9][0-9]{9}\b/g, '[PHONE_REDACTED]'],
  [/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, '[EMAIL_REDACTED]'],
]

const newId = (prefix: string) => {
  const random = typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`
  return `${prefix}_${random}`
}

const safeSessionStorage = (): Storage | null => {
  try {
    if (typeof window === 'undefined') return null
    return window.sessionStorage
  } catch {
    return null
  }
}

const currentRoute = () => {
  if (typeof window === 'undefined') return 'server'
  return window.location.pathname || '/'
}

export function getTelemetrySessionId(): string {
  const storage = safeSessionStorage()
  const existing = storage?.getItem(SESSION_STORAGE_KEY)
  if (existing) return existing

  const userSession = (() => {
    try {
      return authService.getStoredSession()?.user?.id
    } catch {
      return null
    }
  })()
  const next = userSession || newId('uat_session')
  storage?.setItem(SESSION_STORAGE_KEY, next)
  return next
}

export function stripTelemetryPII<T>(value: T): T {
  if (typeof value === 'string') {
    return PII_PATTERNS.reduce((current, [pattern, replacement]) => current.replace(pattern, replacement), value) as T
  }

  if (Array.isArray(value)) {
    return value.map((item) => stripTelemetryPII(item)) as T
  }

  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, item]) => [key, stripTelemetryPII(item)])
    ) as T
  }

  return value
}

export function createTelemetryEvent(
  event: TelemetryEventName,
  payload: TelemetryPayload = {},
  context: TelemetryContext = {},
): TelemetryEvent {
  const sessionId = context.sessionId || getTelemetrySessionId()
  return {
    schema_version: 1,
    event_id: newId('tel'),
    event,
    ts: new Date().toISOString(),
    session_id: stripTelemetryPII(sessionId),
    route: stripTelemetryPII(context.route || currentRoute()),
    payload: stripTelemetryPII(payload),
  }
}

export function emitTelemetry(
  event: TelemetryEventName,
  payload: TelemetryPayload = {},
  context: TelemetryContext = {},
): TelemetryEvent {
  const telemetryEvent = createTelemetryEvent(event, payload, context)
  enqueueTelemetryEvent(telemetryEvent)
  return telemetryEvent
}

export function trackQuerySubmitted(
  query: string,
  persona: PersonaRole | 'anonymous',
  context: TelemetryContext = {},
): TelemetryEvent {
  const sessionId = context.sessionId || getTelemetrySessionId()
  return emitTelemetry('query.submitted', {
    query_chars: query.length,
    persona,
    session_id: sessionId,
  }, { ...context, sessionId })
}

export function trackFirstPaint() {
  const storage = safeSessionStorage()
  if (storage?.getItem(FIRST_PAINT_STORAGE_KEY)) return
  storage?.setItem(FIRST_PAINT_STORAGE_KEY, 'true')

  const readMetrics = () => {
    const perf = typeof performance !== 'undefined' ? performance : null
    const fcp = perf?.getEntriesByName('first-contentful-paint')[0]?.startTime
    emitTelemetry('app.first_paint', {
      fcp_ms: Math.round(fcp ?? perf?.now() ?? 0),
      tti_ms: Math.round(perf?.now() ?? 0),
      cls: Number((window as any).__nrgCls ?? 0),
    })
  }

  if (typeof window === 'undefined') return
  window.setTimeout(readMetrics, 0)
}

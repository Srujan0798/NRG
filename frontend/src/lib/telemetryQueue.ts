import type { TelemetryEvent } from './telemetry'

type TelemetryFetcher = (input: string, init?: RequestInit) => Promise<Response>

interface TelemetryQueueConfig {
  endpoint?: string
  flushIntervalMs?: number
  fetcher?: TelemetryFetcher
  autoStart?: boolean
}

const DEFAULT_ENDPOINT = '/api/telemetry'
const DEFAULT_FLUSH_INTERVAL_MS = 10000
const MAX_BATCH_SIZE = 100

let queue: TelemetryEvent[] = []
let flushTimer: number | null = null
let endpoint = DEFAULT_ENDPOINT
let flushIntervalMs = DEFAULT_FLUSH_INTERVAL_MS
let fetcher: TelemetryFetcher | null = null
let autoStart = true

const getFetcher = (): TelemetryFetcher | null => {
  if (fetcher) return fetcher
  if (typeof window === 'undefined' || typeof window.fetch !== 'function') return null
  return window.fetch.bind(window)
}

const exposeDebugHandle = () => {
  if (typeof window === 'undefined') return
  window.__nrgTelemetry = {
    flush: flushTelemetryQueue,
    queueSize: () => queue.length,
  }
}

export function configureTelemetryQueue(config: TelemetryQueueConfig = {}) {
  endpoint = config.endpoint ?? endpoint
  flushIntervalMs = config.flushIntervalMs ?? flushIntervalMs
  fetcher = config.fetcher ?? fetcher
  autoStart = config.autoStart ?? autoStart
  exposeDebugHandle()
}

export function startTelemetryQueue() {
  if (!autoStart || typeof window === 'undefined' || flushTimer) {
    exposeDebugHandle()
    return
  }

  flushTimer = window.setInterval(() => {
    void flushTelemetryQueue()
  }, flushIntervalMs)
  exposeDebugHandle()
}

export function stopTelemetryQueue() {
  if (flushTimer) {
    window.clearInterval(flushTimer)
    flushTimer = null
  }
}

export function enqueueTelemetryEvent(event: TelemetryEvent) {
  queue.push(event)
  startTelemetryQueue()
}

export async function flushTelemetryQueue(): Promise<{ accepted: number; attempted: number }> {
  if (queue.length === 0) return { accepted: 0, attempted: 0 }

  const activeFetcher = getFetcher()
  if (!activeFetcher) return { accepted: 0, attempted: 0 }

  const batch = queue.splice(0, MAX_BATCH_SIZE)
  try {
    const response = await activeFetcher(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ events: batch }),
      keepalive: true,
    })

    if (!response.ok) {
      queue = [...batch, ...queue]
      return { accepted: 0, attempted: batch.length }
    }

    return { accepted: batch.length, attempted: batch.length }
  } catch {
    queue = [...batch, ...queue]
    return { accepted: 0, attempted: batch.length }
  }
}

export function getTelemetryQueueSize() {
  return queue.length
}

export function resetTelemetryQueueForTests() {
  stopTelemetryQueue()
  queue = []
  endpoint = DEFAULT_ENDPOINT
  flushIntervalMs = DEFAULT_FLUSH_INTERVAL_MS
  fetcher = null
  autoStart = true
  if (typeof window !== 'undefined') {
    delete window.__nrgTelemetry
  }
}

declare global {
  interface Window {
    __nrgTelemetry?: {
      flush: () => Promise<{ accepted: number; attempted: number }>
      queueSize: () => number
    }
  }
}

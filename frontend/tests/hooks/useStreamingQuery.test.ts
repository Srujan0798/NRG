import React, { act, useEffect } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { useStreamingQuery, EventSourceLike } from '../../src/hooks/useStreamingQuery'

globalThis.IS_REACT_ACT_ENVIRONMENT = true

type Listener = (event: MessageEvent<string>) => void

class FakeEventSource implements EventSourceLike {
  public listeners = new Map<string, Listener[]>()
  public onmessage: ((event: MessageEvent<string>) => void) | null = null
  public onerror: ((event: Event) => void) | null = null
  public closed = false

  addEventListener(type: string, listener: EventListenerOrEventListenerObject) {
    const handler = listener as Listener
    const current = this.listeners.get(type) ?? []
    this.listeners.set(type, [...current, handler])
  }

  close() {
    this.closed = true
  }

  emit(type: string, payload: unknown = {}) {
    const data = typeof payload === 'string' ? payload : JSON.stringify(payload)
    const event = { data } as MessageEvent<string>
    for (const listener of this.listeners.get(type) ?? []) listener(event)
  }
}

const roots: Array<{ root: Root; container: HTMLDivElement }> = []

function renderHook(source: FakeEventSource, silenceTimeoutMs = 25000) {
  const snapshots: Array<ReturnType<typeof useStreamingQuery>> = []

  const Probe = () => {
    const hook = useStreamingQuery({
      eventSourceFactory: () => source,
      silenceTimeoutMs,
    })

    useEffect(() => {
      snapshots.push(hook)
    })

    return null
  }

  const container = document.createElement('div')
  document.body.appendChild(container)
  const root = createRoot(container)
  act(() => root.render(React.createElement(Probe)))
  roots.push({ root, container })

  return {
    latest: () => snapshots[snapshots.length - 1],
  }
}

afterEach(() => {
  for (const { root, container } of roots.splice(0)) {
    act(() => root.unmount())
    container.remove()
  }
  jest.useRealTimers()
})

describe('useStreamingQuery', () => {
  it('closes the active stream when aborted', () => {
    const source = new FakeEventSource()
    const hook = renderHook(source)

    act(() => {
      hook.latest().startStream('Top funding agencies')
    })
    expect(hook.latest().isStreaming).toBe(true)

    act(() => {
      hook.latest().abortStream()
    })

    expect(source.closed).toBe(true)
    expect(hook.latest().isStreaming).toBe(false)
  })

  it('treats heartbeat events as activity', () => {
    jest.useFakeTimers()
    const source = new FakeEventSource()
    const hook = renderHook(source)

    act(() => {
      hook.latest().startStream('Top funding agencies')
    })

    act(() => {
      jest.advanceTimersByTime(24000)
      source.emit('heartbeat')
      jest.advanceTimersByTime(24000)
    })

    expect(hook.latest().error).toBeNull()
    expect(hook.latest().isRecoverableError).toBe(false)
    expect(source.closed).toBe(false)
  })

  it('turns 25 seconds of silence into a recoverable user-facing error', () => {
    jest.useFakeTimers()
    const source = new FakeEventSource()
    const hook = renderHook(source)

    act(() => {
      hook.latest().startStream('Top funding agencies')
    })

    act(() => {
      jest.advanceTimersByTime(25000)
    })

    expect(hook.latest().isStreaming).toBe(false)
    expect(hook.latest().isRecoverableError).toBe(true)
    expect(hook.latest().error).toBe('This is taking longer than usual. Please try again.')
    expect(source.closed).toBe(true)
  })

  it('preserves low confidence from streamed answer payloads', () => {
    const source = new FakeEventSource()
    const hook = renderHook(source)

    act(() => {
      hook.latest().startStream('unclear AI query')
      source.emit('answer', {
        phase: 'answer',
        response: 'Please ask a clearer research question.',
        answer_confidence: 'needs_clarification',
        citations: [],
        sql_results: [],
      })
    })

    expect(hook.latest().answerConfidence).toBe('needs_clarification')
    expect(hook.latest().isVerified).toBe(true)
  })
})

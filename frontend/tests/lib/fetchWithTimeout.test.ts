import { fetchWithTimeout } from '../../src/utils/fetchWithTimeout'

describe('fetchWithTimeout', () => {
  afterEach(() => {
    jest.useRealTimers()
    jest.restoreAllMocks()
    delete (global as any).fetch
  })

  it('aborts a request after the configured timeout', async () => {
    jest.useFakeTimers()
    const fetchMock = jest.fn((_input, init) => new Promise((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => reject(init.signal?.reason || new DOMException('Aborted', 'AbortError')))
    }) as Promise<Response>)
    ;(global as any).fetch = fetchMock

    const request = fetchWithTimeout('/health', { timeoutMs: 25 })

    jest.advanceTimersByTime(25)

    await expect(request).rejects.toMatchObject({ name: 'TimeoutError' })
    expect(fetchMock.mock.calls[0][1]?.signal).toBeInstanceOf(AbortSignal)
  })

  it('propagates caller aborts to the underlying fetch', async () => {
    const controller = new AbortController()
    ;(global as any).fetch = jest.fn((_input, init) => new Promise((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => reject(init.signal?.reason || new DOMException('Aborted', 'AbortError')))
    }) as Promise<Response>)

    const request = fetchWithTimeout('/stats', { signal: controller.signal, timeoutMs: 1000 })
    controller.abort(new DOMException('Route changed', 'AbortError'))

    await expect(request).rejects.toMatchObject({ name: 'AbortError' })
  })
})

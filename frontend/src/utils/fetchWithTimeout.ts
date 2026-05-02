export interface FetchWithTimeoutInit extends RequestInit {
  timeoutMs?: number
}

export async function fetchWithTimeout(
  input: RequestInfo | URL,
  { timeoutMs = 15000, signal, ...init }: FetchWithTimeoutInit = {},
): Promise<Response> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => {
    controller.abort(new DOMException('Request timed out', 'TimeoutError'))
  }, timeoutMs)

  const abortFromCaller = () => {
    controller.abort(signal?.reason || new DOMException('Request aborted', 'AbortError'))
  }

  if (signal?.aborted) {
    abortFromCaller()
  } else {
    signal?.addEventListener('abort', abortFromCaller, { once: true })
  }

  try {
    return await fetch(input, {
      ...init,
      signal: controller.signal,
    })
  } finally {
    window.clearTimeout(timeout)
    signal?.removeEventListener('abort', abortFromCaller)
  }
}

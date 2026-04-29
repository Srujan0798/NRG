import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import App from '../../src/App'
import { ThemeProvider } from '../../src/design-system/ThemeProvider'
import { authService, type AuthSession } from '../../src/services/authService'
import { queryService } from '../../src/services/queryService'

jest.mock('../../src/components/Skeleton/SkeletonLoader', () => ({
  SkeletonLoader: () => <div data-testid="skeleton-loader" />,
}))

globalThis.IS_REACT_ACT_ENVIRONMENT = true

const roots: Array<{ root: Root; container: HTMLDivElement }> = []

const researcherSession: AuthSession = {
  accessToken: '',
  refreshToken: '',
  tokenType: 'cookie',
  user: {
    id: 'u-researcher',
    username: 'researcher@iitgn.ac.in',
    role: 'researcher',
    tier: 1,
  },
}

function renderApp(pathname: string, session: AuthSession | null = researcherSession) {
  window.history.pushState({}, '', pathname)
  sessionStorage.clear()
  if (session) {
    sessionStorage.setItem('nrg.auth.session', JSON.stringify(session))
  }

  const container = document.createElement('div')
  document.body.appendChild(container)
  const root = createRoot(container)
  act(() => root.render(
    <ThemeProvider>
      <App />
    </ThemeProvider>
  ))
  roots.push({ root, container })
  return container
}

async function flushAuthEffects() {
  await act(async () => {
    await Promise.resolve()
    await Promise.resolve()
  })
}

beforeEach(() => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  })
  Object.defineProperty(window.performance, 'getEntriesByName', {
    writable: true,
    value: jest.fn().mockReturnValue([]),
  })
  jest.spyOn(authService, 'fetchSession').mockRejectedValue(new Error('No cookie session'))
  jest.spyOn(queryService, 'listAuditEvents').mockResolvedValue({
    chain_status: 'intact',
    total: 1,
    events: [
      {
        id: 'audit-route-1',
        hmac: 'hmac-route-1',
        timestamp: new Date(Date.UTC(2026, 3, 29, 9, 0)).toISOString(),
        actor: 'ministry@nrg.gov.in',
        persona: 'government',
        action: 'query.executed',
        integrity_status: 'intact',
        tier: 2,
      },
    ],
  })
})

afterEach(() => {
  jest.restoreAllMocks()
  sessionStorage.clear()
  for (const { root, container } of roots.splice(0)) {
    act(() => root.unmount())
    container.remove()
  }
})

describe('App answer-engine routing', () => {
  it('renders the answer-engine login surface at /login', async () => {
    const container = renderApp('/login', null)

    await flushAuthEffects()

    expect(container.querySelector('[data-testid="answer-engine-login"]')).not.toBeNull()
    expect(authService.fetchSession).not.toHaveBeenCalled()
  })

  it('maps role and audit routes to the answer-engine surfaces', async () => {
    const routes = [
      ['/app/researcher', 'tier-dashboard'],
      ['/app/government', 'tier-dashboard'],
      ['/app/industry', 'tier-dashboard'],
      ['/app/audit', 'audit-list'],
    ]

    for (const [path, testId] of routes) {
      const container = renderApp(path)
      await flushAuthEffects()

      expect(container.querySelector(`[data-testid="${testId}"]`)).not.toBeNull()

      const mounted = roots.pop()
      if (mounted) {
        act(() => mounted.root.unmount())
        mounted.container.remove()
      }
    }
  })

  it('keeps a successful login when startup session restore finishes late', async () => {
    let rejectRestore: ((error: Error) => void) | null = null
    jest.mocked(authService.fetchSession).mockImplementation(() => new Promise((_, reject) => {
      rejectRestore = reject
    }))
    jest.spyOn(authService, 'login').mockImplementation(async () => {
      authService.saveSession(researcherSession)
      return researcherSession
    })

    const container = renderApp('/login', null)
    await flushAuthEffects()

    const submit = container.querySelector('[data-testid="login-submit"]') as HTMLButtonElement
    await act(async () => {
      submit.dispatchEvent(new MouseEvent('click', { bubbles: true }))
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(window.location.pathname).toBe('/app/researcher')
    rejectRestore?.(new Error('late restore miss'))
    await flushAuthEffects()

    expect(window.location.pathname).toBe('/app/researcher')
    expect(container.querySelector('[data-testid="tier-dashboard"]')).not.toBeNull()
  })
})

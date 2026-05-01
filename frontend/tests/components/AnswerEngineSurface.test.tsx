import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import {
  AnswerEngineAnswer,
  AnswerEngineAudit,
  AnswerEngineDashboard,
  AnswerEngineHome,
  AnswerEngineLogin,
} from '../../src/views/AnswerEngine'
import { queryService } from '../../src/services/queryService'

globalThis.IS_REACT_ACT_ENVIRONMENT = true

const roots: Array<{ root: Root; container: HTMLDivElement }> = []

function render(ui: React.ReactElement) {
  const container = document.createElement('div')
  document.body.appendChild(container)
  const root = createRoot(container)
  act(() => root.render(ui))
  roots.push({ root, container })
  return container
}

async function flushStreamStart() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0))
    await Promise.resolve()
  })
}

afterEach(() => {
  jest.restoreAllMocks()
  for (const { root, container } of roots.splice(0)) {
    act(() => root.unmount())
    container.remove()
  }
})

describe('AnswerEngine surface', () => {
  it('renders the login screen as a focused auth surface', () => {
    const container = render(
      <AnswerEngineLogin
        onLogin={async () => true}
        error={null}
        backendAvailable
      />
    )

    expect(container.querySelector('[data-testid="answer-engine-login"]')).not.toBeNull()
    expect(container.querySelector('[data-testid="login-username"]')).not.toBeNull()
    expect(container.querySelector('[data-testid="login-password"]')).not.toBeNull()
    expect(container.textContent).toContain('Sovereign intelligence over India')
    expect(container.textContent).toContain('Sign in')
  })

  it('renders the hero with one primary query input and four suggestions', () => {
    const container = render(
      <AnswerEngineHome
        role="researcher"
        tier={1}
        username="researcher@iitgn.ac.in"
        onLogout={() => undefined}
        onQuerySubmit={() => undefined}
        onNavigate={() => undefined}
      />
    )

    expect(container.querySelector('[data-testid="answer-engine-hero"]')).not.toBeNull()
    expect(container.querySelectorAll('[data-testid="suggestion-chip"]')).toHaveLength(4)
    expect(container.querySelector('[data-testid="answer-engine-query"]')).not.toBeNull()
    expect(container.textContent).toContain("Sovereign intelligence over India's research database")
    expect(container.textContent).toContain('Who are the top researchers in hydrogen catalysis?')
    expect(container.textContent).toContain('List top 10 institutions by average researcher h-index')
  })

  it('shows persona-specific query suggestions without changing the primary query contract', () => {
    const container = render(
      <AnswerEngineHome
        role="industry"
        tier={3}
        username="partner@industry.in"
        onLogout={() => undefined}
        onQuerySubmit={() => undefined}
        onNavigate={() => undefined}
      />
    )

    expect(container.querySelectorAll('[data-testid="suggestion-chip"]')).toHaveLength(4)
    expect(container.querySelector('[data-testid="answer-engine-query"]')).not.toBeNull()
    expect(container.textContent).toContain('Which IIT has the strongest AI research program?')
    expect(container.textContent).toContain('Compare CSIR labs by research output')
    expect(container.textContent).not.toContain('Who are the top researchers in hydrogen catalysis?')
  })

  it('keeps tier dashboards to query-first layout plus three supporting panels', () => {
    const container = render(
      <AnswerEngineDashboard
        role="industry"
        tier={3}
        username="partner@industry.in"
        onLogout={() => undefined}
        onQuerySubmit={() => undefined}
        onNavigate={() => undefined}
      />
    )

    expect(container.querySelector('[data-testid="tier-dashboard"]')).not.toBeNull()
    expect(container.querySelectorAll('[data-testid="supporting-panel"]')).toHaveLength(3)
    expect(container.textContent).toContain('Industry view')
    expect(container.textContent).toContain('Knowledge map')
  })

  it('renders the audit list with filters and drawer-ready rows', async () => {
    jest.spyOn(queryService, 'listAuditEvents').mockResolvedValue({
      chain_status: 'intact',
      total: 20,
      events: Array.from({ length: 20 }, (_, index) => ({
        id: `audit-${index}`,
        hmac: `hmac-${index}`,
        timestamp: new Date(Date.UTC(2026, 3, 29, 8, index)).toISOString(),
        actor: 'ministry@nrg.gov.in',
        persona: 'government',
        action: 'query.executed',
        integrity_status: 'intact',
        tier: 2,
      })),
    })

    const container = render(
      <AnswerEngineAudit
        role="government"
        tier={2}
        username="ministry@nrg.gov.in"
        onLogout={() => undefined}
        onNavigate={() => undefined}
      />
    )

    await act(async () => {
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(container.querySelector('[data-testid="audit-list"]')).not.toBeNull()
    expect(container.querySelectorAll('[data-testid="audit-row"]').length).toBeGreaterThan(10)
    expect(container.textContent).toContain('Chain intact')
    expect(container.textContent).toContain('Filter by user')
  })

  it('starts only one stream for the answer route query', async () => {
    sessionStorage.setItem('nrg.lastQuery', 'Top funding agencies by total grant amount last 5 years')
    const stream = {
      addEventListener: jest.fn(),
      close: jest.fn(),
      onmessage: null,
      onerror: null,
    } as unknown as EventSource
    const streamSpy = jest.spyOn(queryService, 'streamQuery').mockReturnValue(stream)

    render(
      <AnswerEngineAnswer
        role="researcher"
        tier={1}
        username="researcher@iitgn.ac.in"
        onLogout={() => undefined}
        onNavigate={() => undefined}
      />
    )

    await flushStreamStart()

    expect(streamSpy).toHaveBeenCalledTimes(1)
  })

  it('does not duplicate the initial answer stream under React StrictMode', async () => {
    sessionStorage.setItem('nrg.lastQuery', 'Top funding agencies by total grant amount last 5 years')
    const stream = {
      addEventListener: jest.fn(),
      close: jest.fn(),
      onmessage: null,
      onerror: null,
    } as unknown as EventSource
    const streamSpy = jest.spyOn(queryService, 'streamQuery').mockReturnValue(stream)

    render(
      <React.StrictMode>
        <AnswerEngineAnswer
          role="researcher"
          tier={1}
          username="researcher@iitgn.ac.in"
          onLogout={() => undefined}
          onNavigate={() => undefined}
        />
      </React.StrictMode>
    )

    await flushStreamStart()

    expect(streamSpy).toHaveBeenCalledTimes(1)
  })

  it('starts a fresh stream when a follow-up query is submitted on the answer route', async () => {
    sessionStorage.setItem('nrg.lastQuery', 'Top funding agencies by total grant amount last 5 years')
    const stream = {
      addEventListener: jest.fn(),
      close: jest.fn(),
      onmessage: null,
      onerror: null,
    } as unknown as EventSource
    const streamSpy = jest.spyOn(queryService, 'streamQuery').mockReturnValue(stream)

    const container = render(
      <AnswerEngineAnswer
        role="researcher"
        tier={1}
        username="researcher@iitgn.ac.in"
        onLogout={() => undefined}
        onNavigate={() => undefined}
      />
    )

    await flushStreamStart()

    const input = container.querySelector('[data-testid="answer-engine-query"]') as HTMLInputElement
    const form = input.closest('form') as HTMLFormElement

    await act(async () => {
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set?.call(
        input,
        'TRL-9 innovations in clean energy'
      )
      input.dispatchEvent(new Event('input', { bubbles: true }))
      form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    })
    await flushStreamStart()

    expect(streamSpy).toHaveBeenCalledTimes(2)
    expect(streamSpy.mock.calls[1][0].query).toBe('TRL-9 innovations in clean energy')
    expect(container.textContent).toContain('TRL-9 innovations in clean energy')
  })
})

import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import ErrorState from '../../src/components/ErrorState/ErrorState'

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

afterEach(() => {
  for (const { root, container } of roots.splice(0)) {
    act(() => root.unmount())
    container.remove()
  }
})

describe('ErrorState', () => {
  it.each([
    ['recoverable', 'Try that again'],
    ['restricted', 'Access restricted'],
    ['system', 'Request not completed'],
  ] as const)('renders the %s tier without leaking traces', (tier, headline) => {
    const container = render(<ErrorState tier={tier} traceId="trace-secret-001" errorCode="E2E" />)
    const text = container.textContent || ''

    expect(text).toContain(headline)
    expect(text).not.toContain('trace-secret-001')
    expect(text).not.toContain('Traceback')
    expect(text).not.toContain('Error:')
  })

  it('sanitizes raw exception messages before rendering', () => {
    const container = render(<ErrorState tier="system" message="TypeError: Cannot read properties of undefined" />)
    const text = container.textContent || ''

    expect(text).toContain('Use the reference code')
    expect(text).not.toContain('TypeError:')
    expect(text).not.toContain('undefined')
  })
})

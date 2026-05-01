import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { ErrorBoundary } from '../../src/components/ErrorBoundary/ErrorBoundary'

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

const ThrowingWidget = () => {
  throw new Error('TypeError: Cannot read properties of undefined at SecretStack')
}

describe('ErrorBoundary', () => {
  let consoleError: jest.SpyInstance

  beforeEach(() => {
    consoleError = jest.spyOn(console, 'error').mockImplementation(() => undefined)
  })

  afterEach(() => {
    consoleError.mockRestore()
    for (const { root, container } of roots.splice(0)) {
      act(() => root.unmount())
      container.remove()
    }
  })

  it('renders a safe page recovery surface without raw exception details', () => {
    const container = render(
      <ErrorBoundary>
        <ThrowingWidget />
      </ErrorBoundary>,
    )

    const text = container.textContent || ''

    expect(container.querySelector('[data-testid="nrg-error-boundary"]')).not.toBeNull()
    expect(text).toContain('NRG could not render this section')
    expect(text).toContain('Reference code')
    expect(text).toContain('No research data was exposed')
    expect(text).not.toContain('TypeError')
    expect(text).not.toContain('undefined')
    expect(text).not.toContain('SecretStack')
    expect(container.querySelector('pre')).toBeNull()
  })

  it('renders a compact widget fallback without exposing a stack trace', () => {
    const container = render(
      <ErrorBoundary scope="widget">
        <ThrowingWidget />
      </ErrorBoundary>,
    )

    const text = container.textContent || ''

    expect(text).toContain('Widget failed to load')
    expect(text).toContain('Reference code')
    expect(text).not.toContain('TypeError')
    expect(text).not.toContain('SecretStack')
    expect(container.querySelector('pre')).toBeNull()
  })
})

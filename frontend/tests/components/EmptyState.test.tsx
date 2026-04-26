import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import EmptyState from '../../src/components/EmptyState/EmptyState'

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

describe('EmptyState', () => {
  it.each([
    ['noData', 'No data found'],
    ['noCitations', 'No citations available'],
    ['noAuditEvents', 'No audit events yet'],
    ['noPublications', 'No publications found'],
    ['noGraph', 'No graph edges found'],
    ['noFilters', 'No filters selected'],
  ] as const)('renders copy and CTA for %s', (cause, headline) => {
    const onPrimary = jest.fn()
    const container = render(<EmptyState cause={cause} onPrimary={onPrimary} />)

    expect(container.textContent).toContain(headline)
    const button = container.querySelector('button') as HTMLButtonElement
    expect(button).not.toBeNull()
    expect(button.textContent?.trim().length).toBeGreaterThan(3)
  })
})

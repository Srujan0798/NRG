import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { OperationsShell } from '../../src/components/OperationsShell/OperationsShell'

jest.mock('../../src/components/PersonaToggle', () => ({
  __esModule: true,
  default: () => <div data-testid="persona-toggle">Persona toggle</div>,
}))

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

describe('OperationsShell', () => {
  it('renders shell landmarks and tier scope', () => {
    const container = render(
      <OperationsShell
        role="researcher"
        tier={1}
        username="researcher@iitgn.ac.in"
        onLogout={() => undefined}
        inspector={<div data-testid="proof-slot">Proof slot</div>}
      >
        <div data-testid="workbench-slot">Workbench slot</div>
      </OperationsShell>
    )

    expect(container.querySelector('[data-testid="operations-shell"]')).not.toBeNull()
    expect(container.querySelector('main')).not.toBeNull()
    expect(container.querySelector('nav')).not.toBeNull()
    expect(container.querySelector('[data-testid="tier-scope-banner"]')?.textContent).toContain('Researcher')
    expect(container.querySelector('[data-testid="workbench-slot"]')).not.toBeNull()
    expect(container.querySelector('[data-testid="proof-slot"]')).not.toBeNull()
  })
})

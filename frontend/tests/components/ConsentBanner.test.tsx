import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { ConsentBanner } from '../../src/components/ConsentBanner'

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
  localStorage.clear()
})

describe('ConsentBanner', () => {
  it('persists dismissal for the active role across reloads', () => {
    const container = render(<ConsentBanner role="researcher" />)
    const dismiss = container.querySelector('[data-testid="dismiss-consent-banner"]') as HTMLButtonElement

    act(() => {
      dismiss.click()
    })

    expect(localStorage.getItem('nrg.consentBanner.dismissed.researcher')).toBe('true')

    const reloaded = render(<ConsentBanner role="researcher" />)
    expect(reloaded.textContent).not.toContain('DPDP Act 2023')
  })
})

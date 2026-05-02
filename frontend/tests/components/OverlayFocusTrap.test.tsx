import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { Drawer, Modal } from '../../src/components/ui'

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

function pressTab(shiftKey = false) {
  act(() => {
    document.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'Tab',
      shiftKey,
      bubbles: true,
      cancelable: true,
    }))
  })
}

afterEach(() => {
  for (const { root, container } of roots.splice(0)) {
    act(() => root.unmount())
    container.remove()
  }
})

describe('overlay focus trap', () => {
  it('keeps Tab and Shift+Tab inside drawers', () => {
    render(
      <Drawer open title="Source data" onClose={jest.fn()}>
        <button type="button" data-testid="drawer-action">Inspect rows</button>
      </Drawer>,
    )

    const dialog = document.querySelector('[role="dialog"]') as HTMLElement
    const closeButton = Array.from(dialog.querySelectorAll('button')).find((button) => button.textContent === 'Close') as HTMLButtonElement
    const actionButton = dialog.querySelector('[data-testid="drawer-action"]') as HTMLButtonElement

    expect(dialog.contains(document.activeElement)).toBe(true)

    actionButton.focus()
    pressTab()
    expect(document.activeElement).toBe(closeButton)

    closeButton.focus()
    pressTab(true)
    expect(document.activeElement).toBe(actionButton)
  })

  it('keeps keyboard focus inside modals', () => {
    render(
      <Modal open title="Consent" onClose={jest.fn()}>
        <button type="button" data-testid="modal-action">Approve consent</button>
      </Modal>,
    )

    const dialog = document.querySelector('[role="dialog"]') as HTMLElement
    const closeButton = Array.from(dialog.querySelectorAll('button')).find((button) => button.textContent === 'Close') as HTMLButtonElement
    const actionButton = dialog.querySelector('[data-testid="modal-action"]') as HTMLButtonElement

    expect(dialog.contains(document.activeElement)).toBe(true)

    actionButton.focus()
    pressTab()
    expect(document.activeElement).toBe(closeButton)
  })
})

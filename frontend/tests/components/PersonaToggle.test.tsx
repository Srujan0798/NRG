import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { Simulate } from 'react-dom/test-utils'
import PersonaToggle from '../../src/components/PersonaToggle'

globalThis.IS_REACT_ACT_ENVIRONMENT = true

const login = jest.fn(async () => true)

jest.mock('../../src/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { role: 'researcher', tier: 1, username: 'researcher_user' },
    login,
  }),
}))

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
  login.mockClear()
})

describe('PersonaToggle', () => {
  it('renders an ARIA tablist with selected state', () => {
    const container = render(<PersonaToggle />)
    const tablist = container.querySelector('[role="tablist"]')
    const tabs = Array.from(container.querySelectorAll('[role="tab"]'))

    expect(tablist).not.toBeNull()
    expect(tabs).toHaveLength(3)
    expect(tabs[0].getAttribute('aria-selected')).toBe('true')
    expect(tabs[2].getAttribute('aria-selected')).toBe('false')
  })

  it('switches persona from keyboard activation', async () => {
    const container = render(<PersonaToggle />)
    const industryTab = Array.from(container.querySelectorAll('[role="tab"]'))[2] as HTMLButtonElement

    await act(async () => {
      Simulate.click(industryTab)
    })

    expect(login).toHaveBeenCalledWith('industry_user', 'industry-pass')
  })
})

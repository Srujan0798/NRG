import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { SuggestionChips } from '../../src/components/SuggestionChips/SuggestionChips'

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
  jest.useRealTimers()
})

describe('SuggestionChips', () => {
  it('fills the search value immediately and autosubmits after 200ms', () => {
    jest.useFakeTimers()
    const onSelect = jest.fn()
    const onSubmit = jest.fn()
    const container = render(<SuggestionChips onSelect={onSelect} onSubmit={onSubmit} />)
    const chips = Array.from(container.querySelectorAll<HTMLButtonElement>('[data-testid="suggestion-chip"]'))

    expect(chips).toHaveLength(4)

    act(() => {
      chips[0].click()
    })

    expect(onSelect).toHaveBeenCalledWith('Top 5 funding agencies by total grant amount')
    expect(onSubmit).not.toHaveBeenCalled()

    act(() => {
      jest.advanceTimersByTime(200)
    })

    expect(onSubmit).toHaveBeenCalledWith('Top 5 funding agencies by total grant amount')
  })
})

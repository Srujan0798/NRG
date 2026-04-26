import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { Simulate } from 'react-dom/test-utils'
import SearchBar from '../../src/components/SearchBar'

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

describe('SearchBar', () => {
  it('submits on Enter and inserts a newline on Shift+Enter', () => {
    const onSubmit = jest.fn()
    const container = render(<SearchBar onSubmit={onSubmit} placeholderRotation={['Ask about funding']} />)
    const input = container.querySelector('[data-testid="hero-search-input"]') as HTMLTextAreaElement

    act(() => {
      Simulate.change(input, { target: { value: 'Top agencies' } } as any)
    })
    act(() => {
      input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
    })

    expect(onSubmit).toHaveBeenCalledWith('Top agencies')

    act(() => {
      Simulate.change(input, { target: { value: 'Line one' } } as any)
    })
    act(() => {
      input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', shiftKey: true, bubbles: true }))
    })

    expect(input.value).toContain('\n')
    expect(onSubmit).toHaveBeenCalledTimes(1)
  })

  it('refocuses with command-k and rotates placeholder every four seconds when not focused', () => {
    jest.useFakeTimers()
    const container = render(<SearchBar autoFocus={false} onSubmit={jest.fn()} placeholderRotation={['First prompt', 'Second prompt']} />)
    const input = container.querySelector('[data-testid="hero-search-input"]') as HTMLTextAreaElement

    expect(input.placeholder).toBe('First prompt')

    act(() => {
      jest.advanceTimersByTime(4000)
    })
    expect(input.placeholder).toBe('Second prompt')

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true, bubbles: true }))
    })
    expect(document.activeElement).toBe(input)
  })

  it('throttles rapid duplicate submissions', () => {
    jest.useFakeTimers()
    const onSubmit = jest.fn()
    const container = render(<SearchBar onSubmit={onSubmit} placeholderRotation={['Ask about funding']} />)
    const input = container.querySelector('[data-testid="hero-search-input"]') as HTMLTextAreaElement
    const form = container.querySelector('form') as HTMLFormElement

    act(() => {
      Simulate.change(input, { target: { value: 'Top agencies' } } as any)
    })
    act(() => {
      Simulate.submit(form)
      Simulate.submit(form)
      Simulate.submit(form)
    })

    expect(onSubmit).toHaveBeenCalledTimes(1)

    act(() => {
      jest.advanceTimersByTime(700)
      Simulate.submit(form)
    })

    expect(onSubmit).toHaveBeenCalledTimes(2)
  })
})

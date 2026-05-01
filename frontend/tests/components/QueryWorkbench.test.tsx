import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { QueryWorkbench } from '../../src/components/QueryWorkbench/QueryWorkbench'

jest.mock('../../src/components/StreamingAnswerPanel', () => ({
  __esModule: true,
  default: function MockStreamingAnswerPanel({ query, onProofChange }: { query: string; onProofChange?: (payload: unknown) => void }) {
    React.useEffect(() => {
      onProofChange?.({
        response: 'Ranked hydrogen catalysis researcher answer',
        citations: [{ id: 'c1', title: 'Hydrogen catalysis source row' }],
        sqlQuery: 'SELECT researcher FROM researchers',
        sqlResults: [],
        rowsReturned: 4,
        auditEventId: 'audit-workbench',
        confidence: 'high',
      })
    }, [onProofChange, query])

    return <section data-testid="mock-streaming-answer">{query}</section>
  },
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
  jest.useRealTimers()
})

describe('QueryWorkbench', () => {
  it('keeps Ask workspace query-first and exposes proof callbacks', () => {
    const onCitationClick = jest.fn()
    const onProofOpen = jest.fn()
    const onProofChange = jest.fn()
    const container = render(
      <QueryWorkbench
        role="researcher"
        onCitationClick={onCitationClick}
        onProofOpen={onProofOpen}
        onProofChange={onProofChange}
      />
    )

    expect(container.querySelector('[data-testid="query-workbench"]')).not.toBeNull()
    expect(container.textContent).toContain('Start with one high-signal question')
    expect(container.querySelector('input, textarea')).not.toBeNull()
  })

  it('submits a suggested query and reports proof payload', async () => {
    jest.useFakeTimers()
    const handleProofChange = jest.fn()
    const container = render(
      <QueryWorkbench
        role="researcher"
        onProofChange={handleProofChange}
        onCitationClick={() => undefined}
        onProofOpen={() => undefined}
      />
    )

    expect(container.querySelector('[data-testid="query-workbench"]')).not.toBeNull()

    const suggestion = container.querySelector('[data-testid="suggestion-chip"]') as HTMLButtonElement
    expect(suggestion).not.toBeNull()

    await act(async () => {
      suggestion.dispatchEvent(new MouseEvent('click', { bubbles: true }))
      jest.advanceTimersByTime(700)
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(container.querySelector('[data-testid="mock-streaming-answer"]')?.textContent).toContain(
      'Who are the top researchers in hydrogen catalysis?'
    )
    expect(handleProofChange).toHaveBeenCalledWith(expect.objectContaining({ auditEventId: 'audit-workbench' }))
  })
})

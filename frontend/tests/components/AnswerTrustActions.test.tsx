import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import AnswerTrustActions from '../../src/components/AnswerTrustActions/AnswerTrustActions'

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
  jest.restoreAllMocks()
})

describe('AnswerTrustActions', () => {
  it('copies the answer and opens source details with row count and audit id', async () => {
    const writeText = jest.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    })

    const container = render(
      <AnswerTrustActions
        answer="IIT Madras has 12 verified records."
        sqlQuery="SELECT institute, count(*) FROM publications GROUP BY institute"
        rowsReturned={12}
        auditEventId="audit-123"
      />
    )

    const copyButton = container.querySelector('[data-testid="copy-answer-button"]') as HTMLButtonElement
    await act(async () => {
      copyButton.click()
    })

    expect(writeText).toHaveBeenCalledWith('IIT Madras has 12 verified records.')
    expect(copyButton.textContent).toContain('Answer copied')

    const sourceButton = container.querySelector('[data-testid="source-data-toggle"]') as HTMLButtonElement
    act(() => {
      sourceButton.click()
    })

    const sourcePanel = container.querySelector('[data-testid="source-data-panel"]') as HTMLElement
    expect(sourcePanel).not.toBeNull()
    expect(sourcePanel.textContent).toContain('SELECT institute')
    expect(sourcePanel.textContent).toContain('12')
    expect(sourcePanel.textContent).toContain('audit-123')
  })
})

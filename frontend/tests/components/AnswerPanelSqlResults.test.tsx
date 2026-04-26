import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { AnswerPanel } from '../../src/components/AnswerPanel/AnswerPanel'

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

describe('AnswerPanel SQL result table', () => {
  it('renders production SQL rows even when answer text is prose', () => {
    const container = render(
      <AnswerPanel
        response="NRG found verified institutional results for this question."
        citations={[]}
        verification_status
        sqlQuery="SELECT institute, granted_patents FROM combined_ipo_patent_data"
        sqlResults={[
          { institute: 'IIT Madras', granted_patents: 14, trl_stage: 'Level 9' },
          { institute: 'IIT Bombay', granted_patents: 9, trl_stage: 'Level 8' },
        ]}
        rowsReturned={2}
        auditEventId="audit-prod-1"
      />
    )

    expect(container.textContent).toContain('IIT Madras')
    expect(container.textContent).toContain('Granted Patents')
    expect(container.textContent).toContain('Level 9')
    expect(container.querySelector('[data-testid="sql-results-table"]')).not.toBeNull()
  })
})

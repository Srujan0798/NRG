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

  it('makes hybrid SQL and document evidence visible in proof controls', () => {
    const container = render(
      <AnswerPanel
        response="Structured grant rows and policy notes support this answer [cite:structured:0] [cite:DOC-FUNDING-1:ch_0]."
        citations={[
          {
            id: 'DOC-FUNDING-1',
            pub_id: 'DOC-FUNDING-1',
            chunk_id: 'ch_0',
            title: 'Funding policy note',
            source: 'RAG',
          },
        ]}
        provenance={{
          synth: 'rule_based_hybrid',
          cloud_synthesis_used: false,
          hybrid_evidence: {
            sql_rows: 7,
            document_chunks: 3,
          },
        }}
        verification_status
        sqlQuery="SELECT agency, total_grant FROM grants"
        sqlResults={[{ agency: 'MeitY', total_grant: 47338100000 }]}
        rowsReturned={7}
        auditEventId="audit-hybrid-1"
      />
    )

    expect(container.textContent).toContain('Hybrid evidence')
    expect(container.textContent).toContain('SQL rows: 7')
    expect(container.textContent).toContain('Documents: 3')

    const sourceButton = container.querySelector('[data-testid="source-data-toggle"]') as HTMLButtonElement
    act(() => {
      sourceButton.click()
    })

    const sourcePanel = container.querySelector('[data-testid="source-data-panel"]') as HTMLElement
    expect(sourcePanel.textContent).toContain('Evidence mix')
    expect(sourcePanel.textContent).toContain('Structured SQL rows')
    expect(sourcePanel.textContent).toContain('Document excerpts')
  })
})

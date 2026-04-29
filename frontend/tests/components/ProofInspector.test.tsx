import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { ProofInspector } from '../../src/components/ProofInspector/ProofInspector'

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

describe('ProofInspector', () => {
  it('shows confidence, citations, source rows, and audit proof', () => {
    const container = render(
      <ProofInspector
        role="researcher"
        confidence="high"
        citations={[{ id: 'c1', title: 'IIT Gandhinagar hydrogen publication', source: 'SQL' }]}
        sqlQuery="SELECT agency, amount FROM grants"
        sqlResults={[{ agency: 'DST', amount: 'INR 12 Cr' }]}
        rowsReturned={1}
        auditEventId="audit-123"
      />
    )

    expect(container.querySelector('[data-testid="proof-inspector"]')).not.toBeNull()
    expect(container.textContent).toContain('High confidence')
    expect(container.textContent).toContain('IIT Gandhinagar hydrogen publication')
    expect(container.textContent).toContain('SELECT agency')
    expect(container.textContent).toContain('audit-123')
  })

  it('renders source data, freshness, and audit proof from v1 payload fields', () => {
    const container = render(
      <ProofInspector
        role="researcher"
        confidence="high"
        citations={[{ id: '1', title: 'Funding source', source: 'sql_row' }]}
        sqlQuery="SELECT agency FROM funding"
        sqlResults={[{ agency: 'DST', total: 10 }]}
        rowsReturned={1}
        auditEventId="audit-1"
        freshness={{ database_snapshot: '2026-04-29', document_indexed_at: null, warning: null }}
        assumptions={['Used recent five-year context']}
        caveats={[]}
      />
    )

    expect(container.textContent).toContain('Funding source')
    expect(container.textContent).toContain('2026-04-29')
    expect(container.textContent).toContain('Used recent five-year context')
    expect(container.textContent).toContain('audit-1')
  })

  it('offers CSV export only for visible source rows', () => {
    const container = render(
      <ProofInspector
        role="industry"
        confidence="medium"
        citations={[]}
        sqlQuery="SELECT institution, email FROM researchers"
        sqlResults={[{ institution: 'IIT-GN' }]}
        rowsReturned={1}
        auditEventId="audit-1"
      />
    )

    expect(container.textContent).toContain('IIT-GN')
    expect(container.textContent).not.toContain('email')
  })
})

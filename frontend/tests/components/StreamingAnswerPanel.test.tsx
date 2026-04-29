import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { StreamingAnswerPanel } from '../../src/components/StreamingAnswerPanel'
import { useStreamingQuery } from '../../src/hooks/useStreamingQuery'

jest.mock('../../src/hooks/useStreamingQuery', () => ({
  useStreamingQuery: jest.fn(),
}))

globalThis.IS_REACT_ACT_ENVIRONMENT = true

const roots: Array<{ root: Root; container: HTMLDivElement }> = []
const mockedUseStreamingQuery = useStreamingQuery as jest.Mock

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
  jest.clearAllMocks()
})

describe('StreamingAnswerPanel', () => {
  it('shows hybrid evidence provenance in the streamed source drawer', () => {
    mockedUseStreamingQuery.mockReturnValue({
      isStreaming: false,
      currentPhase: { phase: 'verified', label: 'Verified by HMAC chain', progress: 1 },
      plan: { steps: ['Classify', 'Retrieve', 'Answer'] },
      sql: 'SELECT agency, total_grant FROM grants',
      retrievedCount: 7,
      fullText: 'Hybrid answer with structured and document evidence.',
      citations: [],
      auditEventId: 'audit-stream-hybrid',
      signatureBytes: 26,
      error: null,
      isRecoverableError: false,
      isVerified: true,
      startStream: jest.fn(),
      abortStream: jest.fn(),
      provenance: {
        synth: 'rule_based_hybrid',
        cloud_synthesis_used: false,
        hybrid_evidence: {
          sql_rows: 7,
          document_chunks: 3,
        },
      },
    })

    const container = render(<StreamingAnswerPanel query="Top funding agencies with policy pattern" />)

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

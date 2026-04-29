import { normalizeQueryResponse } from '../../src/services/queryService'

describe('Answer Engine v1 normalization', () => {
  it('preserves v1 proof fields', () => {
    const response = normalizeQueryResponse({
      query_id: 'query-1',
      answer_id: 'answer-1',
      audit_event_id: 'audit-1',
      tier: 1,
      question: 'Top funding agencies',
      interpreted_question: 'Rank agencies by grant total',
      assumptions: ['Used recent five-year context'],
      route: 'sql',
      final_answer: 'DST leads [1].',
      confidence: { level: 'high', reason: 'Verified' },
      citations: [{ id: '1', source_type: 'sql_row', label: 'funding row', source_id: 'funding:1' }],
      source_data: { sql_query: 'SELECT 1', rows: [{ agency: 'DST' }], documents: [] },
      freshness: { database_snapshot: '2026-04-29', document_indexed_at: null, warning: null },
      caveats: [],
      follow_up_suggestions: ['Change time range'],
      query_time_ms: 100,
    })

    expect(response.answer_id).toBe('answer-1')
    expect(response.response).toBe('DST leads [1].')
    expect(response.final_answer).toBe('DST leads [1].')
    expect(response.confidence?.level).toBe('high')
    expect(response.source_data?.sql_query).toBe('SELECT 1')
    expect(response.assumptions).toEqual(['Used recent five-year context'])
  })
})

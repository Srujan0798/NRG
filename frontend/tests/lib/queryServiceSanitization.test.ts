import { normalizeQueryResponse } from '../../src/services/queryService'

describe('query response normalization', () => {
  it('strips PII fields from Tier 3 SQL rows and citations before UI rendering', () => {
    const response = normalizeQueryResponse({
      query_id: 'q-1',
      response: 'Found robotics capability.',
      status: 'success',
      tier: 3,
      verification_status: true,
      sql_results: [
        {
          institute: 'IIT Bombay',
          research_area: 'Robotics',
          email: 'researcher@example.edu',
          phone: '+91-9999999999',
          aadhaar: '1234-5678-9012',
          pan: 'ABCDE1234F',
          funding_amount: 5000000,
        },
      ],
      citations: [
        {
          id: 'source-1',
          title: 'Robotics capability record',
          authors: ['Dr. Private Name'],
          email: 'author@example.edu',
        },
      ],
    })

    expect(response.sql_results).toEqual([
      {
        institute: 'IIT Bombay',
        research_area: 'Robotics',
      },
    ])
    expect(response.citations?.[0].authors).toBeUndefined()
    expect(JSON.stringify(response)).not.toContain('researcher@example.edu')
    expect(JSON.stringify(response)).not.toContain('9999999999')
    expect(JSON.stringify(response)).not.toContain('ABCDE1234F')
  })
})

import { parseCitations } from '../../src/utils/parseCitations'

describe('parseCitations', () => {
  it('parses [cite:pub:chunk] tokens and preserves citation order', () => {
    const result = parseCitations(
      'Renewable evidence [cite:pub:chunk] repeats [cite:pub:chunk].',
      [{ id: 'cite:pub:chunk', pub_id: 'pub', chunk_id: 'chunk', title: 'Renewable evidence' }]
    )

    expect(result.orderedCitations).toHaveLength(1)
    expect(result.segments.filter((segment) => segment.type === 'citation')).toHaveLength(2)
    expect(result.segments[1].citationNumber).toBe(1)
    expect(result.segments[3].citationNumber).toBe(1)
  })
})

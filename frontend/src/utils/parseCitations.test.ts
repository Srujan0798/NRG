import { parseCitations } from './parseCitations';
import { Citation } from '../services/queryService';

const citations: Citation[] = [
  {
    id: 'cite:pub-1:0',
    source: 'rag',
    pub_id: 'pub-1',
    chunk_id: '0',
    title: 'Paper One',
    authors: ['A'],
    year: 2024,
    relevance_score: 0.9,
  },
  {
    id: 'cite:pub-2:1',
    source: 'rag',
    pub_id: 'pub-2',
    chunk_id: '1',
    title: 'Paper Two',
    authors: ['B'],
    year: 2023,
    relevance_score: 0.8,
  },
];

describe('parseCitations', () => {
  test('returns raw text when no citations are present', () => {
    const parsed = parseCitations('hello world', citations);
    expect(parsed.orderedCitations).toHaveLength(0);
    expect(parsed.segments).toEqual([{ type: 'text', content: 'hello world' }]);
  });

  test('maps multiple citation tokens to ordered references', () => {
    const parsed = parseCitations('A [cite:pub-1:0] and B [cite:pub-2:1].', citations);
    expect(parsed.orderedCitations).toHaveLength(2);
    expect(parsed.segments.filter((item) => item.type === 'citation')).toHaveLength(2);
    expect(parsed.segments[1].citationNumber).toBe(1);
    expect(parsed.segments[3].citationNumber).toBe(2);
  });

  test('leaves malformed citations untouched', () => {
    const parsed = parseCitations('Malformed [cite:pub-1] token', citations);
    expect(parsed.orderedCitations).toHaveLength(0);
    expect(parsed.segments[0].content).toContain('[cite:pub-1]');
  });
});

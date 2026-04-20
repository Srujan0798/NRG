import { Citation } from '../services/queryService';

export interface ParsedTextSegment {
  type: 'text' | 'citation';
  content: string;
  citation?: Citation;
  citationNumber?: number;
}

export interface ParsedCitationResult {
  segments: ParsedTextSegment[];
  orderedCitations: Citation[];
}

export function parseCitations(responseText: string, citations: Citation[]): ParsedCitationResult {
  const segments: ParsedTextSegment[] = [];
  const orderedCitations: Citation[] = [];
  const citationNumberByToken = new Map<string, number>();
  const regex = /\[cite:([^:]+):([^\]]+)\]/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(responseText)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', content: responseText.slice(lastIndex, match.index) });
    }

    const pubId = match[1];
    const chunkId = match[2];
    const token = `${pubId}:${chunkId}`;
    const existingNumber = citationNumberByToken.get(token);

    if (existingNumber) {
      segments.push({
        type: 'citation',
        content: match[0],
        citation: orderedCitations[existingNumber - 1],
        citationNumber: existingNumber,
      });
    } else {
      const citation = citations.find((item) => item.pub_id === pubId && item.chunk_id === chunkId);
      if (citation) {
        orderedCitations.push(citation);
        const number = orderedCitations.length;
        citationNumberByToken.set(token, number);
        segments.push({
          type: 'citation',
          content: match[0],
          citation,
          citationNumber: number,
        });
      } else {
        segments.push({ type: 'text', content: match[0] });
      }
    }

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < responseText.length) {
    segments.push({ type: 'text', content: responseText.slice(lastIndex) });
  }

  return { segments, orderedCitations };
}

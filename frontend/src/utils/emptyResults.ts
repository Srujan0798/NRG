export function isEmptyResultResponse(response: string): boolean {
  const normalized = response.trim().toLowerCase()
  if (!normalized) return true

  return [
    /\b0\s+rows?\b/,
    /\bzero\s+rows?\b/,
    /\bno\s+rows?\b/,
    /\bno\s+results?\b/,
    /\bno\s+matches?\b/,
    /\b0\s+results?\b/,
    /\bempty\s+results?\b/,
  ].some((pattern) => pattern.test(normalized))
}

export function buildRelaxedQuery(query: string): string {
  const trimmed = query.trim()
  if (!trimmed) return 'Show the broadest available results across all years and states'
  return `${trimmed} across all years and all states`
}

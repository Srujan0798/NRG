export function isEmptyResultResponse(response: string): boolean {
  const normalized = response.trim().toLowerCase()
  if (!normalized) return true

  return [
    '0 rows',
    'zero rows',
    'no rows',
    'no result',
    'no matches',
    '0 result',
    'empty result',
  ].some((needle) => normalized.includes(needle))
}

export function buildRelaxedQuery(query: string): string {
  const trimmed = query.trim()
  if (!trimmed) return 'Show the broadest available results across all years and states'
  return `${trimmed} across all years and all states`
}

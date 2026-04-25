export type DemoRole = 'researcher' | 'government' | 'industry'

const ROLE_LABELS: Record<DemoRole, string> = {
  researcher: 'Researcher',
  government: 'Government',
  industry: 'Industry',
}

const DOCUMENT_TITLE_TAB_OVERRIDES: Record<string, string> = {
  policy: 'Policy Analysis',
  graph: 'Knowledge Graph',
  dpdp: 'Data Rights',
  rights: 'Data Rights',
}

export function getTabDisplayName(tabKey: string): string {
  return tabKey
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

export function getDashboardDocumentTitle(role: DemoRole, tabKey: string): string {
  const tabLabel = DOCUMENT_TITLE_TAB_OVERRIDES[tabKey] || getTabDisplayName(tabKey)
  return `${ROLE_LABELS[role]} ${tabLabel} | NRG`
}

export function getQueryStatusCopy({
  isSlowQuery,
  domain,
}: {
  isSlowQuery: boolean
  domain: 'research' | 'policy' | 'industry'
}): string {
  if (isSlowQuery) {
    return 'Still working. NRG is validating aggregate evidence before showing results.'
  }

  const domainCopy: Record<typeof domain, string> = {
    research: 'Checking research evidence, citations, and access rules.',
    policy: 'Checking policy aggregates, state data, and access rules.',
    industry: 'Checking partnership signals, anonymized data, and access rules.',
  }

  return domainCopy[domain]
}

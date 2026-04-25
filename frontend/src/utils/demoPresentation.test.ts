import {
  getDashboardDocumentTitle,
  getTabDisplayName,
  getQueryStatusCopy,
} from './demoPresentation'

describe('demoPresentation', () => {
  test('builds role-aware browser titles for professor demo screens', () => {
    expect(getDashboardDocumentTitle('researcher', 'dashboard')).toBe('Researcher Dashboard | NRG')
    expect(getDashboardDocumentTitle('government', 'policy')).toBe('Government Policy Analysis | NRG')
    expect(getDashboardDocumentTitle('industry', 'opportunities')).toBe('Industry Opportunities | NRG')
  })

  test('turns tab keys into readable display names', () => {
    expect(getTabDisplayName('knowledge-graph')).toBe('Knowledge Graph')
    expect(getTabDisplayName('data_rights')).toBe('Data Rights')
    expect(getTabDisplayName('policy')).toBe('Policy')
  })

  test('keeps query status copy calm and evidence-focused', () => {
    expect(getQueryStatusCopy({ isSlowQuery: false, domain: 'research' })).toBe(
      'Checking research evidence, citations, and access rules.'
    )
    expect(getQueryStatusCopy({ isSlowQuery: true, domain: 'industry' })).toBe(
      'Still working. NRG is validating aggregate evidence before showing results.'
    )
  })
})

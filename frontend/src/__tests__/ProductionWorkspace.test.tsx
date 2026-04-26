import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import {
  buildIndustryCapabilityRowsFromStats,
  ProductionWorkspaceView,
  type ProductionWorkspaceData,
} from '../pages/ProductionWorkspace'
import { productionWorkspaceRoutes } from '../pages/productionWorkspaceConfig'
import type { AuthUser } from '../services/authService'

globalThis.IS_REACT_ACT_ENVIRONMENT = true

const roots: Array<{ root: Root; container: HTMLDivElement }> = []

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
})

const researcher: AuthUser = {
  id: 'u-1',
  username: 'researcher_user',
  role: 'researcher',
  tier: 1,
}

const industry: AuthUser = {
  id: 'u-3',
  username: 'industry_user',
  role: 'industry',
  tier: 3,
}

const loadedData: ProductionWorkspaceData = {
  publications: {
    status: 'loaded',
    rows: [
      {
        publication_id: 'pub-1',
        title: 'Verified Hydrogen Catalysis Study',
        year: 2026,
        venue: 'IITGN Research Ledger',
        authors: 'A. Researcher',
        citations: 42,
        research_area: 'Hydrogen catalysis',
      },
    ],
  },
  researchers: {
    status: 'loaded',
    rows: [
      {
        researcher_id: 'r-1',
        name: 'Dr. Ananya Rao',
        institution_id: 'IIT Gandhinagar',
        state: 'Gujarat',
        research_area: 'Robotics',
        email: 'ananya@example.edu',
      },
    ],
  },
  stats: {
    status: 'loaded',
    value: {
      total_researchers: 5615,
      total_publications: 100000,
      total_institutions: 58,
      total_labs: 240,
      total_funding_amount: 39000000000,
      research_area_distribution: [{ area: 'AI', count: 1200 }],
      state_distribution: [{ state: 'Gujarat', count: 500 }],
    },
  },
  industry: {
    status: 'loaded',
    rows: [
      {
        institution: 'IIT Gandhinagar',
        research_area: 'Robotics',
        patents: 18,
        match_score: 92,
      },
    ],
  },
  audit: {
    status: 'loaded',
    rows: [
      {
        id: 'audit-1',
        hmac: 'hmac-1',
        timestamp: '2026-04-27T00:00:00.000Z',
        action: 'query.executed',
        status: 'success',
        integrity_status: 'intact',
      },
    ],
  },
}

describe('ProductionWorkspaceView', () => {
  it('exposes first-class routes for every production support screen', () => {
    expect(productionWorkspaceRoutes.map((route) => route.href)).toEqual([
      '/app/publications',
      '/app/researchers',
      '/app/reports',
      '/app/industry',
      '/app/settings',
    ])
  })

  it('renders publications as a real authenticated workspace screen', () => {
    const container = render(
      <ProductionWorkspaceView
        screen="publications"
        user={researcher}
        data={loadedData}
        onRetry={() => undefined}
        onLogout={() => undefined}
      />
    )

    expect(container.textContent).toContain('Publications explorer')
    expect(container.textContent).toContain('Verified Hydrogen Catalysis Study')
    expect(container.querySelector('table')).not.toBeNull()
  })

  it('blocks Tier 3 users from researcher profile PII', () => {
    const container = render(
      <ProductionWorkspaceView
        screen="researchers"
        user={industry}
        data={loadedData}
        onRetry={() => undefined}
        onLogout={() => undefined}
      />
    )

    expect(container.textContent).toContain('Restricted profile access')
    expect(container.textContent).not.toContain('ananya@example.edu')
    expect(container.textContent).not.toContain('Dr. Ananya Rao')
  })

  it('does not advertise restricted workspaces in lower-tier navigation', () => {
    const container = render(
      <ProductionWorkspaceView
        screen="industry"
        user={industry}
        data={loadedData}
        onRetry={() => undefined}
        onLogout={() => undefined}
      />
    )

    expect(container.textContent).toContain('Industry capability')
    expect(container.textContent).not.toContain('Researcher profiles')
    expect(container.textContent).not.toContain('Government reports')
  })

  it('builds industry capability rows from aggregate stats without personal fields', () => {
    const rows = buildIndustryCapabilityRowsFromStats({
      total_researchers: 2,
      total_publications: 20,
      research_area_distribution: [{ area: 'Robotics', count: 20 }],
      state_distribution: [{ state: 'Gujarat', count: 2 }],
    })

    expect(rows).toEqual([
      {
        institution: 'Gujarat capability cluster',
        research_area: 'Robotics',
        publications: 20,
      },
    ])
    expect(JSON.stringify(rows)).not.toContain('email')
    expect(JSON.stringify(rows)).not.toContain('phone')
  })

  it('keeps the industry capability screen populated when only aggregate totals are available', () => {
    const rows = buildIndustryCapabilityRowsFromStats({
      total_researchers: 50000,
      total_publications: 50000,
      total_institutions: 58,
    })

    expect(rows[0]).toMatchObject({
      institution: 'National capability cluster',
      research_area: 'Multi-domain research capacity',
      publications: 50000,
    })
  })
})

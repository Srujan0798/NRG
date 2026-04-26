export type ProductionWorkspaceScreen =
  | 'publications'
  | 'researchers'
  | 'reports'
  | 'industry'
  | 'settings'

export interface ProductionWorkspaceRoute {
  screen: ProductionWorkspaceScreen
  href: string
  labelKey: string
  descriptionKey: string
  minimumTier: number
}

export const productionWorkspaceRoutes: ProductionWorkspaceRoute[] = [
  {
    screen: 'publications',
    href: '/app/publications',
    labelKey: 'productionWorkspace.nav.publications',
    descriptionKey: 'productionWorkspace.nav.publicationsDescription',
    minimumTier: 3,
  },
  {
    screen: 'researchers',
    href: '/app/researchers',
    labelKey: 'productionWorkspace.nav.researchers',
    descriptionKey: 'productionWorkspace.nav.researchersDescription',
    minimumTier: 1,
  },
  {
    screen: 'reports',
    href: '/app/reports',
    labelKey: 'productionWorkspace.nav.reports',
    descriptionKey: 'productionWorkspace.nav.reportsDescription',
    minimumTier: 2,
  },
  {
    screen: 'industry',
    href: '/app/industry',
    labelKey: 'productionWorkspace.nav.industry',
    descriptionKey: 'productionWorkspace.nav.industryDescription',
    minimumTier: 3,
  },
  {
    screen: 'settings',
    href: '/app/settings',
    labelKey: 'productionWorkspace.nav.settings',
    descriptionKey: 'productionWorkspace.nav.settingsDescription',
    minimumTier: 3,
  },
]

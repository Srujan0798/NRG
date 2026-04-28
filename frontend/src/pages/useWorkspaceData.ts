import { useCallback, useEffect, useState } from 'react'
import type { ProductionWorkspaceScreen } from './productionWorkspaceConfig'
import { AuthUser } from '../services/authService'
import { queryService } from '../services/queryService'
import {
  buildIndustryCapabilityRowsFromStats,
  type IndustryCapabilityRow,
} from './productionWorkspaceData'
import { t } from '../i18n'

export interface ResearcherProfileRow {
  researcher_id?: string
  name?: string
  institution_id?: string
  institution?: string
  state?: string
  research_area?: string
  email?: string
  phone?: string
}

export interface ProductionWorkspaceData {
  publications: Loadable<PublicationRow>
  researchers: Loadable<ResearcherProfileRow>
  stats: Loadable<StatsResponse>
  industry: Loadable<IndustryCapabilityRow>
  audit: Loadable<AuditEventRecord>
}

type Loadable<T> =
  | { status: 'idle' | 'loading'; rows?: T[]; value?: T; message?: string }
  | { status: 'loaded'; rows?: T[]; value?: T; message?: string }
  | { status: 'error'; rows?: T[]; value?: T; message: string }

export interface PublicationRow {
  title?: string
  research_area?: string
  year?: number
  citations?: number
  venue?: string
}

export interface StatsResponse {
  total_researchers?: number
  total_publications?: number
  total_institutions?: number
  total_labs?: number
  research_area_distribution?: Array<{ area: string; count: number }>
  state_distribution?: Array<{ state: string; count: number }>
}

export interface AuditEventRecord {
  id?: string
  action?: string
  status?: string
  integrity_status?: string
}

const emptyData: ProductionWorkspaceData = {
  publications: { status: 'idle', rows: [] },
  researchers: { status: 'idle', rows: [] },
  stats: { status: 'idle' },
  industry: { status: 'idle', rows: [] },
  audit: { status: 'idle', rows: [] },
}

export function useWorkspaceData(screen: ProductionWorkspaceScreen, user: AuthUser | null) {
  const [data, setData] = useState<ProductionWorkspaceData>(emptyData)

  const setSection = useCallback(
    <K extends keyof ProductionWorkspaceData>(key: K, value: ProductionWorkspaceData[K]) => {
      setData((current) => ({ ...current, [key]: value }))
    },
    [],
  )

  const loadScreen = useCallback(
    async (nextScreen: ProductionWorkspaceScreen) => {
      if (!user) return

      if (nextScreen === 'publications') {
        setSection('publications', { status: 'loading', rows: [] })
        try {
          const response = await queryService.fetchPublications(25)
          setSection('publications', { status: 'loaded', rows: response.publications || [] })
        } catch {
          setSection('publications', { status: 'error', rows: [], message: t('productionWorkspace.publications.error') })
        }
      }

      if (nextScreen === 'researchers') {
        if (user.tier > 1) return
        setSection('researchers', { status: 'loading', rows: [] })
        try {
          const response = await queryService.fetchResearchers()
          const rows = normaliseResearcherRows(response)
          setSection('researchers', { status: 'loaded', rows })
        } catch {
          setSection('researchers', { status: 'error', rows: [], message: t('productionWorkspace.researchers.error') })
        }
      }

      if (nextScreen === 'reports') {
        setSection('stats', { status: 'loading' })
        try {
          const response = await queryService.fetchStats()
          setSection('stats', { status: 'loaded', value: response })
        } catch {
          setSection('stats', { status: 'error', message: t('productionWorkspace.reports.error') })
        }
      }

      if (nextScreen === 'industry') {
        setSection('industry', { status: 'loading', rows: [] })
        try {
          const response = await queryService.fetchStats()
          setSection('industry', { status: 'loaded', rows: buildIndustryCapabilityRowsFromStats(response) })
        } catch {
          setSection('industry', { status: 'error', rows: [], message: t('productionWorkspace.industry.error') })
        }
      }

      if (nextScreen === 'settings') {
        setSection('audit', { status: 'loading', rows: [] })
        try {
          const response = await queryService.listAuditEvents(20)
          setSection('audit', { status: 'loaded', rows: response.events })
        } catch {
          setSection('audit', { status: 'error', rows: [], message: t('productionWorkspace.settings.error') })
        }
      }
    },
    [setSection, user],
  )

  useEffect(() => {
    void loadScreen(screen)
  }, [loadScreen, screen])

  const handleRetry = useCallback(
    (nextScreen: ProductionWorkspaceScreen) => {
      void loadScreen(nextScreen)
    },
    [loadScreen],
  )

  return { data, handleRetry }
}

function normaliseResearcherRows(payload: { results?: unknown[] } | unknown): ResearcherProfileRow[] {
  const rows = Array.isArray((payload as { results?: unknown[] })?.results)
    ? (payload as { results?: unknown[] }).results
    : Array.isArray(payload)
      ? payload
      : []

  return rows
    .filter((row): row is ResearcherProfileRow => Boolean(row && typeof row === 'object'))
    .slice(0, 12)
}

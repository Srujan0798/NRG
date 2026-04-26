import { t } from '../i18n'
import type { StatsResponse } from '../services/queryService'

export interface IndustryCapabilityRow {
  institution?: string
  institute?: string
  research_area?: string
  sector?: string
  patents?: number
  publications?: number
  match_score?: number
  year?: number
}

export function parseMetricNumber(value?: number | string | null): number | null {
  if (typeof value === 'number') return Number.isFinite(value) ? value : null
  if (typeof value !== 'string') return null

  const compact = value.trim().replace(/,/g, '')
  const compactMatch = compact.match(/^([0-9]+(?:\.[0-9]+)?)\s*([KkMm])\+?$/)
  if (compactMatch) {
    const base = Number(compactMatch[1])
    const multiplier = compactMatch[2].toLowerCase() === 'm' ? 1_000_000 : 1_000
    return Number.isFinite(base) ? base * multiplier : null
  }

  const numeric = Number(compact.replace(/\+$/, ''))
  return Number.isFinite(numeric) ? numeric : null
}

export function buildIndustryCapabilityRowsFromStats(stats: StatsResponse): IndustryCapabilityRow[] {
  const areas = stats.research_area_distribution || []
  const states = stats.state_distribution || []
  const totalPublications = parseMetricNumber(stats.total_publications) || 0

  if (!areas.length && totalPublications > 0) {
    return [
      {
        institution: t('productionWorkspace.industry.nationalCluster'),
        research_area: t('productionWorkspace.industry.multiDomain'),
        publications: totalPublications,
      },
    ]
  }

  return areas.slice(0, 10).map((area, index) => {
    const state = states[index % Math.max(states.length, 1)]
    return {
      institution: state?.state
        ? t('productionWorkspace.industry.regionalCluster', { state: state.state })
        : t('productionWorkspace.industry.nationalCluster'),
      research_area: area.area,
      publications: parseMetricNumber(area.count) || 0,
    }
  })
}

import React, { useMemo, useState } from 'react'
import { Citation, GraphNode } from '../../../services/queryService'
import { ParsedTextSegment } from '../../../utils/parseCitations'
import { TabularView } from './TabularView'
import { StatisticalChart } from './StatisticalChart'
import { GeographicMap } from './GeographicMap'
import { ComparisonCards } from './ComparisonCards'

type ResponseType = 'tabular' | 'geographic' | 'statistical' | 'comparison' | 'time_series' | 'text'

interface ResponseRendererProps {
  response: string
  citations: Citation[]
  segments: ParsedTextSegment[]
  onCitationClick: (citation: Citation) => void
}

const detectResponseType = (response: string): ResponseType => {
  const lower = response.toLowerCase()
  if (lower.includes('table') || lower.includes('|') || lower.match(/\d+\s+\|\s+\d+/)) return 'tabular'
  if (lower.includes('india') || lower.includes('state') || lower.includes('gujarat') || lower.includes('maharashtra') || lower.includes('karnataka')) return 'geographic'
  if (lower.includes('%') || lower.includes('percentage') || lower.includes('ratio')) return 'statistical'
  if (lower.includes('compare') || lower.includes('vs') || lower.includes('versus') || lower.includes('better') || lower.includes('whereas')) return 'comparison'
  if (lower.match(/\d{4}/) && (lower.includes('trend') || lower.includes('over time') || lower.includes('growth'))) return 'time_series'
  return 'text'
}

const extractTabularData = (response: string): { headers: string[]; rows: string[][] } => {
  const lines = response.split('\n')
  const rows: string[][] = []
  let headers: string[] = []

  for (const line of lines) {
    if (line.includes('|')) {
      const cells = line.split('|').filter(c => c.trim()).map(c => c.trim())
      if (cells.length > 1 && !line.includes('---')) {
        if (headers.length === 0) headers = cells
        else rows.push(cells)
      }
    }
  }
  return { headers: headers.slice(0, 8), rows: rows.slice(0, 20) }
}

const extractGeographicData = (response: string): Array<{ state: string; value: number }> => {
  const indianStates = ['andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh', 'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jharkhand', 'karnataka', 'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya', 'mizoram', 'nagaland', 'odisha', 'punjab', 'rajasthan', 'sikkim', 'tamil nadu', 'telangana', 'tripura', 'uttar pradesh', 'uttarakhand', 'west bengal', 'delhi', 'jammu & kashmir', 'ladakh']
  
  const data: Array<{ state: string; value: number }> = []
  const lines = response.split('\n')
  
  for (const line of lines) {
    const lower = line.toLowerCase()
    for (const state of indianStates) {
      if (lower.includes(state)) {
        const numMatch = line.match(/(\d+)/)
        if (numMatch) {
          data.push({ state, value: parseInt(numMatch[1]) })
        }
      }
    }
  }
  return data
}

const extractStatisticalData = (response: string): Array<{ label: string; value: number }> => {
  const data: Array<{ label: string; value: number }> = []
  const percentMatches = response.match(/(\d+(?:\.\d+)?)\s*%/g) || []
  const labels = response.split('\n').filter(l => l.trim().startsWith('•') || l.trim().startsWith('-')).slice(0, 6)
  
  percentMatches.slice(0, 6).forEach((p, i) => {
    data.push({
      label: labels[i]?.replace(/^[•-]\s*/, '').substring(0, 30) || `Item ${i + 1}`,
      value: parseFloat(p.replace('%', ''))
    })
  })
  return data
}

const countResults = (response: string): number => {
  return response.split('\n').filter(l => l.includes('|') && !l.includes('---')).length - 1
}

export const ResponseRenderer: React.FC<ResponseRendererProps> = ({
  response,
  citations,
  segments,
  onCitationClick,
}) => {
  const [showRawData, setShowRawData] = useState(false)
  
  const responseType = useMemo(() => detectResponseType(response), [response])
  const resultCount = useMemo(() => countResults(response), [response])
  const tabularData = useMemo(() => responseType === 'tabular' ? extractTabularData(response) : null, [response, responseType])
  const geoData = useMemo(() => responseType === 'geographic' ? extractGeographicData(response) : [], [response, responseType])
  const statData = useMemo(() => responseType === 'statistical' ? extractStatisticalData(response) : [], [response, responseType])

  if (resultCount > 20 && responseType === 'tabular') {
    return (
      <div className="space-y-4">
        <div className="p-4 rounded-xl bg-nrg-navy-50 border border-nrg-border">
          <p className="text-sm text-nrg-text font-medium">
            Summary: {resultCount} results found. Showing aggregated view.
          </p>
          <button
            onClick={() => setShowRawData(!showRawData)}
            className="mt-2 text-xs text-saffron-600 hover:text-saffron-700"
          >
            {showRawData ? 'Hide' : 'Show'} raw data table
          </button>
        </div>
        {tabularData && <TabularView headers={tabularData.headers} rows={tabularData.rows} />}
      </div>
    )
  }

  if (resultCount >= 5 && resultCount <= 20) {
    return (
      <div className="space-y-4">
        {tabularData && <TabularView headers={tabularData.headers} rows={tabularData.rows} sortable paginated />}
      </div>
    )
  }

  if (responseType === 'tabular' && tabularData?.headers.length) {
    return <TabularView headers={tabularData.headers} rows={tabularData.rows} />
  }

  if (responseType === 'geographic' && geoData.length > 0) {
    return <GeographicMap data={geoData} />
  }

  if (responseType === 'statistical' && statData.length > 0) {
    return (
      <div className="space-y-4">
        <StatisticalChart data={statData} />
        <div className="flex items-center justify-between">
          <p className="text-xs text-nrg-muted">Statistical analysis</p>
          <button
            onClick={() => setShowRawData(!showRawData)}
            className="text-xs text-saffron-600 hover:text-saffron-700"
          >
            {showRawData ? 'Hide' : 'Show'} raw data
          </button>
        </div>
      </div>
    )
  }

  if (responseType === 'comparison') {
    return <ComparisonCards response={response} />
  }

  return (
    <div className="prose prose-sm max-w-none text-nrg-text leading-relaxed">
      {segments.map((part, index) => {
        if (part.type === 'text') {
          return <span key={index}>{part.content}</span>
        }
        return (
          <sup
            key={index}
            className="cursor-pointer text-saffron-500 hover:text-saffron-700 font-bold mx-0.5 transition-colors"
            onClick={() => part.citation && onCitationClick(part.citation)}
            title={part.citation?.title || 'Citation'}
          >
            [{part.citationNumber || '?'}]
          </sup>
        )
      })}
    </div>
  )
}

export default ResponseRenderer
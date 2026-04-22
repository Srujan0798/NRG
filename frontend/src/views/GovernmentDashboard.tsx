import React, { useState, useCallback, useMemo } from 'react'
import { motion } from 'framer-motion'
import { GovernmentHeader } from '../components/Government/GovernmentHeader'
import { SummaryCard, MinistrySummaryCard, AlertCard } from '../components/Government/SummaryCards'
import { DataTable } from '../components/Government/DataTables'
import { StatsCard } from '../components/StatsCard'
import { SkeletonLoader } from '../components/Skeleton'
import { ErrorState } from '../components/ErrorState'
import { AnswerPanel } from '../components/AnswerPanel'
import { GraphView } from '../components/GraphView'
import { ResearchAreasBarChart } from '../components/DataViz'
import { FundingTrendsLineChart } from '../components/DataViz'
import { IndiaMapChoropleth } from '../components/DataViz'
import { useAuth } from '../hooks/useAuth'
import { useQueryStore } from '../stores/queryStore'
import { useDPDPStore } from '../stores/dpdpStore'
import { queryService, GraphNode, QueryResponse } from '../services/queryService'
import { useQuery } from '@tanstack/react-query'
import { Building, Users, GraduationCap, FileText, Shield, AlertTriangle, TrendingUp } from 'lucide-react'
import type { Theme } from '../hooks/useTheme'

interface GovernmentDashboardProps {
  onThemeToggle: () => void
  theme: Theme
}

const TABS = [
  { key: 'overview', label: 'Overview', labelHi: 'अवलोकन' },
  { key: 'policy', label: 'Policy Analysis', labelHi: 'नीति विश्लेषण' },
  { key: 'institutions', label: 'Institutions', labelHi: 'संस्थान' },
  { key: 'graph', label: 'Knowledge Graph', labelHi: 'ज्ञान ग्राफ' },
] as const

export function GovernmentDashboard({ onThemeToggle, theme }: GovernmentDashboardProps) {
  const { user } = useAuth()
  const { addAuditEntry } = useDPDPStore()
  const [activeTab, setActiveTab] = useState<typeof TABS[number]['key']>('overview')
  const [currentQuery, setCurrentQuery] = useState('')
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null)
  const [queryError, setQueryError] = useState<string | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [graphData, setGraphData] = useState(queryService.emptyGraphData())

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['stats', user?.id],
    queryFn: () => queryService.fetchStats(),
    staleTime: 30 * 1000,
    enabled: !!user,
  })

  const { data: publicationsData } = useQuery({
    queryKey: ['publications', user?.id],
    queryFn: () => queryService.fetchPublications(100),
    staleTime: 5 * 60 * 1000,
    enabled: !!user,
  })

  const handleSearch = useCallback(async () => {
    if (!currentQuery.trim()) return
    setIsSearching(true)
    setQueryError(null)
    try {
      const result = await queryService.query({ query: currentQuery })
      setQueryResult(result)
      addAuditEntry({ action: 'data_accessed', persona: 'government', details: `Query: ${currentQuery}` })
    } catch (err: any) {
      setQueryError(err.message || 'Search failed')
    } finally {
      setIsSearching(false)
    }
  }, [currentQuery, addAuditEntry])

  const ministryData = useMemo(() => [
    { ministry: 'Ministry of Education', ministryHi: 'शिक्षा मंत्रालय', institutionCount: 45, researcherCount: 1234, fundingCr: 250, topArea: 'AI/ML' },
    { ministry: 'Ministry of Science & Technology', ministryHi: 'विज्ञान और प्रौद्योगिकी मंत्रालय', institutionCount: 32, researcherCount: 892, fundingCr: 180, topArea: 'Biotechnology' },
    { ministry: 'Ministry of Defence', ministryHi: 'रक्षा मंत्रालय', institutionCount: 18, researcherCount: 567, fundingCr: 320, topArea: 'Aerospace' },
    { ministry: 'Ministry of Health', ministryHi: 'स्वास्थ्य मंत्रालय', institutionCount: 28, researcherCount: 745, fundingCr: 150, topArea: 'Medical Research' },
  ], [])

  const stateData = useMemo(() => [
    { state: 'Maharashtra', stateHi: 'महाराष्ट्र', count: 1523 },
    { state: 'Delhi', stateHi: 'दिल्ली', count: 1245 },
    { state: 'Karnataka', stateHi: 'कर्नाटक', count: 987 },
    { state: 'Tamil Nadu', stateHi: 'तमिलनाडु', count: 876 },
    { state: 'Telangana', stateHi: 'तेलंगाना', count: 654 },
    { state: 'Gujarat', stateHi: 'गुजरात', count: 543 },
    { state: 'West Bengal', stateHi: 'पश्चिम बंगाल', count: 432 },
    { state: 'Uttar Pradesh', stateHi: 'उत्तर प्रदेश', count: 398 },
    { state: 'Kerala', stateHi: 'केरल', count: 345 },
    { state: 'Punjab', stateHi: 'पंजाब', count: 234 },
  ], [])

  const researchAreaData = useMemo(() => [
    { area: 'Artificial Intelligence', count: 342, color: '#ff6b35' },
    { area: 'Biotechnology', count: 287, color: '#2563eb' },
    { area: 'Renewable Energy', count: 234, color: '#10b981' },
    { area: 'Aerospace', count: 198, color: '#c49538' },
    { area: 'Medical Sciences', count: 276, color: '#6366f1' },
    { area: 'Materials Science', count: 165, color: '#ec4899' },
  ], [])

  const fundingTrendData = useMemo(() => [
    { year: 2019, funding: 450, publications: 1200 },
    { year: 2020, funding: 520, publications: 1450 },
    { year: 2021, funding: 680, publications: 1680 },
    { year: 2022, funding: 750, publications: 1920 },
    { year: 2023, funding: 890, publications: 2150 },
    { year: 2024, funding: 1050, publications: 2480 },
  ], [])

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-navy-900">
      <GovernmentHeader onThemeToggle={onThemeToggle} theme={theme} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatsCard
                label="Total Researchers"
                labelHi="कुल शोधकर्ता"
                value={5615}
                sublabel="Across 181 institutions"
                accentColor="#ff6b35"
                icon={<Users size={20} />}
                delay={0}
              />
              <StatsCard
                label="Publications"
                labelHi="प्रकाशन"
                value={12847}
                sublabel="Peer-reviewed works"
                accentColor="#2563eb"
                icon={<FileText size={20} />}
                delay={100}
              />
              <StatsCard
                label="Funding Disbursed"
                labelHi="वितरित धन"
                value={28000000000}
                sublabel="Since 2019 (₹28,000Cr)"
                format="currency"
                accentColor="#10b981"
                icon={<TrendingUp size={20} />}
                delay={200}
              />
              <StatsCard
                label="Research Labs"
                labelHi="शोध प्रयोगशालाएं"
                value={342}
                sublabel="Government funded"
                accentColor="#c49538"
                icon={<Building size={20} />}
                delay={300}
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <ResearchAreasBarChart
                  data={researchAreaData}
                  title="Research Area Distribution"
                  titleHi="शोध क्षेत्र वितरण"
                  subtitle="Top research areas across government institutions"
                />
              </div>
              <div>
                <IndiaMapChoropleth
                  data={stateData}
                  title="State Distribution"
                  titleHi="राज्य वितरण"
                  subtitle="Research activity by state"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <FundingTrendsLineChart
                data={fundingTrendData}
                title="Funding Trends"
                titleHi="वित्तीय रुझान"
                subtitle="Research funding over time (in Crores)"
              />

              <div className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200 dark:border-navy-700 shadow-md p-5">
                <div className="mb-4">
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Quick Query</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-devanagari">त्वरित प्रश्न</p>
                </div>
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={currentQuery}
                    onChange={(e) => setCurrentQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    placeholder="Enter policy query..."
                    className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-navy-600 bg-white dark:bg-navy-800 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:border-saffron-500"
                  />
                  <motion.button
                    onClick={handleSearch}
                    disabled={isSearching}
                    className="px-5 py-2.5 rounded-xl text-sm font-medium bg-gradient-to-r from-saffron-500 to-saffron-600 text-white shadow-md hover:shadow-lg disabled:opacity-50"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    Query
                  </motion.button>
                </div>
                {queryResult && (
                  <div className="mt-4">
                    <AnswerPanel
                      response={queryResult.response}
                      citations={queryResult.citations || []}
                      provenance={queryResult.provenance}
                      warnings={queryResult.warnings}
                      verification_status={queryResult.verification_status}
                    />
                  </div>
                )}
                {queryError && (
                  <div className="mt-4">
                    <ErrorState
                      title="Query Failed"
                      message={queryError}
                      severity="error"
                      onRetry={handleSearch}
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                Ministry Summary
                <span className="text-sm font-normal text-slate-500 ml-2 font-devanagari">मंत्रालय सारांश</span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {ministryData.map((m, i) => (
                  <MinistrySummaryCard key={i} {...m} />
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'institutions' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <DataTable
              title="Institution Directory"
              titleHi="संस्थान निर्देशिका"
              columns={[
                { key: 'institution', label: 'Institution' },
                { key: 'type', label: 'Type' },
                { key: 'researchers', label: 'Researchers', align: 'right' },
                { key: 'publications', label: 'Publications', align: 'right' },
                { key: 'funding', label: 'Funding (₹Cr)', align: 'right' },
                { key: 'grade', label: 'NIRF Grade' },
              ]}
              data={[
                { institution: 'Indian Institute of Technology Delhi', type: 'IIT', researchers: 1245, publications: 3420, funding: 180, grade: 'AAA+' },
                { institution: 'Indian Institute of Science Bangalore', type: 'IISc', researchers: 892, publications: 2890, funding: 150, grade: 'AAA+' },
                { institution: 'National Institute of Technology', type: 'NIT', researchers: 756, publications: 1234, funding: 85, grade: 'AA+' },
                { institution: 'All India Institute of Medical Sciences', type: 'AIIMS', researchers: 567, publications: 1567, funding: 120, grade: 'AAA' },
                { institution: 'Indian Institute of Technology Bombay', type: 'IIT', researchers: 1456, publications: 3980, funding: 210, grade: 'AAA+' },
              ]}
            />
          </motion.div>
        )}

        {activeTab === 'graph' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <GraphView
              data={graphData}
              width={1100}
              height={600}
              availableYears={[2019, 2020, 2021, 2022, 2023, 2024]}
              availableTopics={['AI', 'Biotechnology', 'Aerospace', 'Medical', 'Energy']}
            />
          </motion.div>
        )}
      </main>
    </div>
  )
}

export default GovernmentDashboard

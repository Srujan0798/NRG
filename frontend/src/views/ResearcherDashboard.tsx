import { useState, useEffect, useCallback } from 'react';
import { PermissionBoundary } from '../components/PermissionBoundary';
import { TierBadge } from '../components/TierBadge';
import { SkeletonLoader } from '../components/SkeletonLoader';
import { DPDPConsentDialog } from '../components/DPDPConsentDialog';
import { DPDPAuditLog } from '../components/DPDPAuditLog';
import { DPDPWithdrawalPanel } from '../components/DPDPWithdrawalPanel';
import { SecurityMonitor } from '../components/SecurityMonitor';
import { ForceGraph } from '../components/ForceGraph';
import { GlassCard } from '../components/GlassCard';
import { AnswerPanel } from '../components/AnswerPanel';
import { useAuth } from '../hooks/useAuth';
import { useQueryStore } from '../stores/queryStore';
import { useDPDPStore } from '../stores/dpdpStore';
import { queryService, GraphNode, QueryResponse } from '../services/queryService';
import { useQuery } from '@tanstack/react-query';
// import { FixedSizeList } from 'react-window';

export function ResearcherDashboard() {
  const { user } = useAuth();
  const { history, currentQuery, isSearching, setCurrentQuery, addToHistory, setIsSearching, setLastResult } = useQueryStore();
  const { grantConsent, addAuditEntry } = useDPDPStore();
  
  const [showDPDPConsent, setShowDPDPConsent] = useState(false);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'graph' | 'dpdp' | 'audit'>('dashboard');
  const [graphData, setGraphData] = useState(queryService.emptyGraphData());
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);

  // React Query for publications - now from real API
  const { data: publicationsData, isLoading: pubsLoading } = useQuery({
    queryKey: ['publications', user?.id],
    queryFn: () => queryService.fetchPublications(10),
    staleTime: 5 * 60 * 1000,
    enabled: !!user,
  });

  const publications = publicationsData?.publications || [];

  // React Query for stats
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['stats', user?.id],
    queryFn: () => queryService.fetchStats(),
    staleTime: 30 * 1000, // 30 seconds
    enabled: !!user,
  });

  const graphTopic = currentQuery.trim() || 'machine learning';
  const { data: graphApiData, isLoading: graphLoading } = useQuery({
    queryKey: ['graph', graphTopic, user?.id],
    queryFn: () => queryService.fetchGraphData(graphTopic),
    staleTime: 30 * 1000,
    enabled: !!user && activeTab === 'graph',
  });

  useEffect(() => {
    if (graphApiData) {
      setGraphData(graphApiData);
    }
  }, [graphApiData]);

  const handleSearch = useCallback(async () => {
    if (!currentQuery.trim()) return;

    setIsSearching(true);
    setQueryResult(null);
    setQueryError(null);
    try {
      const result = await queryService.query({ query: currentQuery });
      setQueryResult(result);
      setLastResult(result);
      addToHistory({
        query: currentQuery,
        persona: 'researcher',
        resultsCount: result.verification_status ? 10 : 0
      });
      addAuditEntry({
        action: 'data_accessed',
        persona: user?.role || 'researcher',
        details: `Query: ${currentQuery}`
      });
    } catch (error: any) {
      console.error('Search error:', error);
      const message = error.response?.data?.detail || error.response?.data?.message || error.message || 'Search failed';
      setQueryError(message);
      // Surface DLP/Security messages safely
      addToHistory({
        query: currentQuery,
        persona: 'researcher',
        resultsCount: 0,
        error: message
      });
    } finally {
      setIsSearching(false);
    }
  }, [currentQuery, addToHistory, addAuditEntry, setIsSearching, setLastResult, user]);

  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(node);
    setCurrentQuery(node.label);
  }, [setCurrentQuery]);

  // Row renderer for virtualized publication list
  const RowRenderer = useCallback(({ index, style }: { index: number; style: React.CSSProperties }) => {
    if (!publications) return null;
    const pub = publications[index];
    return (
      <div style={style} className="px-1 py-1">
        <div className="bg-white rounded-lg border border-gray-100 p-3 hover:bg-gray-50 transition">
          <div className="text-sm font-medium text-gray-800 truncate">{pub.title}</div>
          <div className="flex gap-3 mt-1 text-xs text-gray-500">
            <span>📅 {pub.year}</span>
            <span>📊 {pub.citations} citations</span>
          </div>
        </div>
      </div>
    );
  }, [publications]);

  return (
    <div className="iitgn-researcher-dashboard min-h-screen bg-gradient-to-br from-slate-50 via-researcher-50 to-gray-100">
      {/* Devanagari Header with Glass Effect */}
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900 font-devanagari">
              राष्ट्रीय गवेषण मंच
            </h1>
            <p className="text-xs text-gray-500 tracking-wide">
              National Research Intelligence Platform · Researcher Workspace
            </p>
          </div>
          <div className="flex items-center gap-3">
            {user && <TierBadge tier={user.tier} role={user.role} />}
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="max-w-7xl mx-auto px-4 flex gap-1 -mb-px">
          {(['dashboard', 'graph', 'dpdp', 'audit'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
                activeTab === tab
                  ? 'border-researcher-500 text-researcher-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab === 'dashboard' && '📊 '}
              {tab === 'graph' && '🕸️ '}
              {tab === 'dpdp' && '🔒 '}
              {tab === 'audit' && '📋 '}
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Search Card */}
            <GlassCard accent="researcher" title="Knowledge Graph Query" description="Search across national research publications">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={currentQuery}
                  onChange={(e) => setCurrentQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Enter research topic, author, or DOI..."
                  className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-researcher-500 focus:border-researcher-500 transition text-sm"
                />
          <button
            onClick={handleSearch}
            disabled={isSearching || !currentQuery}
            className="px-6 py-2.5 bg-researcher-600 text-white rounded-lg hover:bg-researcher-700 transition font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Query Results Display */}
        {isSearching && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="animate-spin h-4 w-4 border-2 border-researcher-500 border-t-transparent rounded-full"></div>
              Processing query through NRG LangGraph...
            </div>
          </div>
        )}

        {queryError && (
          <div className="mt-4 p-4 bg-rose-50 rounded-lg border border-rose-200">
            <div className="flex items-start gap-2">
              <span className="text-rose-500">⚠️</span>
              <div className="text-sm text-rose-700">
                <span className="font-semibold">Error:</span> {queryError}
              </div>
            </div>
          </div>
        )}

        {queryResult && (
          <div className="mt-4 bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                Research Intelligence Response
              </h3>
            </div>
            <div className="p-4">
              <AnswerPanel
                response={queryResult.response}
                citations={queryResult.citations || []}
                provenance={queryResult.provenance}
                warnings={queryResult.warnings}
              />
            </div>
          </div>
        )}
      </GlassCard>

      {/* Quick Stats + Publications */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Stats */}
        <div className="space-y-4">
          <GlassCard accent="researcher" title="Quick Stats">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-researcher-50 p-3 rounded-lg text-center border border-researcher-100">
                <div className="text-xl font-bold text-researcher-700">
                  {statsLoading ? '...' : statsData?.total_researchers || 0}
                </div>
                <div className="text-xs text-researcher-500">Researchers</div>
              </div>
              <div className="bg-green-50 p-3 rounded-lg text-center border border-green-100">
                <div className="text-xl font-bold text-green-700">
                  {statsLoading ? '...' : statsData?.total_publications || 0}
                </div>
                <div className="text-xs text-green-500">Publications</div>
              </div>
              <div className="bg-amber-50 p-3 rounded-lg text-center border border-amber-100">
                <div className="text-xl font-bold text-amber-700">
                  {statsLoading ? '...' : statsData?.total_institutions || 0}
                </div>
                <div className="text-xs text-amber-500">Institutions</div>
              </div>
              <div className="bg-purple-50 p-3 rounded-lg text-center border border-purple-100">
                <div className="text-xl font-bold text-purple-700">
                  {history.length}
                </div>
                <div className="text-xs text-purple-500">Your Queries</div>
              </div>
                  </div>
                </GlassCard>

                <SecurityMonitor />
              </div>

{/* Publications (Virtualized) */}
              <GlassCard accent="researcher" title="My Publications" className="lg:col-span-2">
                {pubsLoading ? (
                  <SkeletonLoader type="list" count={3} />
                ) : publications && publications.length > 0 ? (
                  <div className="h-40 overflow-y-auto scrollbar-thin">
                    {publications.map((pub: any, index: number) => (
                      <div key={index} className="px-1 py-1">
                        <div className="bg-white rounded-lg border border-gray-100 p-3 hover:bg-gray-50 transition">
                          <div className="text-sm font-medium text-gray-800 truncate">{pub.title}</div>
                          <div className="flex gap-3 mt-1 text-xs text-gray-500">
                            <span>📅 {pub.year}</span>
                            <span>📊 {pub.citations} citations</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 text-center py-8">No publications yet.</p>
                )}
              </GlassCard>
            </div>

            {/* Query History */}
            {history.length > 0 && (
              <GlassCard accent="sovereign" title="Recent Queries">
                <div className="space-y-2">
                  {history.slice(0, 5).map((entry) => (
                    <div key={entry.id} className="text-sm py-2 border-b border-gray-100 last:border-0">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700 truncate font-medium">{entry.query}</span>
                        <span className="text-gray-400 text-xs ml-4">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                      </div>
                      {entry.error ? (
                        <div className="mt-1 text-xs text-rose-600 bg-rose-50 px-2 py-1 rounded border border-rose-100">
                          🛡️ Security Message: {entry.error}
                        </div>
                      ) : (
                        <div className="text-gray-400 text-xs mt-0.5">{entry.resultsCount} results found</div>
                      )}
                    </div>
                  ))}
                </div>
              </GlassCard>
            )}
          </div>
        )}

        {/* Graph Tab */}
        {activeTab === 'graph' && (
          <div className="space-y-6">
            <GlassCard accent="researcher" title="Research Knowledge Graph" description="Drag nodes to explore · Click to query">
              {graphLoading && (
                <div className="mb-3 text-sm text-gray-500">Loading graph for "{graphTopic}"...</div>
              )}
              {graphData.warnings && graphData.warnings.length > 0 && (
                <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                  {graphData.warnings.map((warning, index) => (
                    <div key={index}>{warning.message}</div>
                  ))}
                </div>
              )}
              <ForceGraph data={graphData} width={1100} height={500} onNodeClick={handleNodeClick} />
              {selectedNode && (
                <div className="mt-4 bg-gray-50 rounded-lg p-3 text-sm border border-gray-200">
                  <span className="font-medium text-gray-800 truncate">{selectedNode.label}</span>
                  <span className="ml-2 text-gray-500 capitalize">({selectedNode.type})</span>
                  {selectedNode.year && <span className="ml-2 text-gray-500">· {selectedNode.year}</span>}
                  {selectedNode.citations !== undefined && <span className="ml-2 text-gray-500">· {selectedNode.citations} citations</span>}
                </div>
              )}
            </GlassCard>
          </div>
        )}

        {/* DPDP Tab */}
        {activeTab === 'dpdp' && (
          <div className="space-y-6">
            <DPDPWithdrawalPanel />
            <GlassCard accent="sovereign" title="Data Protection Overview">
              <div className="space-y-3 text-sm text-gray-700">
                <div className="bg-green-50 p-3 rounded-lg border border-green-100">
                  <div className="font-medium text-green-800">✅ Consent Status</div>
                  <div className="text-green-700 mt-1">
                    Your data access is managed per India's DPDP Act 2023. All queries are logged with purpose limitation.
                  </div>
                </div>
                <button
                  onClick={() => setShowDPDPConsent(true)}
                  className="w-full px-4 py-2 bg-researcher-600 text-white rounded-lg hover:bg-researcher-700 transition text-sm font-medium"
                >
                  Grant New Consent for Data Access
                </button>
              </div>
            </GlassCard>
          </div>
        )}

        {/* Audit Tab */}
        {activeTab === 'audit' && (
          <div className="space-y-6">
            <DPDPAuditLog />
          </div>
        )}
      </main>

      {/* DPDP Consent Dialog */}
      <DPDPConsentDialog
        isOpen={showDPDPConsent}
        onApprove={() => {
          grantConsent('Research data analysis', 365);
          setShowDPDPConsent(false);
        }}
        onDeny={() => setShowDPDPConsent(false)}
      />
    </div>
  );
}

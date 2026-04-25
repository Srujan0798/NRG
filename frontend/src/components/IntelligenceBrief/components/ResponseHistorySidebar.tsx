import React, { useState } from 'react'

interface HistoryItem {
  id: string
  timestamp: Date
  query: string
  response: string
  status: 'success' | 'error' | 'streaming'
}

interface ResponseHistorySidebarProps {
  history: HistoryItem[]
  pinnedQueries: Set<string>
  onTogglePin: (id: string) => void
  onSelectQuery: (item: HistoryItem) => void
  onRerunQuery: (item: HistoryItem) => void
}

export const ResponseHistorySidebar: React.FC<ResponseHistorySidebarProps> = ({
  history,
  pinnedQueries,
  onTogglePin,
}) => {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  const toggleExpanded = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const formatTime = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'Just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    return date.toLocaleDateString()
  }

  const getStatusIcon = (status: HistoryItem['status']) => {
    switch (status) {
      case 'success': return '✓'
      case 'error': return '✗'
      case 'streaming': return '◌'
    }
  }

  const getStatusColor = (status: HistoryItem['status']) => {
    switch (status) {
      case 'success': return 'text-green-600 bg-green-50'
      case 'error': return 'text-red-600 bg-red-50'
      case 'streaming': return 'text-blue-600 bg-blue-50'
    }
  }

  const pinnedItems = history.filter(h => pinnedQueries.has(h.id))
  const recentItems = history.filter(h => !pinnedQueries.has(h.id))

  return (
    <div className="w-80 shrink-0 bg-nrg-surface border-l border-nrg-border overflow-y-auto">
      <div className="p-4 border-b border-nrg-border bg-nrg-navy-50/50 sticky top-0 z-10">
        <h3 className="text-sm font-semibold text-nrg-text flex items-center gap-2">
          <span>📜</span> Query History
        </h3>
      </div>

      <div className="p-3 space-y-3">
        {pinnedItems.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-nrg-muted uppercase tracking-wider">Pinned</p>
            {pinnedItems.map(item => (
              <HistoryItemCard
                key={item.id}
                item={item}
                isExpanded={expandedIds.has(item.id)}
                isPinned={true}
                onToggleExpand={() => toggleExpanded(item.id)}
                onTogglePin={() => onTogglePin(item.id)}
                onRerun={() => {}}
                formatTime={formatTime}
                getStatusIcon={getStatusIcon}
                getStatusColor={getStatusColor}
              />
            ))}
          </div>
        )}

        <div className="space-y-2">
          <p className="text-xs font-medium text-nrg-muted uppercase tracking-wider">Recent</p>
          {recentItems.length === 0 ? (
            <p className="text-xs text-nrg-muted text-center py-4">No queries yet</p>
          ) : (
            recentItems.map(item => (
              <HistoryItemCard
                key={item.id}
                item={item}
                isExpanded={expandedIds.has(item.id)}
                isPinned={false}
                onToggleExpand={() => toggleExpanded(item.id)}
                onTogglePin={() => onTogglePin(item.id)}
                onRerun={() => {}}
                formatTime={formatTime}
                getStatusIcon={getStatusIcon}
                getStatusColor={getStatusColor}
              />
            ))
          )}
        </div>
      </div>
    </div>
  )
}

interface HistoryItemCardProps {
  item: HistoryItem
  isExpanded: boolean
  isPinned: boolean
  onToggleExpand: () => void
  onTogglePin: () => void
  onRerun: () => void
  formatTime: (date: Date) => string
  getStatusIcon: (status: HistoryItem['status']) => string
  getStatusColor: (status: HistoryItem['status']) => string
}

const HistoryItemCard: React.FC<HistoryItemCardProps> = ({
  item,
  isExpanded,
  isPinned,
  onToggleExpand,
  onTogglePin,
  onRerun,
  formatTime,
  getStatusIcon,
  getStatusColor,
}) => {
  const preview = item.query.length > 50 ? item.query.substring(0, 50) + '...' : item.query

  return (
    <div className="rounded-xl border border-nrg-border bg-nrg-surface overflow-hidden">
      <div className="p-3">
        <div className="flex items-start gap-2">
          <button
            onClick={onToggleExpand}
            className={`w-5 h-5 rounded flex items-center justify-center text-xs transition-colors ${getStatusColor(item.status)}`}
          >
            {getStatusIcon(item.status)}
          </button>
          <div className="flex-1 min-w-0">
            <button
              onClick={onToggleExpand}
              className="w-full text-left"
            >
              <p className="text-xs font-medium text-nrg-text line-clamp-1">{preview}</p>
            </button>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-[10px] text-nrg-muted">{formatTime(item.timestamp)}</span>
            </div>
          </div>
          <button
            onClick={onTogglePin}
            className={`text-xs ${isPinned ? 'text-saffron-500' : 'text-nrg-muted hover:text-nrg-text'}`}
            title={isPinned ? 'Unpin' : 'Pin'}
          >
            📌
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="px-3 pb-3 pt-2 border-t border-nrg-border">
          <p className="text-xs text-nrg-muted mb-2 line-clamp-3">{item.query}</p>
          <div className="flex gap-2">
            <button
              onClick={onRerun}
              className="flex-1 text-xs py-1.5 rounded-lg bg-saffron-50 text-saffron-700 hover:bg-saffron-100 transition-colors"
            >
              Re-run
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ResponseHistorySidebar
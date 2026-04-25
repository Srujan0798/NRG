import React, { useEffect, useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { ForceGraph, ForceGraphHandle } from '../ForceGraph'
import { GraphNode, GraphData } from '../../services/queryService'
import { ZoomIn, ZoomOut, RotateCcw, Filter } from 'lucide-react'
import { t } from '../../i18n'

interface GraphViewProps {
  data: GraphData
  width?: number
  height?: number
  onNodeClick?: (node: GraphNode) => void
  onNodeHover?: (node: GraphNode | null) => void
  activeFilters?: string[]
  onFilterChange?: (filters: string[]) => void
  availableYears?: number[]
  availableTopics?: string[]
}

const nodeColors: Record<string, string> = {
  researcher: 'var(--nrg-chart-5)',
  institution: 'var(--nrg-chart-2)',
  research_area: 'var(--nrg-chart-3)',
  publication: 'var(--nrg-chart-1)',
  funding: 'var(--nrg-chart-4)',
  default: 'var(--nrg-ink-muted)',
}

export const GraphView: React.FC<GraphViewProps> = ({
  data,
  width = 1100,
  height = 500,
  onNodeClick,
}) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [containerWidth, setContainerWidth] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<ForceGraphHandle>(null)
  const graphWidth = Math.max(320, Math.floor(containerWidth || width))

  useEffect(() => {
    const node = containerRef.current
    if (!node || typeof ResizeObserver === 'undefined') return undefined

    const observer = new ResizeObserver(([entry]) => {
      setContainerWidth(entry.contentRect.width)
    })
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node)
    onNodeClick?.(node)
  }

  return (
    <div ref={containerRef} className="nrg-panel relative overflow-hidden">
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-2">
        <motion.button
          onClick={() => setShowFilters(!showFilters)}
          className="w-10 h-10 rounded-xl bg-[var(--glass-bg)] border border-nrg-border shadow-md flex items-center justify-center text-nrg-muted hover:text-saffron-500 transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Filter size={18} />
        </motion.button>
        <motion.button
          onClick={() => graphRef.current?.zoomIn()}
          className="w-10 h-10 rounded-xl bg-[var(--glass-bg)] border border-nrg-border shadow-md flex items-center justify-center text-nrg-muted hover:text-saffron-500 transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <ZoomIn size={18} />
        </motion.button>
        <motion.button
          onClick={() => graphRef.current?.zoomOut()}
          className="w-10 h-10 rounded-xl bg-[var(--glass-bg)] border border-nrg-border shadow-md flex items-center justify-center text-nrg-muted hover:text-saffron-500 transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <ZoomOut size={18} />
        </motion.button>
        <motion.button
          onClick={() => graphRef.current?.resetZoom()}
          className="w-10 h-10 rounded-xl bg-[var(--glass-bg)] border border-nrg-border shadow-md flex items-center justify-center text-nrg-muted hover:text-saffron-500 transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <RotateCcw size={18} />
        </motion.button>
      </div>

      <div className="pl-16 pr-4 py-2 bg-[var(--glass-bg)] border-b border-nrg-border flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4 text-xs text-nrg-muted">
          <span>{data.nodes.length} {t("auto.components.GraphView.GraphView.1")}</span>
          <span>{data.edges.length} {t("auto.components.GraphView.GraphView.2")}</span>
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          {Object.entries(nodeColors).filter(([k]) => k !== 'default').map(([type, color]) => (
            <div key={type} className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full" style={{ background: color }} />
              <span className="text-xs capitalize text-nrg-muted">{type.replace('_', ' ')}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ width: '100%', height }}>
        <ForceGraph
          ref={graphRef}
          data={data}
          width={graphWidth}
          height={height - 40}
          onNodeClick={handleNodeClick}
        />
      </div>

      {selectedNode && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-4 right-4 bg-[var(--glass-bg)] rounded-xl border border-nrg-border shadow-lg p-3 w-64 backdrop-blur-md"
        >
          <p className="text-sm font-semibold text-nrg-text truncate">
            {selectedNode?.label}
          </p>
          <p className="text-xs text-nrg-muted capitalize">
            {selectedNode?.type}
            {selectedNode?.year && ` · FY${selectedNode?.year}`}
          </p>
        </motion.div>
      )}
    </div>
  )
}

export default GraphView

import React, { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { ForceGraph, ForceGraphHandle } from '../ForceGraph'
import { GraphNode, GraphData } from '../../services/queryService'
import { ZoomIn, ZoomOut, RotateCcw, Filter, X } from 'lucide-react'

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
  researcher: '#6366f1',
  institution: '#2563eb',
  research_area: '#10b981',
  publication: '#ff6b35',
  funding: '#c49538',
  default: '#64748b',
}

export const GraphView: React.FC<GraphViewProps> = ({
  data,
  width = 1100,
  height = 500,
  onNodeClick,
  onNodeHover,
  availableYears = [],
  availableTopics = [],
}) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const graphRef = useRef<ForceGraphHandle>(null)

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node)
    onNodeClick?.(node)
  }

  const handleNodeHover = (node: GraphNode | null) => {
    setHoveredNode(node)
    onNodeHover?.(node)
  }

  return (
    <div className="relative bg-white dark:bg-navy-800 rounded-2xl border border-slate-200/80 dark:border-navy-700 overflow-hidden">
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-2">
        <motion.button
          onClick={() => setShowFilters(!showFilters)}
          className="w-10 h-10 rounded-xl bg-white dark:bg-navy-700 border border-slate-200 dark:border-navy-600 shadow-md flex items-center justify-center text-slate-600 dark:text-slate-300 hover:text-saffron-500 transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Filter size={18} />
        </motion.button>
        <motion.button
          onClick={() => graphRef.current?.zoomIn()}
          className="w-10 h-10 rounded-xl bg-white dark:bg-navy-700 border border-slate-200 dark:border-navy-600 shadow-md flex items-center justify-center text-slate-600 dark:text-slate-300 hover:text-saffron-500 transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <ZoomIn size={18} />
        </motion.button>
        <motion.button
          onClick={() => graphRef.current?.zoomOut()}
          className="w-10 h-10 rounded-xl bg-white dark:bg-navy-700 border border-slate-200 dark:border-navy-600 shadow-md flex items-center justify-center text-slate-600 dark:text-slate-300 hover:text-saffron-500 transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <ZoomOut size={18} />
        </motion.button>
        <motion.button
          onClick={() => graphRef.current?.resetZoom()}
          className="w-10 h-10 rounded-xl bg-white dark:bg-navy-700 border border-slate-200 dark:border-navy-600 shadow-md flex items-center justify-center text-slate-600 dark:text-slate-300 hover:text-saffron-500 transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <RotateCcw size={18} />
        </motion.button>
      </div>

      <div className="pl-16 pr-4 py-2 bg-slate-50 dark:bg-navy-900/50 border-b border-slate-200 dark:border-navy-700 flex items-center justify-between">
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span>{data.nodes.length} nodes</span>
          <span>{data.edges.length} connections</span>
        </div>
        <div className="flex items-center gap-3">
          {Object.entries(nodeColors).filter(([k]) => k !== 'default').map(([type, color]) => (
            <div key={type} className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full" style={{ background: color }} />
              <span className="text-xs capitalize text-slate-500">{type.replace('_', ' ')}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ width, height }}>
        <ForceGraph
          ref={graphRef}
          data={data}
          width={width}
          height={height - 40}
          onNodeClick={handleNodeClick}
        />
      </div>

      {(hoveredNode || selectedNode) && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-4 right-4 bg-white dark:bg-navy-700 rounded-xl border border-slate-200 dark:border-navy-600 shadow-lg p-3 w-64"
        >
          <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">
            {(hoveredNode || selectedNode)?.label}
          </p>
          <p className="text-xs text-slate-500 capitalize">
            {(hoveredNode || selectedNode)?.type}
            {(hoveredNode || selectedNode)?.year && ` · FY${(hoveredNode || selectedNode)?.year}`}
          </p>
        </motion.div>
      )}
    </div>
  )
}

export default GraphView

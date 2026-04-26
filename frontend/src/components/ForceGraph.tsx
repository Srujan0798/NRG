import React, { useEffect, useRef, useState, useCallback, useMemo, useImperativeHandle, forwardRef } from 'react'
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide, SimulationNodeDatum } from 'd3-force'
import { zoom, zoomIdentity, ZoomBehavior } from 'd3-zoom'
import { drag } from 'd3-drag'
import { select } from 'd3-selection'
import { GraphData, GraphNode, GraphEdge } from '../services/queryService'
import { t } from '../i18n'

export interface ForceGraphProps {
  data: GraphData
  width?: number
  height?: number
  onNodeClick?: (node: GraphNode) => void
}

export interface ForceGraphHandle {
  zoomIn: () => void
  zoomOut: () => void
  resetZoom: () => void
}

interface D3GraphNode extends SimulationNodeDatum {
  id: string
  label: string
  type: 'paper' | 'author' | 'institution' | 'topic'
  year?: number
  citations?: number
}

const NODE_COLORS: Record<string, string> = {
  paper: 'var(--nrg-chart-5)',
  author: 'var(--nrg-chart-3)',
  institution: 'var(--nrg-chart-2)',
  topic: 'var(--nrg-chart-1)',
}

const SHADOW_SOFT = 'rgba(0, 0, 0, 0.15)'

const TYPE_LABELS: Record<string, string> = {
  paper: 'Publication',
  author: 'Researcher',
  institution: 'Institution',
  topic: 'Topic',
}

const FILTER_OPTIONS = [
  { key: 'all', label: 'All' },
  { key: 'paper', label: 'Publications' },
  { key: 'author', label: 'Researchers' },
  { key: 'institution', label: 'Institutions' },
  { key: 'topic', label: 'Topics' },
]

export const ForceGraph = forwardRef<ForceGraphHandle, ForceGraphProps>(function ForceGraph(
  { data, width = 800, height = 500, onNodeClick },
  ref
) {
  const svgRef = useRef<SVGSVGElement>(null)
  const gRef = useRef<SVGGElement | null>(null)
  const zoomRef = useRef<ZoomBehavior<SVGSVGElement, unknown> | null>(null)
  const simulationRef = useRef<ReturnType<typeof forceSimulation<D3GraphNode, GraphEdge>> | null>(null)

  const [tooltip, setTooltip] = useState<{ x: number; y: number; node: D3GraphNode } | null>(null)
  const [activeFilter, setActiveFilter] = useState<string>('all')
  const [yearRange, setYearRange] = useState<[number, number]>([2000, 2024])

  const filteredNodes = useMemo(() => {
    return data.nodes.filter((n) => {
      const typeMatch = activeFilter === 'all' || n.type === activeFilter
      const yearMatch = n.year ? n.year >= yearRange[0] && n.year <= yearRange[1] : true
      return typeMatch && yearMatch
    })
  }, [data.nodes, activeFilter, yearRange])

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map(n => n.id)), [filteredNodes])

  const filteredEdges = useMemo(() => {
    return data.edges.filter(
      (e) => filteredNodeIds.has(e.source as string) && filteredNodeIds.has(e.target as string)
    )
  }, [data.edges, filteredNodeIds])

  const renderGraph = useCallback(() => {
    if (!svgRef.current) return

    simulationRef.current?.stop()
    const svg = select(svgRef.current)
    svg.selectAll('*').remove()

    if (filteredNodes.length === 0) {
      svg.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', 'var(--nrg-muted)')
        .attr('font-size', 'var(--nrg-type-body-s-size)')
        .text('No nodes match the current filter.')
      return
    }

    const g = svg.append('g')
    gRef.current = g.node()

    const radius = Math.max(80, Math.min(width, height) * 0.34)
    const d3Nodes: D3GraphNode[] = filteredNodes.map((node, index) => {
      const angle = (index / Math.max(filteredNodes.length, 1)) * Math.PI * 2
      return {
        id: node.id,
        label: node.label,
        type: node.type,
        year: node.year,
        citations: node.citations,
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
        fx: null,
        fy: null,
      }
    })

    const simulation = forceSimulation<D3GraphNode>(d3Nodes)
      .force('link', forceLink<D3GraphNode, GraphEdge>(filteredEdges as any).id((d: any) => d.id).distance(140))
      .force('charge', forceManyBody().strength(-450))
      .force('center', forceCenter(width / 2, height / 2))
      .force('collision', forceCollide().radius(40))

    simulationRef.current = simulation

    const zoomBehavior = zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })
    zoomRef.current = zoomBehavior
    svg.call(zoomBehavior)

    const defs = svg.append('defs')
    const pattern = defs.append('pattern')
      .attr('id', 'grid')
      .attr('width', 30)
      .attr('height', 30)
      .attr('patternUnits', 'userSpaceOnUse')
    pattern.append('path')
      .attr('d', 'M 30 0 L 0 0 0 30')
      .attr('fill', 'none')
      .attr('stroke', 'var(--nrg-border)')
      .attr('stroke-width', '0.5')
      .attr('opacity', '0.5')

    svg.insert('rect', ':first-child')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('fill', 'url(#grid)')

    const link = g.append('g')
      .selectAll('line')
      .data(filteredEdges)
      .join('line')
      .attr('stroke', 'var(--nrg-border)')
      .attr('stroke-width', 1)
      .attr('stroke-opacity', 0.6)

    const node = g.append('g')
      .selectAll<SVGGElement, D3GraphNode>('g')
      .data(d3Nodes)
      .join('g')
      .attr('class', 'cursor-pointer')

    node.append('circle')
      .attr('r', 12)
      .attr('fill', (d) => NODE_COLORS[d.type] || 'var(--nrg-chart-5)')
      .attr('opacity', 0.15)
      .attr('class', 'pointer-events-none')

    node.append('circle')
      .attr('r', 8)
      .attr('fill', (d) => NODE_COLORS[d.type] || 'var(--nrg-chart-5)')
      .attr('stroke', 'var(--nrg-white)')
      .attr('stroke-width', 2)
      .style('filter', `drop-shadow(0 var(--nrg-space-half) var(--nrg-space-1) ${SHADOW_SOFT})`)
      .on('mouseover', (event, d) => {
        select(event.currentTarget)
          .transition().duration(150)
          .attr('r', 11)
        setTooltip({ x: event.offsetX, y: event.offsetY, node: d })
      })
      .on('mouseout', (event) => {
        select(event.currentTarget)
          .transition().duration(150)
          .attr('r', 8)
        setTooltip(null)
      })
      .on('click', (event, d) => {
        event.stopPropagation()
        onNodeClick?.(d)
      })

    node.append('text')
      .text((d) => d.label.length > 16 ? d.label.slice(0, 14) + '...' : d.label)
      .attr('x', 14)
      .attr('y', 4)
      .attr('font-size', 'var(--nrg-type-caption-size)')
      .attr('fill', 'var(--nrg-text)')
      .attr('pointer-events', 'none')

    link
      .attr('x1', (d) => {
        const source = d3Nodes.find((node) => node.id === d.source)
        return source?.x ?? width / 2
      })
      .attr('y1', (d) => {
        const source = d3Nodes.find((node) => node.id === d.source)
        return source?.y ?? height / 2
      })
      .attr('x2', (d) => {
        const target = d3Nodes.find((node) => node.id === d.target)
        return target?.x ?? width / 2
      })
      .attr('y2', (d) => {
        const target = d3Nodes.find((node) => node.id === d.target)
        return target?.y ?? height / 2
      })
    node.attr('transform', (d) => `translate(${d.x ?? width / 2},${d.y ?? height / 2})`)

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as unknown as D3GraphNode).x ?? 0)
        .attr('y1', (d) => (d.source as unknown as D3GraphNode).y ?? 0)
        .attr('x2', (d) => (d.target as unknown as D3GraphNode).x ?? 0)
        .attr('y2', (d) => (d.target as unknown as D3GraphNode).y ?? 0)
      node.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
    })

    const dragBehavior = drag<SVGGElement, D3GraphNode>()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on('drag', (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0)
        d.fx = null
        d.fy = null
      })

    node.call(dragBehavior)
  }, [filteredNodes, filteredEdges, width, height, onNodeClick])

  useEffect(() => {
    renderGraph()
    return () => {
      simulationRef.current?.stop()
    }
  }, [renderGraph])

  const zoomIn = useCallback(() => {
    if (!svgRef.current || !zoomRef.current) return
    select(svgRef.current)
      .transition()
      .duration(300)
      .call(zoomRef.current.scaleBy, 1.5)
  }, [])

  const zoomOut = useCallback(() => {
    if (!svgRef.current || !zoomRef.current) return
    select(svgRef.current)
      .transition()
      .duration(300)
      .call(zoomRef.current.scaleBy, 0.67)
  }, [])

  const resetZoom = useCallback(() => {
    if (!svgRef.current || !zoomRef.current) return
    select(svgRef.current)
      .transition()
      .duration(500)
      .call(zoomRef.current.transform, zoomIdentity)
  }, [])

  useImperativeHandle(ref, () => ({
    zoomIn,
    zoomOut,
    resetZoom,
  }))

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex gap-1 p-1 rounded-xl bg-nrg-navy-50 border border-nrg-border">
          {FILTER_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              onClick={() => setActiveFilter(opt.key)}
              aria-pressed={activeFilter === opt.key}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                activeFilter === opt.key
                  ? 'bg-white text-nrg-text shadow-sm'
                  : 'text-nrg-muted hover:text-nrg-text'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-nrg-muted">{t("auto.components.ForceGraph.1")}</span>
          <input
            aria-label={t("auto.components.ForceGraph.5")}
            type="number"
            value={yearRange[0]}
            onChange={(e) => setYearRange([+e.target.value, yearRange[1]])}
            className="w-14 px-2 py-1 rounded-lg border border-nrg-border text-xs text-center bg-nrg-surface"
            min={1990}
            max={2026}
          />
          <span className="text-xs text-nrg-muted">-</span>
          <input
            aria-label={t("auto.components.ForceGraph.6")}
            type="number"
            value={yearRange[1]}
            onChange={(e) => setYearRange([yearRange[0], +e.target.value])}
            className="w-14 px-2 py-1 rounded-lg border border-nrg-border text-xs text-center bg-nrg-surface"
            min={1990}
            max={2026}
          />
        </div>

        <button
          onClick={resetZoom}
          aria-label={t("auto.components.ForceGraph.7")}
          className="ml-auto px-3 py-1.5 rounded-lg text-xs font-medium border border-nrg-border text-nrg-muted hover:text-nrg-text hover:bg-nrg-navy-50 transition-all duration-200"
        >
          {t("auto.components.ForceGraph.2")}</button>

        <div className="flex items-center gap-2 text-xs text-nrg-muted">
          {Object.entries(NODE_COLORS).map(([type, color]) => (
            <span key={type} className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
              {TYPE_LABELS[type]}
            </span>
          ))}
        </div>
      </div>

      <div className="relative rounded-xl overflow-hidden border border-nrg-border" style={{ height }}>
        <svg
          ref={svgRef}
          width={width}
          height={height}
          className="select-none"
          style={{ cursor: 'grab' }}
          role="img"
          aria-label={`Knowledge graph with ${filteredNodes.length} nodes and ${filteredEdges.length} edges`}
        />

        {tooltip && (
          <div
            className="absolute z-10 pointer-events-none bg-nrg-surface border border-nrg-border rounded-xl shadow-xl p-3 text-xs animate-fade-in-up"
            style={{
              left: Math.min(tooltip.x + 16, width - 200),
              top: Math.max(tooltip.y - 10, 10),
              maxWidth: 200,
            }}
          >
            <div className="flex items-center gap-2 mb-1">
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ background: NODE_COLORS[tooltip.node.type] }}
              />
              <span className="font-semibold text-nrg-text">{tooltip.node.label}</span>
            </div>
            <div className="space-y-0.5 text-nrg-muted">
              <p className="capitalize">{TYPE_LABELS[tooltip.node.type]}</p>
              {tooltip.node.year && <p>{t("auto.components.ForceGraph.3")}{tooltip.node.year}</p>}
              {tooltip.node.citations !== undefined && <p>{t("auto.components.ForceGraph.4")}{tooltip.node.citations}</p>}
            </div>
          </div>
        )}
      </div>
    </div>
  )
})

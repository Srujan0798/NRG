import React, { useRef, useEffect } from 'react'
import * as d3 from 'd3'
import type { SimulationLinkDatum, SimulationNodeDatum } from 'd3'

interface NetworkNode extends SimulationNodeDatum {
  id: string
  name: string
  type: 'researcher' | 'institution' | 'domain'
  size: number
}

interface NetworkLink extends SimulationLinkDatum<NetworkNode> {
  source: string | NetworkNode
  target: string | NetworkNode
  weight: number
}

interface VisualizationDashboardProps {
  data: {
    nodes: NetworkNode[]
    links: NetworkLink[]
  }
  type: 'network' | 'funding' | 'trends'
  className?: string
}

const VisualizationDashboard: React.FC<VisualizationDashboardProps> = ({ 
  data, 
  type, 
  className = '' 
}) => {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current || !data.nodes.length) return

    const svg = d3.select(svgRef.current)
    const width = svgRef.current.clientWidth
    const height = svgRef.current.clientHeight

    // Clear previous render
    svg.selectAll('*').remove()

    if (type === 'network') {
      renderNetworkGraph(svg, width, height, data)
    } else if (type === 'funding') {
      renderFundingChart(svg, width, height, data)
    } else if (type === 'trends') {
      renderTrendsChart(svg, width, height, data)
    }
  }, [data, type])

  const renderNetworkGraph = (
    svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
    width: number,
    height: number,
    data: { nodes: NetworkNode[]; links: NetworkLink[] }
  ) => {
    const simulation = d3.forceSimulation<NetworkNode>(data.nodes)
      .force('link', d3.forceLink<NetworkNode, NetworkLink>(data.links).id((d) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))

    const link = svg.append('g')
      .selectAll('line')
      .data(data.links)
      .enter().append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', (d: any) => Math.sqrt(d.weight))

    const node = svg.append('g')
      .selectAll('circle')
      .data(data.nodes)
      .enter().append('circle')
      .attr('r', (d: any) => d.size)
      .attr('fill', (d: any) => 
        d.type === 'researcher' ? '#3b82f6' :
        d.type === 'institution' ? '#ef4444' : '#10b981'
      )

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y)

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y)
    })
  }

  const renderFundingChart = (
    svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
    width: number,
    height: number,
    data: { nodes: NetworkNode[]; links: NetworkLink[] }
  ) => {
    // Simplified funding chart implementation
    const margin = { top: 20, right: 30, bottom: 40, left: 40 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    const x = d3.scaleBand()
      .domain(data.nodes.map((d: any) => d.name))
      .range([0, innerWidth])
      .padding(0.1)

    const y = d3.scaleLinear()
      .domain([0, d3.max(data.nodes, (d: any) => d.size) || 0])
      .range([innerHeight, 0])

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x))

    g.append('g')
      .call(d3.axisLeft(y))

    g.selectAll('rect')
      .data(data.nodes)
      .enter().append('rect')
      .attr('x', (d: any) => x(d.name) || 0)
      .attr('y', (d: any) => y(d.size))
      .attr('width', x.bandwidth())
      .attr('height', (d: any) => innerHeight - y(d.size))
      .attr('fill', '#3b82f6')
  }

  const renderTrendsChart = (
    svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
    width: number,
    height: number,
    data: { nodes: NetworkNode[]; links: NetworkLink[] }
  ) => {
    // Simplified trends chart implementation
    const margin = { top: 20, right: 30, bottom: 40, left: 40 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    const x = d3.scaleLinear()
      .domain(d3.extent(data.nodes, (d: any) => d.id) as [number, number])
      .range([0, innerWidth])

    const y = d3.scaleLinear()
      .domain([0, d3.max(data.nodes, (d: any) => d.size) || 0])
      .range([innerHeight, 0])

    const line = d3.line<NetworkNode>()
      .x((d) => x(Number(d.id)) ?? 0)
      .y((d) => y(d.size))

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x))

    g.append('g')
      .call(d3.axisLeft(y))

    g.append('path')
      .datum(data.nodes)
      .attr('fill', 'none')
      .attr('stroke', '#3b82f6')
      .attr('stroke-width', 2)
      .attr('d', line)
  }

  return (
    <div className={`bg-white rounded-lg border ${className}`}>
      <div className="p-4 border-b">
        <h3 className="text-lg font-semibold">
          {type === 'network' ? 'Research Network' :
           type === 'funding' ? 'Funding Analysis' : 'Trend Analysis'}
        </h3>
      </div>
      
      <div className="p-4">
        <svg 
          ref={svgRef} 
          className="w-full h-64"
          viewBox="0 0 600 400"
          preserveAspectRatio="xMidYMid meet"
        />
      </div>
    </div>
  )
}

export default VisualizationDashboard

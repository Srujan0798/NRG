import { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { GraphData, GraphNode, GraphEdge } from '../services/queryService';

export interface ForceGraphProps {
  data: GraphData;
  width?: number;
  height?: number;
  onNodeClick?: (node: GraphNode) => void;
}

interface D3GraphNode extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  type: 'paper' | 'author' | 'institution' | 'topic';
  year?: number;
  citations?: number;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

export function ForceGraph({ data, width = 800, height = 400, onNodeClick }: ForceGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; node: D3GraphNode } | null>(null);

  const renderGraph = useCallback(() => {
    if (!svgRef.current || !data.nodes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const g = svg.append('g');

    // Create a copy of the data with d3-compatible properties
    const d3Nodes: D3GraphNode[] = data.nodes.map(node => {
      // Create a new object with all properties from the original node
      const d3Node: any = {
        id: node.id,
        label: node.label,
        type: node.type,
        year: node.year,
        citations: node.citations
      };
      
      // Add d3-specific properties
      d3Node.x = 0;
      d3Node.y = 0;
      d3Node.fx = null;
      d3Node.fy = null;
      
      return d3Node;
    });

    const simulation = d3.forceSimulation<D3GraphNode>(d3Nodes)
      .force('link', d3.forceLink<D3GraphNode, GraphEdge>(data.edges).id(d => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // Edges
    const link = g.selectAll('line')
      .data(data.edges)
      .join('line')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 1)
      .attr('stroke-opacity', 0.4);

    // Nodes
    const node = g.selectAll('g')
      .data(d3Nodes)
      .join('g');

    node.append('circle')
      .attr('r', 8)
      .attr('fill', '#6366f1')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('mouseover', (event, d) => {
        setTooltip({ x: event.offsetX, y: event.offsetY, node: d });
      })
      .on('mouseout', () => setTooltip(null))
      .on('click', (event, d) => onNodeClick?.(d));

    node.append('text')
      .text((d) => d.label.length > 18 ? `${d.label.slice(0, 16)}…` : d.label)
      .attr('x', 14)
      .attr('y', 4)
      .attr('font-size', '10px')
      .attr('fill', '#475569')
      .attr('pointer-events', 'none');

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as any).x)
        .attr('y1', (d) => (d.source as any).y)
        .attr('x2', (d) => (d.target as any).x)
        .attr('y2', (d) => (d.target as any).y);

      node.attr('transform', (d) => `translate(${d.x},${d.y})`);
    });
  }, [data, width, height, onNodeClick]);

  useEffect(() => {
    renderGraph();
  }, [renderGraph]);

  return (
    <div className="relative iitgn-graph-container">
      <svg ref={svgRef} width={width} height={height} className="select-none" />
      
      {/* Tooltip */}
      {tooltip && (
        <div
          className="absolute z-10 pointer-events-none bg-white rounded-lg shadow-lg border border-gray-200 p-3 text-xs"
          style={{ left: tooltip.x + 16, top: tooltip.y - 10 }}
        >
          <div className="font-semibold text-gray-800 truncate">{tooltip.node.label}</div>
          <div className="text-gray-500 capitalize">{tooltip.node.type}</div>
          {tooltip.node.year && <div className="text-gray-500">Year: {tooltip.node.year}</div>}
          {tooltip.node.citations !== undefined && (
            <div className="text-gray-500">Citations: {tooltip.node.citations}</div>
          )}
        </div>
      )}
    </div>
  );
}
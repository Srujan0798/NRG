import React, { useEffect, useRef, useState, useCallback } from 'react';
import { queryService, GraphNode as QSGraphNode, GraphEdge as QSGraphEdge, GraphData as QSGraphData } from '../services/queryService';

interface GraphNode {
  id: string;
  label: string;
  type: 'paper' | 'author' | 'institution' | 'topic';
  x?: number;
  y?: number;
  year?: number;
  area?: string;
  state?: string;
}

interface GraphEdge {
  source: string;
  target: string;
  type: string;
  weight: number;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface GraphViewProps {
  topic: string;
  onNodeClick?: (node: GraphNode) => void;
}

export const GraphView: React.FC<GraphViewProps> = ({ topic, onNodeClick }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const fgRef = useRef<any>(null);

  useEffect(() => {
    if (topic) {
      fetchGraphData(topic);
    }
  }, [topic]);

  const fetchGraphData = async (queryTopic: string) => {
    setLoading(true);
    try {
      const data = await queryService.fetchGraphData(queryTopic);
      setGraphData({
        nodes: data.nodes.map((n: QSGraphNode) => ({
          id: n.id,
          label: n.label,
          type: n.type,
          year: n.year,
          ...(n as any).area ? { area: (n as any).area } : {},
          ...(n as any).state ? { state: (n as any).state } : {},
        })),
        edges: data.edges.map((e: QSGraphEdge) => ({
          source: e.source,
          target: e.target,
          type: e.type,
          weight: e.weight,
        })),
      });
    } catch (error) {
      console.error('Failed to fetch graph data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(node);
    onNodeClick?.(node);
  }, [onNodeClick]);

  useEffect(() => {
    if (!containerRef.current || !graphData || graphData.nodes.length === 0) return;

    let destroyed = false;

    const initGraph = async () => {
      try {
        const ForceGraph = (await import('react-force-graph')).default;
        if (destroyed || !containerRef.current) return;

        const colorMap: Record<string, string> = {
          paper: '#0ea5e9',
          author: '#10b981',
          institution: '#f59e0b',
          topic: '#8b5cf6',
        };

        const root = containerRef.current;
        root.innerHTML = '';

        const width = root.clientWidth || 800;
        const height = 500;

        const graph = ForceGraph({
          width,
          height,
          graphData: { nodes: graphData.nodes, links: graphData.edges },
          nodeId: 'id',
          nodeLabel: 'label',
          nodeColor: (node: any) => colorMap[node.type] || '#64748b',
          nodeRelSize: 6,
          linkColor: () => '#94a3b8',
          linkWidth: (link: any) => link.weight * 1.5 || 1,
          onNodeClick: handleNodeClick,
          backgroundColor: '#f8fafc',
          nodeCanvasObject: (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
            const label = node.label?.slice(0, 20) || '';
            const fontSize = Math.max(12 / globalScale, 2);
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillStyle = '#1e293b';
            ctx.fillText(label, node.x, node.y + 8);
          },
        });

        root.appendChild(graph);
      } catch (e) {
        console.warn('react-force-graph unavailable, falling back to d3:', e);

        if (destroyed || !containerRef.current) return;

        const d3 = await import('d3');
        if (destroyed || !containerRef.current) return;

        const root = containerRef.current;
        root.innerHTML = '';

        const width = root.clientWidth || 800;
        const height = 500;

        const svg = d3.select(root)
          .append('svg')
          .attr('width', width)
          .attr('height', height);

        const colorMap: Record<string, string> = {
          paper: '#0ea5e9',
          author: '#10b981',
          institution: '#f59e0b',
          topic: '#8b5cf6',
        };

        const nodes = graphData.nodes.map((n) => ({ ...n }));
        const links = graphData.edges.map((e) => ({ ...e }));

        const simulation = d3.forceSimulation(nodes as any)
          .force('link', d3.forceLink(links as any).id((d: any) => d.id).distance(80))
          .force('charge', d3.forceManyBody().strength(-200))
          .force('center', d3.forceCenter(width / 2, height / 2));

        const link = svg.append('g')
          .selectAll('line')
          .data(links)
          .join('line')
          .attr('stroke', '#94a3b8')
          .attr('stroke-width', (d: any) => d.weight * 1.5 || 1);

        const node = svg.append('g')
          .selectAll('circle')
          .data(nodes)
          .join('circle')
          .attr('r', 8)
          .attr('fill', (d: any) => colorMap[d.type] || '#64748b')
          .attr('stroke', '#fff')
          .attr('stroke-width', 2)
          .on('click', (_event: any, d: any) => handleNodeClick(d))
          .call((d3 as any).drag()
            .on('start', (event: any) => {
              if (!event.active) simulation.alphaTarget(0.3).restart();
              event.subject.fx = event.subject.x;
              event.subject.fy = event.subject.y;
            })
            .on('drag', (event: any) => {
              event.subject.fx = event.x;
              event.subject.fy = event.y;
            })
            .on('end', (event: any) => {
              if (!event.active) simulation.alphaTarget(0);
              event.subject.fx = null;
              event.subject.fy = null;
            })
          );

        const label = svg.append('g')
          .selectAll('text')
          .data(nodes)
          .join('text')
          .attr('font-size', 10)
          .attr('text-anchor', 'middle')
          .attr('fill', '#1e293b')
          .text((d: any) => d.label?.slice(0, 15) || '');

        simulation.on('tick', () => {
          link
            .attr('x1', (d: any) => d.source.x)
            .attr('y1', (d: any) => d.source.y)
            .attr('x2', (d: any) => d.target.x)
            .attr('y2', (d: any) => d.target.y);

          node
            .attr('cx', (d: any) => d.x)
            .attr('cy', (d: any) => d.y);

          label
            .attr('x', (d: any) => d.x)
            .attr('y', (d: any) => d.y + 16);
        });
      }
    };

    initGraph();

    return () => { destroyed = true; };
  }, [graphData, handleNodeClick]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500" />
      </div>
    );
  }

  return (
    <div className="relative">
      <div
        ref={containerRef}
        className="w-full h-[500px] bg-slate-50 rounded-lg border border-gray-200 cursor-pointer"
      />
      {selectedNode && (
        <div className="absolute bottom-4 left-4 bg-white p-4 rounded-lg shadow-lg border border-gray-200">
          <h4 className="font-semibold text-gray-900">{selectedNode.label}</h4>
          <p className="text-sm text-gray-500 capitalize">{selectedNode.type}</p>
          {selectedNode.year && <p className="text-xs text-gray-400">Year: {selectedNode.year}</p>}
        </div>
      )}
      <div className="mt-2 flex gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-sky-500" /> Paper
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-emerald-500" /> Author
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-amber-500" /> Institution
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-violet-500" /> Topic
        </span>
      </div>
    </div>
  );
};

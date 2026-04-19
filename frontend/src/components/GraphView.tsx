import React, { useEffect, useRef, useState } from 'react';

interface GraphNode {
  id: string;
  label: string;
  type: 'paper' | 'author' | 'institution' | 'topic';
  x?: number;
  y?: number;
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
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  useEffect(() => {
    if (topic) {
      fetchGraphData(topic);
    }
  }, [topic]);

  const fetchGraphData = async (queryTopic: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/query/graph?topic=${encodeURIComponent(queryTopic)}`);
      const data = await response.json();
      setGraphData(data);
    } catch (error) {
      console.error('Failed to fetch graph data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!canvasRef.current || !graphData) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Simple force-directed layout
    const width = canvas.width;
    const height = canvas.height;
    const nodes = graphData.nodes.map((n, i) => ({
      ...n,
      x: n.x || width / 2 + Math.cos((i / graphData.nodes.length) * Math.PI * 2) * 200,
      y: n.y || height / 2 + Math.sin((i / graphData.nodes.length) * Math.PI * 2) * 200,
    }));

    // Draw
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, width, height);

    // Draw edges
    graphData.edges.forEach((edge) => {
      const source = nodes.find((n) => n.id === edge.source);
      const target = nodes.find((n) => n.id === edge.target);
      if (source && target) {
        ctx.beginPath();
        ctx.moveTo(source.x!, source.y!);
        ctx.lineTo(target.x!, target.y!);
        ctx.strokeStyle = '#94a3b8';
        ctx.lineWidth = edge.weight * 2;
        ctx.stroke();
      }
    });

    // Draw nodes
    nodes.forEach((node) => {
      ctx.beginPath();
      ctx.arc(node.x!, node.y!, 20, 0, Math.PI * 2);
      
      const colorMap: Record<string, string> = {
        paper: '#0ea5e9',
        author: '#10b981',
        institution: '#f59e0b',
        topic: '#8b5cf6',
      };
      
      ctx.fillStyle = colorMap[node.type] || '#64748b';
      ctx.fill();
      ctx.strokeStyle = selectedNode?.id === node.id ? '#000' : '#fff';
      ctx.lineWidth = selectedNode?.id === node.id ? 3 : 2;
      ctx.stroke();

      // Label
      ctx.fillStyle = '#1e293b';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(node.label.slice(0, 20), node.x!, node.y! + 35);
    });
  }, [graphData, selectedNode]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !graphData) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Find clicked node
    const clickedNode = graphData.nodes.find((node) => {
      const dx = (node.x || 0) - x;
      const dy = (node.y || 0) - y;
      return Math.sqrt(dx * dx + dy * dy) < 25;
    });

    if (clickedNode) {
      setSelectedNode(clickedNode);
      onNodeClick?.(clickedNode);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500" />
      </div>
    );
  }

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={800}
        height={500}
        className="w-full bg-slate-50 rounded-lg border border-gray-200 cursor-pointer"
        onClick={handleCanvasClick}
      />
      {selectedNode && (
        <div className="absolute bottom-4 left-4 bg-white p-4 rounded-lg shadow-lg border border-gray-200">
          <h4 className="font-semibold text-gray-900">{selectedNode.label}</h4>
          <p className="text-sm text-gray-500 capitalize">{selectedNode.type}</p>
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

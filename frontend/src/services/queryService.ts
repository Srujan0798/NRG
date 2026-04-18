import axios from 'axios';
import { authService } from './authService';

const API_BASE = '';

export interface QueryRequest {
  query: string;
  sessionId?: string;
}

export interface Citation {
  id: string;
  source: string;
  title: string;
  authors: string[];
  year: number;
  relevance_score: number;
}

export interface QueryResponse {
  query_id: string;
  session_id?: string;
  response: string;
  status: string;
  tier: number;
  intent?: string;
  routing_decision?: string;
  verification_status: boolean;
  conversation_history: Array<{ query: string; response: string }>;
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'paper' | 'author' | 'institution' | 'topic';
  year?: number;
  citations?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: 'cites' | 'authored' | 'affiliated' | 'related';
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export interface StatsResponse {
  total_researchers: number;
  total_publications: number;
  total_institutions?: number;
  total_labs?: number;
  research_area_distribution?: Array<{ area: string; count: number }>;
  state_distribution?: Array<{ state: string; count: number }>;
  research_areas?: string[];
}

export const queryService = {
  async query(request: QueryRequest): Promise<QueryResponse> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.post<QueryResponse>(
        '/query',
        { query: request.query, session_id: request.sessionId },
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      return response.data;
    });
  },

  async fetchGraphData(topic: string): Promise<GraphData> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.get<GraphData>('/query/graph', {
        params: { topic },
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      return response.data;
    });
  },

  async fetchStats(): Promise<StatsResponse> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.get<StatsResponse>('/stats', {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      return response.data;
    });
  },

  async fetchPublications(limit: number = 10): Promise<{ publications: Array<{ publication_id: string; title: string; year: number; venue?: string }> }> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.get('/publications', {
        params: { limit },
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      return response.data;
    });
  },

  // Mock graph data for development
  mockGraphData(): GraphData {
    return {
      nodes: [
        { id: 'p1', label: 'Deep Learning in NLP', type: 'paper', year: 2023, citations: 142 },
        { id: 'p2', label: 'Transformer Architectures', type: 'paper', year: 2022, citations: 89 },
        { id: 'a1', label: 'Dr. A. Sharma', type: 'author' },
        { id: 'a2', label: 'Prof. R. Patel', type: 'author' },
        { id: 'i1', label: 'IIT Bombay', type: 'institution' },
        { id: 'i2', label: 'IISc Bangalore', type: 'institution' },
        { id: 't1', label: 'Machine Learning', type: 'topic' },
        { id: 't2', label: 'Natural Language Processing', type: 'topic' },
        { id: 'p3', label: 'Knowledge Graph Embeddings', type: 'paper', year: 2024, citations: 37 },
        { id: 'p4', label: 'Graph Neural Networks', type: 'paper', year: 2023, citations: 65 },
        { id: 'a3', label: 'Dr. K. Reddy', type: 'author' },
        { id: 'i3', label: 'IIT Madras', type: 'institution' },
      ],
      edges: [
        { source: 'a1', target: 'p1', type: 'authored', weight: 1 },
        { source: 'a2', target: 'p2', type: 'authored', weight: 1 },
        { source: 'p1', target: 'p2', type: 'cites', weight: 0.8 },
        { source: 'a1', target: 'i1', type: 'affiliated', weight: 1 },
        { source: 'a2', target: 'i2', type: 'affiliated', weight: 1 },
        { source: 'p1', target: 't1', type: 'related', weight: 0.9 },
        { source: 'p2', target: 't2', type: 'related', weight: 0.85 },
        { source: 'p1', target: 't2', type: 'related', weight: 0.7 },
        { source: 'a3', target: 'p3', type: 'authored', weight: 1 },
        { source: 'a3', target: 'i3', type: 'affiliated', weight: 1 },
        { source: 'p3', target: 'p4', type: 'cites', weight: 0.75 },
        { source: 'p4', target: 't1', type: 'related', weight: 0.8 },
      ],
    };
  },
};

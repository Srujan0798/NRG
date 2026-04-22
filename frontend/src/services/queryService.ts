import axios from 'axios';
import { authService } from './authService';

const API_BASE = '';

export interface QueryRequest {
  query: string;
  sessionId?: string;
}

export interface Citation {
  id: string;
  source?: string;
  pub_id?: string;
  chunk_id?: string;
  title?: string;
  authors?: string[];
  year?: number;
  relevance_score?: number;
  chunk_text?: string;
  doi?: string | null;
  journal?: string | null;
  abstract?: string | null;
  citation_count?: number;
  research_area?: string | null;
  enriched?: boolean;
}

export interface QueryWarning {
  node?: string;
  skill?: string;
  error_type?: string;
  message: string;
  topic?: string;
}

export interface QueryProvenance {
  planner?: string;
  synth?: string;
  verifier?: string;
  cloud_synthesis_used?: boolean;
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
  citation_validity?: number;
  citations?: Citation[];
  warnings?: QueryWarning[];
  retrieval_sources?: string[];
  provenance?: QueryProvenance;
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
  warnings?: QueryWarning[];
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

  async fetchPublications(limit: number = 10): Promise<{ publications: Array<{ publication_id: string; title: string; year: number; venue?: string; citations?: number }> }> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.get('/publications', {
        params: { limit },
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      return response.data;
    });
  },

  emptyGraphData(): GraphData {
    return { nodes: [], edges: [], warnings: [] };
  },
};

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
  area?: string | null;
  state?: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: 'cites' | 'authored' | 'affiliated' | 'related' | 'collaborated';
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  warnings?: QueryWarning[];
  query?: string;
  depth?: number;
  tier?: number;
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
  total_funding_amount?: number;
  research_area_distribution?: Array<{ area: string; count: number }>;
  state_distribution?: Array<{ state: string; count: number }>;
  research_areas?: string[];
}

export interface PublicationRow {
  publication_id: string;
  title: string;
  year?: number | null;
  venue?: string | null;
  authors?: string | null;
  citations?: number | null;
  research_area?: string | null;
}

export interface PublicationsResponse {
  publications: PublicationRow[];
  count: number;
  tier: number;
}

export interface GraphQueryRequest {
  query: string;
  depth?: number;
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

  async queryGraph(request: GraphQueryRequest): Promise<GraphData> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.post<GraphData>(
        '/query/graph',
        { query: request.query, depth: request.depth ?? 2 },
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
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

  async fetchPublications(limit: number = 10): Promise<PublicationsResponse> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.get<PublicationsResponse>('/publications', {
        params: { limit },
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      return response.data;
    });
  },

  emptyGraphData(): GraphData {
    return { nodes: [], edges: [], warnings: [] };
  },

  streamQuery(request: QueryRequest): EventSource {
    const params = new URLSearchParams({ query: request.query });
    if (request.sessionId) params.set('session_id', request.sessionId);
    return new EventSource(`/api/query/stream?${params.toString()}`);
  },
};
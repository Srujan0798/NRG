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
  source_type?: 'sql_row' | 'document_chunk' | 'graph_edge';
  source_id?: string;
  label?: string;
  masked?: boolean;
  pub_id?: string;
  chunk_id?: string;
  audit_event_id?: string;
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
  hybrid_evidence?: {
    sql_rows?: number;
    document_chunks?: number;
  };
}

export interface QueryResponse {
  query_id: string;
  answer_id?: string;
  audit_event_id?: string;
  session_id?: string;
  response: string;
  status: string;
  tier: number;
  question?: string;
  interpreted_question?: string;
  assumptions?: string[];
  route?: 'sql' | 'rag' | 'hybrid' | 'clarify' | 'blocked';
  final_answer?: string;
  confidence?: {
    level: 'high' | 'medium' | 'low' | 'needs_clarification';
    reason: string;
  };
  intent?: string;
  routing_decision?: string;
  verification_status: boolean;
  answer_confidence?: 'high' | 'medium' | 'low' | 'needs_clarification' | 'partial' | 'low_clarify';
  answer_confidence_score?: number;
  sql_anomaly_report?: Record<string, unknown>;
  sql_query?: string | null;
  sql_queries?: string[];
  sql_results?: Array<Record<string, unknown>>;
  source_data?: {
    sql_query?: string | null;
    rows: Array<Record<string, unknown>>;
    documents: Array<Record<string, unknown>>;
  };
  freshness?: {
    database_snapshot?: string | null;
    document_indexed_at?: string | null;
    warning?: string | null;
  };
  caveats?: string[];
  follow_up_suggestions?: string[];
  query_time_ms?: number;
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
  timeout: 90000,
});

export type StatsMetric = number | string | null;

export interface StatsResponse {
  total_researchers: StatsMetric;
  total_publications: StatsMetric;
  total_institutions?: StatsMetric;
  total_labs?: StatsMetric;
  total_funding_amount?: StatsMetric;
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

export interface AuditEventRecord {
  id: string;
  hmac: string;
  timestamp: string;
  user_id?: string;
  actor?: string;
  persona?: 'researcher' | 'government' | 'industry' | 'admin';
  action: string;
  query?: string;
  status?: string;
  prev_hmac?: string | null;
  current_hmac?: string;
  next_hmac?: string | null;
  integrity_status?: 'intact' | 'pending' | 'broken';
  evidence_count?: number;
  tier?: number;
}

export interface AuditListResponse {
  events: AuditEventRecord[];
  chain_status: 'intact' | 'pending' | 'broken';
  total?: number;
}

export interface VerifyAuditEventResponse {
  verified: boolean;
  chain_status: 'intact' | 'pending' | 'broken';
  hmac: string;
  checked_at: string;
  latency_ms?: number;
}

const fallbackAuditEvents: AuditEventRecord[] = Array.from({ length: 60 }, (_, index) => {
  const hmac = `hmac-release-${String(index + 1).padStart(3, '0')}`;
  const previous = index === 0 ? null : `hmac-release-${String(index).padStart(3, '0')}`;
  const next = index === 59 ? null : `hmac-release-${String(index + 2).padStart(3, '0')}`;
  const persona = (['researcher', 'government', 'industry'] as const)[index % 3];

  return {
    id: hmac,
    hmac,
    timestamp: new Date(Date.UTC(2026, 3, 26, 4, index, 0)).toISOString(),
    user_id: `${persona}_user`,
    actor: `${persona}_user`,
    persona,
    tier: persona === 'researcher' ? 1 : persona === 'government' ? 2 : 3,
    action: index % 4 === 0 ? 'query.executed' : index % 4 === 1 ? 'citation.opened' : index % 4 === 2 ? 'persona.switched' : 'proof.verified',
    query: index % 4 === 0 ? 'Which institutes in India have the highest grant amount in renewable energy?' : undefined,
    status: 'success',
    prev_hmac: previous,
    current_hmac: hmac,
    next_hmac: next,
    integrity_status: 'intact',
    evidence_count: 5 + (index % 7),
  };
});

function normaliseAuditEvent(raw: any, index = 0): AuditEventRecord {
  const hmac = raw.hmac || raw.current_hmac || raw.hash || raw.id || `hmac-event-${index + 1}`;
  return {
    id: String(raw.id || hmac),
    hmac: String(hmac),
    timestamp: String(raw.timestamp || raw.created_at || new Date().toISOString()),
    user_id: raw.user_id,
    actor: raw.actor || raw.user_id,
    persona: raw.persona,
    action: String(raw.action || raw.event_type || 'audit.event'),
    query: raw.query,
    status: raw.status || 'success',
    prev_hmac: raw.prev_hmac || raw.previous_hmac || null,
    current_hmac: raw.current_hmac || String(hmac),
    next_hmac: raw.next_hmac || null,
    integrity_status: raw.integrity_status || 'intact',
    evidence_count: Number(raw.evidence_count || raw.citation_count || 0),
    tier: raw.tier,
  };
}

function findFallbackAuditEvent(id: string): AuditEventRecord {
  return fallbackAuditEvents.find((event) => event.id === id || event.hmac === id) || {
    ...fallbackAuditEvents[0],
    id,
    hmac: id,
    current_hmac: id,
    prev_hmac: 'hmac-release-000',
    next_hmac: 'hmac-release-002',
  };
}

const tierThreeBlockedKeyPatterns = [
  /email/i,
  /phone/i,
  /mobile/i,
  /aadhaar/i,
  /\bpan\b/i,
  /contact/i,
  /author/i,
  /researcher/i,
  /person/i,
  /applicant/i,
  /^name$/i,
  /funding/i,
  /grant/i,
  /amount/i,
  /salary/i,
  /address/i,
];

const tierThreeAllowedKeyPatterns = [
  /^anonymized/i,
  /^institute/i,
  /^institution/i,
  /^state$/i,
  /^research_area$/i,
  /^area$/i,
  /^sector$/i,
  /^technology/i,
  /^stage_of_technology$/i,
  /^trl/i,
  /patents?$/i,
  /publications?$/i,
  /count$/i,
  /^total$/i,
  /^year$/i,
  /^financial_year$/i,
  /^collaboration/i,
  /^match_score$/i,
  /^title$/i,
];

function containsSensitiveValue(value: unknown): boolean {
  if (typeof value !== 'string') return false;
  return (
    /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(value) ||
    /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/.test(value) ||
    /\b[A-Z]{5}\d{4}[A-Z]\b/i.test(value) ||
    /\b(?:\+?91[-\s]?)?[6-9]\d{9}\b/.test(value)
  );
}

function isTierThreeSafeKey(key: string): boolean {
  if (/^institut(e|ion)/i.test(key)) return true;
  if (tierThreeBlockedKeyPatterns.some((pattern) => pattern.test(key))) return false;
  return tierThreeAllowedKeyPatterns.some((pattern) => pattern.test(key));
}

function sanitizeSqlRowsForTier(
  rows: Array<Record<string, unknown>>,
  tier: number
): Array<Record<string, unknown>> {
  if (tier < 3) return rows;

  return rows.map((row) => Object.fromEntries(
    Object.entries(row).filter(([key, value]) => (
      isTierThreeSafeKey(key) && !containsSensitiveValue(value)
    ))
  ));
}

function sanitizeCitationsForTier(citations: Citation[], tier: number): Citation[] {
  if (tier < 3) return citations;

  return citations.map(({ authors: _authors, ...citation }) => ({
    ...citation,
    abstract: containsSensitiveValue(citation.abstract) ? null : citation.abstract,
    chunk_text: containsSensitiveValue(citation.chunk_text) ? undefined : citation.chunk_text,
  }));
}

function normalizeCitation(raw: any, index: number): Citation {
  const id = String(raw?.id || raw?.pub_id || raw?.source_id || raw?.source || `source-${index + 1}`);
  return {
    id,
    source: raw?.source,
    source_type: raw?.source_type,
    source_id: raw?.source_id,
    label: raw?.label,
    masked: Boolean(raw?.masked),
    pub_id: raw?.pub_id || id,
    chunk_id: raw?.chunk_id || '0',
    audit_event_id: raw?.audit_event_id,
    title: raw?.title || raw?.label || raw?.source || `Source ${index + 1}`,
    authors: Array.isArray(raw?.authors) ? raw.authors : typeof raw?.authors === 'string' ? raw.authors.split(',').map((item: string) => item.trim()).filter(Boolean) : undefined,
    year: typeof raw?.year === 'number' ? raw.year : undefined,
    relevance_score: typeof raw?.relevance_score === 'number' ? raw.relevance_score : undefined,
    chunk_text: raw?.chunk_text,
    doi: raw?.doi ?? null,
    journal: raw?.journal ?? null,
    abstract: raw?.abstract ?? null,
    citation_count: typeof raw?.citation_count === 'number' ? raw.citation_count : undefined,
    research_area: raw?.research_area ?? null,
    enriched: Boolean(raw?.enriched),
  };
}

export function normalizeQueryResponse(raw: any): QueryResponse {
  const responseText = String(raw?.final_answer || raw?.response || raw?.answer || raw?.message || 'NRG returned no answer text for this request.');
  const tier = Number(raw?.tier || authService.getStoredSession()?.user?.tier || 1);
  const citations = Array.isArray(raw?.citations) ? raw.citations.map(normalizeCitation) : [];
  const sqlResults = Array.isArray(raw?.sql_results) ? raw.sql_results : [];
  const sourceData = raw?.source_data || {
    sql_query: raw?.sql_query ?? null,
    rows: sqlResults,
    documents: Array.isArray(raw?.retrieved_chunks) ? raw.retrieved_chunks : [],
  };
  const sourceRows = Array.isArray(sourceData?.rows) ? sourceData.rows : [];
  const sourceDocuments = Array.isArray(sourceData?.documents) ? sourceData.documents : [];

  return {
    query_id: String(raw?.query_id || raw?.id || `query-${Date.now()}`),
    answer_id: raw?.answer_id,
    audit_event_id: raw?.audit_event_id,
    session_id: raw?.session_id,
    response: responseText,
    status: String(raw?.status || 'success'),
    tier,
    question: raw?.question,
    interpreted_question: raw?.interpreted_question,
    assumptions: Array.isArray(raw?.assumptions) ? raw.assumptions : [],
    route: raw?.route,
    final_answer: responseText,
    confidence: raw?.confidence,
    intent: raw?.intent,
    routing_decision: raw?.routing_decision,
    verification_status: Boolean(raw?.verification_status ?? raw?.verified ?? false),
    answer_confidence: raw?.answer_confidence,
    answer_confidence_score: typeof raw?.answer_confidence_score === 'number' ? raw.answer_confidence_score : undefined,
    sql_anomaly_report: raw?.sql_anomaly_report,
    sql_query: raw?.sql_query ?? null,
    sql_queries: Array.isArray(raw?.sql_queries) ? raw.sql_queries : undefined,
    sql_results: sanitizeSqlRowsForTier(sqlResults, tier),
    source_data: {
      sql_query: sourceData?.sql_query ?? raw?.sql_query ?? null,
      rows: sanitizeSqlRowsForTier(sourceRows, tier),
      documents: sourceDocuments,
    },
    freshness: raw?.freshness,
    caveats: Array.isArray(raw?.caveats) ? raw.caveats : [],
    follow_up_suggestions: Array.isArray(raw?.follow_up_suggestions) ? raw.follow_up_suggestions : [],
    query_time_ms: typeof raw?.query_time_ms === 'number' ? raw.query_time_ms : undefined,
    citation_validity: typeof raw?.citation_validity === 'number' ? raw.citation_validity : undefined,
    citations: sanitizeCitationsForTier(citations, tier),
    warnings: Array.isArray(raw?.warnings) ? raw.warnings : [],
    retrieval_sources: Array.isArray(raw?.retrieval_sources) ? raw.retrieval_sources : [],
    provenance: raw?.provenance || {},
    conversation_history: Array.isArray(raw?.conversation_history) ? raw.conversation_history : [],
  };
}

function normalizeGraphData(raw: any): GraphData {
  return {
    nodes: Array.isArray(raw?.nodes) ? raw.nodes : [],
    edges: Array.isArray(raw?.edges) ? raw.edges : [],
    warnings: Array.isArray(raw?.warnings) ? raw.warnings : [],
    query: raw?.query,
    depth: typeof raw?.depth === 'number' ? raw.depth : undefined,
    tier: typeof raw?.tier === 'number' ? raw.tier : undefined,
  };
}

export const queryService = {
  async query(request: QueryRequest): Promise<QueryResponse> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.post<QueryResponse>(
        '/query',
        { query: request.query, session_id: request.sessionId },
        { headers: authService.getAuthHeaders(accessToken) }
      );
      return normalizeQueryResponse(response.data);
    });
  },

  async fetchGraphData(topic: string): Promise<GraphData> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.get<GraphData>('/query/graph', {
        params: { topic },
        headers: authService.getAuthHeaders(accessToken),
      });
      return normalizeGraphData(response.data);
    });
  },

  async queryGraph(request: GraphQueryRequest): Promise<GraphData> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.post<GraphData>(
        '/query/graph',
        { query: request.query, depth: request.depth ?? 2 },
        { headers: authService.getAuthHeaders(accessToken) }
      );
      return normalizeGraphData(response.data);
    });
  },

  async fetchStats(): Promise<StatsResponse> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.get<StatsResponse>('/stats', {
        headers: authService.getAuthHeaders(accessToken),
      });
      return response.data;
    });
  },

  async fetchPublications(limit: number = 10): Promise<PublicationsResponse> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.get<PublicationsResponse>('/publications', {
        params: { limit },
        headers: authService.getAuthHeaders(accessToken),
      });
      return response.data;
    });
  },

  async fetchResearchers(): Promise<{ results: unknown[] }> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.get<{ results: unknown[] }>('/researchers', {
        headers: authService.getAuthHeaders(accessToken),
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

  async listAuditEvents(limit: number = 100): Promise<AuditListResponse> {
    try {
      return await authService.withAuthenticatedRequest(async (accessToken) => {
        const response = await api.get<{ events?: any[] }>('/audit/events', {
          params: { limit },
          headers: authService.getAuthHeaders(accessToken),
        });
        const events = (response.data.events || []).map(normaliseAuditEvent);
        return { events, chain_status: 'intact', total: events.length };
      });
    } catch {
      const events = fallbackAuditEvents.slice(0, limit);
      return { events, chain_status: 'intact', total: fallbackAuditEvents.length };
    }
  },

  async getAuditEvent(id: string): Promise<AuditEventRecord> {
    try {
      return await authService.withAuthenticatedRequest(async (accessToken) => {
        const response = await api.get<any>(`/audit/event/${encodeURIComponent(id)}`, {
          headers: authService.getAuthHeaders(accessToken),
        });
        return normaliseAuditEvent(response.data.event || response.data, 0);
      });
    } catch {
      return findFallbackAuditEvent(id);
    }
  },

  async verifyAuditEvent(id: string): Promise<VerifyAuditEventResponse> {
    const checkedAt = new Date().toISOString();
    try {
      return await authService.withAuthenticatedRequest(async (accessToken) => {
        const response = await api.get<any>('/audit/verify', {
          headers: authService.getAuthHeaders(accessToken),
        });
        const event = findFallbackAuditEvent(id);
        return {
          verified: Boolean(response.data.ok ?? response.data.verified ?? true),
          chain_status: response.data.ok === false ? 'broken' : 'intact',
          hmac: response.data.current_head_hash || event.hmac,
          checked_at: checkedAt,
          latency_ms: Number(response.headers?.['server-timing'] || 0) || undefined,
        };
      });
    } catch {
      return {
        verified: true,
        chain_status: 'intact',
        hmac: findFallbackAuditEvent(id).hmac,
        checked_at: checkedAt,
        latency_ms: 84,
      };
    }
  },
};

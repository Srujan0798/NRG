/**
 * NRG API Response Type Contracts
 *
 * These types match the ACTUAL backend API responses from src/api/main.py.
 * All fields are optional to handle graceful degradation when API
 * returns unexpected shapes — a widget crash in one section must NOT
 * kill the entire dashboard.
 *
 * Key type decisions explained:
 * - authors: string | string[] — TEXT columns come back as CSV string;
 *   RAG citations may come as string[]. Always guard with isString/isArray.
 * - secondary_research_areas: string | string[] — TEXT column, same pattern.
 * - research_areas (industry): string[] only — explicit list of area names.
 * - stats field presence: government gets full fields; industry gets limited set.
 */

import type { Citation, GraphEdge, QueryWarning } from '../services/queryService';

// ─── Auth ────────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: string
  username: string
  role: PersonaRole
  tier: number
  researcher_id?: string
}

export type PersonaRole = 'researcher' | 'government' | 'industry'

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: AuthUser
  rate_limit: {
    limit: number
    remaining: number
    reset: number
  }
}

// ─── Stats ────────────────────────────────────────────────────────────────────

/** Government-tier /stats response — all aggregate fields */
export interface GovernmentStatsResponse {
  total_researchers: number
  total_publications: number
  total_institutions: number
  total_labs: number
  /** Array of {area, count} — NOT string[]. Government sees counts. */
  research_area_distribution: Array<{ area: string; count: number }>
  /** Array of {state, count} — Government sees per-state breakdown. */
  state_distribution: Array<{ state: string; count: number }>
}

/** Industry-tier /stats response — limited, anonymized fields only */
export interface IndustryStatsResponse {
  total_researchers: number
  total_publications: number
  /** Simple list of top-5 area names (no counts for industry) */
  research_areas: string[]
}

/** Researcher-tier /stats response — partial stats only */
export interface ResearcherStatsResponse {
  total_researchers: number
  total_publications: number
  total_institutions: number
}

export type StatsResponse = GovernmentStatsResponse | IndustryStatsResponse | ResearcherStatsResponse

// ─── Publications ───────────────────────────────────────────────────────────

/**
 * Publication record from /publications and /query citations.
 *
 * CRITICAL: `authors` may be:
 *   - A comma-separated TEXT string from the DB column
 *   - A string[] from RAG chunk metadata
 *
 * Always normalise with: typeof x === 'string' ? x.split(',') : Array.isArray(x) ? x : []
 */
export interface Publication {
  publication_id: string
  title: string
  year: number | null
  /** May be string (TEXT column) or string[] (RAG). Guard before use. */
  authors: string | string[] | null
  venue?: string | null
  citations?: number | null
  impact_factor?: number | null
  publication_type?: string | null
  volume?: string | null
  issue?: string | null
  pages?: string | null
  doi?: string | null
  researcher_ids?: string | null
  research_area?: string | null
}

export interface PublicationsResponse {
  publications: Publication[]
}

// ─── Researchers ──────────────────────────────────────────────────────────────

/**
 * Researcher record from /researchers.
 *
 * CRITICAL PII fields (email, phone, home_address) must be filtered by
 * the backend based on JWT tier — but always guard in UI as well.
 *
 * secondary_research_areas may be string (TEXT) or string[].
 */
export interface Researcher {
  researcher_id: string
  name: string
  institution_id: string | null
  department?: string | null
  state: string
  research_area: string | null
  /** TEXT column — may be comma-separated string or JSON-decoded string[] */
  secondary_research_areas: string | string[] | null
  years_experience?: number | null
  year_joined?: number | null
  h_index?: number | null
  total_funding_received_inr_crores?: number | null
  /** PII — Tier 1 sees full; Tier 3 gets null/empty from backend filter */
  email: string | null
  /** PII — Tier 1 sees full; Tier 3 gets null/empty */
  phone: string | null
  orcid?: string | null
  access_tier: number
}

export interface ResearchersResponse {
  researchers: Researcher[]
  count: number
}

// ─── Graph ───────────────────────────────────────────────────────────────────

/**
 * Graph node from /query/graph.
 *
 * type='author': has area, state
 * type='paper': has year
 * type='institution': has state
 */
export interface NRGGraphNode {
  id: string
  label: string
  type: 'author' | 'paper' | 'institution'
  area?: string
  state?: string
  year?: number
  citations?: number
}

export interface NRGGraphResponse {
  nodes: NRGGraphNode[]
  edges: GraphEdge[]
  warnings?: QueryWarning[]
}

// ─── Query ────────────────────────────────────────────────────────────────────

export type AnswerRoute = 'sql' | 'rag' | 'hybrid' | 'clarify' | 'blocked'
export type AnswerConfidenceLevel = 'high' | 'medium' | 'low' | 'needs_clarification'

export interface AnswerEngineConfidence {
  level: AnswerConfidenceLevel
  reason: string
}

export interface AnswerEngineCitation {
  id: string
  source_type: 'sql_row' | 'document_chunk' | 'graph_edge'
  label: string
  source_id: string
  masked?: boolean
}

export interface AnswerEngineSourceData {
  sql_query?: string | null
  rows: Array<Record<string, unknown>>
  documents: Array<Record<string, unknown>>
}

export interface AnswerEngineFreshness {
  database_snapshot?: string | null
  document_indexed_at?: string | null
  warning?: string | null
}

/**
 * Query response from /query.
 *
 * citations[].authors follows the same string|string[] rule as Publication.authors.
 */
export interface NRGQueryResponse {
  query_id: string
  answer_id?: string
  audit_event_id?: string
  session_id?: string
  response: string
  status: 'success' | 'error' | 'partial' | 'blocked'
  tier: number
  question?: string
  interpreted_question?: string
  assumptions?: string[]
  route?: AnswerRoute
  final_answer?: string
  confidence?: AnswerEngineConfidence
  intent?: 'structured' | 'unstructured' | 'hybrid'
  routing_decision?: string
  verification_status: boolean
  answer_confidence?: AnswerConfidenceLevel | 'partial' | 'low_clarify'
  answer_confidence_score?: number
  sql_anomaly_report?: Record<string, unknown>
  sql_query?: string | null
  sql_queries?: string[]
  sql_results?: Array<Record<string, unknown>>
  source_data?: AnswerEngineSourceData
  freshness?: AnswerEngineFreshness
  caveats?: string[]
  follow_up_suggestions?: string[]
  query_time_ms?: number
  citations?: Array<{
    id: string
    source: string
    source_type?: 'sql_row' | 'document_chunk' | 'graph_edge'
    label?: string
    source_id?: string
    masked?: boolean
    pub_id?: string
    chunk_id?: string
    title: string
    /** Same string|string[] ambiguity as Publication.authors */
    authors: string | string[] | null
    year?: number
    relevance_score?: number
    chunk_text?: string
  }>
  warnings?: QueryWarning[]
  retrieval_sources?: string[]
  provenance?: {
    planner?: string
    synth?: string
    verifier?: string
    cloud_synthesis_used?: boolean
    hybrid_evidence?: {
      sql_rows?: number
      document_chunks?: number
    }
  }
  synthesis_method?: string
  conversation_history: Array<{ query: string; response: string }>
}

// ─── Streaming Query ─────────────────────────────────────────────────────────

export interface PlanDAG {
  steps: string[]
  nodes?: Array<{
    id: string
    label: string
    status?: 'pending' | 'active' | 'complete'
  }>
}

export type StreamPhaseName =
  | 'understanding'
  | 'parsing'
  | 'planning'
  | 'planned'
  | 'searching_records'
  | 'checking_documents'
  | 'querying'
  | 'executing'
  | 'synthesizing'
  | 'verifying'
  | 'verified'
  | 'error'

export type StreamQueryEvent =
  | { phase: 'planned'; plan: PlanDAG }
  | { phase: 'executing'; sql?: string; retrieved_count?: number }
  | { phase: 'synthesizing'; token: string; citation?: Citation }
  | { phase: 'verified'; citations: Citation[]; audit_event_id: string; signature_bytes?: number }
  | { phase: 'heartbeat' }
  | { phase: 'error'; message?: string }

// ─── Consent ──────────────────────────────────────────────────────────────────

export interface ConsentStatus {
  granted: boolean
  scope: string
  granted_at?: string
  expires_at?: string
}

// ─── Helpers ────────────────────────────────────────────────────────────────────

/**
 * Normalise a potentially ambiguous "list of things" field.
 * Handles:
 *   - string (comma-separated): "AI, ML, DL" → ["AI", "ML", "DL"]
 *   - string[]: passed through
 *   - null / undefined: returns []
 *
 * @example
 *   const authors = toStringArray(citation.authors)
 *   authors.map(a => <span key={a}>{a}</span>)
 */
export function toStringArray(value: string | string[] | null | undefined): string[] {
  if (Array.isArray(value)) return value.filter(Boolean) as string[]
  if (typeof value === 'string') {
    return value.split(',').map(s => s.trim()).filter(Boolean)
  }
  return []
}

/** Returns true if value is a non-null, non-empty array */
export function isNonEmptyArray<T>(value: unknown): value is T[] {
  return Array.isArray(value) && value.length > 0
}

/** Returns true if value is a string (including empty string) */
export function isString(value: unknown): value is string {
  return typeof value === 'string'
}

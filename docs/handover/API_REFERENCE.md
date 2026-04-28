# NRG API Reference

## Human-Edited API Documentation with Persona Examples

**Version:** 1.0
**Base URL:** `http://localhost:8000` (production: `https://nrg.iitgn.ac.in`)
**Authentication:** Bearer JWT (RS256) — tokens expire in 1 hour

---

## 1. Authentication

### 1.1 Login — Researcher (Tier 1)

Runtime paths: `POST /login` and `POST /auth/login`.

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "researcher_user-researcher_user",
    "username": "researcher_user",
    "role": "researcher",
    "tier": 1
  }
}
```

### 1.2 Login — Government (Tier 2)

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"gov_user","password":"gov-pass"}'
```

### 1.3 Login — Industry (Tier 3)

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"industry_user","password":"industry-pass"}'
```

### 1.4 Refresh Token

Runtime paths: `POST /refresh` and `POST /auth/refresh`.

```bash
curl -X POST http://localhost:8000/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```

### 1.5 Logout

Runtime paths: `POST /logout` and `POST /auth/logout`.

```bash
curl -X POST http://localhost:8000/logout \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```

### 1.6 Current Session

```bash
curl http://localhost:8000/auth/session \
  -H "Authorization: Bearer <access_token>"
```

Returns the active authenticated session claims without exposing signing material.

---

## 2. Query Endpoint — The Core of NRG

### 2.1 Natural Language Query (All Personas)

**Researcher asks:** "Find robotics researchers in Gujarat"

```bash
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"query":"find robotics researchers in Gujarat"}'
```

**Response:**
```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "session-uuid",
  "response": "There are 23 robotics researchers in Gujarat. Top researchers include Dr. Priya Sharma (IIT Gandhinagar, h-index 45) and Dr. Amit Patel (IIT Bombay, h-index 38).",
  "status": "success",
  "tier": 1,
  "intent": "structured",
  "routing_decision": "text_to_sql",
  "verification_status": true,
  "citations": [
    {
      "id": "pub_001",
      "title": "Advances in Industrial Robotics",
      "year": 2024,
      "authors": ["P. Sharma", "A. Patel"]
    }
  ],
  "provenance": {
    "planner": "gpt-4o",
    "synth": "local",
    "cloud_synthesis_used": false
  },
  "warnings": []
}
```

**Government asks:** "Show me state-wise research funding trends"

```json
{
  "query": "Show me state-wise research funding trends",
  "tier": 2,
  "intent": "structured",
  "response": "Funding distribution by state: Maharashtra ₹2,400 Cr, Karnataka ₹1,800 Cr, Tamil Nadu ₹1,200 Cr, Gujarat ₹980 Cr. Overall national funding increased 18% YoY.",
  "citations": [...],
  "provenance": {"synth": "cloud_llm"}
}
```

**Industry asks:** "Who works on hydrogen fuel cells?"

```json
{
  "query": "Who works on hydrogen fuel cells?",
  "tier": 3,
  "intent": "structured",
  "response": "12 researchers across India work on hydrogen fuel cells. Top institutions: IIT Bombay, IISc Bangalore, IIT Madras. Research areas include PEMFC, solid oxide fuel cells, hydrogen storage.",
  "citations": [...],
  "tier_enforced": true,
  "personal_data_accessible": false
}
```

### 2.2 Multi-Hop Query (Complex)

**Researcher asks:** "Compare AI research output between Gujarat and Karnataka over the last 5 years"

```json
{
  "query": "Compare AI research output between Gujarat and Karnataka over the last 5 years",
  "status": "success",
  "intent": "structured",
  "routing_decision": "text_to_sql",
  "planner_output": {
    "sub_queries": [
      "SELECT COUNT(*) FROM publications WHERE state='Gujarat' AND year>=2021 AND research_area='AI'",
      "SELECT COUNT(*) FROM publications WHERE state='Karnataka' AND year>=2021 AND research_area='AI'",
      "SELECT SUM(funding) FROM funding WHERE state='Gujarat' AND year>=2021",
      "SELECT SUM(funding) FROM funding WHERE state='Karnataka' AND year>=2021"
    ],
    "dag_execution": "sequential"
  },
  "response": "Gujarat: 1,245 publications, ₹340 Cr funding. Karnataka: 2,890 publications, ₹890 Cr funding. Karnataka leads by 2.3x in publication volume and 2.6x in funding.",
  "verification_status": true
}
```

---

## 3. Data Endpoints — Direct Access

### 3.1 Get Researchers

**Researcher (Tier 1) sees full details:**

```bash
curl "http://localhost:8000/researchers?limit=5&state=Gujarat" \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "researchers": [
    {
      "researcher_id": "RES-00001",
      "name": "Dr. Rajesh Patel",
      "email": "rajesh.patel@iitgn.ac.in",
      "phone": "+91-79-XXXX-XXXX",
      "institution_id": "INST-001",
      "state": "Gujarat",
      "research_area": "Artificial Intelligence",
      "year_joined": 2015,
      "h_index": 42,
      "publications": 156
    }
  ],
  "total": 142,
  "limit": 5,
  "offset": 0
}
```

**Government (Tier 2) sees anonymized data:**

```json
{
  "researchers": [
    {
      "state": "Gujarat",
      "research_area": "Artificial Intelligence",
      "count": 142,
      "avg_h_index": 31,
      "institutions": 8
    }
  ]
}
```

**Industry (Tier 3) sees names and research areas only:**

```json
{
  "researchers": [
    {
      "name": "Dr. Rajesh Patel",
      "research_area": "Artificial Intelligence",
      "institution": "IIT Gandhinagar"
    }
  ]
}
```

### 3.2 Get Publications

```bash
curl "http://localhost:8000/publications?limit=10&year=2024" \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "publications": [
    {
      "publication_id": "PUB-001",
      "title": "Deep Learning for Computer Vision",
      "year": 2024,
      "authors": ["R. Patel", "S. Sharma"],
      "abstract": "This paper presents...",
      "citations": 45,
      "research_area": "Computer Vision"
    }
  ],
  "total": 5000,
  "limit": 10,
  "offset": 0
}
```

### 3.3 Get Statistics

```bash
curl "http://localhost:8000/stats" \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "total_researchers": 5615,
  "total_publications": 12000,
  "total_institutions": 181,
  "total_labs": 889,
  "total_projects": 8048,
  "total_patents": 3000,
  "total_collaborations": 5000
}
```

### 3.4 Get Labs

```bash
curl "http://localhost:8000/labs?limit=10" \
  -H "Authorization: Bearer <access_token>"
```

### 3.5 Get Funding Records

```bash
curl "http://localhost:8000/funding?limit=20&state=Gujarat" \
  -H "Authorization: Bearer <access_token>"
```

---

## 4. Graph Endpoint — Knowledge Visualization

### 4.1 Knowledge Graph

**Researcher asks:** "Show me the research network around machine learning"

```bash
curl "http://localhost:8000/query/graph?topic=machine%20learning" \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "nodes": [
    {"id": "n1", "label": "Machine Learning", "type": "topic", "count": 2450},
    {"id": "n2", "label": "Deep Learning", "type": "topic", "count": 1820},
    {"id": "n3", "label": "Dr. R. Patel", "type": "author", "h_index": 42},
    {"id": "n4", "label": "Dr. S. Sharma", "type": "author", "h_index": 38},
    {"id": "n5", "label": "IIT Bombay", "type": "institution"},
    {"id": "n6", "label": "IIT Gandhinagar", "type": "institution"}
  ],
  "edges": [
    {"source": "n1", "target": "n2", "type": "related", "weight": 0.9},
    {"source": "n3", "target": "n1", "type": "authored", "weight": 1.0},
    {"source": "n4", "target": "n1", "type": "authored", "weight": 0.85},
    {"source": "n3", "target": "n5", "type": "affiliated", "weight": 1.0},
    {"source": "n5", "target": "n6", "type": "collaboration", "weight": 0.6}
  ]
}
```

---

## 5. DPDP Compliance Endpoints

### 5.1 Grant Consent (Researcher)

```bash
curl -X POST "http://localhost:8000/consent" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"scope":"research_access"}'
```

**Response:**
```json
{
  "success": true,
  "consent_id": "consent-uuid",
  "scope": "research_access",
  "granted_at": "2026-04-24T10:30:00Z",
  "description": "Access research data for academic collaboration"
}
```

### 5.2 List My Consents

```bash
curl "http://localhost:8000/me/consents" \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "consents": [
    {
      "scope": "research_access",
      "active": true,
      "granted_at": "2026-04-24T10:30:00Z",
      "description": "Access research data"
    },
    {
      "scope": "profile_visibility",
      "active": true,
      "granted_at": "2026-04-24T10:30:00Z",
      "description": "Allow others to find my profile"
    }
  ]
}
```

### 5.3 Export My Data

```bash
curl "http://localhost:8000/me/data" \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "user_id": "researcher-1",
  "export_timestamp": "2026-04-24T10:30:00Z",
  "consents": [...],
  "profile": {
    "name": "Dr. Rajesh Patel",
    "email": "rajesh.patel@iitgn.ac.in",
    "institution": "IIT Gandhinagar",
    "research_area": "Artificial Intelligence",
    "publications": 156,
    "h_index": 42
  },
  "audit_events": [
    {"timestamp": "2026-04-24T09:00:00Z", "action": "login"},
    {"timestamp": "2026-04-24T09:01:00Z", "action": "query", "query": "find robotics researchers"}
  ]
}
```

### 5.4 Delete My Data (Right to Erasure)

```bash
curl -X DELETE "http://localhost:8000/me/data" \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "success": true,
  "consents_deleted": 3,
  "events_anonymized": 47,
  "message": "Your data has been anonymized. Consent records retained for legal compliance."
}
```

### 5.5 Admin and Data Principal Aliases

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/dpdp/export` | Required | Alternate data-export path for authenticated principals. |
| POST | `/dpdp/erase` | Required | Alternate erasure request path for authenticated principals. |
| GET | `/dpdp/consents` | Required | Lists consent state through the DPDP path. |
| DELETE | `/consent/{scope}` | Required | Revokes one consent scope. |
| GET | `/admin/dpdp/stats` | Admin | Reports DPDP request and consent statistics. |

---

## 6. Audit Endpoints

### 6.1 Verify Audit Chain Integrity

```bash
curl http://localhost:8000/audit/verify
```

**Response:**
```json
{
  "valid": true,
  "events_checked": 6079,
  "first_hash": "0000a1b2c3d4...",
  "last_hash": "ffff1a2b3c4d...",
  "chain_intact": true
}
```

### 6.2 Get Audit Events

```bash
curl "http://localhost:8000/audit/events?limit=100&user_id=researcher-1" \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "events": [
    {
      "event_type": "query",
      "user_id": "researcher-1",
      "timestamp": "2026-04-24T10:30:00Z",
      "query_id": "550e8400-e29b-41d4-a716-446655440000",
      "hash": "abc123..."
    },
    {
      "event_type": "auth",
      "user_id": "researcher-1",
      "timestamp": "2026-04-24T10:29:00Z",
      "action": "login"
    }
  ],
  "total": 47
}
```

---

## 7. Health Endpoints

### 7.1 Basic Health

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "timestamp": "2026-04-24T10:30:00Z",
  "version": "1.0.0"
}
```

### 7.2 Full Health Check

```bash
curl http://localhost:8000/health/all
```

```json
{
  "api": "healthy",
  "database": "healthy",
  "llm": {
    "ready": true,
    "provider": "nvidia",
    "model": "nvidia/llama-3.1-70b-instruct",
    "fallback_chain": ["nvidia", "openai", "anthropic", "local_llm", "rule_based"]
  },
  "qdrant": "healthy",
  "redis": "healthy",
  "audit_chain": "intact"
}
```

---

## 8. Additional Production Endpoints

These endpoints are active in `src/api/main.py` and `src/api/routes/`.

### 8.1 SSO

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/auth/sso/login` | No | Returns authorization URL and state for the configured SSO provider. |
| POST | `/auth/sso/callback` | No | Exchanges provider callback data for an NRG session. |
| GET | `/auth/sso/status` | No | Reports whether SSO is configured and enabled. |

### 8.2 Streaming Query

`POST /api/query/stream` emits server-sent events for long-running queries.

```bash
curl -N -X POST http://localhost:8000/api/query/stream \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"query":"Compare AI research output between Gujarat and Karnataka over the last 5 years"}'
```

Events include phase updates such as `intent_detection`, `retrieval`, `synthesis`, and final answer payloads.

### 8.3 Telemetry, Feedback, and Ingest

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/telemetry` | Optional session | Accepts frontend telemetry payloads. |
| POST | `/api/feedback` | Required | Records answer feedback for later review. |
| POST | `/api/ingest` | Admin | Starts a document/data ingest job. |
| GET | `/api/ingest/{job_id}` | Admin | Reads ingest job status. |

### 8.4 Detailed Health and Operations

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health/killer_queries` | No | Runs or reports critical query health checks. |
| GET | `/health/llm` | No | Reports configured LLM provider readiness. |
| GET | `/api/providers/health` | No | Reports provider mesh health. |
| GET | `/health/db` | No | Reports database connectivity and table state. |
| GET | `/health/qdrant` | No | Reports Qdrant readiness. |
| GET | `/api/vectors/health` | No | Reports vector collection health. |
| GET | `/admin/slo` | Admin | Reports SLO status and current budget state. |
| GET | `/metrics` | No | Prometheus metrics endpoint. |
| GET | `/api/metrics` | No | JSON metrics endpoint. |
| POST | `/api/reindex` | Admin | Starts vector reindexing. |

### 8.5 Remaining Data Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/projects` | Required | Returns tier-filtered project rows. |
| GET | `/patents` | Required | Returns tier-filtered patent rows. |
| GET | `/collaborations` | Required | Returns tier-filtered collaboration rows. |
| GET | `/research-documents` | Required | Returns accessible research-document metadata. |
| POST | `/query/graph` | Required | Builds a graph response for a supplied query. |
| GET | `/query/graph` | Required | Reads graph data for a supplied topic. |
| GET | `/api/internal/tier_diff` | Internal | Compares tier-filtered response shapes for audits. |

### 8.6 Admin RBAC

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/admin/rbac` | Admin | Lists persona and role rules. |
| POST | `/api/admin/rbac` | Admin | Creates a persona rule. |
| GET | `/api/admin/rbac/{persona_name}` | Admin | Reads one persona rule. |
| PUT | `/api/admin/rbac/{persona_name}` | Admin | Updates one persona rule. |
| DELETE | `/api/admin/rbac/{persona_name}` | Admin | Deletes one persona rule. |

### 8.7 Frontend Fallback

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/{full_path:path}` | No | Serves the frontend application for non-API paths. |

---

## 9. Error Responses

| Code | Meaning | Common Cause |
|------|---------|--------------|
| **400** | Bad Request | Malformed JSON, missing required fields |
| **401** | Unauthorized | Invalid/expired JWT, missing token |
| **403** | Forbidden | Tier insufficient for requested data |
| **404** | Not Found | Resource doesn't exist |
| **422** | Unprocessable Entity | PII detected in query |
| **423** | Account Locked | Brute-force protection triggered |
| **429** | Rate Limit Exceeded | Too many requests, wait and retry |
| **500** | Internal Server Error | System error, check logs |
| **503** | Service Unavailable | LLM providers down, falls back to local |

### Example Error Responses

**PII Detected (422):**
```json
{
  "detail": "Security violation: PII detected in query. Aadhaar numbers are not allowed.",
  "code": "PII_VIOLATION",
  "query_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Tier Insufficient (403):**
```json
{
  "detail": "Access denied. Industry tier (Tier 3) cannot access researcher email addresses.",
  "code": "TIER_INSUFFICIENT",
  "required_tier": 1,
  "current_tier": 3
}
```

**Rate Limited (429):**
```json
{
  "detail": "Rate limit exceeded. Please wait 60 seconds.",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```

---

## 10. Rate Limits by Tier

| Tier | Requests/minute | Queries/hour |
|------|----------------|--------------|
| Tier 1 (Researcher) | 60 | 500 |
| Tier 2 (Government) | 120 | 1000 |
| Tier 3 (Industry) | 30 | 200 |

---

## 11. Common Workflows

### 10.1 Complete Query Flow (Researcher)

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}' \
  | jq -r '.access_token')

# 2. Query
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"find robotics researchers in Gujarat"}'

# 3. Get citation details
curl "http://localhost:8000/publications/pub_001" \
  -H "Authorization: Bearer $TOKEN"

# 4. Check audit
curl http://localhost:8000/audit/verify
```

### 10.2 Government Statistical Query

```bash
# Login as government
TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"gov_user","password":"gov-pass"}' \
  | jq -r '.access_token')

# Query aggregated stats
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"state-wise research funding for the last 3 years"}'
```

### 10.3 Industry Partner Discovery

```bash
# Login as industry
TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"industry_user","password":"industry-pass"}' \
  | jq -r '.access_token')

# Find researchers in domain (no personal data)
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"who is working on electric vehicle battery technology"}'
```

---

## 12. Real-time Streaming

NRG uses server-sent events at `POST /api/query/stream` for streaming responses.

```bash
curl -N -X POST http://localhost:8000/api/query/stream \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"query":"list all AI researchers in India with their publication counts"}'
```

Expected event types: `phase`, `chunk`, `final`, and `error`.

---

*Document version: 1.0*
*Last updated: 2026-04-29*
*API version: 1.0*
*For questions: api@nrg.iitgn.ac.in*

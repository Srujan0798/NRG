# NRG API Specification

**Version:** 1.0  
**Base URL:** `http://localhost:8000`  
**Authentication:** Bearer JWT (RS256)

---

## 1. Authentication

### 1.1 Login

```
POST /login
Content-Type: application/json

Request:
{
  "username": "researcher_user",
  "password": "researcher-pass"
}

Response (200):
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_expires_in": 604800,
  "user": {
    "id": "researcher_user-researcher_user",
    "username": "researcher_user",
    "role": "researcher",
    "tier": 1,
    "researcher_id": "researcher-1"
  }
}
```

### 1.2 Refresh Token

```
POST /refresh
Content-Type: application/json

Request:
{
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}

Response (200):
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 1.3 Logout

```
POST /logout
Authorization: Bearer <access_token>
Content-Type: application/json

Request:
{
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}

Response (200):
{
  "status": "revoked"
}
```

---

## 2. Query Endpoint

### 2.1 Execute Query

```
POST /query
Authorization: Bearer <access_token>
Content-Type: application/json

Request:
{
  "query": "AI researchers in Gujarat",
  "session_id": "optional-session-id"
}

Response (200):
{
  "query_id": "uuid",
  "session_id": "session-uuid",
  "response": "There are 142 AI researchers in Gujarat...",
  "status": "success",
  "tier": 1,
  "intent": "structured",
  "routing_decision": "text_to_sql",
  "verification_status": true,
  "citations": [
    {
      "id": "pub_001",
      "title": "Deep Learning for Computer Vision",
      "year": 2024,
      "authors": ["R. Patel", "S. Sharma"]
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

---

## 3. Data Endpoints

### 3.1 Get Researchers

```
GET /researchers?limit=10&state=Gujarat
Authorization: Bearer <access_token>

Response (200):
{
  "researchers": [
    {
      "researcher_id": "RES-00001",
      "name": "Dr. Rajesh Patel",
      "institution_id": "INST-001",
      "state": "Gujarat",
      "research_area": "Artificial Intelligence",
      "year_joined": 2015,
      "h_index": 42
    }
  ],
  "total": 142,
  "limit": 10,
  "offset": 0
}
```

### 3.2 Get Publications

```
GET /publications?limit=20&year=2024
Authorization: Bearer <access_token>

Response (200):
{
  "publications": [...],
  "total": 5000,
  "limit": 20,
  "offset": 0
}
```

### 3.3 Get Statistics

```
GET /stats
Authorization: Bearer <access_token>

Response (200):
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

---

## 4. Graph Endpoint

### 4.1 Knowledge Graph

```
GET /query/graph?topic=machine%20learning
Authorization: Bearer <access_token>

Response (200):
{
  "nodes": [
    {"id": "n1", "label": "Machine Learning", "type": "topic"},
    {"id": "n2", "label": "Deep Learning", "type": "topic"},
    {"id": "n3", "label": "Dr. R. Patel", "type": "author"}
  ],
  "edges": [
    {"source": "n1", "target": "n2", "type": "related", "weight": 0.8},
    {"source": "n3", "target": "n1", "type": "authored", "weight": 1.0}
  ]
}
```

---

## 5. DPDP Compliance Endpoints

### 5.1 Grant Consent

```
POST /consent
Authorization: Bearer <access_token>
Content-Type: application/json

Request:
{
  "scope": "research_access"
}

Response (200):
{
  "success": true,
  "consent_id": "uuid",
  "scope": "research_access",
  "granted_at": "2026-04-21T10:30:00Z"
}
```

### 5.2 List Consents

```
GET /me/consents
Authorization: Bearer <access_token>

Response (200):
{
  "consents": [
    {
      "scope": "research_access",
      "active": true,
      "granted_at": "2026-04-21T10:30:00Z",
      "description": "Access research data"
    }
  ]
}
```

### 5.3 Export User Data

```
GET /me/data
Authorization: Bearer <access_token>

Response (200):
{
  "user_id": "user-123",
  "export_timestamp": "2026-04-21T10:30:00Z",
  "consents": [...],
  "audit_events": [...]
}
```

### 5.4 Delete User Data (Right to Erasure)

```
DELETE /me/data
Authorization: Bearer <access_token>

Response (200):
{
  "success": true,
  "consents_deleted": 3,
  "events_anonymized": 47
}
```

---

## 6. Audit Endpoints

### 6.1 Verify Audit Chain

```
GET /audit/verify

Response (200):
{
  "valid": true,
  "events_checked": 6079,
  "first_hash": "0000...",
  "last_hash": "ffff..."
}
```

### 6.2 Get Audit Events

```
GET /audit/events?limit=100&user_id=user-123

Response (200):
{
  "events": [
    {
      "event_type": "query",
      "user_id": "user-123",
      "timestamp": "2026-04-21T10:30:00Z",
      "hash": "abc123..."
    }
  ],
  "total": 47
}
```

---

## 7. Health Endpoints

### 7.1 Basic Health

```
GET /health

Response (200):
{
  "status": "healthy",
  "timestamp": "2026-04-21T10:30:00Z"
}
```

### 7.2 Full Health Check

```
GET /health/all

Response (200):
{
  "api": "healthy",
  "database": "healthy",
  "llm": {
    "ready": true,
    "provider": "nvidia",
    "model": "nvidia/llama-3.1-70b-instruct"
  },
  "qdrant": "healthy",
  "redis": "healthy"
}
```

---

## Error Responses

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid/missing token |
| 403 | Forbidden - Tier insufficient |
| 404 | Not Found |
| 423 | Account Locked (brute-force) |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

### Example Error

```json
{
  "detail": "Security violation: PII detected in query"
}
```

---

**Generated:** 2026-04-21  
**Version:** 1.0
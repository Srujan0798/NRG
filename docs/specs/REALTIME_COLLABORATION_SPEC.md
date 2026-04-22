# Feature Spec: Real-Time Collaboration Features
**Phase:** Phase 3 (Month 14–16)
**Document Status:** Draft
**Author:** NRG Platform Team

---

## 1. Problem Statement

Currently, NRG is a single-user query system. When a researcher shares a query URL with a colleague, the colleague sees the same static response — but:

1. **No collaborative querying** — multiple users can't build on each other's queries in real-time
2. **No shared workspaces** — a team can't maintain a shared set of saved queries and insights
3. **No presence** — users don't know if teammates are online or researching the same topic
4. **No real-time annotations** — a team can't annotate a research finding without leaving the platform

The Core_Idea_Clean.md describes NRG as "the Research OS of India" — an operating system implies collaboration, not just individual use.

---

## 2. Goals

1. **Shared query sessions** — multiple users can join the same query session and see real-time updates
2. **Team workspaces** — shared folders for saved queries, annotations, and insights
3. **User presence** — see who's online in your team and what they're researching
4. **Inline annotations** — comment on specific research findings without leaving the platform

---

## 3. Non-Goals

- Real-time collaborative editing of query text — too complex for Phase 3
- Video/audio conferencing — integrate with external tools (Google Meet, Zoom)
- Public collaboration spaces — teams are invite-only
- Real-time data updates — query results reflect the database at query time, not live

---

## 4. User Stories

### Story 1: Shared Research Session
> **Actor:** Dr. Patel (Researcher, IIT Gandhinagar)
> **Scenario:** Dr. Patel is researching hydrogen catalysis with a colleague, Dr. Sharma. She shares a session link. Both see the same query results. When Dr. Sharma adds an annotation "See also: related work at IIT Bombay", Dr. Patel sees it appear in real-time.
> **Result:** Faster collaborative insight generation without switching to a separate chat tool.

### Story 2: Team Workspace
> **Actor:** Government analyst, Ministry of Education
> **Scenario:** The analyst's team maintains a shared workspace "India AI Research 2026". They save queries, tag important publications, and add annotations. New team members can see the full research context.
> **Result:** Institutional knowledge doesn't leave when people change roles.

### Story 3: Research Annotation
> **Actor:** Industry R&D manager
> **Scenario:** The manager sees a publication in query results and adds an annotation "Potential partnership candidate". The research team lead sees the annotation when they run the same query.
> **Result:** Research findings flow to the right people without email chains.

---

## 5. Architecture

### 5.1 Core Services

```
┌─────────────────────────────────────────────────────────┐
│                    NRG Backend                            │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Query API   │  │ Workspace API│  │ Annotation API │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘  │
│         │                │                  │           │
│  ┌──────▼────────────────▼──────────────────▼────────┐  │
│  │              Collaboration Service                 │  │
│  │  - Session management                              │  │
│  │  - Presence (WebSocket)                           │  │
│  │  - Real-time sync (Redis Pub/Sub)                  │  │
│  └──────────────────────┬─────────────────────────────┘  │
└─────────────────────────┼────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
    ┌──────────────────┐    ┌──────────────────┐
    │  Redis (Pub/Sub) │    │  PostgreSQL       │
    │  Real-time events│    │  Workspaces,      │
    │  Presence state  │    │  Annotations      │
    └──────────────────┘    └──────────────────┘
```

### 5.2 WebSocket Protocol

```
Client → Server:
  { "type": "join_session", "session_id": "abc123" }
  { "type": "leave_session", "session_id": "abc123" }
  { "type": "annotation_create", "session_id": "abc123", "data": {...} }
  { "type": "ping" }

Server → Client:
  { "type": "session_joined", "users": ["user1", "user2"] }
  { "type": "user_joined", "user": "user2" }
  { "type": "user_left", "user": "user2" }
  { "type": "annotation_created", "annotation": {...} }
  { "type": "presence_update", "users": [...] }
```

---

## 6. Data Model

### 6.1 PostgreSQL Tables

```sql
-- Teams (groups of users)
CREATE TABLE teams (
    team_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tier_access INT DEFAULT 1
);

-- Team membership
CREATE TABLE team_members (
    team_id UUID REFERENCES teams(team_id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'member',  -- 'owner', 'member'
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_id, user_id)
);

-- Workspaces (shared folders within a team)
CREATE TABLE workspaces (
    workspace_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(team_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT FALSE
);

-- Saved queries within a workspace
CREATE TABLE saved_queries (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    query_params JSONB,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Annotations on research findings
CREATE TABLE annotations (
    annotation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Reference to the finding being annotated
    publication_id VARCHAR(255),
    researcher_id VARCHAR(255),
    query_id UUID REFERENCES saved_queries(query_id),
    -- Annotation content
    content TEXT NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Location in the response
    response_fingerprint VARCHAR(64),  -- hash of the response for deduplication
    chunk_index INT,
    -- Visibility
    team_id UUID REFERENCES teams(team_id),  -- NULL = private
    is_pinned BOOLEAN DEFAULT FALSE
);

-- Query sessions (ephemeral, not persisted long-term)
CREATE TABLE query_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    query_text TEXT NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- sessions expire after 24 hours
    workspace_id UUID REFERENCES workspaces(workspace_id)
);

CREATE INDEX idx_annotations_team ON annotations(team_id);
CREATE INDEX idx_annotations_publication ON annotations(publication_id);
CREATE INDEX idx_saved_queries_workspace ON saved_queries(workspace_id);
```

### 6.2 Redis Structures

```
# Presence (set of active users per workspace)
workspace:{workspace_id}:presence -> SET of user_ids with TTL

# Session participants
session:{session_id}:participants -> SET of user_ids

# Real-time annotation feed (last 50 annotations per workspace)
workspace:{workspace_id}:annotations -> LIST (capped at 50)
```

---

## 7. Feature Details

### 7.1 Shared Query Sessions

**Flow:**
1. User A runs a query → gets `session_id` in response
2. User A shares the `session_id` link with User B
3. User B joins the session via WebSocket
4. Both users see the same query results
5. When User B annotates a finding, User A sees it appear in real-time

**API:**
```
POST /sessions              — Create a new session
GET  /sessions/{id}         — Get session state
POST /sessions/{id}/join    — Join a session (WebSocket upgrade)
DELETE /sessions/{id}        — End session
```

**WebSocket events:**
- `user_joined` — when someone joins
- `user_left` — when someone leaves
- `annotation_created` — new annotation in session
- `query_result_updated` — (future) when query results change

### 7.2 Team Workspaces

**Flow:**
1. Create a team → invite members
2. Create workspaces within the team (e.g., "India AI Research 2026")
3. Save queries to the workspace
4. All team members can see saved queries and annotations

**API:**
```
POST   /teams                      — Create team
GET    /teams/{id}                 — Get team details
POST   /teams/{id}/members         — Add member
DELETE /teams/{id}/members/{uid}   — Remove member

POST   /workspaces                 — Create workspace
GET    /workspaces/{id}            — Get workspace with saved queries
PUT    /workspaces/{id}            — Update workspace
DELETE /workspaces/{id}            — Delete workspace

GET    /workspaces/{id}/annotations — Get all annotations
GET    /workspaces/{id}/saved_queries — Get all saved queries
```

### 7.3 Inline Annotations

**Flow:**
1. User runs a query → sees results
2. User clicks "annotate" on a specific finding
3. Modal opens → user types annotation
4. Annotation is saved (to workspace or private)
5. Other team members see the annotation when they run the same query

**API:**
```
POST   /annotations                — Create annotation
GET    /annotations/{id}          — Get annotation
PUT    /annotations/{id}          — Update annotation
DELETE /annotations/{id}          — Delete annotation
PATCH  /annotations/{id}/pin      — Pin/unpin annotation
```

### 7.4 User Presence

**Flow:**
1. User logs in → added to "online" set for their workspaces
2. Presence shown in workspace sidebar: "3 members online"
3. When user closes browser/tab → removed after 30s timeout (heartbeat)
4. Workspace members see who's researching what via status messages

**Redis TTL-based presence:**
```
SET workspace:{id}:presence:{user_id} {metadata} EX 60
# Refreshed every 30s via heartbeat
# Auto-expires after 60s if no heartbeat
```

---

## 8. Tier Enforcement in Collaboration

| Tier | Collaboration Features |
|------|----------------------|
| 1 (Researcher) | Can create teams, invite other Tier 1 users, share findings |
| 2 (Government) | Can create government-only workspaces, no external sharing |
| 3 (Industry) | Can create industry workspaces, limited to industry tier members |

**Cross-tier collaboration:** Not supported. Government and Industry workspaces are siloed.

---

## 9. Security Considerations

| Concern | Mitigation |
|---------|------------|
| Unauthorized session access | Session tokens are cryptographically signed; exp after 24h |
| Annotation injection | All annotation content sanitized (strip HTML, limit length) |
| Team data leaks | Workspace membership validated on every API call |
| WebSocket connection hijacking | JWT validated on WebSocket handshake |
| Presence spoofing | Heartbeat prevents stale presence; server-authoritative |

---

## 10. Performance Requirements

| Metric | Target | Notes |
|--------|--------|-------|
| WebSocket connection latency | < 50ms | Within region |
| Annotation sync latency | < 200ms | From create to other users seeing it |
| Presence update latency | < 500ms | User appears online after login |
| Concurrent WebSocket connections | 1,000+ | Per workspace channel |
| Max annotations per workspace | 10,000 | Paginated API, Redis-capped feed |

---

## 11. Implementation Phases

### Phase 1: Core Collaboration Infrastructure (Month 14)
- [ ] PostgreSQL tables for teams, workspaces, annotations
- [ ] Redis Pub/Sub setup
- [ ] Team and workspace CRUD APIs
- [ ] Basic WebSocket server for presence

### Phase 2: Shared Sessions (Month 15)
- [ ] Session creation and joining APIs
- [ ] WebSocket event pipeline for session events
- [ ] Real-time annotation sync
- [ ] Session expiry (24h TTL)

### Phase 3: Annotation Deepening (Month 16)
- [ ] Annotation threading (replies)
- [ ] Annotation search
- [ ] Notification system (email/in-app for new annotations)
- [ ] Export annotations to PDF

---

## 12. Dependencies

| Dependency | Owner | Blocker For |
|-----------|-------|-------------|
| Redis Pub/Sub | Infra | Real-time events |
| PostgreSQL (production) | Infra | Persistent data |
| WebSocket server (FastAPI WebSockets) | Backend | Shared sessions |
| Notification service (email/SMTP) | Infra | Annotation notifications |
| JWT with WebSocket handshake | Auth | Secure session join |

---

## 13. Open Questions

1. **Annotation deduplication** — When is an annotation on the "same finding" vs a different finding? Use response fingerprint + chunk index?
2. **Free vs paid tiers** — Should collaboration be a paid feature? How many team members free vs paid?
3. **Data residency for collaboration** — If a government user annotates in a shared workspace, does that data stay on Indian servers only?
4. **Real-time cursor tracking** — Should we show where other users' cursors are (like Google Docs)? High complexity.
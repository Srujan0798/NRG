# NRG Production Walkthrough Guide

## Overview

This guide provides a step-by-step walkthrough of the NRG system for production verification and evaluator handoff.

---

## Quick Access Credentials

| Persona | Username | Password | Access Level |
|---------|----------|----------|--------------|
| Researcher | `researcher_user` | `researcher-pass` | Tier 1 - Full |
| Government | `gov_user` | `government-pass` | Tier 2 - Aggregated |
| Industry | `industry_user` | `industry-pass` | Tier 3 - Anonymized |

---

## Step 1: System Startup

```bash
# Start all services
docker compose --profile prod up -d

# Verify services are healthy
docker compose ps

# Access points:
# - Frontend: http://localhost (port 3000 for direct access)
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

---

## Step 2: Authentication

### Login via API

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "researcher_user", "password": "researcher-pass"}'
```

Response includes:
- `access_token`: JWT token (valid 1 hour)
- `refresh_token`: For token renewal
- `expires_in`: Token lifetime in seconds

### Login via Frontend

1. Open http://localhost:3000
2. Select persona (Researcher / Government / Industry)
3. Enter credentials
4. Click "Access Platform"

---

## Step 3: Making Queries

### Via API

```bash
# Get token first
TOKEN="your_jwt_token_here"

# Submit query
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many publications are there?"}'
```

Response includes:
```json
{
  "audit_event_id": "abc123...",
  "sql_query": "SELECT COUNT(*) AS count FROM publications...",
  "sql_results": [{"count": 12000}],
  "response": "There are 12,000 publications in the database.",
  "citations": [...],
  "tier": 1
}
```

### Via Frontend

1. Login and access dashboard
2. Type question in natural language search bar
3. Press Enter or click Search
4. View results with:
   - Natural language answer
   - SQL query (expandable)
   - Data table
   - Citations
   - Audit badge

---

## Step 4: Understanding Results

### Researcher Dashboard (Tier 1)

- Full researcher profiles with contact information
- Publication details with citation counts
- Funding history per researcher
- Lab and collaboration information

### Government Dashboard (Tier 2)

- Aggregated institutional statistics
- State-wise research trends
- Funding distribution analytics
- Policy-ready reports

### Industry Dashboard (Tier 3)

- Anonymized research capability overview
- Partnership opportunity descriptions
- No personal identifiers (email, phone, specific names)
- Institutional-level collaboration matching

---

## Step 5: Verifying Audit Trail

### API Verification

```bash
# Check audit chain integrity
curl http://localhost:8000/health/all \
  -H "Authorization: Bearer $TOKEN"
```

Response includes `audit_chain_valid: true` when chain is intact.

### Visual Verification

Every query result displays:
- "Verified" badge with audit event ID
- Timestamp of query execution
- Chain integrity indicator

---

## Step 6: Critical Query Examples

### Query 1: Top Funding Agencies

**Question**: "Show me the top 5 funding agencies by total grant amount"

**Expected SQL**:
```sql
SELECT gov_organisation_name, SUM(grant_received) AS total_grant
FROM innovation_grant_from_govt
GROUP BY gov_organisation_name
ORDER BY total_grant DESC
LIMIT 5
```

**Expected Results**: Table with agency names and total grants

---

### Query 2: TRL Progression

**Question**: "Show the technology readiness level progression for IIT Madras"

**Expected SQL**: CTE-based query joining `innovations_at_various_stages_of_technology_readiness_level`

**Expected Results**: Pipeline showing stages from Lab Validation to Market Ready

---

### Query 3: Research Output Comparison

**Question**: "Compare AI research output between IIT Bombay and IIT Madras over the last 5 years"

**Expected SQL**: Multi-year comparison with aggregation by institution

**Expected Results**: Side-by-side comparison table/chart

---

## Step 7: Security Verification

### PII Blocking

```bash
# Attempt query with PII
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Find researcher with Aadhaar 1234-5678-9012"}'
```

**Expected**: `400 Bad Request` with "PII detected" error

---

### Tier Isolation

```bash
# As Tier 3 user, query for researcher details
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $TIER3_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me contact details for researchers working on AI"}'
```

**Expected**: Anonymized results without email/phone/personal identifiers

---

## Step 8: Performance Verification

### Latency Check

```bash
time curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many institutions are there?"}'
```

**Expected**: Response in < 2 seconds for simple queries

---

## Troubleshooting

### Service Not Starting

```bash
# Check logs
docker compose logs api
docker compose logs postgres

# Restart services
docker compose restart
```

### Database Connection Error

```bash
# Verify PostgreSQL is running
docker compose ps postgres

# Check DATABASE_URL
echo $DATABASE_URL
```

### Authentication Failure

1. Verify credentials in `.env` file
2. Check JWT secret is properly configured
3. Ensure token hasn't expired (1 hour lifetime)

---

## Support

For issues:
1. Check API docs at http://localhost:8000/docs
2. Review audit logs in `.audit/chain.jsonl`
3. Check system health at http://localhost:8000/health/all

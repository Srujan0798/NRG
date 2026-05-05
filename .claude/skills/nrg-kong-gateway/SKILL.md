---
name: nrg-kong-gateway
description: Use when configuring or reviewing NRG Kong routes, gateway plugins, DLP behavior, tier-based rate limits, or upstream connectivity.
---

# NRG Kong Gateway Skill

API gateway configuration, DLP rules, rate limiting, and sovereign routing for the National Research Graph (NRG).

## When to Use

Use this skill when:
- Configuring Kong routes, services, or plugins for NRG APIs
- Implementing DLP (Data Loss Prevention) rules on API responses
- Setting up tier-based rate limiting at the gateway level
- Debugging Kong → upstream connectivity issues
- Adding new NRG microservices behind Kong

## NRG Kong Architecture

```
Client → Nginx (SSL termination) → Kong (8000/8443) → Upstream Services
                                      ├── /api/v1/query  → NRG API (:8000)
                                      ├── /api/v1/audit  → Audit Service
                                      ├── /api/v1/admin  → Admin APIs (IP-restricted)
                                      └── /health        → Health checks
```

Kong runs as the API gateway layer. All external traffic enters through Kong.

## Service Definitions

### NRG API Service

```yaml
# kong.yaml declarative config snippet
services:
  - name: nrg-api
    url: http://nrg-api:8000
    routes:
      - name: nrg-api-routes
        paths:
          - /api/v1/query
          - /api/v1/search
          - /api/v1/researchers
          - /api/v1/publications
        strip_path: false
        preserve_host: true
        protocols:
          - https
    plugins:
      - name: rate-limiting
        config:
          minute: 60
          policy: redis
          redis_host: redis
          redis_port: 6379
      - name: cors
        config:
          origins:
            - "https://nrg.gov.in"
          methods: [GET, POST, OPTIONS]
          headers: [Authorization, Content-Type]
      - name: request-transformer
        config:
          add:
            headers:
              - "X-Forwarded-By:kong"
```

### Audit Service

```yaml
  - name: nrg-audit
    url: http://nrg-audit:8001
    routes:
      - name: audit-routes
        paths:
          - /api/v1/audit
        strip_path: false
    plugins:
      - name: ip-restriction
        config:
          allow:
            - 10.0.0.0/8      # Internal VPC
            - 127.0.0.1/32    # localhost
```

## DLP Plugin Rules

NRG uses custom Kong DLP to prevent data exfiltration:

```lua
-- custom kong plugin: nrg-dlp
local _M = {}

_M.PRIORITY = 1000
_M.VERSION = "1.0.0"

local SENSITIVE_PATTERNS = {
  { pattern = "[A-Z]{5}[0-9]{4}[A-Z]", label = "PAN" },          -- Indian PAN
  { pattern = "[0-9]{12}", label = "AADHAAR" },                   -- Aadhaar (naive)
  { pattern = "\\b(?:private|confidential|restricted)\\b", label = "CLASSIFIED" },
}

function _M:access(conf)
  -- DLP runs on response, but we can set flags here
  kong.service.request.set_header("X-DLP-Check", "enabled")
end

function _M:header_filter(conf)
  local content_type = kong.response.get_header("Content-Type")
  if content_type and content_type:find("application/json", 1, true) then
    kong.ctx.plugin.dlp_check = true
  end
end

function _M:body_filter(conf)
  if not kong.ctx.plugin.dlp_check then return end
  
  local chunk = ngx.arg[1]
  if chunk then
    for _, rule in ipairs(SENSITIVE_PATTERNS) do
      if chunk:find(rule.pattern) then
        kong.response.set_status(403)
        kong.response.set_header("Content-Type", "application/json")
        ngx.arg[1] = '{"error":"DLP_VIOLATION","detail":"Response contains sensitive data"}'
        ngx.arg[2] = true
        return
      end
    end
  end
end

return _M
```

## Tier-Based Rate Limiting

Apply different rate limits per API key / JWT claim:

```yaml
plugins:
  - name: rate-limiting-advanced
    config:
      limit:
        - 10    # public tier
        - 60    # industry tier
        - 120   # academic tier
        - 300   # government tier
      window_size:
        - 60
        - 60
        - 60
        - 60
      identifier: "consumer"
      strategy: "redis"
      redis:
        host: redis
        port: 6379
```

Or use ACL + consumer groups:

```bash
# Create consumers per tier
curl -X POST http://localhost:8001/consumers \
  --data "username=gov-tier" \
  --data "custom_id=gov-001"

# Assign rate limit
curl -X POST http://localhost:8001/consumers/gov-tier/plugins \
  --data "name=rate-limiting" \
  --data "config.minute=300" \
  --data "config.policy=redis"
```

## JWT Authentication Plugin

```yaml
plugins:
  - name: jwt
    config:
      uri_param_names: []
      cookie_names: []
      key_claim_name: iss
      secret_is_base64: false
      claims_to_verify:
        - exp
      anonymous: null
      run_on_preflight: true
      maximum_expiration: 86400
```

## Request/Response Logging

Log all requests for audit trail:

```yaml
plugins:
  - name: file-log
    config:
      path: /var/log/kong/access.log
      reopen: true
  - name: statsd
    config:
      host: statsd
      port: 8125
      metrics:
        - name: request_count
          stat_type: counter
          sample_rate: 1
        - name: latency
          stat_type: timer
          sample_rate: 1
        - name: status_count
          stat_type: counter
          sample_rate: 1
```

## Health Check Configuration

```yaml
services:
  - name: nrg-api
    healthchecks:
      active:
        healthy:
          interval: 10
          http_statuses: [200]
          successes: 2
        unhealthy:
          interval: 10
          http_statuses: [500, 502, 503]
          timeouts: 5
          http_failures: 3
        http_path: /health
        timeout: 5
        type: http
```

## Sovereign Constraints

1. **No Kong Cloud:** Self-hosted Kong only (Kong Gateway OSS or Enterprise on-prem)
2. **SSL termination at Nginx:** Kong receives HTTP from Nginx; Nginx handles TLS
3. **No external auth providers:** JWT only, no OAuth2 to foreign IDPs
4. **DLP active on all egress:** Every response scanned for PAN, Aadhaar, classified markers
5. **Admin API locked down:** Kong Admin API (8001/8444) never exposed externally; bind to localhost or internal VPC only

## Debugging Commands

```bash
# Check Kong routes
curl http://localhost:8001/services

# Check plugin chains for a route
curl "http://localhost:8001/routes/{route_id}/plugins"

# Test upstream directly (bypass Kong)
curl http://nrg-api:8000/health

# View Kong error logs
docker logs kong-gateway 2>&1 | grep ERROR

# Reload declarative config
kong reload
```

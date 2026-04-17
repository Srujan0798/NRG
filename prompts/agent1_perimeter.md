# Agent 1: Perimeter Recovery

## Objective
Restore Kong perimeter and RS256 JWT + DLP runtime.

## Must Fix
- Kong boot failure from missing rsa_public_key in infrastructure/kong/kong.yml for RS256 jwt_secrets.
- Keep RS256 (no downgrade to HS256).

## Scope
- infrastructure/kong/kong.yml
- infrastructure/kong/docker-compose.yml
- infrastructure/kong/ssl/jwt_rsa.pub
- infrastructure/kong/plugins/dlp/*

## Done Criteria
1. docker shows nrg-kong-gateway healthy
2. :8000 and :8002 reachable
3. /login and protected route through Kong work
4. DLP blocks Aadhaar/PAN/phone with DLP_VIOLATION
5. pytest tests/security/test_kong_dlp_runtime.py -q passes

## Current State (from CFO Assessment)
- Kong is DOWN: nrg-kong-gateway is down (Exited (1))
- Ports 8000/8002 not listening
- Kong boot error: missing rsa_public_key for RS256 JWT

## Action Required
1. Check infrastructure/kong/kong.yml has valid rsa_public_key for all consumers (researcher, government, industry)
2. If key missing/expired, generate new RS256 key pair
3. Ensure KONG_PLUGINS includes dlp plugin
4. Restart Kong container with docker-compose
5. Verify :8000 and :8002 respond
6. Run security tests through Kong gateway

## Key Files to Modify
- infrastructure/kong/kong.yml - Add/verify rsa_public_key for each consumer
- infrastructure/kong/docker-compose.yml - Ensure plugin path mounted
- infrastructure/kong/plugins/dlp/* - Custom DLP plugin if needed
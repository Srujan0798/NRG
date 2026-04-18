# NRG Kong Gateway Specification v1.0

## Plugin Bundle

Kong declarative config (`infrastructure/kong/kong.yml`) includes:

| Plugin | Purpose | Defends Against |
|--------|---------|----------------|
| `rate-limiting-advanced` | Tiered rate limits | DoS attacks |
| `request-size-limit` | Max request size | Buffer overflow |
| `jwt` | Token validation | Unauthorized access |
| `acl` | Role-based access | Privilege escalation |
| `file-log` | Audit trail | Repudiation |

### Rate Limiting by Tier

```yaml
plugins:
  - name: rate-limiting
    config:
      minute: 100  # researcher
      policy: local
```

| Tier | Requests/Minute |
|------|---------------|
| Researcher | 100 |
| Government | 50 |
| Industry | 20 |

### Request Size Limit

```yaml
plugins:
  - name: request-size-limit
    config:
      allowed_payload_size: 100  # KB
      size_unit: kilobyte
```

### JWT Validation

```yaml
plugins:
  - name: jwt
    config:
      claims_to_verify:
        - exp
      key_claim_name: iss
```

### ACL (Role Enforcement)

```yaml
plugins:
  - name: acl
    config:
      allow:
        - researcher
        - government
        - industry
      hide_groups_header: false
```

## Usage

```bash
# Validate Kong config
deck validate -c infrastructure/kong/kong.yml

# Sync config to Kong
deck sync -c infrastructure/kong/kong.yml
```

## Testing

```bash
# Test rate limiting
curl -i -H "Authorization: Bearer $TOKEN" http://localhost:8000/query

# Test ACL
curl -i -H "Authorization: Bearer $TOKEN" http://localhost:8000/researchers
```

---

*deck validate passes; pytest covers each plugin.*
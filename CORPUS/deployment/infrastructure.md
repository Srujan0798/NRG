# POINTER: Infrastructure

> **Do not trust this file as the source of truth.** Read the actual files listed below.

## Where to Read

| Topic | Actual Source Files | What to Verify |
|-------|--------------------|----------------|
| **K8s** | `infrastructure/helm/` | Charts, manifests |
| **Kong** | `infrastructure/kong/` | Gateway config, JWT validation, rate limits |
| **Nginx** | `infrastructure/nginx/` | Reverse proxy, SSL, static files |
| **Monitoring** | `infrastructure/prometheus/`, `infrastructure/grafana/` | Metrics, dashboards, alerts |
| **Cron** | `infrastructure/cron/` | Scheduled jobs |

## Verification Commands

```bash
# Check helm charts
ls infrastructure/helm/

# Check kong config
ls infrastructure/kong/

# Check nginx config
ls infrastructure/nginx/

# Check monitoring
ls infrastructure/prometheus/ infrastructure/grafana/
```

**Read the actual source files. Do not trust this pointer.**

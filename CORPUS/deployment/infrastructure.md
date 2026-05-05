# NRG Infrastructure

## Sovereign Cluster (Production)

NRG deploys on a sovereign Kubernetes cluster (IIT-GN IT managed).

## Components

| Component | Path | Purpose |
|-----------|------|---------|
| **Kong** | `infrastructure/kong/` | API gateway, JWT validation, rate limiting |
| **Nginx** | `infrastructure/nginx/` | Reverse proxy, static file serving, SSL termination |
| **Helm** | `infrastructure/helm/` | K8s deployment charts |
| **Prometheus** | `infrastructure/prometheus/` | Metrics collection |
| **Grafana** | `infrastructure/grafana/` | Metrics dashboards |
| **Monitoring** | `infrastructure/monitoring/` | Alerts, SLO tracking |
| **Llama** | `infrastructure/llama/` | Local SLM deployment path (future) |

## Kong Gateway

- JWT validation at edge
- Rate limiting per tier
- Route to API service
- SSL certificate management

## Nginx

- Serves static frontend build
- Proxies API requests to Kong
- Handles SPA fallback routing
- Compression, caching headers

## Kubernetes

- Namespaced deployment
- HPA for API pods
- Persistent volumes for PostgreSQL
- Secrets for credentials
- ConfigMaps for app config

## Monitoring Stack

- **Prometheus:** Scrapes metrics from API, Kong, Nginx
- **Grafana:** Dashboards for latency, throughput, errors
- **Alerts:** P0 on SLO breach, P1 on error rate spike

## Security

- TLS 1.3 everywhere
- Network policies between namespaces
- Pod security standards
- Secrets encrypted at rest

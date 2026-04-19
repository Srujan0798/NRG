# Capacity Plan for NRG

## Executive Summary

NRG is designed to support India's research intelligence needs with sovereign compliance. This document outlines capacity planning for production deployment.

## Current Baseline

| Metric | Value |
|--------|-------|
| Max sustained QPS | 20 |
| p95 latency | < 10s |
| Database size | ~1 GB (200 researchers, 500 publications) |
| Vector index | ~500K chunks (estimated at full scale) |

## Per-University Estimate

Assuming 50 universities with concurrent access:

| Metric | Per University | Total (50) |
|--------|---------------|-----------|
| Concurrent users | 20 | 1,000 |
| Daily queries | 500 | 25,000 |
| Peak QPS | 5 | 250 |

## Node Count Requirements

### Current Staging (Minimum)

- API pods: 2 (min), 10 (max)
- LLM pods: 1 GPU node
- DB: 1 primary + 1 replica
- Qdrant: 1 node

### Production (50 universities)

- API pods: 10 (min), 50 (max)
- LLM pods: 3 GPU nodes (load balanced)
- DB: 1 primary + 2 read replicas
- Qdrant: 3-node cluster
- Redis: 3-node sentinel cluster

## Resource Requirements

| Component | CPU | Memory | Storage | Notes |
|-----------|-----|--------|---------|-------|
| API | 2 cores | 4 GB | - | Per pod |
| LLM | 8 cores | 24 GB VRAM | 50 GB | GPU required |
| Postgres | 4 cores | 16 GB | 500 GB | SSD recommended |
| Qdrant | 4 cores | 16 GB | 1 TB | Vector storage |
| Redis | 2 cores | 8 GB | 50 GB | Cache + sessions |

## Scaling Triggers

- Scale API when CPU > 70% or latency p95 > 10s
- Scale LLM when queue depth > 100
- Scale DB when connection pool > 80%

## Cost Estimate (Monthly)

| Component | Staging | Production |
|-----------|---------|-----------|
| Compute | ₹50,000 | ₹500,000 |
| GPU | ₹100,000 | ₹300,000 |
| Storage | ₹10,000 | ₹100,000 |
| **Total** | **₹160,000** | **₹900,000** |

## RTO/RPO

- RTO: 60 minutes
- RPO: < 1 hour
- Backup frequency: Hourly incremental, daily full

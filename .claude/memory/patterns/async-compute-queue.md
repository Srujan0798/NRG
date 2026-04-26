---
name: Async compute queue for SLURM/AIRAWAT (60s gateway timeout)
description: Sovereign HPC clusters (C-DAC AIRAWAT, SLURM-scheduled DGX-A100 nodes) queue jobs asynchronously. Government load balancers kill open HTTP at 60s. NRG must return 202+task-id and poll/WebSocket for completion.
type: feedback
---

When NRG is deployed on the sovereign cluster, inference jobs land on SLURM-scheduled DGX-A100 nodes (C-DAC AIRAWAT or equivalent). SLURM is a queue, not a synchronous service — jobs wait, run, return at unpredictable wall-clock latency. Synchronous HTTP request/response patterns from the FastAPI app to the inference node are fundamentally incompatible:

- Indian government load balancers (NIC, MeitY-spec ingress) terminate open HTTP connections at **60 seconds** by policy. There is no override.
- A SLURM-queued LLM inference job can wait 30-180s before a GPU is free. Sync HTTP returns `504 Gateway Timeout` long before the result is ready.
- The current `src/config/llm_config.py` mesh assumes synchronous provider calls. That works for cloud providers (OpenAI/Anthropic with their own internal queues). It will NOT work for self-hosted SLURM-scheduled inference.

**Required pattern for sovereign deploy:**

1. `/query` returns `202 Accepted` with `{ "task_id": "<uuid>", "poll_url": "/api/tasks/<uuid>" }` immediately.
2. Backend enqueues the inference job via Celery + Redis (or equivalent — RabbitMQ, NATS, AWS SQS-on-prem). Worker submits to SLURM via `sbatch`, captures the SLURM job id.
3. Frontend polls `/api/tasks/<uuid>` every 1-2s OR receives `/ws/tasks/<uuid>` WebSocket events. Mid-computation transparency (`ux_audit/protocol.md` §11.5 / §12) updates the user during the wait.
4. When SLURM job completes, worker writes result to Redis with TTL, marks task DONE, audit-binds the run.
5. Polling endpoint returns `200` with the full /query response shape (audit_event_id + sql_query + sql_results + answer_confidence) when DONE; `202` while RUNNING.

**Why:** A 504 mid-session ends the credibility test. The cluster is the only path to the 600 GB data and the 1000-user load proof; if NRG cannot run on it, none of LB-1..LB-7 evidence transfers.

**How to apply:**
- Master plan M1 (Infrastructure) acceptance must include "Celery + Redis broker deployed; SLURM `sbatch` worker tested end-to-end on staging cluster".
- New protocol when ready: **LB-9 — Async Compute Queue** (sketched, not yet promoted to file). Owner: devops + backend.
- Risk register Risk #24 covers the live failure mode (60s gateway kill).
- Local dev can keep the synchronous path; cluster deploy requires the async path. The mesh config picks the path based on `NRG_DEPLOY_TARGET=local|cluster`.
- The change touches the orchestration node interface — every node that calls an LLM provider must be `await`-friendly and not assume <60s wall-clock. Most are already async; verify with grep.

**Source:** The Principal Auditor 2026-04-26 (D2 §"Deployment Integration", D6 Risk #8, D7 GAP — async). Promoted 2026-04-26.

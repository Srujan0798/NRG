---
name: NetworkPolicy + WORM audit logs (egress control story)
description: Sovereignty proof needs more than HMAC chain. Kubernetes NetworkPolicy enforces zero-trust pod-to-pod traffic; WORM (Write Once Read Many) storage on the audit log makes it tamper-evident at the storage layer. Both are required to credibly answer "how do you know data didn't leave?".
type: feedback
---

The HMAC chain proves audit-event integrity (chain hash, per-user binding). It does NOT prove the data physically stayed inside the sovereign cluster, and it does not protect the audit log itself from a privileged operator with shell access who could `rm` or `truncate` the file. Two additional layers close that gap:

### 1. Kubernetes NetworkPolicy (zero-trust pod traffic)

- Default-deny ingress + egress on every namespace.
- Explicit allow rules per pod-pair: `nrg-api → postgres` (5432), `nrg-api → qdrant` (6333), `nrg-api → llm-mesh` (8080), `nrg-api → langfuse` (3000). Nothing else.
- `postgres` and `qdrant` pods have **zero egress to internet** — verified by exec-ing into the pod and confirming `curl https://google.com` times out.
- Cross-namespace traffic blocked unless explicitly listed.
- Government cluster ingress restricted to MeitY-approved IPs only via `LoadBalancer` annotation.
- Tested at deploy-time and continuously by `tests/security/test_network_policy.py` (uses kubectl exec to attempt forbidden connections).

### 2. WORM (Write Once Read Many) on the audit log

- Audit chain file (`.audit/chain.jsonl`) backed by S3-compatible object storage with **Object Lock in compliance mode** (or the Indian-cloud equivalent: NIC, Yotta, CtrlS all offer this).
- Retention period set to legal floor (DPDP §17(2) — 7 years for processing records).
- Once written, an object cannot be deleted or overwritten — even by the root account — for the retention period. Privileged shell access cannot tamper.
- Local `.audit/chain.jsonl` is a write-through cache; the WORM object store is the source of truth.
- `verify_chain()` cross-checks: each block of N events written to local also has a corresponding immutable object in WORM; missing objects = tampering attempt.
- Documented in `docs/security/AUDIT_WORM_GUARANTEES.md` (NEW, written by the agent that lands this).

**Why:** External reviewers ask the same compounding question every time: "what if a DBA / sysadmin / state actor with cluster shell access wants to remove evidence?" HMAC chain alone fails that test — the chain is just bytes on a disk the operator owns. WORM at the storage layer is the correct answer in compliance regimes (DPDP §17 retention + the equivalent of HIPAA / SOX / PCI-DSS).

**How to apply:**
- Master plan M1 (Infrastructure) acceptance must include: "NetworkPolicy applied; pod-to-pod allow-list verified; WORM-locked object storage configured for audit chain".
- Master plan M4 (Security Hardening) extends to: "test_network_policy.py exercises 10+ forbidden pod connections, all blocked".
- Audit chain rebuild script (`scripts/audit_rebuild.py`) MUST refuse to run if WORM source-of-truth and local cache disagree by more than the in-flight buffer; instead it pages on-call.
- Cross-reference Risk #2 (PII leak), Risk #6 (audit chain corruption), Risk #26 (HMAC desync) in `PRODUCTION_LAUNCH_RISK_REGISTER.md`.

**Source:** Principal Engineer & Product Auditor 2026-04-26 (Section 2). Promoted 2026-04-26.

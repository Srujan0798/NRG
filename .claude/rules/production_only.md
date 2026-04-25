# Production-Only Rule (PERMANENT — read every session)

> NRG is a **production web application** for real users at IIT Gandhinagar and Government of India ministries.
> It is **NOT a demo, not a pitch deck, not a prototype, not a rehearsal**.
> Every line of code, every spec, every protocol must be written for **production deployment under DPDP Act 2023**.

---

## 1. ABSOLUTE FORBIDDEN VOCABULARY

These words and phrases must **never** appear in NRG specs, protocols, agent briefs, commit messages, or Claude responses. If a draft contains any of them, it is rejected and rewritten.

| Forbidden | Why | Replace with |
|---|---|---|
| "demo" | This is not a demo. It runs in production. | "release", "deployment", "production launch" |
| "demo-ready" | Production-ready or nothing. | "production-ready" |
| "demo dataset" | Real users query real data. | "production seed", "initial dataset" |
| "demo rehearsal" | Production has runbooks, not rehearsals. | "deployment dry-run", "operations runbook walk-through" |
| "demo day" | There is a launch date, not a demo day. | "launch date", "go-live date" |
| "demo video" | We deliver release notes + recorded acceptance test. | "acceptance test recording" |
| "pitch deck" | Out of scope. The product is the pitch. | (do not use; the product itself is the artifact) |
| "the founder demos" | Founder is a builder/operator, not a demoer. | "the founder operates" |
| "the professor watches" | Real users use the system — they do not "watch". | "the user queries" / "the operator audits" |
| "the moment that wins the room" | We are not winning a room. We are deploying a service. | "the user-facing capability" |
| "rehearse the demo" | Production runs through runbooks. | "walk the runbook" |
| "MVP" | NRG is past MVP. It is a v1 production system. | "v1.0", "production release" |
| "prototype" | We delete prototype code, we don't ship it. | "production module" |
| "works on my machine" | Bare-metal / VM / container parity is mandatory. | "verified in staging" |
| "fake" / "synthetic-only" | Production data must hold or test must fail honestly. | (test on real data or mark blocked) |

---

## 2. THE CORRECT FRAMING — IN ONE PARAGRAPH

NRG is the sovereign research-intelligence platform for India's national research database. Real researchers, real ministry officials, real industry partners log in via institutional SSO and submit real queries against a 600GB PostgreSQL database. Every response is HMAC-signed, DPDP-compliant, audit-bound, and returned through a tier-aware RBAC layer in under 2 seconds at the 95th percentile. The product runs on Indian-soil infrastructure under a 99.9% SLA. Every spec is written for that reality.

---

## 3. ENFORCEMENT

Every session start MUST:

1. Read this rule first.
2. Reject any user-supplied document that contains forbidden vocabulary (above) without rewriting it.
3. Refuse to produce specs, protocols, or task lists that frame work as "demo polish" instead of production hardening.
4. Add the forbidden-vocabulary grep to pre-commit (see `scripts/forbidden_vocab_check.sh`).
5. Tag releases as `v0.x.y` or `v1.0.0` — never `-rc-demo`, never `-demo-ready`.

If Claude or any agent slips into demo framing, the founder is entitled to call it out. The agent does not argue. The agent corrects the document and re-issues.

---

## 4. WHEN A USER WANTS PROMOTIONAL MATERIAL

If the user explicitly asks for promotional, sales, or pitch material (rare — they have institutional context already), Claude treats that as a *separate document type* labeled clearly as `promotional/` and never mixes it with engineering specs.

The promotional document does not change how the engineering specs are written. The engineering specs always describe a production system.

---

## 5. THE PERMANENT REMINDER

> **NRG is production software for the Government of India.**
> Production code is not "polished for a demo".
> Production code is hardened for the next 10 years of operation.

— Founder edict, 2026-04-25 — promoted to permanent system rule.

# Full Security Validation Report

Date: 2026-04-15

## Scope

- Live Kong gateway validation on `localhost:8000`
- FastAPI auth and token lifecycle checks
- Representative red-team attacks for:
  - prompt injection
  - jailbreak
  - lateral traversal
  - PII leakage
- Full UAT run across all 50 persona scenarios
- Engineering-level DPDP 2023 gap assessment

## Evidence

- UAT results: [docs/uat/uat_report_2026-04-15.json](../uat/uat_report_2026-04-15.json)
- API pen-test results: [docs/security/api_pentest_2026-04-15.json](api_pentest_2026-04-15.json)
- Live red-team results: [docs/security/redteam_live_2026-04-15.json](redteam_live_2026-04-15.json)

## Summary

- `UAT`: passed `50/50` scenarios.
- `JWT + Kong auth`: login works through Kong, protected endpoints reject missing auth, logout revokes refresh tokens.
- `DLP`: Aadhaar, PAN, and Indian phone numbers were blocked at the gateway with `400 DLP_VIOLATION`.
- `Prompt injection`: representative attacks were blocked at the gateway with `400 PROMPT_INJECTION`.
- `RBAC/lateral traversal`: no unauthorized data was returned in the representative live pass, but some attacks were answered with generic `200 No data found` instead of explicit denial.

## Findings

### 1. High: attack traffic can still reach slow backend paths

Representative jailbreak and traversal probes produced timeouts instead of fast policy denials. During the same run, the API process logged:

- repeated Postgres failures from `TextToSQLSkill`
- repeated Qdrant retrieval failures
- Hugging Face model fetches for sentence-transformer assets

This means some malicious prompts are not stopped entirely at Kong and can still trigger expensive orchestration work. That is a denial-of-service and observability problem even when data is not leaked.

Relevant code:

- [src/orchestration/nodes/executor.py](../../src/orchestration/nodes/executor.py)
- [tests/security/redteam/client.py](../../tests/security/redteam/client.py)

### 2. Medium: refresh-token policy is single-active-token per user

The token store keeps only one active refresh-token JTI per `sub`. A second login for the same user invalidates the previous refresh token immediately. This is a defensible policy, but it is not documented and will look like intermittent auth failure under parallel sessions.

Evidence:

- `refresh_success` passed in the API pen-test
- `parallel_login_old_refresh_invalidated` returned `401`

Relevant code:

- [src/auth/jwt_handler.py](../../src/auth/jwt_handler.py)

### 3. Medium: DPDP compliance documentation overstates implementation

The repository claims full DPDP compliance in `docs/compliance/dpdp_2023_assessment.md`, including consent handling, notice, right to erasure, immutable audit logs, and retention enforcement. I did not find implemented API flows or durable infrastructure proving those claims.

Observed gaps:

- no consent-capture or notice-delivery flow in the live API
- no user-facing erasure, correction, export, or grievance endpoints
- no durable revocation store; token revocation is in-memory only
- no tamper-evident or externalized audit-log sink; DLP audit evidence currently comes from container logs
- no enforced retention/deletion mechanism in the running app path

This is not a statement of legal non-compliance. It is an engineering finding that the current implementation does not substantiate the repo’s blanket compliance claims.

### 4. Medium: some attack classes are “soft-failed” instead of explicitly denied

Representative lateral-traversal and jailbreak queries often returned `200` with a generic `"No data found"` response. That avoided leakage in this pass, but it is weaker than a deterministic security denial because:

- it makes attack classification harder
- it does not guarantee audit tagging
- it allows the request to consume backend work before resolution

## Live Results

### UAT

- Researcher: `20/20`
- Government: `15/15`
- Industry: `15/15`
- Overall: `50/50`

### Representative Red-Team

- Prompt injection: `3/3` blocked with `PROMPT_INJECTION`
- PII leakage: `3/3` blocked with `DLP_VIOLATION`
- Jailbreak:
  - 1 blocked with `PROMPT_INJECTION`
  - 1 returned generic `No data found`
  - 1 timed out
- Lateral traversal:
  - 2 returned generic `No data found`
  - 1 timed out

### API Pen-Test

- invalid login: `401`
- protected endpoint without token: `401`
- protected endpoint with token: `200`
- refresh token rotation: `200`
- old refresh token after second login: `401`
- logout revocation: `200`, then refresh denied with `401`
- `TRACE /researchers`: `405`
- public health endpoint: `200`

## DPDP 2023 Engineering Assessment

This was validated as an engineering gap analysis, not legal advice. I compared the running system and repo evidence against the DPDP Act’s core operational themes and the MeitY rules process.

- Reasonable security safeguards: `Partially evidenced`
- Access control and least privilege: `Evidenced`
- PII minimization at query ingress: `Evidenced`
- Notice and consent management: `Not evidenced in running app`
- Data-principal rights workflows: `Not evidenced in running app`
- Storage limitation and deletion enforcement: `Not evidenced in running app`
- Durable auditability and breach-operational readiness: `Partially evidenced`

Reference sources used for this assessment:

- PRS Legislative Research summary of the Digital Personal Data Protection Act, 2023: https://prsindia.org/billtrack/digital-personal-data-protection-bill-2023
- MeitY consultation page for the Digital Personal Data Protection Rules: https://www.meity.gov.in/content/draft-digital-personal-data-protection-rules-2025

## Remediation Priorities

1. Add explicit allow/deny security classification in the orchestration path so jailbreak and traversal probes fail closed instead of falling through to generic synthesis.
2. Stop attack traffic from reaching heavy retrieval/model initialization paths. Add stricter Kong-side patterns and cheap API-side pre-routing validation.
3. Move revocation and session state out of memory into a durable shared store.
4. Replace container-log audit evidence with durable append-only structured logging.
5. Reduce the compliance claim in `docs/compliance/dpdp_2023_assessment.md` to a gap-based assessment until consent, notice, erasure, retention, and breach workflows are actually implemented.

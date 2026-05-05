> **DEPRECATED FORMAT:** This protocol uses the old ═══ format.
> **Current format:** Use `.claude/assignment_template.md` for all new assignments.

═══════════════════════════════════════════════════════════════
TASK: #35 — THE NON-REPUDIATION LOCK
AGENT: backend / security
PRIORITY: P0-blocker (Quality Bar Constraint #2)
═══════════════════════════════════════════════════════════════

FILES:
  - src/audit/__init__.py (AuditLogger.log_event — add per-user binding)
  - src/audit/per_user_keys.py (NEW — key derivation)
  - src/auth/jwt_handler.py (expose jti + kid for audit binding)
  - src/api/main.py (pass user_id + jti + request_fingerprint to logger)
  - tests/security/test_audit_chain.py (extend — per-user verify)
  - tests/security/test_non_repudiation.py (NEW — 10+ scenarios)
  - .claude/QUALITY_BAR.md (Constraint #2 reference)

PROBLEM:
  HMAC chain is tamper-proof at chain level, but a stolen JWT lets an attacker impersonate a user.
  Current audit events carry action + timestamp + HMAC — NO per-user binding. Non-repudiation
  (proving THIS user took THIS action at THIS time, undeniable) is broken.

ACTION:
  Phase 1 — FORTIFY: Per-user signing key derivation
    1a. Create src/audit/per_user_keys.py with `derive_user_key(user_id, jwt_kid, salt) -> bytes`.
        Use HKDF-SHA256: master_key = HMAC_SK. Derive per-user key = HKDF(master, info=user_id+kid, salt=rotating_salt).
    1b. Rotating salt stored in env (AUDIT_ROTATING_SALT) + versioned for rotation.
    1c. Cache derived keys (LRU, max 10k entries) to avoid HKDF per event.
  
  Phase 2 — ELEVATE: Multi-party attestation + request fingerprint
    2a. Extend AuditEvent schema with fields: user_id, persona, jwt_jti, request_fingerprint
        (IP + UA + TLS session hash), api_signature, db_signature.
    2b. API layer signs event with api_master_key. DB layer (audit write) signs with db_master_key.
        verify_chain() validates BOTH signatures — tampering from either side detected.
    2c. Request fingerprint: hash(ip + user_agent + tls_session_id) — optional but logged for forensics.
    2d. All auth-ful endpoints in src/api/main.py must pass user_id + jti to AuditLogger.
  
  Phase 3 — IMMORTALIZE: Verification + forensics
    3a. verify_chain() returns 4-tuple: (valid_chain, valid_per_user, valid_multi_party, errors).
    3b. Add scripts/audit_forensics.py — query audit events by user_id + time range, verify
        per-user signatures, flag discrepancies.
    3c. tests/security/test_non_repudiation.py covers:
        - Event with valid user + valid signature → accepted
        - Event with stolen JWT (wrong jti) → rejected
        - Event tampered at API layer (bad api_sig) → rejected
        - Event tampered at DB layer (bad db_sig) → rejected
        - Salt rotation: old events still verify with old salt version
        - Request fingerprint mismatch → flagged (not blocked, logged for review)

SKILLS TO USE:
  - /security-auditor — HMAC/HKDF patterns, key rotation, attestation design
  - /python-backend — LRU cache, async patterns, API integration
  - /testing-strategy — Adversarial test design, 10+ non-repudiation scenarios
  - /code-review-and-quality — Self-review before submitting

ACCEPTANCE CRITERIA:
  - [ ] Every audit event carries (user_id, persona, jti, fingerprint, api_sig, db_sig)
  - [ ] derive_user_key() produces stable output for (user, kid, salt) triple
  - [ ] Salt rotation supported (events with old salt still verify)
  - [ ] verify_chain() rejects events with broken per-user OR multi-party signatures
  - [ ] All endpoints pass user_id + jti to AuditLogger (grep-verified, zero missed)
  - [ ] tests/security/test_non_repudiation.py — 10+ scenarios all pass
  - [ ] Quality Bar Constraint #2 compliance score: 8+/10

BEFORE COMMIT:
  - Run /pre-commit
  - Run /security-auditor on the changes
  - Verify no PII in audit logs (persona name ok, no raw email/phone)
  - Report Quality Bar compliance delta

GURU ASSIGNMENT NOTE:
  The HMAC chain we built in #9 is strong but insufficient. A stolen JWT — from phishing,
  session hijacking, XSS, or any compromise — lets an attacker do anything as that user,
  and the audit log says it WAS that user. No way to prove otherwise. For a sovereign
  platform serving government + research data, non-repudiation is not optional. DPDP 2023
  expects accountability per individual. Courts expect forensic evidence. This protocol
  closes the audit forgery window. After this, every action is cryptographically bound
  to a specific user + specific JWT + specific request context. Stolen JWT? We know.
  Tampered DB? We know. Tampered API call? We know.

AGENT INSTRUCTIONS (verbatim):
  - Read .agents/AGENTS.md, shishya_universal.md
  - Read every SKILL.md listed above
  - Read .claude/QUALITY_BAR.md — this closes Constraint #2
  - Read .claude/NRG_CONSTITUTION.md §9 (Per-User Non-Repudiation)
  - Fortify → Elevate → Immortalize
  - /pre-commit before committing

DEPENDS ON: #19 (security tests green baseline)
═══════════════════════════════════════════════════════════════
